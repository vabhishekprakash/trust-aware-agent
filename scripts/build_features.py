"""Build the feature table for a graded run: free signals only, with provenance.

Usage:
    python scripts/build_features.py --traces data/traces/dev-v1check data/traces/dev-reserve \
        --rows reports/dev-run-v1b.jsonl reports/dev-run-reserve.jsonl --out reports/features-dev

Reads each item's trace (for the features) and its graded row (for the
label). Features come from the run only; the item-record fields the trace
also carries (evidence block, bucket, calculator flags) go into a separate
strata block for reporting and never into the features. Writes
<out>.jsonl (one row per item: item_id, source, label, strata, features)
and <out>.md (the provenance list with the inference-time statement, then
summary statistics per feature by label and by bucket). Refuses test.
"""

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from agent.retriever import bge_embedder, load_chunks, load_index  # noqa: E402
from signals.process import PROVENANCE as PROCESS_PROVENANCE  # noqa: E402
from signals.process import leaked_fields, process_features, stratum  # noqa: E402
from signals.retrieval_support import NLI_MODEL  # noqa: E402
from signals.retrieval_support import PROVENANCE as SUPPORT_PROVENANCE  # noqa: E402
from signals.retrieval_support import nli_model, support_features  # noqa: E402

BUCKETS = ("answerable", "ambiguous", "unanswerable", "false_premise")
EXCLUDED = {
    "evidence.retrieved, evidence.rank, evidence.page_retrieved": "computed from the item's gold evidence quote",
    "bucket": "the item's label bucket",
    "needs_calculator, spurious_calc": "the item's calculator flag and a flag derived from it",
    "gold_answer, gold_aliases, readings, premise_fix, expected": "the item's reference answer and expected action",
}


def mean_sd(values):
    if not values:
        return "n=0"
    if len(values) == 1:
        return f"{values[0]:.3f}"
    return f"{statistics.mean(values):.3f} (sd {statistics.stdev(values):.3f})"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--traces", nargs="+", required=True)
    parser.add_argument("--rows", nargs="+", required=True)
    parser.add_argument("--out", default=str(ROOT / "reports" / "features-dev"))
    parser.add_argument("--no-nli", action="store_true")
    args = parser.parse_args()
    if any("test" in Path(p).name for p in args.traces + args.rows):
        print("refusing to read the test split")
        return 1

    chunks = load_chunks(ROOT / "data" / "corpus" / "chunks.jsonl")
    by_id = {c["id"]: c for c in chunks}
    embed = bge_embedder()
    index = load_index(ROOT / "data" / "index", chunks, embed)
    if index is None:
        print("no index for the current chunks; run scripts/build_index.py first")
        return 1
    vector_of = {c["id"]: index.vectors[i] for i, c in enumerate(chunks)}
    nli = None if args.no_nli else nli_model()
    if nli is None:
        print(f"NLI model {NLI_MODEL} not available; entailment features left out", flush=True)

    out_rows = []
    for trace_dir, rows_path in zip(args.traces, args.rows):
        source = Path(trace_dir).name
        rows = {json.loads(l)["item_id"]: json.loads(l) for l in Path(rows_path).read_text(encoding="utf-8").splitlines() if l.strip()}
        for item_id, row in rows.items():
            trace = json.loads((Path(trace_dir) / f"{item_id}.json").read_text(encoding="utf-8"))
            assert trace["response"] == row["response"], f"{item_id}: trace and graded row differ"
            ids = [h["id"] for h in trace["retrieval"]]
            features = process_features(trace)
            features.update(support_features(trace["response"], [by_id[i]["text"] for i in ids], embed=embed,
                                             chunk_vectors=np.stack([vector_of[i] for i in ids]), nli=nli))
            out_rows.append({"item_id": item_id, "source": source, "label": row["grade"]["label"], "grade": row["grade"]["grade"],
                             "strata": stratum(trace), "leaked_fields_present_in_trace": leaked_fields(trace), "features": features})
            print(f"{item_id} {trace['bucket']:<14} label={row['grade']['label']} " + " ".join(f"{k}={v}" for k, v in list(features.items())[-5:]), flush=True)

    out = Path(args.out)
    with out.with_suffix(".jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for r in out_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    names = list(out_rows[0]["features"].keys())
    provenance = {**PROCESS_PROVENANCE, **SUPPORT_PROVENANCE}
    lines = ["# Feature table, dev, free signals only", "",
             f"{len(out_rows)} items from {', '.join(Path(t).name for t in args.traces)}; labels from the graded rows (1 = CORRECT). "
             "Every feature below is computed from the agent's own run: the trace it wrote and the texts of the chunks it retrieved. "
             "Each is computable at inference time on a question with no known answer, because none reads the item record. "
             "The strata block kept next to the features (bucket, evidence retrieved, rank, calculator flag) is ground truth for reporting only.",
             "", "## Excluded from the features, ground truth", ""]
    for k, why in EXCLUDED.items():
        lines.append(f"- {k}: {why}.")
    lines += ["", "## Provenance and the inference-time statement", "", "| feature | comes from | at inference time |", "|---|---|---|"]
    for n in names:
        lines.append(f"| {n} | {provenance.get(n, '?')} | yes, from the run |")
    decisive = [r for r in out_rows if r["strata"]["bucket"] == "answerable" and r["strata"]["evidence_retrieved"]]
    lines += ["", "## Mean by label (1 = CORRECT), pooled and in the decisive stratum, then by bucket", "",
              f"Pooled means mix the buckets, and the buckets differ in label rate, so a pooled gap can be a bucket difference. "
              f"The decisive stratum is answerable items with the evidence retrieved, {sum(r['label'] for r in decisive)} right against "
              f"{len(decisive) - sum(r['label'] for r in decisive)} wrong here, where retrieval is held fixed and the model's judgement decides.", "",
              "| feature | pooled label 1 | pooled label 0 | decisive label 1 | decisive label 0 | " + " | ".join(BUCKETS) + " | constant? |",
              "|---|---|---|---|---|" + "---|" * len(BUCKETS) + "---|"]
    for n in names:
        by_label = defaultdict(list)
        by_bucket = defaultdict(list)
        by_decisive = defaultdict(list)
        for r in out_rows:
            v = r["features"].get(n)
            if v is None:
                continue
            by_label[r["label"]].append(float(v))
            by_bucket[r["strata"]["bucket"]].append(float(v))
            if r in decisive:
                by_decisive[r["label"]].append(float(v))
        all_values = by_label[0] + by_label[1]
        constant = "yes" if len(set(all_values)) <= 1 else ""
        lines.append(f"| {n} | {mean_sd(by_label[1])} | {mean_sd(by_label[0])} | {mean_sd(by_decisive[1])} | {mean_sd(by_decisive[0])} | "
                     + " | ".join(mean_sd(by_bucket[b]) for b in BUCKETS) + f" | {constant} |")
    missing = [n for n in provenance if n not in names]
    if missing:
        lines += ["", f"Not computed in this table: {', '.join(missing)}."]
    constant_names = [n for n in names if len({r["features"].get(n) for r in out_rows}) <= 1]
    lines += ["", "A gap between the decisive-stratum label columns is the signal that matters. A gap between the bucket columns says the feature may be a bucket detector; the M4 test decides."
              + (f" Constant on dev, to be dropped at M4: {', '.join(constant_names)}." if constant_names else "")]
    out.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
