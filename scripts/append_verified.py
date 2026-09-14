"""Append late-verified items to the candidate file without touching existing ids.

Usage: python scripts/append_verified.py <verdicts.json> <batches-dir>
Reads data/eval/items_unverified.jsonl, recovers each item's verifier index from
the batch files it was checked in, applies the verdicts (keep, fix with a page
check on any new quote, drop), gives the survivors ids after the current highest,
appends them to data/eval/items_candidates.jsonl, empties items_unverified.jsonl,
and appends a paragraph to reports/item-drafting.md. Existing ids never change,
because the owner's blind sheets refer to them.
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANDIDATES = ROOT / "data" / "eval" / "items_candidates.jsonl"
UNVERIFIED = ROOT / "data" / "eval" / "items_unverified.jsonl"
BLIND_KEY = ROOT / "data" / "eval" / "blind40_key.jsonl"
REPORT = ROOT / "reports" / "item-drafting.md"
BUCKETS = ["answerable", "ambiguous", "unanswerable", "false_premise"]


def read_jsonl(path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def write_jsonl(path, rows):
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + ("\n" if rows else ""), encoding="utf-8", newline="\n")


def key(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


verdict_path, batches_dir = sys.argv[1:3]
top = json.load(open(verdict_path, encoding="utf-8"))
data = top.get("result", top)
if isinstance(data, str):
    data = json.loads(data)
verdicts = {v["index"]: v for v in data["verdicts"]}

index_by_question = {}
for path in Path(batches_dir).glob("batch_*.jsonl"):
    for it in read_jsonl(path):
        index_by_question[key(it["question"])] = it["index"]

pages = read_jsonl(ROOT / "data" / "corpus" / "pages.jsonl")
page_keys = defaultdict(list)
for p in pages:
    page_keys[p["printed_page"] or str(p["page"])].append(key(p["text"]))


def quotes_ok(item):
    for e in item.get("evidence") or []:
        k = key(e.get("quote"))
        if len(k) < 20 or not any(k in pk for pk in page_keys.get(str(e.get("page")), [])):
            return False
    return True


unverified = read_jsonl(UNVERIFIED)
candidates = read_jsonl(CANDIDATES)
used_ids = {r["id"] for r in candidates} | {r["id"] for r in read_jsonl(BLIND_KEY)}
next_no = max(int(i[1:]) for i in used_ids) + 1

kept, dropped, still = [], [], []
for it in unverified:
    idx = index_by_question.get(key(it["question"]))
    v = verdicts.get(idx) if idx is not None else None
    if v is None:
        still.append(it)
        continue
    if v["verdict"] == "drop":
        dropped.append((it, v["reason"]))
        continue
    merged = dict(it)
    if v["verdict"] == "fix" and v.get("fixed"):
        for field, value in v["fixed"].items():
            if value not in (None, "", []):
                merged[field] = value
        if merged.get("bucket") not in BUCKETS or not quotes_ok(merged):
            dropped.append((it, "fix proposed but the result failed the checks: " + v["reason"]))
            continue
    merged["verifier"] = v["verdict"]
    merged["verifier_reason"] = v["reason"]
    kept.append(merged)


def page_sort_key(item):
    page = str((item.get("evidence") or [{}])[0].get("page", ""))
    return (0, int(page)) if page.isdigit() else (1, page)


kept.sort(key=lambda it: (BUCKETS.index(it["bucket"]), page_sort_key(it), it["question"]))
new_records = []
for it in kept:
    new_records.append({
        "id": f"q{next_no:04d}",
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
    next_no += 1

write_jsonl(CANDIDATES, candidates + new_records)
write_jsonl(UNVERIFIED, still)
per_bucket = {b: sum(1 for r in candidates + new_records if r["bucket"] == b) for b in BUCKETS}
lines = [
    "",
    "## Late verification",
    "",
    f"The verifier batches that had hit the session limit were resumed. Of the {len(unverified)} items",
    f"they covered, {len(kept)} were kept ({sum(1 for it in kept if it['verifier'] == 'fix')} with a fix) and {len(dropped)} dropped;"
    f" {len(still)} remain unverified. The kept items were appended with ids from",
    f"q{next_no - len(kept):04d} on; no existing id changed. Candidates in items_candidates.jsonl per bucket, blind",
    "hold-back excluded: " + ", ".join(f"{b} {per_bucket[b]}" for b in BUCKETS) + ".",
    "",
]
for it, reason in dropped:
    lines.append(f"- dropped [{it['bucket']}] {it['question']}")
    lines.append(f"    - {reason}")
with REPORT.open("a", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(lines) + "\n")
print(f"kept {len(kept)}, dropped {len(dropped)}, still unverified {len(still)}; candidates now {len(candidates) + len(new_records)}")
print("per bucket:", per_bucket)
