"""Build the final blind grader check from real dev outputs: a sheet for the owner, a key kept aside.

Usage:
    python scripts/final_blind_check.py [--n 20] [--seed 42]

Draws n dev items, stratified by bucket in proportion, from the graded
dev rows (the agent's real responses), writes reports/final-blind-sheet.md
with question, reference and response in a shuffled order and no grades,
and data/eval/final_blind_key.jsonl with the grader's records. The owner
grades the sheet without opening the key; scripts/compare_grader_check.py
--sheet reports/final-blind-sheet.md --key data/eval/final_blind_key.jsonl
then reports agreement. Drawn from dev only, before the test read, so the
grader's sign-off number is not entangled with the test numbers.
"""

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from grader_check import reference_text  # noqa: E402

SHEET = ROOT / "reports" / "final-blind-sheet.md"
KEY = ROOT / "data" / "eval" / "final_blind_key.jsonl"
BUCKETS = ("answerable", "ambiguous", "unanswerable", "false_premise")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rows", nargs="+", default=[str(ROOT / "reports" / "dev-run-v1b.jsonl"), str(ROOT / "reports" / "dev-run-reserve.jsonl")])
    parser.add_argument("--items", nargs="+", default=[str(ROOT / "data" / "eval" / "dev.jsonl")])
    parser.add_argument("--n", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if any("test" in Path(p).name for p in args.rows + args.items):
        print("refusing to read the test split")
        return 1
    if SHEET.exists() and not args.force:
        print(f"{SHEET} exists and may hold the owner's grades; pass --force to rebuild")
        return 1
    items = {}
    for p in args.items:
        for l in Path(p).read_text(encoding="utf-8").splitlines():
            if l.strip():
                it = json.loads(l)
                items[it["id"]] = it
    rows = []
    for p in args.rows:
        rows += [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]
    by_bucket = defaultdict(list)
    for r in rows:
        by_bucket[r["bucket"]].append(r)
    rng = random.Random(args.seed)
    total = len(rows)
    quotas = {b: max(1, round(args.n * len(by_bucket[b]) / total)) for b in BUCKETS}
    while sum(quotas.values()) > args.n:
        quotas[max(quotas, key=quotas.get)] -= 1
    while sum(quotas.values()) < args.n:
        quotas["answerable"] += 1
    picked = []
    for b in BUCKETS:
        picked += rng.sample(by_bucket[b], quotas[b])
    rng.shuffle(picked)

    KEY.parent.mkdir(parents=True, exist_ok=True)
    with KEY.open("w", encoding="utf-8", newline="\n") as f:
        for n, r in enumerate(picked, start=1):
            rec = dict(r["grade"])
            rec.update(sheet_no=n, item_id=r["item_id"], question=r["question"], draft=r["response"], condition="agent_output",
                       reference=reference_text(items[r["item_id"]]), bucket=r["bucket"], action=r["action"])
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    lines = ["# Final blind grader check: real agent outputs from dev", "",
             f"{len(picked)} outputs of the agent on development questions ({', '.join(f'{b} {quotas[b]}' for b in BUCKETS)}), in a shuffled order. "
             "Grade each CORRECT, PARTIAL or WRONG by the rules in docs/annotation-guide.md and write it after 'grade:'. A clarifying question that names both "
             "readings of an ambiguous item is CORRECT; a bare abstention on a false premise is PARTIAL. Do not open data/eval/final_blind_key.jsonl until the "
             "sheet is done. scripts/compare_grader_check.py reports the agreement; that number is the grader's signed-off figure in the report.", ""]
    for n, r in enumerate(picked, start=1):
        lines += [f"### {n}", "", f"question: {r['question']}", ""]
        lines += [f"reference: {line}" for line in reference_text(items[r["item_id"]])]
        lines += ["", f"output: {r['response']}", "", "grade:", ""]
    SHEET.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"sheet: {SHEET}\nkey: {KEY}\nquotas: {quotas}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
