"""Compare the owner's blind item labels with the drafted labels on the 40 held-back items.

Usage:
    python scripts/compare_blind_items.py [--sheet reports/blind-40.md]

Parses each '## n. qNNNN' block of the filled sheet (bucket, answer or readings
or correction, page), joins it to data/eval/blind40_key.jsonl, and reports
bucket agreement per drafted bucket plus an answer check for the items whose
bucket agrees: for answerable items whether the owner's text contains the gold
answer or an alias; for ambiguous items whether it names both drafted
readings' answers; for false-premise items how many content words the owner's
correction shares with the drafted premise fix. Every disagreement is listed
in full in reports/item-check-result.md, because the heuristics only sort the
cases; a person reads them.
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from calibration.grader import answer_tokens, mentions_gold, normalise  # noqa: E402

KEY = ROOT / "data" / "eval" / "blind40_key.jsonl"
RESULT = ROOT / "reports" / "item-check-result.md"
BUCKETS = ["answerable", "ambiguous", "unanswerable", "false_premise"]
STOP = {"the", "a", "an", "of", "in", "to", "and", "or", "for", "on", "by", "at", "is", "are", "with", "that", "it", "as", "from", "this", "not", "be", "was", "which", "than"}


def read_sheet(path: Path) -> dict:
    blocks = {}
    current = None
    field = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        head = re.match(r"^##\s+\d+\.\s+(q\d{4})\s*$", raw)
        if head:
            current = head.group(1)
            blocks[current] = {"bucket": "", "answer": "", "page": ""}
            field = "question"
            continue
        if current is None:
            continue
        low = raw.lower()
        if low.startswith("bucket:"):
            blocks[current]["bucket"] = raw.split(":", 1)[1].strip().lower().replace(" ", "_")
            field = "bucket"
        elif low.startswith("answer / readings / correction:"):
            blocks[current]["answer"] = raw.split(":", 1)[1].strip()
            field = "answer"
        elif low.startswith("page:"):
            blocks[current]["page"] = raw.split(":", 1)[1].strip()
            field = "page"
        elif raw.strip():
            if field == "answer":
                blocks[current]["answer"] += "\n" + raw.strip()
            elif field == "page":
                blocks[current]["page"] += "\n" + raw.strip()
    return blocks


def words(text: str) -> set:
    return set(normalise(text).split()) - STOP


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sheet", default=str(ROOT / "reports" / "blind-40.md"))
    args = parser.parse_args()

    owner = read_sheet(Path(args.sheet))
    key = {r["id"]: r for r in (json.loads(l) for l in KEY.read_text(encoding="utf-8").splitlines() if l.strip())}
    rows = []
    for item_id, item in key.items():
        o = owner.get(item_id)
        if o is None or not o["bucket"]:
            rows.append({"id": item_id, "item": item, "owner": o, "bucket_agree": None, "answer_check": "no owner label"})
            continue
        bucket_agree = o["bucket"] == item["bucket"]
        check, detail = "n/a", ""
        if bucket_agree:
            text = o["answer"]
            if item["bucket"] == "answerable":
                hit = mentions_gold(text, item["gold_answer"], item.get("gold_aliases") or [])
                check = "matches gold or alias" if hit else "does not contain gold or alias; read it"
            elif item["bucket"] == "ambiguous":
                named = []
                for i in range(1, len(item["readings"]) + 1):
                    tokens = answer_tokens(item, f"reading{i}")
                    named.append(bool(words(text) & tokens))
                check = "names both drafted answers" if all(named) else f"names {sum(named)} of {len(named)} drafted answers; read it"
            elif item["bucket"] == "false_premise":
                shared = words(text) & words(item["premise_fix"])
                check = f"correction shares {len(shared)} content words with the drafted fix" + ("" if len(shared) >= 3 else "; read it")
            else:
                check = "bucket agreed; no answer to compare"
        rows.append({"id": item_id, "item": item, "owner": o, "bucket_agree": bucket_agree, "answer_check": check})

    lines = [
        "# Blind item check: result",
        "",
        "The owner labelled 40 held-back items from the handbook alone, without the drafted labels.",
        "Bucket agreement is exact. The answer check is a heuristic that sorts the agreed items; the",
        "disagreements are listed in full below for a person to read.",
        "",
        "## Bucket agreement per drafted bucket",
        "",
        "    drafted bucket   items  bucket agreed  owner's bucket when different",
    ]
    total = agreed = 0
    for b in BUCKETS:
        group = [r for r in rows if r["item"]["bucket"] == b]
        ok = sum(1 for r in group if r["bucket_agree"])
        others = Counter(r["owner"]["bucket"] for r in group if r["bucket_agree"] is False)
        lines.append(f"    {b:<16} {len(group):>5}  {ok:>13}  " + (", ".join(f"{k} {v}" for k, v in others.items()) or "-"))
        total += len(group)
        agreed += ok
    lines += ["", f"overall bucket agreement: {agreed} of {total} ({100 * agreed / total:.0f} percent)", ""]
    lines += ["## Answer check on the items whose bucket agreed", ""]
    for b in BUCKETS:
        group = [r for r in rows if r["item"]["bucket"] == b and r["bucket_agree"]]
        counts = Counter(r["answer_check"].split(";")[0] for r in group)
        lines.append(f"- {b}: " + (", ".join(f"{k} {v}" for k, v in counts.items()) or "none agreed"))
    lines += ["", "## Bucket disagreements", ""]
    dis = [r for r in rows if r["bucket_agree"] is False]
    if not dis:
        lines.append("None.")
    for r in dis:
        it = r["item"]
        lines += [
            f"### {r['id']}: drafted {it['bucket']}, owner {r['owner']['bucket']}",
            "",
            f"question: {it['question']}",
            "",
            f"owner: {r['owner']['answer']}",
            f"owner page: {r['owner']['page']}",
            "",
        ]
        if it["bucket"] == "ambiguous":
            for i, rd in enumerate(it["readings"], start=1):
                lines.append(f"drafted reading {i}: {rd['reading']} -> {rd['answer']} (page {rd['page']})")
        elif it["bucket"] == "answerable":
            lines.append(f"drafted gold: {it['gold_answer']} | aliases: {'; '.join(it['gold_aliases'])}")
        elif it["bucket"] == "false_premise":
            lines.append(f"drafted premise fix: {it['premise_fix']}")
        lines += [f"drafted notes: {it['notes']}", ""]
    lines += ["", "## Agreed bucket, answer flagged for reading", ""]
    flagged = [r for r in rows if r["bucket_agree"] and "read it" in r["answer_check"]]
    if not flagged:
        lines.append("None.")
    for r in flagged:
        it = r["item"]
        lines += [f"### {r['id']} ({it['bucket']}): {r['answer_check']}", "", f"question: {it['question']}", "", f"owner: {r['owner']['answer']}", ""]
        if it["bucket"] == "answerable":
            lines.append(f"drafted gold: {it['gold_answer']} | aliases: {'; '.join(it['gold_aliases'])}")
        elif it["bucket"] == "ambiguous":
            for i, rd in enumerate(it["readings"], start=1):
                lines.append(f"drafted reading {i}: {rd['reading']} -> {rd['answer']} (page {rd['page']})")
        elif it["bucket"] == "false_premise":
            lines.append(f"drafted premise fix: {it['premise_fix']}")
        lines.append("")
    missing = [r for r in rows if r["bucket_agree"] is None]
    if missing:
        lines += ["", "## Items without an owner label", ""] + [f"- {r['id']}" for r in missing]
    RESULT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))
    print(f"\nwritten: {RESULT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
