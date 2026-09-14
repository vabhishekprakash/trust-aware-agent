"""Build the blind grader check: model drafts for the owner to grade without seeing the judge.

For each item in the input file the model under test writes drafts under three
conditions: with the item's evidence passage, with no passage, and with a
passage from a different item. That spread gives correct, wrong and borderline
drafts without anyone choosing them by hand. Every draft is graded by the
current grader, the machine grades go to a key file, and a sheet without them
goes to the owner. scripts/compare_grader_check.py reports agreement once the
owner has filled the sheet in.

Usage:
    python scripts/grader_check.py --items data/eval/grader_examples.jsonl --limit 40
    python scripts/grader_check.py --items data/eval/items_candidates.jsonl --limit 40

Writes reports/grader-check-sheet.md (for the owner), data/eval/grader_check_key.jsonl
(machine grades; do not open before the sheet is done), and prints the grade spread.
"""

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from agent.provider import OllamaProvider  # noqa: E402
from calibration.grader import GRADER_VERSION, ProviderJudge, grade  # noqa: E402

SHEET = ROOT / "reports" / "grader-check-sheet.md"
KEY = ROOT / "data" / "eval" / "grader_check_key.jsonl"
SEED = 42

SYSTEM = (
    "You answer questions about the NASA Systems Engineering Handbook using only the passage you are given. "
    "If the passage does not contain the answer, say that the handbook does not say. "
    "If the question could mean two different things, ask which is meant. Answer in one or two sentences."
)
SYSTEM_NO_PASSAGE = (
    "You answer questions about the NASA Systems Engineering Handbook from memory. "
    "Answer in one or two sentences."
)


def read_items(path: Path) -> list[dict]:
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    if rows and "item" in rows[0]:  # the worked-examples file wraps items
        seen, items = set(), []
        for r in rows:
            if r["item"]["id"] not in seen:
                seen.add(r["item"]["id"])
                items.append(r["item"])
        return items
    return rows


def passage(item: dict) -> str:
    return "\n".join(f"(page {e['page']}) {e['quote']}" for e in item.get("evidence", []))


def prompts(item: dict, distractor: dict) -> list[tuple[str, list[dict]]]:
    q = item["question"]
    return [
        ("with_evidence", [{"role": "system", "content": SYSTEM}, {"role": "user", "content": f"Passage:\n{passage(item)}\n\nQuestion: {q}"}]),
        ("no_passage", [{"role": "system", "content": SYSTEM_NO_PASSAGE}, {"role": "user", "content": f"Question: {q}"}]),
        ("distractor", [{"role": "system", "content": SYSTEM}, {"role": "user", "content": f"Passage:\n{passage(distractor)}\n\nQuestion: {q}"}]),
    ]


def reference_text(item: dict) -> list[str]:
    b = item["bucket"]
    if b == "answerable":
        return [f"reference answer: {item['gold_answer']}", f"acceptable forms: {'; '.join(item.get('gold_aliases') or []) or 'none'}"]
    if b == "ambiguous":
        return [f"reading {i}: {r['reading']} -> {r['answer']} (page {r['page']})" for i, r in enumerate(item["readings"], start=1)]
    if b == "unanswerable":
        return ["the handbook does not answer this question"]
    return [f"the question's assumption is false; the handbook says: {item['premise_fix']}"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--items", default=str(ROOT / "data" / "eval" / "grader_examples.jsonl"))
    parser.add_argument("--limit", type=int, default=40, help="number of drafts on the sheet")
    parser.add_argument("--model", default="qwen2.5:3b-instruct")
    parser.add_argument("--judge", default="llama3.1:latest")
    parser.add_argument("--base-url", default="http://localhost:11434")
    args = parser.parse_args()

    items = read_items(Path(args.items))
    rng = random.Random(SEED)
    cache = ROOT / "data" / "cache"
    model = OllamaProvider(model=args.model, base_url=args.base_url, cache_dir=cache)
    judge = ProviderJudge(OllamaProvider(model=args.judge, base_url=args.base_url, cache_dir=cache))

    # Walk the items in a seeded order, rotating the condition with each item, and
    # go round again if the limit needs more drafts than there are items. Every
    # bucket and condition is represented and no draft is chosen by hand.
    order = list(items)
    rng.shuffle(order)
    plan = []
    pass_no = 0
    while len(plan) < args.limit and pass_no < 3:
        for i, item in enumerate(order):
            others = [x for x in items if x["id"] != item["id"] and x["bucket"] != item["bucket"]] or [x for x in items if x["id"] != item["id"]]
            distractor = rng.choice(others)
            plan.append((item, prompts(item, distractor)[(i + pass_no) % 3]))
        pass_no += 1
    plan = plan[: args.limit]

    records = []
    for n, (item, (condition, messages)) in enumerate(plan, start=1):
        draft = model.generate(messages, temperature=0.0, seed=SEED, max_tokens=120).text.strip()
        record = grade(item, draft, judge=judge)
        record.update(n=n, item_id=item["id"], question=item["question"], condition=condition, reference=reference_text(item))
        records.append(record)
        print(f"{n:>2} {item['bucket']:<14} {condition:<13} {record['decided_by']:<6} {record['grade']:<8} {record['flag'] or ''}")

    rng.shuffle(records)  # the sheet order carries no information about condition or grade
    for n, r in enumerate(records, start=1):
        r["sheet_no"] = n

    KEY.parent.mkdir(parents=True, exist_ok=True)
    with KEY.open("w", encoding="utf-8", newline="\n") as out:
        for r in sorted(records, key=lambda r: r["sheet_no"]):
            out.write(json.dumps(r, ensure_ascii=False) + "\n")

    lines = [
        "# Blind grader check",
        "",
        f"{len(records)} drafts written by {args.model} for handbook questions, in a mixed order.",
        "For each one, read the question and the reference, then grade the draft CORRECT, PARTIAL",
        "or WRONG by the rules in docs/annotation-guide.md, and write it after 'grade:'. Do not",
        "open data/eval/grader_check_key.jsonl until the sheet is done. The judge's grades sit",
        "there, and scripts/compare_grader_check.py reports agreement on the binary label.",
        "",
        "The drafts come from three conditions the model does not know it is in: the item's own",
        "evidence passage, no passage, and a passage from a different item. That is how the set",
        "spans correct, wrong and borderline without anyone picking drafts by hand.",
        "",
    ]
    for r in sorted(records, key=lambda r: r["sheet_no"]):
        lines += [f"### {r['sheet_no']}", "", f"question: {r['question']}", ""]
        lines += [f"reference: {line}" for line in r["reference"]]
        lines += ["", f"draft: {r['draft']}", "", "grade:", ""]
    SHEET.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    spread = Counter(r["grade"] for r in records)
    by_condition = Counter((r["condition"], r["grade"]) for r in records)
    print(f"\ngrader {GRADER_VERSION}: machine grade spread {dict(spread)}")
    for c in ("with_evidence", "no_passage", "distractor"):
        print(f"  {c:<13} " + ", ".join(f"{g} {by_condition[(c, g)]}" for g in ("CORRECT", "PARTIAL", "WRONG")))
    print(f"sheet: {SHEET}\nkey: {KEY}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
