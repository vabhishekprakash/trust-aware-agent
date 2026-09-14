"""Recount behind measurement-integrity entry 4: what "roughly halves the error rate" could have come from.

Usage:
    python scripts/integrity_entry4_recount.py     # writes reports/integrity-entry4-recount.md and .json

Post hoc, 2026-09-14, dev only. The M4 reading said that answering the most
confident half of the decisive stratum (answerable items with the evidence
retrieved) roughly halved the error rate. The correction at the time cited the
tie-aware curve over all 70 answered items. This reads the committed
out-of-fold probabilities and reports, inside the decisive stratum, the error
among the most confident half for each fitted variant: tie-aware (every item
tied at the boundary covered together, so a real threshold can reach it) and
rank-ordered (ties split in file order, which no threshold can reach).
Nothing is refit and no test item is read.
"""

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OOF = ROOT / "reports" / "m4-calibration-oof.jsonl"
OUT = ROOT / "reports" / "integrity-entry4-recount"
VARIANTS = [("full", "logistic"), ("full", "logistic+isotonic"), ("minus_logprobs", "logistic"), ("minus_logprobs", "logistic+isotonic")]


def tie_aware_rows(probs, labels):
    """Coverage and error at every threshold a real policy can set (ties covered together)."""
    rows = []
    for t in sorted(set(probs), reverse=True):
        covered = probs >= t
        rows.append({"threshold": float(t), "covered": int(covered.sum()), "errors": int((labels[covered] == 0).sum())})
    return rows


def boot_error_at(probs, labels, threshold, n_boot=1000, seed=42):
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(probs), len(probs))
        p, y = probs[idx], labels[idx]
        c = p >= threshold
        if c.sum():
            vals.append(float((y[c] == 0).mean()))
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def main() -> int:
    rows = [json.loads(l) for l in OOF.read_text(encoding="utf-8").splitlines() if l.strip()]
    decisive = [r for r in rows if r["strata"]["bucket"] == "answerable" and r["strata"]["evidence_retrieved"]]
    labels = np.array([r["label"] for r in decisive])
    n, base_errors = len(decisive), int((labels == 0).sum())
    half = n // 2
    result = {"population": "decisive stratum: answerable items with the evidence retrieved, dev, out-of-fold probabilities", "items": n,
              "errors": base_errors, "base_error": base_errors / n, "half": half, "variants": []}
    for vec, fit in VARIANTS:
        probs = np.array([r[vec][fit] for r in decisive])
        order = sorted(range(n), key=lambda i: -probs[i])  # stable: ties keep file order
        rank_errors = int(sum(labels[i] == 0 for i in order[:half]))
        rows_t = tie_aware_rows(probs, labels)
        near = min(rows_t, key=lambda x: (abs(x["covered"] - half), x["covered"]))
        lo, hi = boot_error_at(probs, labels, near["threshold"])
        result["variants"].append({"vector": vec, "fit": fit, "distinct_values": int(len(set(probs))),
                                   "rank_ordered_top_half": {"covered": half, "errors": rank_errors, "error": rank_errors / half},
                                   "tie_aware_nearest_half": {**near, "error": near["errors"] / near["covered"], "error_interval": [lo, hi]}})
    OUT.with_suffix(".json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8", newline="\n")
    pct = lambda x: f"{100 * x:.0f}"
    lines = ["# Integrity entry 4: the halving figure, recounted", "",
             "Post hoc, 2026-09-14, dev only, from reports/m4-calibration-oof.jsonl. Nothing refit, no test item read.", "",
             f"Population: {result['population']}. {n} items, {base_errors} errors, base error {pct(result['base_error'])} percent. "
             f"The most confident half is {half} items.", "",
             "| vector | fit | distinct values | rank-ordered top half: errors, error % | tie-aware threshold nearest half: covered, errors, error % [95% interval] |",
             "|---|---|---|---|---|"]
    for v in result["variants"]:
        r, t = v["rank_ordered_top_half"], v["tie_aware_nearest_half"]
        lines.append(f"| {v['vector']} | {v['fit']} | {v['distinct_values']} | {r['errors']} of {r['covered']}, {pct(r['error'])} | "
                     f"{t['covered']}, {t['errors']}, {pct(t['error'])} [{pct(t['error_interval'][0])}, {pct(t['error_interval'][1])}] |")
    lines += ["", "Rank-ordered splits ties in file order, which no threshold can do; tie-aware covers every item tied at the boundary.",
              "The confirmed calibrator is minus_logprobs with logistic+isotonic. The bootstrap resamples items (1000, seed 42) at the fixed threshold."]
    OUT.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
