"""Apply verifier verdicts, select items to target, assign ids, hold back the blind 40, write files.

Usage: python finish_items.py <kept.jsonl> <verdicts.json> <drafting-report.md>
Writes data/eval/items_draft.jsonl (labelled items minus the blind 40),
data/eval/blind40_questions.jsonl, data/eval/blind40_key.jsonl,
reports/blind-40.md, reports/item-review-sample.md and reports/item-drafting.md.
"""

import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED = 42
BUCKETS = ["answerable", "ambiguous", "unanswerable", "false_premise"]
TARGET_240 = {"answerable": 84, "ambiguous": 48, "unanswerable": 60, "false_premise": 48}
TARGET_200 = {"answerable": 70, "ambiguous": 40, "unanswerable": 50, "false_premise": 40}
BLIND = {"answerable": 14, "ambiguous": 8, "unanswerable": 10, "false_premise": 8}
REVIEW_PER_BUCKET = 10

kept_path, verdicts_path, code_report = sys.argv[1:4]
items = [json.loads(l) for l in Path(kept_path).read_text(encoding="utf-8").splitlines() if l.strip()]
top = json.load(open(verdicts_path, encoding="utf-8"))
vdata = top.get("result", top)
if isinstance(vdata, str):
    vdata = json.loads(vdata)
verdicts = {v["index"]: v for v in vdata["verdicts"]}

pages = [json.loads(l) for l in (ROOT / "data/corpus/pages.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]


def key(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


page_keys = defaultdict(list)
for p in pages:
    page_keys[p["printed_page"] or str(p["page"])].append(key(p["text"]))


def quotes_ok(item):
    for e in item.get("evidence") or []:
        k = key(e.get("quote"))
        if len(k) < 20 or not any(k in pk for pk in page_keys.get(str(e.get("page")), [])):
            return False
    return True


# 1. apply verdicts; items whose verifier batch never ran are set aside, not dropped
final, dropped, fixed_bad, unverified = [], [], [], []
for it in items:
    v = verdicts.get(it["index"])
    if v is None:
        unverified.append(it)
        continue
    if v["verdict"] == "drop":
        dropped.append((it, v["reason"]))
        continue
    merged = dict(it)
    if v["verdict"] == "fix" and v.get("fixed"):
        for field, value in v["fixed"].items():
            if value not in (None, "", []):
                merged[field] = value
        if merged.get("bucket") not in BUCKETS:
            dropped.append((it, f"fix set an unknown bucket: {merged.get('bucket')}"))
            continue
        if not quotes_ok(merged):
            fixed_bad.append((merged, v["reason"]))
            continue
    merged["verifier"] = v["verdict"]
    merged["verifier_reason"] = v["reason"]
    final.append(merged)

# 2. nothing is locked yet: every verified item stays a candidate until the owner
# has returned the blind sheet and the review sample. Ids are for reference only.
by_bucket = defaultdict(list)
for it in final:
    by_bucket[it["bucket"]].append(it)
counts = {b: len(by_bucket[b]) for b in BUCKETS}
target = {b: min(counts[b], TARGET_240[b]) for b in BUCKETS}
selected, surplus = list(final), []


def page_sort_key(item):
    page = str((item.get("evidence") or [{}])[0].get("page", ""))
    return (0, int(page)) if page.isdigit() else (1, page)


# 3. ids in bucket, page, question order
selected.sort(key=lambda it: (BUCKETS.index(it["bucket"]), page_sort_key(it), it["question"]))
records = []
for n, it in enumerate(selected, start=1):
    records.append({
        "id": f"q{n:04d}",
        "bucket": it["bucket"],
        "question": it["question"],
        "gold_answer": it.get("gold_answer") if it["bucket"] == "answerable" else None,
        "gold_aliases": it.get("gold_aliases") or [] if it["bucket"] == "answerable" else [],
        "readings": it.get("readings") or [] if it["bucket"] == "ambiguous" else [],
        "premise_fix": it.get("premise_fix") if it["bucket"] == "false_premise" else None,
        "expected": {"answerable": "answer", "ambiguous": "clarify", "unanswerable": "abstain", "false_premise": "abstain"}[it["bucket"]],
        "evidence": it["evidence"],
        "notes": it.get("notes") or "",
        "needs_calculator": bool(it.get("needs_calculator")),
        "split": None,
    })

# 4. blind hold-back and review sample, both seed 42 per bucket
blind_ids = set()
for b in BUCKETS:
    ids = sorted(r["id"] for r in records if r["bucket"] == b)
    rng = random.Random(SEED)
    blind_ids.update(rng.sample(ids, min(BLIND[b], len(ids))))
review_ids = set()
for b in BUCKETS:
    ids = sorted(r["id"] for r in records if r["bucket"] == b and r["id"] not in blind_ids)
    rng = random.Random(SEED)
    review_ids.update(rng.sample(ids, min(REVIEW_PER_BUCKET, len(ids))))

main = [r for r in records if r["id"] not in blind_ids]
blind = [r for r in records if r["id"] in blind_ids]


def write_jsonl(path, rows):
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8", newline="\n")


eval_dir = ROOT / "data/eval"
write_jsonl(eval_dir / "items_candidates.jsonl", main)
write_jsonl(eval_dir / "items_unverified.jsonl", [{k: v for k, v in it.items() if k not in ("index", "source")} for it in unverified])
write_jsonl(eval_dir / "blind40_questions.jsonl", [{"id": r["id"], "question": r["question"]} for r in blind])
write_jsonl(eval_dir / "blind40_key.jsonl", blind)

lines = [
    "# Blind labelling sheet: 40 items",
    "",
    "For each question decide, from the handbook alone, which bucket it belongs to",
    "(answerable, ambiguous, unanswerable, false_premise) and write the short answer,",
    "the two readings, or the corrected premise as the bucket requires, with a page.",
    "Do not open data/eval/blind40_key.jsonl until this sheet is done. The key holds",
    "the drafted labels; agreement between the two is reported in the final report.",
    "",
]
for n, r in enumerate(blind, start=1):
    lines += [f"## {n}. {r['id']}", "", r["question"], "", "bucket:", "", "answer / readings / correction:", "", "page:", ""]
(ROOT / "reports/blind-40.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

review = [r for r in records if r["id"] in review_ids]
lines = [
    "# Item review sample: 10 per bucket",
    "",
    f"Drawn with seed {SEED} per bucket from the items not held back for blind labelling.",
    "Mark each keep, fix, or drop. Fixes are applied before the split is made.",
    "",
]
for b in BUCKETS:
    lines += [f"## {b}", ""]
    for r in [x for x in review if x["bucket"] == b]:
        lines += [f"### {r['id']}", "", f"question: {r['question']}", ""]
        if b == "answerable":
            lines += [f"gold answer: {r['gold_answer']}", f"aliases: {'; '.join(r['gold_aliases']) or 'none'}", ""]
        if b == "ambiguous":
            for i, rd in enumerate(r["readings"], start=1):
                lines.append(f"reading {i}: {rd['reading']} -> {rd['answer']} (page {rd['page']})")
            lines.append("")
        if b == "false_premise":
            lines += [f"premise fix: {r['premise_fix']}", ""]
        for e in r["evidence"]:
            lines.append(f"evidence (page {e['page']}): \"{e['quote']}\"")
        lines += ["", f"notes: {r['notes']}", "", "verdict (keep / fix / drop):", ""]
(ROOT / "reports/item-review-sample.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

code_lines = Path(code_report).read_text(encoding="utf-8").splitlines()
vcounts = Counter(v["verdict"] for v in verdicts.values())
lines = [
    "# Item drafting",
    "",
    "How the candidate items were produced and filtered. Every number here comes from",
    "the scripts and workflow runs of 2026-09-09.",
    "",
    "## Counts",
    "",
    *[l for l in code_lines[2:8] if l.strip()],
    f"verifier verdicts: keep {vcounts.get('keep', 0)}, fix {vcounts.get('fix', 0)}, drop {vcounts.get('drop', 0)}",
    f"fixed items whose new quote failed the page check: {len(fixed_bad)}",
    f"candidates after verification per bucket: " + ", ".join(f"{b} {counts[b]}" for b in BUCKETS),
    f"targets for the final set (240 if the buckets allow, else 200): " + ", ".join(f"{b} {TARGET_240[b]} or {TARGET_200[b]}" for b in BUCKETS),
    f"candidates: {len(records)}; held back for the blind item check: {len(blind)}; in items_candidates.jsonl: {len(main)}",
    f"passed the code checks but not yet verified (verifier batches that did not run): {len(unverified)}, "
    f"kept in data/eval/items_unverified.jsonl until they are; per bucket: "
    + ", ".join(f"{b} {sum(1 for it in unverified if it['bucket'] == b)}" for b in BUCKETS),
    "",
    "Nothing is locked. The final 200 or 240 are chosen, and the dev and test split is",
    "made, only after the owner has returned the blind item sheet and the review sample.",
    "",
    "## Limitations, stated plainly",
    "",
    "The items were drafted by language model agents, checked by other language model",
    "agents, and the agent's answers will be graded by a language model judge. The only",
    "human checks are the owner's two 40-item samples: the blind item labels against the",
    "drafted labels, and the blind grades of 40 model drafts against the judge. The code",
    "checks (quote on the stated page, record shape, duplicates) are mechanical and do not",
    "judge whether a question is good. Readers of the final report should weigh every",
    "number with that in mind.",
    "",
    "## Method",
    "",
    "Thirty drafting agents each worked from the cleaned page text: twelve wrote",
    "answerable items over fixed page ranges, six wrote ambiguous items by theme across",
    "the whole book, six wrote unanswerable items by theme and had to record the search",
    "that found nothing, and six wrote false-premise items over page ranges. Code then",
    "rejected any item whose quote was not on its stated page, whose record broke the",
    "guide's shape, or whose question repeated an earlier one. A second set of agents",
    "checked the survivors five at a time, bucket by bucket, trying to find the answer to",
    "each unanswerable question, a dominant reading for each ambiguous one, a premise the",
    "text does not contradict, or a gold answer its quote does not support. Items were",
    f"selected to target with seed {SEED}, keep verdicts before fixes; ids run in bucket and",
    f"page order; the blind 40 and the review sample of 10 per bucket were drawn with seed {SEED}.",
    "",
    "## Blind hold-back",
    "",
    "ids: " + ", ".join(r["id"] for r in blind),
    "",
    "## Dropped by the verifiers",
    "",
]
for it, reason in dropped:
    lines.append(f"- [{it.get('bucket')}] {it.get('question')}")
    lines.append(f"    - {reason}")
for it, reason in fixed_bad:
    lines.append(f"- [{it.get('bucket')}] {it.get('question')} (fix proposed, new quote not on page)")
    lines.append(f"    - {reason}")
(ROOT / "reports/item-drafting.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print("\n".join(lines[6:20]))
