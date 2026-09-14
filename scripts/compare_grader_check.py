"""Report judge agreement with the owner's blind grades from the filled-in grader check sheet.

Usage:
    python scripts/compare_grader_check.py [--sheet reports/grader-check-sheet.md]

Reads each '### n' block's 'grade:' line from the sheet, joins it to the machine
record with the same sheet number in data/eval/grader_check_key.jsonl, and prints
agreement on the binary label (CORRECT = 1, anything else = 0), agreement on the
three-way grade, and the disagreements one per line. The bar the owner set is
about 90 percent binary agreement before mass grading.
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEY = ROOT / "data" / "eval" / "grader_check_key.jsonl"
GRADES = {"CORRECT", "PARTIAL", "WRONG"}


def read_sheet(path: Path) -> dict:
    owner = {}
    current = None
    for line in path.read_text(encoding="utf-8").splitlines():
        head = re.match(r"^###\s+(\d+)\s*$", line)
        if head:
            current = int(head.group(1))
            continue
        body = re.match(r"^grade:\s*(\S+)?", line, re.IGNORECASE)
        if body and current is not None:
            value = (body.group(1) or "").upper().strip(".,;")
            if value in GRADES:
                owner[current] = value
    return owner


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sheet", default=str(ROOT / "reports" / "grader-check-sheet.md"))
    args = parser.parse_args()

    owner = read_sheet(Path(args.sheet))
    key = {r["sheet_no"]: r for r in (json.loads(l) for l in KEY.read_text(encoding="utf-8").splitlines() if l.strip())}
    pairs = [(n, owner[n], key[n]) for n in sorted(owner) if n in key]
    if not pairs:
        print("no graded rows found in the sheet; write CORRECT, PARTIAL or WRONG after 'grade:'")
        return 1

    binary = sum(1 for _, o, r in pairs if (o == "CORRECT") == (r["grade"] == "CORRECT"))
    exact = sum(1 for _, o, r in pairs if o == r["grade"])
    print(f"graded by owner: {len(pairs)} of {len(key)}")
    print(f"binary label agreement: {binary} of {len(pairs)} ({100 * binary / len(pairs):.0f}%)")
    print(f"three-way grade agreement: {exact} of {len(pairs)} ({100 * exact / len(pairs):.0f}%)")
    confusion = Counter((o, r["grade"]) for _, o, r in pairs)
    print("owner grade -> judge grade counts:")
    for (o, j), c in sorted(confusion.items()):
        print(f"  {o:<8} -> {j:<8} {c}")
    disagreements = [(n, o, r) for n, o, r in pairs if (o == "CORRECT") != (r["grade"] == "CORRECT")]
    if disagreements:
        print("binary disagreements:")
        for n, o, r in disagreements:
            print(f"  sheet {n}: owner {o}, judge {r['grade']} by {r['decided_by']}{' (' + r['flag'] + ')' if r.get('flag') else ''}; {r['question'][:70]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
