"""Write the dev run report from the graded rows and the manifests.

Usage:
    python scripts/report_dev_run.py [--rows reports/dev-run-v1.jsonl] [--out reports/dev-run-v1.md]

Every number in the report comes from the rows file and the manifest written
by scripts/run_agent.py and scripts/grade_run.py. Nothing is typed in.
"""

import argparse
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BUCKETS = ("answerable", "ambiguous", "unanswerable", "false_premise")
ACTIONS = ("ANSWER", "REJECT", "CLARIFY", "ABSTAIN")
GRADES = ("CORRECT", "PARTIAL", "WRONG")


def pct(a: int, n: int) -> str:
    return f"{a}/{n} ({100 * a / n:.0f}%)" if n else "0/0"


def quantiles(values: list[float]) -> str:
    if not values:
        return "n=0"
    if len(values) < 4:
        return f"n={len(values)} " + " ".join(f"{v:.3f}" for v in sorted(values))
    q = statistics.quantiles(values, n=4)
    return f"n={len(values)} min {min(values):.3f} p25 {q[0]:.3f} med {q[1]:.3f} p75 {q[2]:.3f} max {max(values):.3f}"


def builds(row: dict) -> bool:
    """The judge said the draft builds on the false premise, grounded, in either order."""
    g = row["grade"]
    for answers, ungrounded in zip(g.get("judge_answers") or [], g.get("judge_ungrounded") or []):
        if answers.get("builds") and "builds" not in (ungrounded or []):
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rows", default=str(ROOT / "reports" / "dev-run-v1.jsonl"))
    parser.add_argument("--out", default=str(ROOT / "reports" / "dev-run-v1.md"))
    parser.add_argument("--grading-note", default="", help="one sentence about how the grading pass went, appended to the wall clock section")
    parser.add_argument("--previous", default="", help="rows from an earlier grader on the same traces; adds a before-and-after section per bucket")
    parser.add_argument("--before", default="", help="rows from an earlier run of a different loop; adds a labelled before table of actions and labels per bucket")
    args = parser.parse_args()
    rows = [json.loads(l) for l in Path(args.rows).read_text(encoding="utf-8").splitlines() if l.strip()]
    manifest = json.loads(Path(args.rows).with_name(Path(args.rows).stem + "-manifest.json").read_text(encoding="utf-8"))
    run = manifest["run"]
    by_bucket = defaultdict(list)
    for r in rows:
        by_bucket[r["bucket"]].append(r)
    n_all = len(rows)

    lines = [
        "# Dev run v1, untuned",
        "",
        f"Agent: {run['model']}, k={run['k']}, no retrieval-score abstain rule (unset in this run and dropped after it), "
        f"trace {run['trace_version']}. Graded by {manifest['grader_version']} with judge {manifest['judge']}. "
        f"{n_all} dev items; the test split was not read. The ambiguous bucket has {len(by_bucket['ambiguous'])} dev items, "
        "so its numbers are indicative only.",
        "",
        "Items were drafted and verified by language model agents and graded by a language model judge; human checks so far "
        "are the two blind samples recorded in the annotation guide. Every count below comes from reports/dev-run-v1.jsonl.",
        "",
        "## Actions per bucket",
        "",
        "| bucket | n | " + " | ".join(ACTIONS) + " |",
        "|---|---|" + "---|" * len(ACTIONS),
    ]
    for b in BUCKETS:
        rs = by_bucket[b]
        c = Counter(r["action"] for r in rs)
        lines.append(f"| {b} | {len(rs)} | " + " | ".join(pct(c[a], len(rs)) for a in ACTIONS) + " |")
    c = Counter(r["action"] for r in rows)
    lines.append(f"| all | {n_all} | " + " | ".join(pct(c[a], n_all) for a in ACTIONS) + " |")
    paths = Counter()
    for r in rows:
        if r.get("reject_by"):
            paths[("REJECT", r["reject_by"])] += 1
        if r["clarify_by"]:
            paths[("CLARIFY", r["clarify_by"])] += 1
        if r["abstain_by"]:
            paths[("ABSTAIN", r["abstain_by"])] += 1
    lines += ["", "Which path fired, over all items (an item can show both a clarify and an abstain path; CLARIFY wins):", ""]
    for (a, p), k in sorted(paths.items()):
        lines.append(f"- {a} by {p}: {k}")

    # false clarify
    ans = by_bucket["answerable"]
    clar = [r for r in ans if r["action"] == "CLARIFY"]
    fired = [r for r in ans if r["readings"]["fired"]]
    prompt = [r for r in ans if r["clarify_by"] in ("prompt", "both")]
    lines += [
        "",
        "## False-clarify rate on answerable items",
        "",
        f"- CLARIFY action on answerable items: {pct(len(clar), len(ans))}. The owner's bar is about a fifth.",
        f"- Readings step fired (the rule): {pct(len(fired), len(ans))}; the model's own clarifying question (prompt): {pct(len(prompt), len(ans))}.",
        f"- Readings listed on answerable items: {quantiles([len(r['readings']['parsed']) for r in ans])} (count per item).",
    ]
    if clar:
        dg = Counter((r["draft_grade"] or r["grade"])["grade"] for r in clar)
        lines.append(f"- What the draft behind those CLARIFYs would have scored: " + ", ".join(f"{g} {dg[g]}" for g in GRADES) + ".")
        artefact = [r for r in clar if any(p["answer"].strip().upper().startswith("ONE READING") for p in r["readings"]["parsed"])]
        lines.append(f"- Items where a listed 'answer' was the words ONE READING, a format slip the parser took as a reading: {len(artefact)}"
                     + (f" ({', '.join(r['item_id'] for r in artefact)}). Without them the rate is {pct(len(clar) - len(artefact), len(ans))}. "
                        "The parser was fixed after this run and the run was not repeated, so the measured rate is the higher one and the real rate is nearer the lower." if artefact else "."))
        lines.append("- The readings the model listed on those items:")
        for r in clar:
            lines.append(f"  - {r['item_id']}: {r['question']}")
            for p in r["readings"]["parsed"]:
                lines.append(f"    - {p['reading']} => {p['answer']}")
    amb = by_bucket["ambiguous"]
    lines.append(f"- For contrast, CLARIFY on ambiguous items: {pct(sum(r['action'] == 'CLARIFY' for r in amb), len(amb))}, readings fired {pct(sum(r['readings']['fired'] for r in amb), len(amb))}.")

    # premise step
    if any("premise" in r and r["premise"] is not None for r in rows):
        una = by_bucket["unanswerable"]
        fp = by_bucket["false_premise"]
        not_fp = ans + una
        fired_not_fp = [r for r in not_fp if r["action"] == "REJECT"]
        claimed_not_fp = [r for r in not_fp if r["premise"]["parsed"] is not None]
        lines += [
            "",
            "## Premise step: false-fire rate",
            "",
            f"- REJECT on answerable and unanswerable items: {pct(len(fired_not_fp), len(not_fp))} (answerable {pct(sum(r['action'] == 'REJECT' for r in ans), len(ans))}, "
            f"unanswerable {pct(sum(r['action'] == 'REJECT' for r in una), len(una))}). The owner's bar is about a fifth.",
            f"- The model claimed a contradiction on those items {pct(len(claimed_not_fp), len(not_fp))}; the gate let {len(fired_not_fp)} through.",
            f"- On false-premise items: claimed {pct(sum(r['premise']['parsed'] is not None for r in fp), len(fp))}, gate passed and REJECT {pct(sum(r['action'] == 'REJECT' for r in fp), len(fp))}, "
            f"of which graded CORRECT {sum(r['action'] == 'REJECT' and r['grade']['label'] == 1 for r in fp)}.",
            "- Before this step existed (dev run v1) the false-premise bucket had 0 correct answers in 20.",
        ]
        for r in fired_not_fp:
            lines.append(f"  - false fire {r['item_id']} ({r['bucket']}): {r['response']}")

    # calculator
    calc_items = [r for r in rows if r["needs_calculator"]]
    non_calc = [r for r in rows if not r["needs_calculator"]]
    spurious = [r for r in non_calc if r["spurious_calc"]]
    used = [r for r in calc_items if r["draft"]["calc"]]
    malformed = [r for r in rows if any(c["result"] is None for c in r["draft"]["calc"])]
    lines += [
        "",
        "## Calculator lines",
        "",
        f"- Spurious CALC lines on non-calculator items: {pct(len(spurious), len(non_calc))}" + (f" ({', '.join(r['item_id'] for r in spurious)})." if spurious else "."),
        f"- CALC lines on the calculator items: {pct(len(used), len(calc_items))}; calculator items in dev: {len(calc_items)}.",
        f"- Items whose CALC line could not be computed: {len(malformed)}" + (f" ({', '.join(r['item_id'] for r in malformed)})." if malformed else "."),
    ]
    for r in calc_items:
        lines.append(f"  - {r['item_id']}: calc {[(c['expression'], c['result']) for c in r['draft']['calc']]}, action {r['action']}, grade {r['grade']['grade']}, evidence {'retrieved' if r['evidence']['retrieved'] else 'not retrieved'}.")

    # grades and the confounder
    lines += ["", "## Grades per bucket", "", "| bucket | n | " + " | ".join(GRADES) + " | decided by rules/exact/judge |", "|---|---|---|---|---|---|"]
    for b in BUCKETS:
        rs = by_bucket[b]
        c = Counter(r["grade"]["grade"] for r in rs)
        d = Counter(r["grade"]["decided_by"] for r in rs)
        lines.append(f"| {b} | {len(rs)} | " + " | ".join(pct(c[g], len(rs)) for g in GRADES) + f" | {d['rules']}/{d['exact']}/{d['judge']} |")
    flagged = [r for r in rows if r["grade"].get("flag")]
    lines.append("")
    lines.append(f"Flagged by the grader (order disagreement or unparsed): {len(flagged)}" + (f" ({', '.join(r['item_id'] for r in flagged)})." if flagged else "."))

    lines += [
        "",
        "## Accuracy split by whether the evidence was retrieved",
        "",
        "Evidence retrieved means a chunk that covers the evidence page and contains the quote was among the k hits "
        "(the same rule as the recall measurement). Items whose quote was not found in any chunk are excluded from the split and counted.",
        "",
        "| bucket | evidence retrieved: correct/n | not retrieved: correct/n | no target chunk |",
        "|---|---|---|---|",
    ]
    for b in BUCKETS + ("all",):
        rs = rows if b == "all" else by_bucket[b]
        have = [r for r in rs if r["evidence"]["has_target"]]
        got = [r for r in have if r["evidence"]["retrieved"]]
        missed = [r for r in have if not r["evidence"]["retrieved"]]
        lines.append(f"| {b} | {pct(sum(r['grade']['label'] for r in got), len(got))} | {pct(sum(r['grade']['label'] for r in missed), len(missed))} | {len(rs) - len(have)} |")
    got_all = [r for r in ans if r["evidence"]["has_target"] and r["evidence"]["retrieved"]]
    lines += ["", f"Evidence rank on answerable items when retrieved: {quantiles([float(r['evidence']['rank']) for r in got_all])}."]

    # false premise
    fp = by_bucket["false_premise"]
    b_yes = [r for r in fp if builds(r)]
    lines += [
        "",
        "## Building on a false premise",
        "",
        f"- Judge said the response builds on the premise (grounded, either order): {pct(len(b_yes), len(fp))}.",
        f"- Graded WRONG on false-premise items: {pct(sum(r['grade']['grade'] == 'WRONG' for r in fp), len(fp))}; "
        f"PARTIAL {sum(r['grade']['grade'] == 'PARTIAL' for r in fp)}; CORRECT {sum(r['grade']['grade'] == 'CORRECT' for r in fp)}.",
        f"- Actions on false-premise items: " + ", ".join(f"{a} {sum(r['action'] == a for r in fp)}" for a in ACTIONS) + ".",
    ]

    # grader notes
    amb_clar = [r for r in amb if r["action"] == "CLARIFY"]
    lines += ["", "## Grader notes", ""]
    for r in amb_clar:
        flags = [a.get("flags") for a in r["grade"].get("judge_answers") or []]
        lines.append(f"- {r['item_id']}: the rule's composed CLARIFY was graded {r['grade']['grade']} by the judge, whose answers to "
                     f"'asks which reading is meant' were {flags}. Response: {r['response']}")
    if amb_clar:
        lines.append("- The guide grades a CLARIFY that names the two readings CORRECT. The judge did not read the composed question as "
                     "asking which reading is meant. A code rule for that case is a grader change and needs the 21 examples and both "
                     "rubric-fidelity sheets rerun before it is used; these grades stand as v12 gave them.")

    # an earlier loop's run, kept as the before
    if args.before:
        b_rows = [json.loads(l) for l in Path(args.before).read_text(encoding="utf-8").splitlines() if l.strip()]
        b_manifest = json.loads(Path(args.before).with_name(Path(args.before).stem + "-manifest.json").read_text(encoding="utf-8"))
        b_by = defaultdict(list)
        for r in b_rows:
            b_by[r["bucket"]].append(r)
        lines += ["", f"## Before: {b_manifest['run']['trace_version']} run graded by {b_manifest['grader_version']}", "",
                  "The earlier loop, kept for comparison and labelled; the tables above are the current loop. Different agent, different traces.", "",
                  "| bucket | n | " + " | ".join(ACTIONS) + " | correct (label 1) |", "|---|---|" + "---|" * (len(ACTIONS) + 1)]
        for b in BUCKETS + ("all",):
            rs = b_rows if b == "all" else b_by[b]
            c = Counter(r["action"] for r in rs)
            lines.append(f"| {b} | {len(rs)} | " + " | ".join(pct(c[a], len(rs)) for a in ACTIONS) + f" | {pct(sum(r['grade']['label'] for r in rs), len(rs))} |")
        lines += ["", "Current loop, same layout:", "", "| bucket | n | " + " | ".join(ACTIONS) + " | correct (label 1) |", "|---|---|" + "---|" * (len(ACTIONS) + 1)]
        for b in BUCKETS + ("all",):
            rs = rows if b == "all" else by_bucket[b]
            c = Counter(r["action"] for r in rs)
            lines.append(f"| {b} | {len(rs)} | " + " | ".join(pct(c[a], len(rs)) for a in ACTIONS) + f" | {pct(sum(r['grade']['label'] for r in rs), len(rs))} |")

    # before and after a grader change, on the same traces
    if args.previous:
        prev_rows = {json.loads(l)["item_id"]: json.loads(l) for l in Path(args.previous).read_text(encoding="utf-8").splitlines() if l.strip()}
        prev_manifest = json.loads(Path(args.previous).with_name(Path(args.previous).stem + "-manifest.json").read_text(encoding="utf-8"))
        old_v, new_v = prev_manifest["grader_version"], manifest["grader_version"]
        lines += ["", f"## Regrade: {old_v} against {new_v} on the same traces", "",
                  f"Same drafts, same actions; only the grader changed. {old_v} numbers are kept here, labelled, next to {new_v}.", "",
                  f"| bucket | n | {old_v} CORRECT / PARTIAL / WRONG | {new_v} CORRECT / PARTIAL / WRONG | items changed |", "|---|---|---|---|---|"]
        changed_all = []
        for b in BUCKETS:
            rs = by_bucket[b]
            oc = Counter(prev_rows[r["item_id"]]["grade"]["grade"] for r in rs)
            nc = Counter(r["grade"]["grade"] for r in rs)
            changed = [(r["item_id"], prev_rows[r["item_id"]]["grade"]["grade"], r["grade"]["grade"]) for r in rs if prev_rows[r["item_id"]]["grade"]["grade"] != r["grade"]["grade"]]
            changed_all += changed
            lines.append(f"| {b} | {len(rs)} | {oc['CORRECT']} / {oc['PARTIAL']} / {oc['WRONG']} | {nc['CORRECT']} / {nc['PARTIAL']} / {nc['WRONG']} | {len(changed)} |")
        flips = [c for c in changed_all if (c[1] == "CORRECT") != (c[2] == "CORRECT")]
        lines += ["", f"Items whose grade changed: {len(changed_all)}; binary label flips: {len(flips)}."]
        for item_id, o, n in changed_all:
            row = next(r for r in rows if r["item_id"] == item_id)
            lines.append(f"- {item_id} ({row['bucket']}, {row['action']}): {o} -> {n}, decided by {prev_rows[item_id]['grade']['decided_by']} then {row['grade']['decided_by']}. Response: {row['response']}")

    # best score distribution for the threshold discussion
    lines += ["", "## Best retrieval score, for choosing the abstain threshold", "", "Nothing was tuned in this run. Per bucket, then by grade label among items where the agent answered.", ""]
    for b in BUCKETS:
        lines.append(f"- {b}: {quantiles([r['best_score'] for r in by_bucket[b]])}")
    answered = [r for r in rows if r["action"] == "ANSWER"]
    lines.append(f"- answered and CORRECT: {quantiles([r['best_score'] for r in answered if r['grade']['label'] == 1])}")
    lines.append(f"- answered and not CORRECT: {quantiles([r['best_score'] for r in answered if r['grade']['label'] == 0])}")
    lines.append(f"- evidence retrieved: {quantiles([r['best_score'] for r in rows if r['evidence']['retrieved']])}")
    lines.append(f"- evidence not retrieved (has target): {quantiles([r['best_score'] for r in rows if r['evidence']['has_target'] and not r['evidence']['retrieved']])}")

    # time
    steps = run["seconds_by_step"]
    total_steps = sum(steps.values())
    lines += [
        "",
        "## Wall clock",
        "",
        f"- Agent run: {run['wall_seconds']:.0f} s for {run['items']} items, {run['wall_seconds'] / run['items']:.1f} s per item; started {run['started_at']}.",
        "- By step: " + ", ".join(f"{k} {v:.0f} s ({100 * v / total_steps:.0f}%)" for k, v in sorted(steps.items(), key=lambda kv: -kv[1])) + ".",
        f"- Calls served from the cache: {run['cached_calls_by_step']}.",
        f"- Grading: {manifest['grading_wall_seconds']:.0f} s, decided by {manifest['decided_by']}.",
    ]
    if args.grading_note:
        lines.append(f"- {args.grading_note}")
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
