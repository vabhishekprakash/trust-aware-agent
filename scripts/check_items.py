"""Code checks on drafted items: quotes on the stated page, record shape, duplicates.

Usage: python verify_items.py <workflow-output.json> <out.json> <report.md>
Reads the drafting workflow's result (items list), checks every evidence quote
against data/corpus/pages.jsonl by printed page label (matching on letters and
digits only, because the extraction has soft hyphens, bullets and odd spaces),
checks the fields the annotation guide requires per bucket, marks near-duplicate
questions, and writes the surviving items plus a report.
"""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
src, out_path, report_path = sys.argv[1:4]

top = json.load(open(src, encoding="utf-8"))
data = top.get("result", top)
if isinstance(data, str):
    data = json.loads(data)
items = data["items"]

pages = [json.loads(l) for l in (ROOT / "data/corpus/pages.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
by_label = defaultdict(list)
for p in pages:
    by_label[p["printed_page"] or str(p["page"])].append(p)


def key(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


page_keys = {label: [key(p["text"]) for p in ps] for label, ps in by_label.items()}
all_keys = [(p["printed_page"], key(p["text"])) for p in pages]


def quote_status(page, quote):
    k = key(quote)
    if len(k) < 20:
        return "too short"
    if any(k in pk for pk in page_keys.get(str(page), [])):
        return "ok"
    elsewhere = [label for label, pk in all_keys if k in pk]
    return f"on {elsewhere}" if elsewhere else "not found"


def words(q):
    return set(re.findall(r"[a-z0-9]+", q.lower())) - {"the", "a", "an", "of", "in", "to", "is", "are", "does", "what", "which", "how", "for", "and", "or", "on", "by", "at", "be", "with", "that", "it", "its", "as", "from", "this", "do", "handbook", "nasa"}


problems = []
kept = []
seen_questions = []
for n, it in enumerate(items):
    errs = []
    b = it.get("bucket")
    q = (it.get("question") or "").strip()
    if not q or not q.endswith("?"):
        errs.append("question missing or not a question")
    ev = it.get("evidence") or []
    if not ev:
        errs.append("no evidence")
    for e in ev:
        st = quote_status(e.get("page"), e.get("quote"))
        if st != "ok":
            errs.append(f"quote p{e.get('page')} {st}: {str(e.get('quote'))[:60]}")
    if b == "answerable":
        if not it.get("gold_answer"):
            errs.append("answerable without gold_answer")
        if it.get("expected") != "answer":
            errs.append("expected should be answer")
        if len((it.get("gold_answer") or "").split()) > 12:
            errs.append("gold_answer longer than 12 words")
    elif b == "ambiguous":
        rd = it.get("readings") or []
        if len(rd) < 2:
            errs.append("ambiguous needs two readings")
        if len(ev) < 2:
            errs.append("ambiguous needs one quote per reading")
        if it.get("expected") != "clarify":
            errs.append("expected should be clarify")
        answers = [key(r.get("answer")) for r in rd]
        if len(set(answers)) < len(answers):
            errs.append("readings share an answer")
    elif b == "unanswerable":
        if it.get("gold_answer"):
            errs.append("unanswerable with gold_answer")
        if it.get("expected") != "abstain":
            errs.append("expected should be abstain")
        if "search" not in (it.get("notes") or "").lower() and "grep" not in (it.get("notes") or "").lower():
            errs.append("notes do not record the search")
    elif b == "false_premise":
        if not it.get("premise_fix"):
            errs.append("false_premise without premise_fix")
        if it.get("expected") != "abstain":
            errs.append("expected should be abstain")
    else:
        errs.append(f"unknown bucket {b}")
    # near-duplicate questions: same normalised text, or Jaccard over content words >= 0.6
    wq = words(q)
    for m, (q2, wq2) in enumerate(seen_questions):
        if key(q) == key(q2):
            errs.append(f"duplicate of item {m}")
            break
        inter = len(wq & wq2)
        union = len(wq | wq2) or 1
        if inter / union >= 0.6 and inter >= 4:
            errs.append(f"near-duplicate of item {m}: {q2[:60]}")
            break
    seen_questions.append((q, wq))
    if errs:
        problems.append((n, it, errs))
    else:
        kept.append({**it, "index": len(kept)})

Path(out_path).write_text("\n".join(json.dumps(i, ensure_ascii=False) for i in kept) + "\n", encoding="utf-8", newline="\n")
lines = ["# Item drafting: code checks", ""]
lines.append(f"drafted {len(items)}, kept {len(kept)}, rejected {len(problems)}")
lines.append("")
lines.append("kept per bucket: " + ", ".join(f"{k} {v}" for k, v in sorted(Counter(i['bucket'] for i in kept).items())))
lines.append("drafted per bucket: " + ", ".join(f"{k} {v}" for k, v in sorted(Counter(i['bucket'] for i in items).items())))
lines.append("drafted per agent: " + ", ".join(f"{k} {v}" for k, v in sorted(data.get('perAgent', {}).items())))
lines.append("")
reasons = Counter(re.sub(r":.*", "", e).strip() for _, _, errs in problems for e in errs)
lines.append("rejection reasons: " + ", ".join(f"{k} {v}" for k, v in reasons.most_common()))
lines.append("")
for n, it, errs in problems:
    lines.append(f"- [{it.get('source')}] {it.get('bucket')}: {it.get('question')}")
    for e in errs:
        lines.append(f"    - {e}")
Path(report_path).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print("\n".join(lines[:8]))
