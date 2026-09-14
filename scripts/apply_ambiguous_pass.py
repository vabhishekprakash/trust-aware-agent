"""Apply the dominant-reading pass to the ambiguous candidates.

Usage: python scripts/apply_ambiguous_pass.py [--owner-decisions data/eval/ambiguous_owner_decisions.json]

Reads data/eval/ambiguous_pass.jsonl (one verdict per ambiguous item: keep,
move, drop, or owner) and, when the owner has returned decisions, a JSON
object of id to keep|move|drop. First it merges the blind hold-back items
back into data/eval/items_candidates.jsonl (the blind check is done and its
record stays in blind40_key.jsonl). Then keep leaves an item as it is, move
turns it into an answerable item built from the reading named by
reading_index, and drop removes it. Items whose verdict is owner and have no
decision yet stay in the bucket untouched. Ids never change. The pass report
goes to reports/ambiguous-calls.md.
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANDIDATES = ROOT / "data" / "eval" / "items_candidates.jsonl"
BLIND_KEY = ROOT / "data" / "eval" / "blind40_key.jsonl"
PASS = ROOT / "data" / "eval" / "ambiguous_pass.jsonl"
REPORT = ROOT / "reports" / "ambiguous-calls.md"


def read_jsonl(path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def write_jsonl(path, rows):
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8", newline="\n")


def move_to_answerable(item, call):
    index = call["reading_index"]
    reading = item["readings"][index]
    # Drafters wrote one quote per reading in reading order; take that one when its
    # page matches, otherwise fall back to any quote on the reading's page.
    aligned = item["evidence"][index:index + 1] if index < len(item["evidence"]) and str(item["evidence"][index]["page"]) == str(reading["page"]) else []
    evidence = aligned or [e for e in item["evidence"] if str(e["page"]) == str(reading["page"])] or item["evidence"][:1]
    if call.get("evidence_indices"):
        # a compound gold drawn from more than one reading keeps every quote it rests on
        evidence = [item["evidence"][i] for i in call["evidence_indices"] if i < len(item["evidence"])]
    evidence = evidence + list(call.get("extra_evidence") or [])
    other = [r for i, r in enumerate(item["readings"]) if i != call["reading_index"]]
    return {
        **item,
        "bucket": "answerable",
        "gold_answer": call["gold_answer"],
        "gold_aliases": call["gold_aliases"],
        "readings": [],
        "expected": "answer",
        "evidence": evidence,
        "notes": (item["notes"] + " | Moved from ambiguous in the dominant-reading pass: " + call.get("owner_reason", call["reason"])
                  + " The other reading was: " + "; ".join(f"{r['reading']} -> {r['answer']} (page {r['page']})" for r in other)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--owner-decisions", default="")
    args = parser.parse_args()

    calls = {c["id"]: c for c in read_jsonl(PASS)}
    decisions = json.load(open(args.owner_decisions, encoding="utf-8")) if args.owner_decisions else {}
    candidates = read_jsonl(CANDIDATES)
    have = {r["id"] for r in candidates}
    merged_back = [r for r in read_jsonl(BLIND_KEY) if r["id"] not in have]
    pool = sorted(candidates + merged_back, key=lambda r: r["id"])

    out, actions = [], Counter()
    moved, dropped, pending = [], [], []
    for item in pool:
        call = calls.get(item["id"]) if item["bucket"] == "ambiguous" else None
        if call is None:
            out.append(item)
            continue
        verdict = call["verdict"]
        if verdict == "owner":
            verdict = decisions.get(item["id"], "owner")
        if verdict == "keep":
            out.append(item)
            actions["keep"] += 1
        elif verdict == "move":
            if "gold_answer" not in call:
                out.append(item)
                pending.append(item["id"])
                actions["owner"] += 1
                continue
            out.append(move_to_answerable(item, call))
            moved.append(item["id"])
            actions["move"] += 1
        elif verdict == "drop":
            dropped.append(item["id"])
            actions["drop"] += 1
        else:
            out.append(item)
            pending.append(item["id"])
            actions["owner"] += 1
    write_jsonl(CANDIDATES, out)

    # The summary counts the recorded outcome of every call, not only what this
    # run changed, so a rerun on an already-applied pool reports the same numbers.
    outcome = Counter()
    moved, dropped, pending = [], [], []
    for item_id, call in calls.items():
        verdict = call.get("owner_decision") or decisions.get(item_id) or call["verdict"]
        if verdict == "owner":
            pending.append(item_id)
        elif verdict == "move":
            moved.append(item_id)
        elif verdict == "drop":
            dropped.append(item_id)
        outcome[verdict] += 1
    actions = outcome

    lines = [
        "# Ambiguous pass: dominant-reading check",
        "",
        "Every ambiguous candidate was tested against one question: would a person asking this",
        "question have both readings in mind? Items with one natural reading move to answerable",
        "or are dropped; duplicates the code check missed are dropped. The verifiers that produced",
        "the bucket were language model agents, and so is the author of this pass, so the twelve",
        "closest calls are left to the owner. Write keep, move or drop after 'decision:' and run",
        "scripts/apply_ambiguous_pass.py with --owner-decisions.",
        "",
        f"- kept: {actions['keep']}",
        f"- moved to answerable: {actions['move']} ({', '.join(moved) or 'none'})",
        f"- dropped: {actions['drop']} ({', '.join(dropped) or 'none'})",
        f"- awaiting the owner's decision: {actions['owner']} ({', '.join(pending) or 'none'})",
        f"- ambiguous items in the pool now: {sum(1 for r in out if r['bucket'] == 'ambiguous')}, of which {actions['owner']} pending",
        f"- candidates in the pool: {len(out)} (blind hold-back merged back in; blind40_key.jsonl keeps the drafted record)",
        "",
        "## The owner's calls",
        "",
    ]
    by_id = {r["id"]: r for r in pool}
    for item_id, call in calls.items():
        if call["verdict"] != "owner" or item_id in decisions:
            continue
        item = by_id[item_id]
        lines += [f"### {item_id}", "", f"question: {item['question']}", ""]
        for i, rd in enumerate(item["readings"], start=1):
            lines.append(f"reading {i}: {rd['reading']} -> {rd['answer']} (page {rd['page']})")
        lines += ["", f"my lean: {call['lean']}. {call['reason']}", "", "decision (keep / move / drop):", ""]
    lines += ["", "## Every call", ""]
    for item_id, call in calls.items():
        lines.append(f"- {item_id}: {call['verdict']}" + (f" (lean {call['lean']})" if call.get("lean") else "") + f". {call['reason']}")
        if call.get("owner_decision"):
            lines.append(f"    - owner's decision: {call['owner_decision']}")
        if call.get("owner_decision_text"):
            lines.append(f"    - owner's words: {call['owner_decision_text']}")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines[9:15]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
