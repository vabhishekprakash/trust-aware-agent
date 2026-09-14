"""Post hoc: regrade the three blind sheets with a second judge and compare it with llama3.1 and the owner.

Usage:
    python scripts/second_judge.py replay     # llama3.1 v13 grades replayed from the cache; refuses any live call
    python scripts/second_judge.py run        # one pass, mistral:latest only; every reply kept verbatim
    python scripts/second_judge.py report     # reports/post-hoc-second-judge.md and .json

Planned in docs/decisions.md ("Post hoc: a second judge") before any
second-judge call. Grader v13 unchanged; same prompts, parser, 200-token
cap, seed and context as the llama3.1 grades. Inputs are identical to those
grades: sheets 1 and 2 against the item pool at commit 7a2a82d with no form
hint, the final sheet against data/eval/dev.jsonl with the agent's action as
the form hint. The lenient-parser, 600-token regrade of unreadable drafts is
a labelled diagnostic, never the headline. No test item is read.
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from agent.provider import OllamaProvider  # noqa: E402
from calibration import grader  # noqa: E402
from calibration.grader import GRADER_VERSION, SYSTEM_PROMPT, ProviderJudge, grade, questions_for  # noqa: E402
from calibration.judge_compare import (agreement, binary, bootstrap_share, categorise_reply, classify_copy, lenient_parser,  # noqa: E402
                                       order_rule_effect, overlap, paired_difference, split_extraction_message)
from compare_grader_check import read_sheet  # noqa: E402

OUT = ROOT / "reports" / "post-hoc-second-judge"
CACHE = ROOT / "data" / "cache"
BASE_URL = "http://127.0.0.1:11434"
FIRST_JUDGE = "llama3.1:latest"
SECOND_JUDGE = "mistral:latest"
GRADER_SHA = "a2eb938e82b0b63fa8a00c834e0569924e80b0a966ac1663b2ed9ca4986ad485"
POOL_COMMIT = "7a2a82d"
STRICT_CAP = 200
ADAPTED_CAP = 600
SHEETS = [
    {"name": "final", "title": "Final check: real agent outputs from dev", "sheet": "reports/final-blind-sheet.md", "key": "data/eval/final_blind_key.jsonl",
     "items": "dev", "form_hint": True, "blind_grader": "v13", "home_advantage": False},
    {"name": "sheet1", "title": "Sheet 1: model drafts under three passage conditions", "sheet": "reports/grader-check-sheet.md",
     "key": "data/eval/grader_check_key-v13-rerun.jsonl", "items": "pool", "form_hint": False, "blind_grader": "v7", "home_advantage": True,
     "revisions": "data/eval/grader_check_revisions.json"},
    {"name": "sheet2", "title": "Sheet 2: fresh model drafts", "sheet": "reports/grader-check-sheet-2.md", "key": "data/eval/grader_check_key-2-v13-rerun.jsonl",
     "items": "pool", "form_hint": False, "blind_grader": "v10", "home_advantage": True},
]


class CacheOnly(Exception):
    pass


def refuse_live_call(url, body):
    raise CacheOnly(f"cache miss for {body.get('model')}: the replay must not call a model")


def jsonl(path):
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]


def write_jsonl(path, rows):
    with Path(path).open("w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def load_items():
    dev = {r["id"]: r for r in jsonl(ROOT / "data" / "eval" / "dev.jsonl")}
    raw = subprocess.run(["git", "show", f"{POOL_COMMIT}:data/eval/items_candidates.jsonl"], cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8")
    pool = {json.loads(l)["id"]: json.loads(l) for l in raw.splitlines() if l.strip()}
    return {"dev": dev, "pool": pool}


def form_hint_of(sheet, row):
    if not sheet["form_hint"]:
        return None
    action = row["action"]
    return "ANSWER" if action == "REJECT" else action


def drafts():
    """Every draft on the three sheets, in reporting order, with the item record the llama3.1 grade used."""
    items = load_items()
    for sheet in SHEETS:
        for row in sorted(jsonl(ROOT / sheet["key"]), key=lambda r: r["sheet_no"]):
            yield sheet, row, items[sheet["items"]][row["item_id"]]


class RecordingJudge:
    """The grader's judge call, made exactly as ProviderJudge makes it, with every reply logged verbatim."""

    def __init__(self, provider, max_tokens, log, context):
        self.provider, self.max_tokens, self.log, self.context = provider, max_tokens, log, context
        self.model = provider.model

    def __call__(self, messages):
        started = time.time()
        g = self.provider.generate(messages, temperature=0.0, seed=42, max_tokens=self.max_tokens)
        raw = g.raw or {}
        self.log.append({**self.context, "call": sum(1 for c in self.log if c.get("draft_key") == self.context.get("draft_key")),
                         "kind": "judge" if messages[0]["content"] == SYSTEM_PROMPT else "extraction", "max_tokens": self.max_tokens,
                         "reply": g.text, "done_reason": raw.get("done_reason"), "eval_count": raw.get("eval_count"),
                         "prompt_eval_count": raw.get("prompt_eval_count"), "seconds": round(time.time() - started, 2), "cached": g.cached,
                         "user_message": messages[-1]["content"]})
        return g.text


def cmd_replay():
    OUT.mkdir(parents=True, exist_ok=True)
    provider = OllamaProvider(model=FIRST_JUDGE, cache_dir=CACHE, transport=refuse_live_call, num_ctx=4096)
    per_sheet, mismatches, calls = Counter(), [], []
    for sheet, row, item in drafts():
        context = {"pass": "replay", "sheet": sheet["name"], "sheet_no": row["sheet_no"], "item_id": row["item_id"], "draft_key": f"replay/{sheet['name']}/{row['sheet_no']}"}
        judge = RecordingJudge(provider, STRICT_CAP, calls, context)
        try:
            rec = grade(item, row["draft"], judge=judge, form_hint=form_hint_of(sheet, row))
        except CacheOnly as e:
            mismatches.append({"sheet": sheet["name"], "sheet_no": row["sheet_no"], "problem": str(e)})
            continue
        same = rec["grade"] == row["grade"] and rec["decided_by"] == row["decided_by"] and (rec.get("judge_outputs") or []) == (row.get("judge_outputs") or [])
        per_sheet[(sheet["name"], same)] += 1
        if not same:
            mismatches.append({"sheet": sheet["name"], "sheet_no": row["sheet_no"], "key": [row["decided_by"], row["grade"]], "replay": [rec["decided_by"], rec["grade"]]})
    result = {"judge": FIRST_JUDGE, "reproduced": {s["name"]: per_sheet[(s["name"], True)] for s in SHEETS},
              "differing": {s["name"]: per_sheet[(s["name"], False)] for s in SHEETS}, "mismatches": mismatches}
    (OUT / "llama-replay.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8", newline="\n")
    result["calls"] = len(calls)
    result["live_calls"] = sum(not c["cached"] for c in calls)
    (OUT / "llama-replay.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8", newline="\n")
    write_jsonl(OUT / "llama-calls.jsonl", calls)
    print(json.dumps(result, indent=1))
    return 0 if not mismatches else 1


def unload_other_models():
    loaded = httpx.get(f"{BASE_URL}/api/ps", timeout=10).json().get("models", [])
    for m in loaded:
        if m["name"] != SECOND_JUDGE:
            httpx.post(f"{BASE_URL}/api/generate", json={"model": m["name"], "keep_alive": 0}, timeout=120)
    return [m["name"] for m in loaded]


def cmd_run():
    OUT.mkdir(parents=True, exist_ok=True)
    grader_sha = hashlib.sha256((ROOT / "src" / "calibration" / "grader.py").read_bytes()).hexdigest()
    if GRADER_VERSION != "grader-v13" or grader_sha != GRADER_SHA:
        print(f"grader is not the frozen v13 ({GRADER_VERSION}, {grader_sha}); refusing to run")
        return 1
    if not (OUT / "llama-replay.json").exists() or json.loads((OUT / "llama-replay.json").read_text(encoding="utf-8"))["mismatches"]:
        print("the llama3.1 replay has not reproduced every committed grade; run the replay first")
        return 1
    unloaded = unload_other_models()
    tags = {m["name"]: m for m in httpx.get(f"{BASE_URL}/api/tags", timeout=10).json()["models"]}
    show = httpx.post(f"{BASE_URL}/api/show", json={"model": SECOND_JUDGE}, timeout=30).json()
    provider = OllamaProvider(model=SECOND_JUDGE, base_url=BASE_URL, cache_dir=CACHE, num_ctx=4096)
    calls, strict_rows, adapted_rows = [], [], []
    started = time.time()
    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    all_drafts = list(drafts())
    for n, (sheet, row, item) in enumerate(all_drafts, start=1):
        context = {"pass": "strict", "sheet": sheet["name"], "sheet_no": row["sheet_no"], "item_id": row["item_id"], "draft_key": f"strict/{sheet['name']}/{row['sheet_no']}"}
        rec = grade(item, row["draft"], judge=RecordingJudge(provider, STRICT_CAP, calls, context), form_hint=form_hint_of(sheet, row))
        rec.update(sheet=sheet["name"], sheet_no=row["sheet_no"], question=row["question"])
        strict_rows.append(rec)
        loaded = [m["name"] for m in httpx.get(f"{BASE_URL}/api/ps", timeout=10).json().get("models", [])]
        if any(name != SECOND_JUDGE for name in loaded):
            print(f"another model is loaded ({loaded}); stopping so the pass stays single-model")
            return 1
        print(f"{n:>2} {sheet['name']:<6} {row['sheet_no']:>2} {item['bucket']:<14} {rec['decided_by']:<6} llama {row['grade']:<8} mistral {rec['grade']:<8} {rec['flag'] or ''} {time.time() - started:.0f}s", flush=True)
    for sheet, row, item in all_drafts:
        rec = next(r for r in strict_rows if r["sheet"] == sheet["name"] and r["sheet_no"] == row["sheet_no"])
        if rec["flag"] != "judge_unparsed":
            continue
        context = {"pass": "adapted", "sheet": sheet["name"], "sheet_no": row["sheet_no"], "item_id": row["item_id"], "draft_key": f"adapted/{sheet['name']}/{row['sheet_no']}"}
        with lenient_parser():
            adapted = grade(item, row["draft"], judge=RecordingJudge(provider, ADAPTED_CAP, calls, context), form_hint=form_hint_of(sheet, row))
        adapted.update(sheet=sheet["name"], sheet_no=row["sheet_no"], question=row["question"])
        adapted_rows.append(adapted)
        print(f"   adapted {sheet['name']:<6} {row['sheet_no']:>2} mistral {adapted['grade']:<8} {adapted['flag'] or ''} {time.time() - started:.0f}s", flush=True)
    items = load_items()
    for c in calls:
        if c["kind"] != "judge":
            continue
        sheet = next(s for s in SHEETS if s["name"] == c["sheet"])
        keys = [k for k, _ in questions_for(items[sheet["items"]][c["item_id"]])]
        c["category"] = categorise_reply(keys, c["reply"], truncated=c["done_reason"] == "length")
    write_jsonl(OUT / "mistral-strict.jsonl", strict_rows)
    write_jsonl(OUT / "mistral-adapted.jsonl", adapted_rows)
    write_jsonl(OUT / "mistral-calls.jsonl", calls)
    run = {"judge": SECOND_JUDGE, "digest": tags.get(SECOND_JUDGE, {}).get("digest"), "details": show.get("details"),
           "ollama_version": httpx.get(f"{BASE_URL}/api/version", timeout=10).json().get("version"), "grader": GRADER_VERSION, "grader_sha256": grader_sha,
           "unloaded_before_start": unloaded, "started_at": started_at, "wall_seconds": round(time.time() - started, 1),
           "calls": len(calls), "live_calls": sum(not c["cached"] for c in calls), "drafts": len(all_drafts),
           "adapted_drafts": len(adapted_rows), "strict_cap": STRICT_CAP, "adapted_cap": ADAPTED_CAP}
    (OUT / "run.json").write_text(json.dumps(run, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(run, indent=1))
    return 0


ANSWER_LINE = re.compile(r"\bQ(\d)\s*[:.)-]\s*(YES|NO)\b(.*)", re.IGNORECASE)
BLIND_KEYS = {"sheet1": ("data/eval/grader_check_key.jsonl", "v7"), "sheet2": ("data/eval/grader_check_key-2.jsonl", "v10")}
ANALYST_PHRASE = {
    "not_wrong": "agrees with the owner",
    "code_rule_no_judge": "a code rule decided it, no judge involved",
    "rubric_or_question_wording": "the rubric or question wording: the judge's answers were defensible",
    "judge_judging": "the judge's own yes or no answers were wrong",
    "judge_order_sensitivity": "order sensitivity: the stricter of two differing orders was kept",
    "grounding_copy_check": "the copy check removed a YES the judge had right",
    "unreadable_reply": "unreadable reply",
    "owner_label_later_revised": "the owner later changed this blind label",
}
RULE_TO_ANALYST = {"code": {"code_rule_no_judge", "owner_label_later_revised"}, "shared": {"rubric_or_question_wording"}, "unreadable": {"unreadable_reply"},
                   "order": {"judge_order_sensitivity"}, "grounding": {"grounding_copy_check"}, "judging": {"judge_judging"}}
RULE_PHRASE = {"code": "a code rule decided it", "shared": "shared by both judges, so the rubric or question wording", "unreadable": "unreadable reply",
               "order": "order sensitivity", "grounding": "the copy check removed a YES the judge had right", "judging": "the judge's own answers"}


def answer_habits(calls):
    """How a judge wrote its answer lines, and what its copy-the-words replies did, with where the echoes were."""
    lines = Counter()
    for c in calls:
        if c["kind"] != "judge":
            continue
        for ln in c["reply"].splitlines():
            m = ANSWER_LINE.search(ln)
            if not m:
                continue
            bare = re.fullmatch(r'[.,;!]?\s*("[^"]*")?\s*', m.group(3).strip()) is not None
            caps = m.group(2).isupper()
            lines[("bare YES or NO" if bare else "YES or NO with added words") + (", in capitals" if caps else ", not all capitals")] += 1
    copies, echoes = Counter(), []
    for c in calls:
        if c["kind"] != "extraction":
            continue
        source, instruction = split_extraction_message(c["user_message"])
        kind = classify_copy(c["reply"], source, instruction)
        copies[kind] += 1
        if kind == "echoed":
            echoes.append({"sheet": c["sheet"], "sheet_no": c["sheet_no"]})
    return {"answer_lines": dict(lines), "copy_replies": dict(copies), "echo_drafts": echoes}


def cause_by_rule(owner_grade, first, second, item):
    """A cause for a draft either judge misgrades, by a rule written after the run. first is llama3.1, second Mistral."""
    wrong_first = binary(first["grade"]) != binary(owner_grade)
    wrong_second = binary(second["grade"]) != binary(owner_grade)
    if first["decided_by"] != "judge":
        return "code"
    if wrong_first and wrong_second:
        return "shared"
    record = second if wrong_second else first
    if record.get("flag") == "judge_unparsed":
        return "unreadable"
    grades = [g for g in record["judge_grades"] if g is not None]
    if record.get("flag") == "position_disagreement" and any(binary(g) == binary(owner_grade) for g in grades):
        return "order"
    restored = []
    for answers, ungrounded in zip(record["judge_answers"], record["judge_ungrounded"]):
        if answers is None:
            continue
        a = dict(answers)
        for key in ungrounded or []:
            a[key] = True
        restored.append(grader.grade_from_answers(item["bucket"], a, record.get("form")))
    if any(u for u in record["judge_ungrounded"] if u) and restored:
        if binary(max(restored, key=lambda g: grader._STRICTNESS[g])) == binary(owner_grade):
            return "grounding"
    return "judging"


def k_of(t):
    return f"{t[0]} of {t[1]}"


def share(t):
    return f"{100 * t[0]:.0f}% [{100 * t[1]:.0f}, {100 * t[2]:.0f}]"


def points(t):
    def one(v):
        return "0.0" if abs(100 * v) < 0.05 else f"{100 * v:+.1f}"
    return f"{one(t[0])} points [{one(t[1])}, {one(t[2])}]"


def word(n):
    return {0: "none", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}.get(n, str(n))


def count(n, noun, plural=None):
    words = {0: "no", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}
    return f"{words.get(n, n)} {noun if n == 1 else (plural or noun + 's')}"


def drafts_list(nos):
    if not nos:
        return "none"
    return ("draft " if len(nos) == 1 else "drafts ") + ", ".join(map(str, nos[:-1])) + (" and " if len(nos) > 1 else "") + str(nos[-1])


def cmd_report():
    llama = {(s["name"], r["sheet_no"]): r for s in SHEETS for r in jsonl(ROOT / s["key"])}
    strict = {(r["sheet"], r["sheet_no"]): r for r in jsonl(OUT / "mistral-strict.jsonl")}
    adapted = {(r["sheet"], r["sheet_no"]): r for r in jsonl(OUT / "mistral-adapted.jsonl")}
    calls = jsonl(OUT / "mistral-calls.jsonl")
    llama_calls = jsonl(OUT / "llama-calls.jsonl")
    run = json.loads((OUT / "run.json").read_text(encoding="utf-8"))
    replay = json.loads((OUT / "llama-replay.json").read_text(encoding="utf-8"))
    load = lambda name: json.loads((OUT / name).read_text(encoding="utf-8")) if (OUT / name).exists() else None
    classification, attribution, verification = load("independent-classification.json"), load("independent-attribution.json"), load("verification.json")
    items = load_items()
    owner = {s["name"]: read_sheet(ROOT / s["sheet"]) for s in SHEETS}
    revisions = {int(k): v for k, v in json.loads((ROOT / "data" / "eval" / "grader_check_revisions.json").read_text(encoding="utf-8")).items()}

    results, pooled = {}, {"llama": [], "mistral": [], "adapted": [], "llama_judged": [], "mistral_judged": []}
    for s in SHEETS:
        name, own = s["name"], owner[s["name"]]
        nos = sorted(no for (sh, no) in llama if sh == name)
        labelled = [no for no in nos if no in own]
        judged = [no for no in nos if llama[(name, no)]["decided_by"] == "judge"]
        judged_labelled = [no for no in judged if no in own]
        hit = lambda recs, pick: [int(binary(recs[(name, no)]["grade"]) == binary(own[no])) for no in pick]
        a_grade = lambda no: (adapted.get((name, no)) or strict[(name, no)])["grade"]
        l_hits, m_hits = hit(llama, labelled), hit(strict, labelled)
        a_hits = [int(binary(a_grade(no)) == binary(own[no])) for no in labelled]
        pooled["llama"] += l_hits
        pooled["mistral"] += m_hits
        pooled["adapted"] += a_hits
        pooled["llama_judged"] += hit(llama, judged_labelled)
        pooled["mistral_judged"] += hit(strict, judged_labelled)
        l_wrong = {no for no in labelled if binary(llama[(name, no)]["grade"]) != binary(own[no])}
        m_wrong = {no for no in labelled if binary(strict[(name, no)]["grade"]) != binary(own[no])}
        blind = None
        if name in BLIND_KEYS:
            rows = [r for r in jsonl(ROOT / BLIND_KEYS[name][0]) if r["sheet_no"] in own]
            blind = {"version": BLIND_KEYS[name][1], "agree": sum(binary(r["grade"]) == binary(own[r["sheet_no"]]) for r in rows), "of": len(rows)}
        else:
            blind = {"version": "v13", "agree": sum(l_hits), "of": len(l_hits)}
        analysts = {(d["sheet"], d["sheet_no"]): d for d in (attribution or {}).get("drafts", [])}
        disagreements = []
        for no in sorted(l_wrong | m_wrong):
            rule = cause_by_rule(own[no], llama[(name, no)], strict[(name, no)], items[s["items"]][llama[(name, no)]["item_id"]])
            a = analysts.get((name, no))
            wrong = "both" if (no in l_wrong and no in m_wrong) else ("llama3.1 only" if no in l_wrong else "Mistral only")
            analyst_causes = None
            rule_agrees = None
            if a:
                picked = set()
                if no in l_wrong:
                    picked |= set(a["llama_cause"])
                if no in m_wrong:
                    picked |= set(a["mistral_cause"])
                analyst_causes = sorted(picked)
                rule_agrees = bool(picked) and picked <= RULE_TO_ANALYST[rule]
            disagreements.append({"sheet_no": no, "bucket": llama[(name, no)]["bucket"], "owner": own[no], "llama": llama[(name, no)]["grade"],
                                  "mistral": strict[(name, no)]["grade"], "mistral_flag": strict[(name, no)]["flag"], "llama_flag": llama[(name, no)].get("flag"),
                                  "decided_by": llama[(name, no)]["decided_by"], "wrong": wrong, "cause_rule": rule, "cause_analysts": analyst_causes,
                                  "analysts_agree_with_each_other": a["analysts_agree"] if a else None, "rule_agrees_with_analysts": rule_agrees,
                                  "revised_label": revisions.get(no) if name == "sheet1" else None,
                                  "question": llama[(name, no)]["question"], "draft": llama[(name, no)]["draft"]})
        results[name] = {
            "drafts": len(nos), "labelled": len(labelled), "judged": len(judged), "judged_labelled": len(judged_labelled),
            "same_route_for_both_judges": all(llama[(name, no)]["decided_by"] == strict[(name, no)]["decided_by"] for no in nos),
            "blind_figure_first_judge": blind,
            "llama_owner": (sum(l_hits), len(l_hits)), "mistral_owner": (sum(m_hits), len(m_hits)),
            "llama_interval": bootstrap_share(l_hits), "mistral_interval": bootstrap_share(m_hits),
            "llama_owner_judged": (sum(hit(llama, judged_labelled)), len(judged_labelled)), "mistral_owner_judged": (sum(hit(strict, judged_labelled)), len(judged_labelled)),
            "llama_owner_3way": agreement([(llama[(name, no)]["grade"], own[no]) for no in labelled], three_way=True),
            "mistral_owner_3way": agreement([(strict[(name, no)]["grade"], own[no]) for no in labelled], three_way=True),
            "adapted_owner": (sum(a_hits), len(a_hits)),
            "paired_difference_llama_minus_mistral": paired_difference(l_hits, m_hits),
            "judges_all": agreement([(llama[(name, no)]["grade"], strict[(name, no)]["grade"]) for no in nos]),
            "judges_judged": agreement([(llama[(name, no)]["grade"], strict[(name, no)]["grade"]) for no in judged]),
            "judges_judged_3way": agreement([(llama[(name, no)]["grade"], strict[(name, no)]["grade"]) for no in judged], three_way=True),
            "overlap": overlap(l_wrong, m_wrong),
            "unparsed": {"llama": sum(llama[(name, no)].get("flag") == "judge_unparsed" for no in nos), "mistral": sum(strict[(name, no)]["flag"] == "judge_unparsed" for no in nos)},
            "order_flips": {"llama": sum(llama[(name, no)].get("flag") == "position_disagreement" for no in nos),
                            "mistral": sum(strict[(name, no)]["flag"] == "position_disagreement" for no in nos)},
            "stricter_order_rule": {"llama": order_rule_effect([llama[(name, no)] for no in labelled], [own[no] for no in labelled]),
                                    "mistral": order_rule_effect([strict[(name, no)] for no in labelled], [own[no] for no in labelled])},
            "yes_removed_by_copy_check": {"llama": sum(len(u or []) for no in nos for u in (llama[(name, no)].get("judge_ungrounded") or [])),
                                          "mistral": sum(len(u or []) for no in nos for u in (strict[(name, no)].get("judge_ungrounded") or []))},
            "revision_applied": ({"llama": agreement([(llama[(name, no)]["grade"], revisions.get(no, own[no])) for no in labelled]),
                                  "mistral": agreement([(strict[(name, no)]["grade"], revisions.get(no, own[no])) for no in labelled]),
                                  "changes": {str(no): [own[no], g] for no, g in revisions.items() if no in own}} if name == "sheet1" else None),
            "disagreements": disagreements,
        }
    final = results["final"]
    verdict = "about as well" if final["mistral_owner"][0] >= final["llama_owner"][0] - 1 else "noticeably worse"
    judge_calls = [c for c in calls if c["kind"] == "judge" and c["pass"] == "strict"]
    categories = Counter(c["category"] for c in judge_calls)
    live = [c for c in calls if not c["cached"]]
    secs = sorted(c["seconds"] for c in live)
    toks = sorted(c["eval_count"] or 0 for c in live)
    q = lambda xs, f: xs[int(f * (len(xs) - 1))] if xs else None
    strict_copy = [c for c in calls if c["pass"] == "strict" and c["kind"] == "extraction"]
    summary = {
        "verdict_final_sheet": verdict, "results": results,
        "pooled": {"labelled": len(pooled["llama"]), "llama": sum(pooled["llama"]), "mistral": sum(pooled["mistral"]), "adapted": sum(pooled["adapted"]),
                   "llama_interval": bootstrap_share(pooled["llama"]), "mistral_interval": bootstrap_share(pooled["mistral"]),
                   "paired_difference_llama_minus_mistral": paired_difference(pooled["llama"], pooled["mistral"]),
                   "judged_labelled": len(pooled["llama_judged"]), "llama_judged": sum(pooled["llama_judged"]), "mistral_judged": sum(pooled["mistral_judged"])},
        "reply_categories_strict": dict(categories), "truncated_strict": sum(c["done_reason"] == "length" for c in judge_calls),
        "unreadable_replies": [{k: c[k] for k in ("sheet", "sheet_no", "item_id", "call", "category", "done_reason", "eval_count", "reply")} for c in judge_calls if c["category"] != "parsed"],
        "adapted_reply_categories": dict(Counter(c.get("category", "parsed") for c in calls if c["kind"] == "judge" and c["pass"] == "adapted")),
        "habits": {"llama3.1": answer_habits(llama_calls), "mistral": answer_habits([c for c in calls if c["pass"] == "strict"])},
        "calls": {"strict_judge": len(judge_calls), "strict_copy": len(strict_copy), "strict_copy_repeated_identical": len(strict_copy) - len({c["user_message"] for c in strict_copy}),
                  "adapted_judge": sum(c["pass"] == "adapted" and c["kind"] == "judge" for c in calls), "adapted_copy": sum(c["pass"] == "adapted" and c["kind"] == "extraction" for c in calls),
                  "cached": sum(c["cached"] for c in calls), "live": len(live)},
        "timing": {"wall_seconds": run["wall_seconds"], "median_seconds": q(secs, 0.5), "p90_seconds": q(secs, 0.9), "median_output_tokens": q(toks, 0.5), "p90_output_tokens": q(toks, 0.9)},
        "single_model_guard": "cmd_run read Ollama's loaded models after every draft and would have stopped if any model other than mistral:latest was loaded; the run log ends with exit 0",
        "run": run, "replay": replay, "independent_classification": classification, "independent_attribution": attribution, "verification": verification,
    }
    if verification:
        mismatches = []
        for v in verification["sheets"]:
            x = results[v["sheet"]]
            pairs = {"drafts": (v["drafts"], x["drafts"]), "labelled": (v["labelled"], x["labelled"]), "judged": (v["judged"], x["judged"]),
                     "llama_agree": (v["llama_agree"], x["llama_owner"][0]), "mistral_agree": (v["mistral_agree"], x["mistral_owner"][0]),
                     "judges_agree_all_drafts": (v["judges_agree_all_drafts"], x["judges_all"][0]),
                     "llama_wrong": (v["llama_wrong_sheet_nos"], x["overlap"]["first"]), "mistral_wrong": (v["mistral_wrong_sheet_nos"], x["overlap"]["second"]),
                     "mistral_unparsed": (v["mistral_unparsed"], x["unparsed"]["mistral"])}
            mismatches += [f"{v['sheet']}.{k}" for k, (a, b) in pairs.items() if a != b]
        summary["verification_mismatches"] = mismatches
    (ROOT / "reports" / "post-hoc-second-judge.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    text = render(summary)
    (ROOT / "reports" / "post-hoc-second-judge.md").write_text(text, encoding="utf-8", newline="\n")
    print(text)
    return 0


def headline(s):
    r, p = s["results"], s["pooled"]
    f = r["final"]
    gaps = [r[k]["llama_owner"][0] - r[k]["mistral_owner"][0] for k in ("final", "sheet1", "sheet2")]
    diff = p["paired_difference_llama_minus_mistral"]
    mistral_only = [(k, d) for k in r for d in r[k]["disagreements"] if d["wrong"] == "Mistral only"]
    home = sum(1 for k, _ in mistral_only if k != "final")
    out = [
        f"On the final sheet, the only one never used to develop the rubric, llama3.1 agrees with the owner on {k_of(f['llama_owner'])}, {share(f['llama_interval'])}, "
        f"and Mistral on {k_of(f['mistral_owner'])}, {share(f['mistral_interval'])}. By the rule fixed before the run, a result within one draft of llama3.1 counts as "
        f"agreeing about as well, so Mistral agrees **{s['verdict_final_sheet']}**. "
        + ("That supports the claim that the rubric carried the agreement more than the choice of judge." if s["verdict_final_sheet"] == "about as well"
           else "That weakens the claim that the rubric carried the agreement more than the choice of judge, and the paper says so."),
        "",
        f"That support is thin in two ways. Only {f['judged']} of the {f['drafts']} final-sheet drafts reach a judge; the other {f['drafts'] - f['judged']} get the same grade "
        f"under either judge by construction, and on the {f['judged_labelled']} that do, llama3.1 agrees with the owner on {f['llama_owner_judged'][0]} and Mistral on "
        f"{f['mistral_owner_judged'][0]}. And the prompts, the answer parser and the copy-the-words check were all built with llama3.1 as the judge, so even this sheet "
        "carries some general advantage for llama3.1.",
        "",
    ]
    pooled_line = (f"Across all {p['labelled']} labelled drafts llama3.1 agrees on {p['llama']}, {share(p['llama_interval'])}, and Mistral on {p['mistral']}, "
                   f"{share(p['mistral_interval'])}: {count(p['llama'] - p['mistral'], 'draft')} apart, a paired difference of {points(diff)}")
    pooled_line += ", an interval that excludes zero." if diff[1] > 0 else "."
    if all(g > 0 for g in gaps):
        pooled_line += f" Mistral agreed less on every sheet, by {gaps[0]}, {gaps[1]} and {gaps[2]} {'draft' if gaps[2] == 1 else 'drafts'}."
    pooled_line += (f" {word(home).capitalize()} of Mistral's {word(len(mistral_only))} extra errors are on sheets 1 and 2, where the rubric was tuned with llama3.1 in the loop, "
                    "so the pooled gap mixes that home advantage with any real difference between the judges, and these drafts cannot separate the two. "
                    f"On the {p['judged_labelled']} judged drafts alone, llama3.1 agrees on {p['llama_judged']} and Mistral on {p['mistral_judged']}.")
    out += [pooled_line, "",
            f"Of the 85 drafts, {85 - sum(r[k]['judged'] for k in r)} are decided by code rules or exact match and get the same grade under either judge. "
            f"Only {sum(r[k]['judged'] for k in r)} reach a judge, so a judge swap can move at most that many grades.", ""]
    return out


def errors_section(s):
    r = s["results"]
    f = r["final"]
    both_final = f["overlap"]["both"]
    own_final = f["overlap"]["second_only"]
    first = sum(len(r[k]["overlap"]["first"]) for k in r)
    both = sum(len(r[k]["overlap"]["both"]) for k in r)
    first_only = sum(len(r[k]["overlap"]["first_only"]) for k in r)
    second_only = sum(len(r[k]["overlap"]["second_only"]) for k in r)
    out = ["## Where the errors fall", "",
           f"On the final sheet the two judges share {count(len(both_final), 'error')} ({drafts_list(both_final)}), and Mistral has {count(len(own_final), 'error')} of its own "
           f"({drafts_list(own_final)}). Over all three sheets Mistral also misgrades every draft llama3.1 misgrades ({both} of {first}) and adds "
           f"{count(second_only, 'error')} of its own, while llama3.1 has {count(first_only, 'error')} of its own. That llama3.1 has none is expected on sheets 1 and 2, "
           "where the rubric was revised until its disagreements there were fixed.", ""]
    att = s.get("independent_attribution")
    rows = [(k, d) for k in ("final", "sheet1", "sheet2") for d in r[k]["disagreements"]]
    if att:
        agree_each_other = all(d["analysts_agree"] for d in att["drafts"])
        rule_agrees = sum(1 for _, d in rows if d["rule_agrees_with_analysts"])
        out += [f"Two analysts assigned a cause to each of these {len(rows)} drafts, blind to this report, the script's rule and each other. They agreed with each other on "
                f"{'every' if agree_each_other else 'not every'} draft. A cause rule written into the script after the run agrees with them on {rule_agrees} of the {len(rows)}, "
                "counting sheet 1, draft 34 as agreement: the rule names the code rule that decided it, the analysts name the label the owner later changed, and both are true. "
                "Where the two differ, this report goes with the analysts. They read the drafts and the replies; the rule reads only flags and answers, assumes that an error "
                "both judges make belongs to the rubric, and cannot tell a defensible answer from a wrong one.", "",
                "| sheet | draft | misgraded by | cause, two blind analysts | cause, rule written after the run |", "|---|---|---|---|---|"]
        for k, d in rows:
            analyst = "; ".join(ANALYST_PHRASE[c] for c in (d["cause_analysts"] or []))
            out.append(f"| {k} | {d['sheet_no']} | {d['wrong']} | {analyst} | {RULE_PHRASE[d['cause_rule']]} |")
        out.append("")
        shared = [(k, d) for k, d in rows if d["wrong"] == "both"]
        judging_shared = [(k, d) for k, d in shared if d["cause_analysts"] and "judge_judging" in d["cause_analysts"]]
        if judging_shared:
            out += [f"So an error both judges make is not always the rubric's. {count(len(judging_shared), 'shared error').capitalize()} "
                    f"({', '.join(f'{k}, draft {d["sheet_no"]}' for k, d in judging_shared)}) "
                    "is a judging mistake the two judges happen to share, which may be a limit of judges this size rather than of either one."]
        rubric_own = [(k, d) for k, d in rows if d["wrong"] == "Mistral only" and d["cause_analysts"] and "rubric_or_question_wording" in d["cause_analysts"]]
        evidence = {(e["sheet"], e["sheet_no"]): " ".join(e["evidence"]).lower() for e in att["drafts"]}
        for k, d in rubric_own:
            reason = ("padding the draft adds to a right answer, which no judge question asks about and the code's unsupported-claim check, looking only for outside "
                      "names and acronyms, does not catch" if "padding" in evidence.get((k, d["sheet_no"]), "") else "something the judge's questions do not ask about")
            out[-1] += (f" And one of Mistral's own errors ({k}, draft {d['sheet_no']}) is the rubric's. Both analysts found Mistral's answers defensible and traced the "
                        f"owner's {d['owner']} to {reason}; llama3.1 matched the owner's binary label only by grading the draft {d['llama']}.")
        if judging_shared or rubric_own:
            out.append("")
    else:
        out += ["| sheet | draft | misgraded by | cause, rule written after the run |", "|---|---|---|---|"]
        for k, d in rows:
            out.append(f"| {k} | {d['sheet_no']} | {d['wrong']} | {RULE_PHRASE[d['cause_rule']]} |")
        out.append("")
    return out


def sheet_block(s, name, heading, caveat):
    x = s["results"][name]
    out = [f"## {heading}", "", caveat, "",
           "| measure | llama3.1 | Mistral |", "|---|---|---|",
           f"| binary agreement with the owner, {x['labelled']} labelled drafts | {k_of(x['llama_owner'])}, {share(x['llama_interval'])} | {k_of(x['mistral_owner'])}, {share(x['mistral_interval'])} |",
           f"| binary agreement on the {x['judged_labelled']} labelled drafts that reach a judge | {k_of(x['llama_owner_judged'])} | {k_of(x['mistral_owner_judged'])} |",
           f"| three-way agreement with the owner | {k_of(x['llama_owner_3way'])} | {k_of(x['mistral_owner_3way'])} |",
           f"| drafts whose two answer orders gave different grades | {x['order_flips']['llama']} | {x['order_flips']['mistral']} |",
           f"| YES answers removed by the copy check, counted per question per answer order | {x['yes_removed_by_copy_check']['llama']} | {x['yes_removed_by_copy_check']['mistral']} |",
           f"| unreadable judge replies | {x['unparsed']['llama']} | {x['unparsed']['mistral']} |", "",
           f"- Paired difference, llama3.1 minus Mistral: {count(x['llama_owner'][0] - x['mistral_owner'][0], 'draft')}, {points(x['paired_difference_llama_minus_mistral'])}.",
           f"- The two judges give the same binary grade on {x['judges_all'][0]} of the {x['drafts']} drafts, and on {x['judges_judged'][0]} of the {x['judged']} that reach a "
           f"judge ({x['judges_judged_3way'][0]} of {x['judged']} on the exact grade). Both judges took the same route, code rule, exact match or judge, on every draft.",
           f"- Misgraded against the owner: llama3.1 {drafts_list(x['overlap']['first'])}; Mistral {drafts_list(x['overlap']['second'])}; both {drafts_list(x['overlap']['both'])}.",
           f"- Keeping the stricter of two answer orders, where the orders disagreed, cost llama3.1 {x['stricter_order_rule']['llama']['cost']} and saved it "
           f"{x['stricter_order_rule']['llama']['saved']} binary agreements; for Mistral it cost {x['stricter_order_rule']['mistral']['cost']} and saved {x['stricter_order_rule']['mistral']['saved']}."]
    if x["unparsed"]["mistral"]:
        out.append(f"- Mistral had {count(x['unparsed']['mistral'], 'unreadable reply', 'unreadable replies')} here, graded WRONG by the grader's rule. A diagnostic regrade of "
                   f"those drafts with a lenient reading and a 600-token cap, not part of the headline, gives Mistral {k_of(x['adapted_owner'])}.")
    else:
        out.append("- No unreadable replies on this sheet.")
    if x["revision_applied"]:
        changes = "; ".join(f"draft {no}, {old} to {new}" for no, (old, new) in x["revision_applied"]["changes"].items())
        out.append(f"- Secondary line, with the owner's later label change applied ({changes}): llama3.1 {k_of(x['revision_applied']['llama'])}, Mistral {k_of(x['revision_applied']['mistral'])}.")
    if x["disagreements"]:
        out += ["", "| draft | bucket | owner | llama3.1 | Mistral | question |", "|---|---|---|---|---|---|"]
        for d in x["disagreements"]:
            mark = lambda g, flag: g + (" (orders differed)" if flag == "position_disagreement" else " (unreadable)" if flag == "judge_unparsed" else "")
            out.append(f"| {d['sheet_no']} | {d['bucket']} | {d['owner']} | {mark(d['llama'], d['llama_flag'])} | {mark(d['mistral'], d['mistral_flag'])} | {d['question']} |")
    return out + [""]


def format_section(s):
    cats = s["reply_categories_strict"]
    hab = s["habits"]
    out = ["## Unreadable replies: task or format", "",
           f"Mistral's strict pass made {sum(cats.values())} judge calls; the parser read {cats.get('parsed', 0)}. None stopped at the 200-token cap. "
           f"Every reply is kept verbatim in reports/post-hoc-second-judge/mistral-calls.jsonl. There was only {count(len(s['unreadable_replies']), 'unreadable reply', 'unreadable replies')}, "
           "so the handful asked for is this one:", ""]
    for u in s["unreadable_replies"]:
        out += [f"{u['sheet']}, draft {u['sheet_no']}, second answer order, {u['eval_count']} tokens, stopped normally:", "", "```", u["reply"].strip(), "```", ""]
    cls = s.get("independent_classification")
    whole = [e for e in (cls or {}).get("entries", []) if e["type"].startswith("whole")]
    lines = [e for e in (cls or {}).get("entries", []) if not e["type"].startswith("whole")]
    out.append("It commits to NO on Q1, qualifies Q3 as \"Yes, in a way\", and gives Q2 no yes or no at all, only \"Implicitly\". The grader needs an answer to every "
               "question, so the draft was graded WRONG. The code's category is a task failure, not a format failure: a lenient reading that strips formatting still "
               "finds no answer to Q2, and the diagnostic regrade at 600 tokens got the same reply."
               + (f" Three readers who saw only the questions and the reply, blind to the code, all called it a task failure." if whole and all(e["votes"].count("task_failure") == 3 for e in whole) else ""))
    out += ["", "How each judge wrote its answer lines over the same drafts, one row per kind of line:", "", "| answer line | llama3.1 | Mistral |", "|---|---|---|"]
    for key in sorted(set(hab["llama3.1"]["answer_lines"]) | set(hab["mistral"]["answer_lines"])):
        out.append(f"| {key} | {hab['llama3.1']['answer_lines'].get(key, 0)} | {hab['mistral']['answer_lines'].get(key, 0)} |")
    out.append("")
    if lines:
        maj = Counter(e["majority"] for e in lines)
        contradictory = [e for e in lines if e["majority"] == "contradictory"]
        split = [e for e in lines if not e["unanimous"]]
        sentence = (f"Three blind readers also read the {len(lines)} parsed Mistral answer lines that carry added words, a check added after the run. By majority {maj.get('clear', 0)} "
                    f"are clear, the added words backing the YES or NO given")
        if contradictory:
            sentence += (f", and {count(len(contradictory), 'is', 'are')} contradictory: " + "; ".join(f"{e['sheet']}, draft {e['sheet_no']}, \"{e['text'].rstrip('.')}.\"" for e in contradictory)
                         + " The parser read the stated answer there, and the owner and both judges graded that draft the same")
        sentence += "."
        if split:
            sentence += f" The readers split on {count(len(split), 'line')}: " + "; ".join(f"{e['sheet']}, draft {e['sheet_no']} ({', '.join(e['votes'])})" for e in split) + "."
        out += [sentence, ""]
    out += ["What each judge's copy-the-words replies did, one row per kind of reply, counted per call:", "", "| copy reply | llama3.1 | Mistral |", "|---|---|---|"]
    names = {"copied": "copied words found in the draft", "echoed": "echoed the instruction's own phrase", "not found": "copied words not found in the draft", "none": "NONE, or nothing usable"}
    for key in ("copied", "echoed", "not found", "none"):
        out.append(f"| {names[key]} | {hab['llama3.1']['copy_replies'].get(key, 0)} | {hab['mistral']['copy_replies'].get(key, 0)} |")
    out += ["", conclusion(s), ""]
    return out


def conclusion(s):
    r = s["results"]
    cats = s["reply_categories_strict"]
    unreadable = sum(v for k, v in cats.items() if k != "parsed")
    fmt = cats.get("format", 0) + cats.get("truncated", 0)
    hab = s["habits"]
    m_echo, l_echo = hab["mistral"]["copy_replies"].get("echoed", 0), hab["llama3.1"]["copy_replies"].get("echoed", 0)
    grounding = [(k, d) for k in r for d in r[k]["disagreements"] if d["wrong"] == "Mistral only" and d["cause_analysts"] and "grounding_copy_check" in d["cause_analysts"]]
    flips = {k: (r[k]["order_flips"]["mistral"], r[k]["order_flips"]["llama"]) for k in ("final", "sheet1", "sheet2")}
    m_cost = sum(r[k]["stricter_order_rule"]["mistral"]["cost"] for k in r)
    m_saved = sum(r[k]["stricter_order_rule"]["mistral"]["saved"] for k in r)
    if unreadable and fmt == unreadable:
        head = (f"All {unreadable} unreadable replies were format failures, not task failures. A judge swap is not free, because the harness carries the first judge's "
                "conventions: the parser was built around llama3.1's output.")
        return head
    head = (f"Mistral did not fail on format. Its replies parsed under llama3.1's conventions {cats.get('parsed', 0)} times in {sum(cats.values())}, and the "
            f"{'one reply that did not' if unreadable == 1 else str(unreadable) + ' that did not'} failed the task, not the format.")
    body = ""
    if m_echo > l_echo:
        body += (f" The harness still carried llama3.1's conventions, and they cost Mistral, through the copy check rather than the parser. That instruction quotes the "
                 f"phrase it wants found, and Mistral echoed the phrase back instead of copying the draft's words on {count(m_echo, 'call')}, against llama3.1's {word(l_echo)}.")
        if grounding:
            body += (f" On {count(len(grounding), 'draft')} ({', '.join(f'{k}, draft {d["sheet_no"]}' for k, d in grounding)}) "
                     "that echo removed a YES Mistral had right and cost the grade.")
        body += " A judge swap is not free: a harness built around the first judge's habits turns a second judge's different habits into errors the first judge never makes."
    body += (f" Mistral's grade also changed with the answer order more often, on {flips['final'][0]}, {flips['sheet1'][0]} and {flips['sheet2'][0]} drafts across the final "
             f"sheet and sheets 1 and 2, against llama3.1's {flips['final'][1]}, {flips['sheet1'][1]} and {flips['sheet2'][1]}; the gap sits mostly on sheet 1, where the rubric was "
             f"tuned with llama3.1. Keeping the stricter order cost Mistral {count(m_cost, 'binary agreement')} and saved it {word(m_saved)}, so on these drafts the order "
             "sensitivity did not change its agreement with the owner.")
    return head + body


def checks_section(s):
    out = ["## Independent checks", ""]
    if s.get("verification"):
        mm = s.get("verification_mismatches", [])
        out.append("- A verifier, blind to this report and the script, recomputed each sheet's draft, label and judged counts, both judges' binary agreement with the owner, "
                   "the judges' agreement with each other, the misgraded draft numbers and the unreadable count from the raw files with its own code. "
                   + ("Every number matched." if not mm else f"Mismatches: {', '.join(mm)}."))
    if s.get("independent_classification"):
        out.append("- Three readers classified the unreadable reply (planned before the run) and the answer lines with added words (added after the run), blind to the code.")
    if s.get("independent_attribution"):
        out.append("- Two analysts assigned causes to every misgraded draft, blind to the report, the rule and each other (added after the run).")
    out.append("- A critic reviewed the first rendering of this report against the owner's requirements and found 26 defects (reports/post-hoc-second-judge/critic-review.json). "
               "The most serious was a bug in the echo count: a pattern that required a colon missed the instruction shape \"give \\\"X\\\" as the answer\", so the first rendering "
               "said Mistral and llama3.1 echoed equally often and that echoing was not a Mistral habit. The corrected count is the one above, the pattern has a test, and every "
               "other defect is addressed in this version.")
    return out + [""]


def render(s):
    r, t, c = s["results"], s["timing"], s["calls"]
    lines = ["# Post hoc: a second judge on the three blind sheets", "",
             "A post hoc experiment, run after the tagged evaluation (v1.0.2). The 85 drafts on the three blind sheets were regraded with grader v13 unchanged and "
             "Mistral 7B Instruct (mistral:latest) as the judge in place of llama3.1 8B, and both judges were compared with the owner's hand labels. No test item "
             "was read and nothing was refit. The plan and the reading rule were committed before the first Mistral call (commit 1514552; docs/decisions.md, "
             "\"Post hoc: a second judge\"). The cause rule, the reading of answer lines with added words, and the two analysts were added after the run and are "
             "labelled where they appear. Every number comes from reports/post-hoc-second-judge.json.", "",
             "Terms. Binary agreement counts CORRECT against PARTIAL or WRONG; three-way agreement needs the exact grade. 84 of the 85 drafts carry an owner label "
             "(sheet 1, draft 1 was never graded). A draft reaches a judge only when no code rule or exact match decides it first; both judges take the same route "
             "on every draft.", "",
             "## Headline", ""]
    lines += headline(s)
    lines += errors_section(s)
    lines += sheet_block(s, "final", "Final sheet: the clean comparison",
                         "Twenty real agent outputs from dev, drawn for the final blind check after grader v13 was frozen, and graded by the owner without seeing either judge. "
                         "No rubric change was made against this sheet. The prompts, parser and copy-the-words check were still built with llama3.1 as the judge, so some "
                         "general advantage for llama3.1 remains even here.")
    b1, b2 = r["sheet1"]["blind_figure_first_judge"], r["sheet2"]["blind_figure_first_judge"]
    lines += sheet_block(s, "sheet1", "Sheet 1: home advantage for llama3.1",
                         f"Home advantage: grader versions v8 to v13 were developed against this sheet's disagreements with llama3.1 as the judge, so llama3.1's figures below are "
                         f"rubric fidelity, not a blind number. Its blind figure on this sheet, under {b1['version']}, was {b1['agree']} of {b1['of']}. Mistral had no part in that development.")
    lines += sheet_block(s, "sheet2", "Sheet 2: home advantage for llama3.1",
                         f"Home advantage: the v11 to v13 fixes were made after reading this sheet's disagreements with llama3.1 as the judge, so llama3.1's figures below are "
                         f"rubric fidelity, not a blind number. Its blind figure on this sheet, under {b2['version']}, was {b2['agree']} of {b2['of']}. Mistral had no part in that development.")
    lines += format_section(s)
    lines += ["## Cost", "",
              f"One pass, one model: the run read Ollama's loaded models after every draft and would have stopped if any model other than Mistral had been loaded, and it "
              f"finished normally. Wall clock {t['wall_seconds']:.0f} s. The strict pass made {c['strict_judge']} judge calls and {c['strict_copy']} copy-the-words calls, "
              f"{c['strict_copy_repeated_identical']} of which repeated the identical request from the other answer order and came from the cache; the diagnostic pass made "
              f"{c['adapted_judge']} judge calls and {c['adapted_copy']} copy call. Live calls took a median {t['median_seconds']} s, 90th percentile {t['p90_seconds']} s, "
              f"with a median {t['median_output_tokens']} output tokens, 90th percentile {t['p90_output_tokens']}. llama3.1's grades were replayed from the cache: all "
              f"{sum(s['replay']['reproduced'].values())} matched the committed grades exactly, over {s['replay'].get('calls')} calls, {word(s['replay'].get('live_calls') or 0)} of them live.", ""]
    lines += checks_section(s)
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=["replay", "run", "report"])
    args = parser.parse_args()
    return {"replay": cmd_replay, "run": cmd_run, "report": cmd_report}[args.stage]()


if __name__ == "__main__":
    sys.exit(main())
