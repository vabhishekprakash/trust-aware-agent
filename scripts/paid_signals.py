"""Run the paid signals over a run's traces: log-probabilities, verbalized confidence, sampling.

Usage:
    python scripts/paid_signals.py --traces data/traces/dev-v1check --only logprobs
    python scripts/paid_signals.py --traces data/traces/dev-v1check          # all three, in cost order

For each trace the draft call's messages are rebuilt exactly (same system
prompt, same passages in the same order, same question) and:
  logprobs    regenerates the draft at temperature 0 with logprobs on and
              stores the raw token sequence, checking the text against the
              trace's draft;
  verbalized  continues the draft conversation with one question asking
              for a number from 0 to 100, passages still in view, raw reply
              stored;
  samples     draws k drafts at temperature 0.7 with seeds 1..k and stores
              them raw.
Records go to <traces>-signals/<id>.json; a manifest records seconds per
item per signal and how many calls came from the cache. The test split is
refused.
"""

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from agent.loop import draft_messages  # noqa: E402
from agent.provider import OllamaProvider  # noqa: E402
from agent.retriever import Hit, load_chunks  # noqa: E402
from signals.verbalized import confidence_messages  # noqa: E402

SIGNALS = ("logprobs", "verbalized", "samples")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--traces", required=True)
    parser.add_argument("--only", choices=SIGNALS, action="append", default=[])
    parser.add_argument("--model", default="qwen2.5:3b-instruct")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--temperature", type=float, default=0.7)
    args = parser.parse_args()
    if "test" in Path(args.traces).name:
        print("refusing to read the test split")
        return 1
    wanted = args.only or list(SIGNALS)

    trace_dir = Path(args.traces)
    out_dir = trace_dir.parent / (trace_dir.name + "-signals")
    out_dir.mkdir(parents=True, exist_ok=True)
    run = json.loads((trace_dir / "_run.json").read_text(encoding="utf-8"))
    by_id = {c["id"]: c for c in load_chunks(ROOT / "data" / "corpus" / "chunks.jsonl")}
    provider = OllamaProvider(model=args.model, cache_dir=ROOT / "data" / "cache", num_ctx=4096)
    manifest_path = out_dir / "_signals.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"model": args.model, "signals": {}}

    for signal in wanted:
        started = time.time()
        cached = 0
        for n, item_id in enumerate(run["ids"], start=1):
            trace = json.loads((trace_dir / f"{item_id}.json").read_text(encoding="utf-8"))
            record_path = out_dir / f"{item_id}.json"
            record = json.loads(record_path.read_text(encoding="utf-8")) if record_path.exists() else {"item_id": item_id}
            hits = [Hit(by_id[h["id"]], h["score"]) for h in trace["retrieval"]]
            messages = draft_messages(trace["question"], hits, trace.get("premise_check", False))
            draft = trace["draft"]["raw"]
            item_started = time.time()
            if signal == "logprobs":
                g = provider.generate(messages, temperature=0.0, seed=trace["seed"], max_tokens=160, logprobs=True, top_logprobs=0)
                record["logprobs"] = {"text": g.text.strip(), "same_text": g.text.strip() == draft, "tokens": g.tokens, "logprobs": g.logprobs,
                                      "cached": g.cached, "seconds": round(time.time() - item_started, 2)}
                cached += int(g.cached)
                shown = f"same_text={record['logprobs']['same_text']} tokens={len(g.logprobs or [])}"
            elif signal == "verbalized":
                g = provider.generate(confidence_messages(messages, trace["draft"]["final"]), temperature=0.0, seed=trace["seed"], max_tokens=12)
                record["verbalized"] = {"reply": g.text.strip(), "sees_passages": True, "cached": g.cached, "seconds": round(time.time() - item_started, 2)}
                cached += int(g.cached)
                shown = f"reply={g.text.strip()!r}"
            else:
                samples = []
                for seed in range(1, args.k + 1):
                    g = provider.generate(messages, temperature=args.temperature, seed=seed, max_tokens=160)
                    samples.append({"seed": seed, "text": g.text.strip(), "cached": g.cached})
                    cached += int(g.cached)
                record["samples"] = {"temperature": args.temperature, "k": args.k, "texts": samples, "seconds": round(time.time() - item_started, 2)}
                shown = f"k={args.k} first={samples[0]['text'][:60]!r}"
            record_path.write_text(json.dumps(record, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
            print(f"{n:>3} {item_id} {signal:<10} {time.time() - item_started:5.1f}s {shown}", flush=True)
        wall = time.time() - started
        manifest["signals"][signal] = {"items": len(run["ids"]), "wall_seconds": round(wall, 1), "seconds_per_item": round(wall / len(run["ids"]), 2),
                                       "cached_calls": cached, "k": args.k if signal == "samples" else None}
        manifest_path.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8", newline="\n")
        print(f"\n{signal}: {wall:.0f}s for {len(run['ids'])} items, {wall / len(run['ids']):.1f}s per item, cached calls {cached}\n", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
