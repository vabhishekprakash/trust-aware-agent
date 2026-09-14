"""Lock the evaluation set at 200 items and split it into dev and test, stratified by bucket, seed 42.

Usage:
    python scripts/lock_and_split.py [--total 200]

Targets (owner's approval of 2026-09-10): unanswerable 50, false premise 40,
ambiguous as many as survive, answerable takes the rest. Within each bucket
the items are drawn with the project seed from the candidates sorted by id,
then each bucket is split in half into dev and test with the same seed.
Writes data/eval/dev.jsonl and data/eval/test.jsonl with the split field set,
data/eval/items_locked.jsonl (both halves), data/eval/items_reserve.jsonl
(candidates not selected, for fixes), and reports/split-summary.md. Refuses
to run if dev.jsonl already exists, because the split is made once.
"""

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANDIDATES = ROOT / "data" / "eval" / "items_candidates.jsonl"
EVAL = ROOT / "data" / "eval"
SEED = 42
BUCKETS = ["answerable", "ambiguous", "unanswerable", "false_premise"]
FIXED = {"unanswerable": 50, "false_premise": 40}


def read_jsonl(path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def write_jsonl(path, rows):
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + ("\n" if rows else ""), encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--total", type=int, default=200)
    args = parser.parse_args()
    if (EVAL / "dev.jsonl").exists():
        print("data/eval/dev.jsonl exists; the split is made once. Remove it deliberately to redo.")
        return 1

    pool = read_jsonl(CANDIDATES)
    by = {b: sorted((r for r in pool if r["bucket"] == b), key=lambda r: r["id"]) for b in BUCKETS}
    target = dict(FIXED)
    target["ambiguous"] = len(by["ambiguous"])
    target["answerable"] = args.total - sum(target.values())
    for b in BUCKETS:
        if target[b] > len(by[b]):
            print(f"not enough {b}: need {target[b]}, have {len(by[b])}")
            return 1

    selected, reserve = [], []
    dev, test = [], []
    for b in BUCKETS:
        rng = random.Random(SEED)
        ids = [r["id"] for r in by[b]]
        chosen = set(rng.sample(ids, target[b]))
        picked = [r for r in by[b] if r["id"] in chosen]
        reserve.extend(r for r in by[b] if r["id"] not in chosen)
        rng = random.Random(SEED)
        order = [r["id"] for r in picked]
        rng.shuffle(order)
        half = len(order) // 2
        dev_ids = set(order[:half])
        for r in picked:
            r = dict(r)
            r["split"] = "dev" if r["id"] in dev_ids else "test"
            (dev if r["split"] == "dev" else test).append(r)
            selected.append(r)
    selected.sort(key=lambda r: r["id"])
    dev.sort(key=lambda r: r["id"])
    test.sort(key=lambda r: r["id"])
    write_jsonl(EVAL / "items_locked.jsonl", selected)
    write_jsonl(EVAL / "dev.jsonl", dev)
    write_jsonl(EVAL / "test.jsonl", test)
    write_jsonl(EVAL / "items_reserve.jsonl", sorted(reserve, key=lambda r: r["id"]))

    counts = {b: (sum(1 for r in dev if r["bucket"] == b), sum(1 for r in test if r["bucket"] == b)) for b in BUCKETS}
    lines = [
        "# Locked set and split",
        "",
        f"Locked on 2026-09-10 at {len(selected)} items from {len(pool)} candidates, seed {SEED}, stratified by bucket.",
        "Test items are read by exactly one script, once, at the end; nothing is tuned on them.",
        "",
        "    bucket           locked  dev  test  reserve",
    ]
    for b in BUCKETS:
        d, t = counts[b]
        lines.append(f"    {b:<16} {d + t:>6}  {d:>3}  {t:>4}  {sum(1 for r in reserve if r['bucket'] == b):>7}")
    lines.append(f"    {'total':<16} {len(selected):>6}  {len(dev):>3}  {len(test):>4}  {len(reserve):>7}")
    lines += ["", "Calculator items in the locked set: " + str(sum(1 for r in selected if r.get("needs_calculator"))) + ".", ""]
    (ROOT / "reports" / "split-summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
