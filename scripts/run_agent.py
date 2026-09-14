"""Run the agent over dev items and write one trace per item.

Usage:
    python scripts/run_agent.py --ids q0004 q0100 --show q0004
    python scripts/run_agent.py --limit 5 --per-bucket
    python scripts/run_agent.py            # the whole dev split

Traces go to data/traces/dev/<id>.json and a summary line per item is
printed: bucket, action, which path decided it, best retrieval score, and
whether any evidence chunk was retrieved. --show prints one trace in full.
The test split is refused.
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from agent.loop import Agent  # noqa: E402
from agent.provider import OllamaProvider  # noqa: E402
from agent.retriever import bge_embedder, load_chunks, load_index  # noqa: E402

TRACES = ROOT / "data" / "traces" / "dev"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--split", default=str(ROOT / "data" / "eval" / "dev.jsonl"))
    parser.add_argument("--ids", nargs="*", default=[])
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--per-bucket", action="store_true", help="take --limit items from each bucket")
    parser.add_argument("--show", default="", help="print this item's trace in full")
    parser.add_argument("--model", default="qwen2.5:3b-instruct")
    parser.add_argument("--k", type=int, default=8)
    parser.add_argument("--abstain-threshold", type=float, default=None)
    args = parser.parse_args()
    if "test" in Path(args.split).name:
        print("refusing to read the test split")
        return 1

    items = [json.loads(l) for l in Path(args.split).read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.ids:
        items = [i for i in items if i["id"] in set(args.ids)]
    elif args.limit and args.per_bucket:
        picked, seen = [], Counter()
        for i in items:
            if seen[i["bucket"]] < args.limit:
                picked.append(i)
                seen[i["bucket"]] += 1
        items = picked
    elif args.limit:
        items = items[: args.limit]

    chunks = load_chunks(ROOT / "data" / "corpus" / "chunks.jsonl")
    index = load_index(ROOT / "data" / "index", chunks, bge_embedder())
    if index is None:
        print("no index for the current chunks; run scripts/build_index.py first")
        return 1
    provider = OllamaProvider(model=args.model, cache_dir=ROOT / "data" / "cache", num_ctx=4096)
    agent = Agent(provider, index, k=args.k, abstain_threshold=args.abstain_threshold)
    TRACES.mkdir(parents=True, exist_ok=True)

    pages_of = {c["id"]: (c["page_start"], c["page_end"]) for c in chunks}
    actions = Counter()
    for item in items:
        trace = agent.run(item["question"], item_id=item["id"])
        trace["bucket"] = item["bucket"]
        evidence_pages = {str(e["page"]) for e in item.get("evidence", [])}
        trace["evidence_page_retrieved"] = any(
            str(pages_of[r["id"]][0]) in evidence_pages or str(pages_of[r["id"]][1]) in evidence_pages for r in trace["retrieval"]
        )
        (TRACES / f"{item['id']}.json").write_text(json.dumps(trace, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        actions[(item["bucket"], trace["action"])] += 1
        print(f"{item['id']} {item['bucket']:<14} {trace['action']:<8} clarify={trace['clarify_by'] or '-':<6} abstain={trace['abstain_by'] or '-':<6} "
              f"best={trace['best_score']:.3f} evidence_page={'yes' if trace['evidence_page_retrieved'] else 'no'} "
              f"readings={len(trace['readings']['parsed'])} calc={len(trace['draft']['calc'])} {trace['seconds']:.0f}s")
    print("\nactions:", dict(actions))
    if args.show:
        print(f"\n=== full trace {args.show} ===")
        print((TRACES / f"{args.show}.json").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
