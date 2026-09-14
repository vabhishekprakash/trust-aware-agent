"""Measure what grader v7 costs per draft, from the cached judge calls of the grader check.

Usage:
    python scripts/grader_cost.py [--items data/eval/items_candidates.jsonl] [--samples 5] [--n-items 200]

For every record in data/eval/grader_check_key.jsonl the script replays the
grader's call sequence against the disk cache only (no model is called):
the two yes-or-no calls, then one copying call per YES that code could not
ground. Each cached reply carries Ollama's own timing, so the per-draft judge
time is the sum of total_duration over those calls. Model load time is shown
separately because it is paid once per model switch, not per call. The draft
generation time comes from the cached calls of the model under test.
"""

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from agent.provider import OllamaProvider  # noqa: E402
from calibration.grader import (  # noqa: E402
    build_extraction_messages,
    build_judge_messages,
    code_quote,
    parse_answers,
    questions_for,
)

KEY = ROOT / "data" / "eval" / "grader_check_key.jsonl"


def cache_only(url, body):
    raise RuntimeError("cache miss: the grader check must have been run with this grader version")


def seconds(raw: dict, key: str) -> float:
    return (raw.get(key) or 0) / 1e9


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--items", default=str(ROOT / "data" / "eval" / "items_candidates.jsonl"))
    parser.add_argument("--judge", default="llama3.1:latest")
    parser.add_argument("--model", default="qwen2.5:3b-instruct")
    parser.add_argument("--samples", type=int, default=5)
    parser.add_argument("--n-items", type=int, default=200)
    args = parser.parse_args()

    items = {r["id"]: r for r in (json.loads(l) for l in Path(args.items).read_text(encoding="utf-8").splitlines() if l.strip())}
    records = [json.loads(l) for l in KEY.read_text(encoding="utf-8").splitlines() if l.strip()]
    cache = ROOT / "data" / "cache"
    judge = OllamaProvider(model=args.judge, cache_dir=cache, transport=cache_only)

    per_draft, calls_per_draft, load = [], [], []
    rule_decided = 0
    misses = 0
    for r in records:
        if r["decided_by"] != "judge":
            rule_decided += 1
            continue
        item = items.get(r["item_id"])
        if item is None:
            misses += 1
            continue
        keys = [k for k, _ in questions_for(item)]
        total, calls = 0.0, 0
        try:
            for order in ("reference_first", "candidate_first"):
                g = judge.generate(build_judge_messages(item, r["draft"], order), temperature=0.0, seed=42, max_tokens=200)
                total += seconds(g.raw, "total_duration") - seconds(g.raw, "load_duration")
                load.append(seconds(g.raw, "load_duration"))
                calls += 1
                parsed = parse_answers(keys, g.text)
                if parsed is None:
                    continue
                answers, _, _ = parsed
                for key, value in answers.items():
                    if value and code_quote(item, r["draft"], key) is None:
                        e = judge.generate(build_extraction_messages(item, r["draft"], key), temperature=0.0, seed=42, max_tokens=200)
                        total += seconds(e.raw, "total_duration") - seconds(e.raw, "load_duration")
                        load.append(seconds(e.raw, "load_duration"))
                        calls += 1
        except RuntimeError:
            misses += 1
            continue
        per_draft.append(total)
        calls_per_draft.append(calls)

    # draft generation time: every cached call of the model under test
    gen = []
    for path in cache.glob("*/*.json"):
        stored = json.loads(path.read_text(encoding="utf-8"))
        if stored.get("request", {}).get("model") == args.model and "Handbook" in json.dumps(stored["request"]["messages"]):
            raw = stored["response"]
            gen.append(seconds(raw, "total_duration") - seconds(raw, "load_duration"))

    judged = len(per_draft)
    n_drafts = args.n_items * args.samples
    share_judged = judged / max(1, judged + rule_decided)
    mean_judge = statistics.mean(per_draft) if per_draft else 0.0
    mean_gen = statistics.mean(gen) if gen else 0.0
    print(f"grader check records: {len(records)}; decided by rules or exact match: {rule_decided}; "
          f"judged: {judged}; not replayable from cache: {misses}")
    if per_draft:
        print(f"judge seconds per judged draft (model load excluded): mean {mean_judge:.1f}, median {statistics.median(per_draft):.1f}, "
              f"min {min(per_draft):.1f}, max {max(per_draft):.1f}")
        print(f"judge calls per judged draft: mean {statistics.mean(calls_per_draft):.2f}, max {max(calls_per_draft)}")
    if load:
        print(f"model load time seen on judge calls: total {sum(load):.0f} s over {sum(1 for x in load if x > 1)} loads")
    if gen:
        print(f"draft generation seconds per draft ({args.model}, {len(gen)} cached calls): mean {mean_gen:.1f}, median {statistics.median(gen):.1f}")
    print(f"\nprojection for {args.n_items} items x {args.samples} samples = {n_drafts} drafts:")
    print(f"  share of drafts reaching the judge (from this check): {100 * share_judged:.0f} percent")
    judge_hours = n_drafts * share_judged * mean_judge / 3600
    gen_hours = n_drafts * mean_gen / 3600
    print(f"  judge time: {judge_hours:.1f} h; draft generation: {gen_hours:.1f} h; together about {judge_hours + gen_hours:.1f} h")
    print(f"  if every draft reached the judge: {n_drafts * mean_judge / 3600:.1f} h of judge time")
    print("  model switching between the judge and the model under test adds load time; grade in one pass per model to avoid it")
    return 0


if __name__ == "__main__":
    sys.exit(main())
