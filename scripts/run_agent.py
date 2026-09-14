"""Run the agent over dev items and write one trace per item.

Usage:
    python scripts/run_agent.py --ids q0004 q0100 --show q0004
    python scripts/run_agent.py --limit 2 --per-bucket
    python scripts/run_agent.py            # the whole dev split

Traces go to data/traces/dev/<id>.json. Each trace carries, on top of what
the loop records, the evidence block (target chunk ids, whether one was
retrieved and at what rank, whether the evidence page was covered), the
item's calculator flag and whether a CALC line was spurious. A run manifest
(_run.json in the same directory) records the wall clock, where the time
went by step, and how many calls came from the cache. --show prints one
trace in full. The test split is refused.
"""

import argparse
import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from agent.evidence import evidence_record  # noqa: E402
from agent.loop import TRACE_VERSION, Agent  # noqa: E402
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
    parser.add_argument("--out", default=str(TRACES))
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
    agent = Agent(provider, index, k=args.k)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    by_id = {c["id"]: c for c in chunks}

    started = time.time()
    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    actions = Counter()
    step_seconds = Counter()
    cached_calls = Counter()
    per_item = []
    for n, item in enumerate(items, start=1):
        trace = agent.run(item["question"], item_id=item["id"])
        trace["bucket"] = item["bucket"]
        trace["evidence"] = evidence_record(item, chunks, [by_id[r["id"]] for r in trace["retrieval"]])
        trace["needs_calculator"] = bool(item.get("needs_calculator"))
        trace["spurious_calc"] = bool(trace["draft"]["calc"]) and not trace["needs_calculator"]
        (out_dir / f"{item['id']}.json").write_text(json.dumps(trace, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        actions[(item["bucket"], trace["action"])] += 1
        step_seconds["retrieval"] += trace["retrieval_seconds"]
        for call in trace["calls"]:
            step_seconds[call["step"]] += call["seconds"]
            cached_calls[call["step"]] += int(call["cached"])
        per_item.append({"id": item["id"], "seconds": trace["seconds"]})
        ev = trace["evidence"]
        print(f"{n:>3} {item['id']} {item['bucket']:<14} {trace['action']:<8} clarify={trace['clarify_by'] or '-':<6} abstain={trace['abstain_by'] or '-':<6} "
              f"best={trace['best_score']:.3f} evidence={'rank ' + str(ev['rank']) if ev['retrieved'] else ('page' if ev['page_retrieved'] else 'no'):<7} "
              f"readings={len(trace['readings']['parsed'])} calc={len(trace['draft']['calc'])}{'!' if trace['spurious_calc'] else ''} {trace['seconds']:.0f}s", flush=True)

    wall = time.time() - started
    manifest = {
        "trace_version": TRACE_VERSION,
        "split": str(Path(args.split).relative_to(ROOT)) if Path(args.split).is_relative_to(ROOT) else args.split,
        "model": args.model,
        "k": args.k,
        "items": len(items),
        "ids": [i["id"] for i in items],
        "started_at": started_at,
        "wall_seconds": round(wall, 1),
        "seconds_by_step": {k: round(v, 1) for k, v in step_seconds.items()},
        "cached_calls_by_step": dict(cached_calls),
        "per_item_seconds": per_item,
        "actions": {f"{b}/{a}": c for (b, a), c in sorted(actions.items())},
    }
    (out_dir / "_run.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"\nactions: {manifest['actions']}\nwall clock {wall:.0f}s for {len(items)} items; by step {manifest['seconds_by_step']}; cached {manifest['cached_calls_by_step']}")
    if args.show:
        print(f"\n=== full trace {args.show} ===")
        print((out_dir / f"{args.show}.json").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
