"""Grade the worked examples with the real judge and write a report for sign-off.

Reads data/eval/grader_examples.jsonl, grades every draft with the staged
grader (rules first, then the judge model in both orders), and writes
reports/grader-examples-<version>.md plus the matching .jsonl with the full
records, where <version> is the grader version (v1, v2, ...). Earlier
versions' .jsonl files in reports/ are picked up for a comparison table.
Every judge call is cached, so rerunning is free.

Usage:
    python scripts/grade_examples.py [--judge llama3.1:latest] [--base-url http://localhost:11434]
"""

import argparse
import datetime as dt
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from agent.provider import OllamaProvider  # noqa: E402
from calibration.grader import GRADER_VERSION, ProviderJudge, grade  # noqa: E402

EXAMPLES = ROOT / "data" / "eval" / "grader_examples.jsonl"
VERSION_TAG = GRADER_VERSION.split("-")[-1]
REPORT_MD = ROOT / "reports" / f"grader-examples-{VERSION_TAG}.md"
REPORT_JSONL = ROOT / "reports" / f"grader-examples-{VERSION_TAG}.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def label_of(expected: str) -> int:
    return 1 if expected == "CORRECT" else 0


def comparison_lines(records: list[dict]) -> list[str]:
    """Grade per grader version for the same drafts, from earlier report files."""
    earlier = sorted(p for p in REPORT_JSONL.parent.glob("grader-examples-v*.jsonl") if p != REPORT_JSONL)
    if not earlier:
        return []
    runs = [(p.stem.split("-")[-1], {r["n"]: r for r in read_jsonl(p)}) for p in earlier]
    runs.append((VERSION_TAG, {r["n"]: r for r in records}))
    lines = [
        "",
        "## Compared with earlier grader versions",
        "",
        "Grade per version for the same drafts. Label agreement counts a record as right when",
        "its 0 or 1 label matches the expectation, which is what the calibrator sees.",
        "",
        "| # | bucket | expected | " + " | ".join(tag for tag, _ in runs) + " |",
        "|---|---|---|" + "---|" * len(runs),
    ]
    for r in records:
        cells = [run.get(r["n"], {}).get("grade", "") for _, run in runs]
        lines.append(f"| {r['n']} | {r['bucket']} | {r['expected']} | " + " | ".join(cells) + " |")
    lines.append("")
    for tag, run in runs:
        rows = [(run[r["n"]], r["expected"]) for r in records if r["n"] in run]
        grades = sum(1 for x, e in rows if x["grade"] == e)
        labels = sum(1 for x, e in rows if x["label"] == label_of(e))
        judged = [x for x, _ in rows if x["decided_by"] == "judge"]
        flips = [x for x in judged if x["flag"] == "position_disagreement"]
        binary = sum(1 for x in flips if len({g == "CORRECT" for g in x["judge_grades"] if g}) > 1)
        lines.append(
            f"- {tag}: grade matches {grades} of {len(rows)}, label matches {labels} of {len(rows)}, "
            f"order flips {len(flips)} of {len(judged)} judged, of which {binary} changed the binary label"
        )
    return lines


def short(text: str, n: int = 72) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 3] + "..."


def cell(text) -> str:
    return str(text).replace("|", "\\|")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--judge", default="llama3.1:latest")
    parser.add_argument("--base-url", default="http://localhost:11434")
    args = parser.parse_args()

    examples = read_jsonl(EXAMPLES)
    provider = OllamaProvider(model=args.judge, base_url=args.base_url, cache_dir=ROOT / "data" / "cache", num_ctx=4096)
    judge = ProviderJudge(provider)

    records = []
    for ex in examples:
        record = grade(ex["item"], ex["draft"], judge=judge)
        record["n"] = ex["n"]
        record["question"] = ex["item"]["question"]
        record["expected"] = ex["expected"]
        record["note"] = ex["note"]
        record["agrees"] = record["grade"] == ex["expected"]
        records.append(record)
        print(f"{ex['n']:>2} {record['bucket']:<14} {record['decided_by']:<6} {record['grade']:<8} expected {ex['expected']:<8} "
              f"{'ok' if record['agrees'] else 'DIFFERS'} {record['flag'] or ''}")

    judged = [r for r in records if r["decided_by"] == "judge"]
    flips = [r for r in judged if r["flag"] == "position_disagreement"]
    unparsed = [r for r in judged if r["flag"] == "judge_unparsed"]
    agree = sum(1 for r in records if r["agrees"])
    by_bucket = Counter(r["bucket"] for r in records)

    REPORT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_JSONL.open("w", encoding="utf-8", newline="\n") as out:
        for r in records:
            out.write(json.dumps(r, ensure_ascii=False) + "\n")

    lines = [
        "# Grader worked examples",
        "",
        f"Run on {dt.date.today().isoformat()} with grader {GRADER_VERSION} and judge model {args.judge}.",
        "Drafts were written by hand to cover correct, wrong, partial, and borderline cases.",
        "The expected column is the grade the example writer intended; a mismatch is not",
        "automatically a grader error, it is a case for the owner to rule on.",
        "",
        "Limitation, stated plainly: the examples, their drafts and the expected grades were",
        "written by a language model, and the grades below come from a language model judge.",
        "The human check of the judge is the owner's blind grading of about 40 model drafts",
        "(reports/grader-check-sheet.md), reported separately.",
        "",
        "## Summary",
        "",
        f"- examples: {len(records)} ({', '.join(f'{k} {v}' for k, v in sorted(by_bucket.items()))})",
        f"- decided by rules or exact match: {len(records) - len(judged)}; by the judge: {len(judged)}",
        f"- grade matches the writer's expectation: {agree} of {len(records)}",
        f"- label (0 or 1) matches the writer's expectation: "
        f"{sum(1 for r in records if r['label'] == label_of(r['expected']))} of {len(records)}",
        f"- judge order flips: {len(flips)} of {len(judged)} judged drafts",
        f"- unparseable judge replies: {len(unparsed)}",
        "",
        "## Results",
        "",
        "| # | bucket | question | draft | form | by | order A | order B | grade | expected | agrees | flag |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in records:
        a, b = (r["judge_grades"] + [None, None])[:2]
        lines.append(
            f"| {r['n']} | {r['bucket']} | {cell(short(r['question'], 60))} | {cell(short(r['draft']))} | {r['form']} "
            f"| {r['decided_by']} | {a or ''} | {b or ''} | {r['grade']} | {r['expected']} "
            f"| {'yes' if r['agrees'] else 'no'} | {r['flag'] or ''} |"
        )
    lines += ["", "## Reasons", ""]
    for r in records:
        lines.append(f"{r['n']}. {cell(r['reason'])}")
        if r["note"]:
            lines.append(f"    writer's note: {r['note']}")
    flagged = [r for r in records if r["flag"] or not r["agrees"]]
    lines += ["", "## For the owner's review", ""]
    if not flagged:
        lines.append("Nothing flagged.")
    for r in flagged:
        reasons = [r["flag"]] if r["flag"] else []
        if not r["agrees"]:
            reasons.append(f"grade {r['grade']} differs from the writer's expectation {r['expected']}")
        lines.append(f"- example {r['n']}: {'; '.join(reasons)}")
        for i, output in enumerate(r["judge_outputs"]):
            lines.append(f"    judge reply {'A' if i == 0 else 'B'}: {cell(short(output, 200))}")
    lines += comparison_lines(records)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"\nreport: {REPORT_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
