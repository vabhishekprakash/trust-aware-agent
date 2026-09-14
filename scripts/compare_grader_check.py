"""Report judge agreement with the owner's blind grades from a filled-in grader check sheet.

Usage:
    python scripts/compare_grader_check.py
    python scripts/compare_grader_check.py --key data/eval/grader_check_key-v8-rerun.jsonl \
        --revisions data/eval/grader_check_revisions.json --out reports/grader-check-rubric-fidelity.md \
        --title "rubric fidelity"

Reads each '### n' block's 'grade:' line from the sheet, joins it to the machine
record with the same sheet number in the key file, prints agreement on the
binary label (CORRECT = 1, anything else = 0) and on the three-way grade, lists
every disagreement with the question, the draft and both grades, and writes the
same to the output file. Without --revisions the figure is the blind number:
the owner graded without seeing the judge. With --revisions (a JSON object of
sheet number to grade, for grades the owner changed after seeing the
disagreements) the figure is rubric fidelity, not blind agreement, and the
report says so. The bar the owner set is about 90 percent binary agreement
before mass grading.
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
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


def binary(grade: str) -> int:
    return 1 if grade == "CORRECT" else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sheet", default=str(ROOT / "reports" / "grader-check-sheet.md"))
    parser.add_argument("--key", default=str(ROOT / "data" / "eval" / "grader_check_key.jsonl"))
    parser.add_argument("--revisions", default="", help="JSON file of sheet number to grade for grades the owner revised after the blind pass")
    parser.add_argument("--out", default=str(ROOT / "reports" / "grader-check-result.md"))
    parser.add_argument("--title", default="blind agreement")
    args = parser.parse_args()

    owner = read_sheet(Path(args.sheet))
    revised = {}
    if args.revisions:
        revised = {int(k): v for k, v in json.load(open(args.revisions, encoding="utf-8")).items()}
        owner.update(revised)
    key = {r["sheet_no"]: r for r in (json.loads(l) for l in Path(args.key).read_text(encoding="utf-8").splitlines() if l.strip())}
    pairs = [(n, owner[n], key[n]) for n in sorted(owner) if n in key]
    ungraded = sorted(n for n in key if n not in owner)
    if not pairs:
        print("no graded rows found in the sheet; write CORRECT, PARTIAL or WRONG after 'grade:'")
        return 1

    agree_binary = sum(1 for _, o, r in pairs if binary(o) == binary(r["grade"]))
    agree_exact = sum(1 for _, o, r in pairs if o == r["grade"])
    confusion = Counter((o, r["grade"]) for _, o, r in pairs)
    disagreements = [(n, o, r) for n, o, r in pairs if binary(o) != binary(r["grade"])]
    grade_only = [(n, o, r) for n, o, r in pairs if binary(o) == binary(r["grade"]) and o != r["grade"]]
    by_bucket, by_bucket_agree = Counter(), Counter()
    by_condition, by_condition_agree = Counter(), Counter()
    for _, o, r in pairs:
        by_bucket[r["bucket"]] += 1
        by_bucket_agree[r["bucket"]] += binary(o) == binary(r["grade"])
        by_condition[r["condition"]] += 1
        by_condition_agree[r["condition"]] += binary(o) == binary(r["grade"])

    first = key[pairs[0][0]]
    lines = [f"# Grader check: {args.title}", ""]
    if revised:
        lines += [
            "This is NOT a blind number. The owner graded the sheet blind once; that figure stands in",
            "reports/grader-check-result.md. Here the grader was changed after the owner's rulings and run",
            f"again on the same drafts, and the owner's grades for sheet numbers {', '.join(map(str, sorted(revised)))} are the",
            "ones the owner revised on seeing the disagreements. The figure measures how faithfully the",
            "fixed grader follows the rubric the owner settled, on drafts the fix was designed against.",
            "",
        ]
    else:
        lines += ["The owner graded the drafts without seeing the judge; the judge's grades were held in a key file.", ""]
    lines += [
        f"Grader {first['grader_version']}, judge {first['judge_model']}, drafts by the model under test.",
        "",
        f"- drafts graded by the owner: {len(pairs)} of {len(key)}" + (f" (no grade written for sheet numbers {', '.join(map(str, ungraded))})" if ungraded else ""),
        f"- binary label agreement (CORRECT against not CORRECT): {agree_binary} of {len(pairs)} ({100 * agree_binary / len(pairs):.0f} percent)",
        f"- three-way grade agreement: {agree_exact} of {len(pairs)} ({100 * agree_exact / len(pairs):.0f} percent)",
        f"- binary agreement per bucket: " + ", ".join(f"{b} {by_bucket_agree[b]} of {by_bucket[b]}" for b in sorted(by_bucket)),
        f"- binary agreement per draft condition: " + ", ".join(f"{c} {by_condition_agree[c]} of {by_condition[c]}" for c in sorted(by_condition)),
        "",
        "Owner grade to judge grade counts:",
        "",
    ]
    for (o, j), c in sorted(confusion.items()):
        lines.append(f"    {o:<8} -> {j:<8} {c}")
    lines += ["", f"## Binary disagreements ({len(disagreements)})", ""]
    if not disagreements:
        lines.append("None.")
    for n, o, r in disagreements:
        lines += [
            f"### sheet {n}: owner {o}, judge {r['grade']} (decided by {r['decided_by']}{', ' + r['flag'] if r.get('flag') else ''})",
            "",
            f"question: {r['question']}",
            "",
            *[f"reference: {line}" for line in r["reference"]],
            "",
            f"draft: {r['draft']}",
            "",
            f"bucket {r['bucket']}, condition {r['condition']}, judge reason: {r.get('reason', '')}",
            "",
        ]
    lines += ["", f"## Grade-only disagreements, same binary label ({len(grade_only)})", ""]
    if not grade_only:
        lines.append("None.")
    for n, o, r in grade_only:
        lines.append(f"- sheet {n}: owner {o}, judge {r['grade']}; {r['question']}")
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))
    print(f"\nwritten: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
