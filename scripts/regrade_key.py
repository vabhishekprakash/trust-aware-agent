"""Regrade an existing grader-check key with the current grader, keeping its drafts.

Usage:
    python scripts/regrade_key.py --key data/eval/grader_check_key.jsonl \
        --pool <items file the sheet was drawn from> --out data/eval/grader_check_key-v13-rerun.jsonl

A rubric-fidelity rerun must grade exactly the drafts the owner graded. This
reads each row of the key (item id, sheet number, condition, draft), takes
the item's fields from the pool file the sheet was built from, grades the
draft with the grader as it is now, and writes a new key with the same sheet
numbers. Nothing is regenerated. scripts/compare_grader_check.py then reports
the effect against the owner's sheet.
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from agent.provider import OllamaProvider  # noqa: E402
from calibration.grader import GRADER_VERSION, ProviderJudge, grade  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--key", required=True)
    parser.add_argument("--pool", required=True, help="items file the sheet was drawn from (an exact snapshot)")
    parser.add_argument("--out", required=True)
    parser.add_argument("--judge", default="llama3.1:latest")
    args = parser.parse_args()
    if "test" in Path(args.pool).name:
        print("refusing to read the test split")
        return 1

    pool = {}
    for line in Path(args.pool).read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            pool[row["id"]] = row
    rows = [json.loads(l) for l in Path(args.key).read_text(encoding="utf-8").splitlines() if l.strip()]
    judge = ProviderJudge(OllamaProvider(model=args.judge, cache_dir=ROOT / "data" / "cache", num_ctx=4096))

    out_rows, changed = [], []
    for old in sorted(rows, key=lambda r: r["sheet_no"]):
        item = pool[old["item_id"]]
        record = grade(item, old["draft"], judge=judge)
        record.update(n=old.get("n"), item_id=old["item_id"], question=old["question"], condition=old.get("condition"),
                      reference=old.get("reference"), sheet_no=old["sheet_no"])
        out_rows.append(record)
        if record["grade"] != old["grade"]:
            changed.append((old["sheet_no"], old["grade"], record["grade"]))
        print(f"{old['sheet_no']:>2} {item['bucket']:<14} {record['decided_by']:<6} {old['grade']:<8} -> {record['grade']:<8} {record['flag'] or ''}", flush=True)

    with Path(args.out).open("w", encoding="utf-8", newline="\n") as f:
        for r in out_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    spread = Counter(r["grade"] for r in out_rows)
    print(f"\n{GRADER_VERSION} against {rows[0]['grader_version']}: {len(changed)} grade changes {changed}; spread {dict(spread)}\n-> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
