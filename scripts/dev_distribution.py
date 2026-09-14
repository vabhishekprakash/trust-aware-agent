"""Print and write the dev label distribution as the calibrator will see it.

Usage:
    python scripts/dev_distribution.py --rows reports/dev-run-v1b.jsonl reports/dev-run-reserve.jsonl \
        --labels "locked 100" "reserve 34" --out reports/dev-distribution.md

Takes one or more graded rows files, reports each on its own and merged:
items, correct labels (label 1) and rate per bucket, the actions behind the
labels, and the decisive stratum (answerable items with the evidence chunk
retrieved). Every number comes from the rows files.
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUCKETS = ("answerable", "ambiguous", "unanswerable", "false_premise")


def pct(a: int, n: int) -> str:
    return f"{a}/{n} ({100 * a / n:.0f}%)" if n else "0/0"


def table(rows: list[dict], title: str) -> list[str]:
    out = [f"### {title}", "", "| bucket | n | correct | actions (count) |", "|---|---|---|---|"]
    for b in BUCKETS + ("all",):
        rs = rows if b == "all" else [r for r in rows if r["bucket"] == b]
        acts = ", ".join(f"{a} {c}" for a, c in sorted(Counter(r["action"] for r in rs).items()))
        out.append(f"| {b} | {len(rs)} | {pct(sum(r['grade']['label'] for r in rs), len(rs))} | {acts} |")
    ans = [r for r in rows if r["bucket"] == "answerable" and r["evidence"]["retrieved"]]
    out += ["", f"Decisive stratum, answerable with evidence retrieved: {pct(sum(r['grade']['label'] for r in ans), len(ans))} correct, "
                f"{len(ans) - sum(r['grade']['label'] for r in ans)} wrong.", ""]
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rows", nargs="+", required=True)
    parser.add_argument("--labels", nargs="+", required=True)
    parser.add_argument("--out", default=str(ROOT / "reports" / "dev-distribution.md"))
    args = parser.parse_args()
    if len(args.rows) != len(args.labels):
        print("one label per rows file")
        return 1
    sets = [[json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()] for p in args.rows]
    ids = [r["item_id"] for rows in sets for r in rows]
    if len(ids) != len(set(ids)):
        print("an item appears in more than one rows file")
        return 1
    lines = ["# Dev label distribution", "", "Label 1 is a CORRECT grade; PARTIAL and WRONG are 0. Sources: " +
             "; ".join(f"{lab} from {Path(p).name}" for lab, p in zip(args.labels, args.rows)) + ".", ""]
    for rows, lab in zip(sets, args.labels):
        lines += table(rows, lab)
    if len(sets) > 1:
        lines += table([r for rows in sets for r in rows], "merged")
    lines += ["The ambiguous bucket is small and its numbers are indicative only. The false-premise bucket has no positive "
              "examples; see reports/premise-step.md and the limitations in docs/annotation-guide.md."]
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
