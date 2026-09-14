"""Post hoc: regrade the three blind sheets with a second judge and compare it with llama3.1 and the owner.

Usage:
    python scripts/second_judge.py replay     # llama3.1 v13 grades replayed from the cache; refuses any live call
    python scripts/second_judge.py run        # one pass, mistral:latest only; every reply kept verbatim
    python scripts/second_judge.py regrade    # mistral:latest only, the drafts whose item differs between the run's pool and the draw-time pool
    python scripts/second_judge.py report     # reports/post-hoc-second-judge.md and .json

Planned in docs/decisions.md ("Post hoc: a second judge") before any
second-judge call. Grader v13 unchanged; same prompts, parser, 200-token
cap, seed and context as the llama3.1 grades. Inputs are identical to those
grades: each sheet against the item pool it was drawn from (sheet 1 at
1cc8664, sheet 2 at 7a2a82d) with no form hint, the final sheet against data/eval/dev.jsonl with the agent's action as
the form hint. The lenient-parser, 600-token regrade of unreadable drafts is
a labelled diagnostic, never the headline. No test item is read.

The first run graded both sheets against 7a2a82d. Sheet 1 was drawn at
1cc8664, and one of its items changed between the two, so the regrade stage
grades that draft again with Mistral and the report merges it in.
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
from calibration.judge_compare import (agreement, binary, bootstrap_share, categorise_reply, classify_copy, copy_target, lenient_parser,  # noqa: E402
                                       order_rule_effect, overlap, paired_difference, split_extraction_message)
from compare_grader_check import read_sheet  # noqa: E402

OUT = ROOT / "reports" / "post-hoc-second-judge"
CACHE = ROOT / "data" / "cache"
BASE_URL = "http://127.0.0.1:11434"
FIRST_JUDGE = "llama3.1:latest"
SECOND_JUDGE = "mistral:latest"
GRADER_SHA = "a2eb938e82b0b63fa8a00c834e0569924e80b0a966ac1663b2ed9ca4986ad485"
RUN_POOL = "7a2a82d"  # the pool the first Mistral run used for both sheets
STRICT_CAP = 200
ADAPTED_CAP = 600
SHEETS = [
    {"name": "final", "title": "Final check: real agent outputs from dev", "sheet": "reports/final-blind-sheet.md", "key": "data/eval/final_blind_key.jsonl",
     "items": "dev", "form_hint": True, "blind_grader": "v13", "home_advantage": False},
    {"name": "sheet1", "title": "Sheet 1: model drafts under three passage conditions", "sheet": "reports/grader-check-sheet.md",
     "key": "data/eval/grader_check_key-v13-rerun.jsonl", "items": "pool", "pool": "1cc8664", "form_hint": False, "blind_grader": "v7", "home_advantage": True,
     "revisions": "data/eval/grader_check_revisions.json"},
    {"name": "sheet2", "title": "Sheet 2: fresh model drafts", "sheet": "reports/grader-check-sheet-2.md", "key": "data/eval/grader_check_key-2-v13-rerun.jsonl",
     "items": "pool", "pool": "7a2a82d", "form_hint": False, "blind_grader": "v10", "home_advantage": True},
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


def pool_at(commit):
    raw = subprocess.run(["git", "show", f"{commit}:data/eval/items_candidates.jsonl"], cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8")
    return {json.loads(l)["id"]: json.loads(l) for l in raw.splitlines() if l.strip()}


def load_items():
    """Items by source: dev, and the pool at every commit a sheet was drawn from or the first run used."""
    items = {"dev": {r["id"]: r for r in jsonl(ROOT / "data" / "eval" / "dev.jsonl")}}
    for commit in {RUN_POOL} | {s["pool"] for s in SHEETS if s.get("pool")}:
        items[f"pool@{commit}"] = pool_at(commit)
    return items


def item_of(items, sheet, item_id, commit=None):
    """The item record a sheet's draft is graded against: its draw-time pool, or dev for the final sheet."""
    if sheet["items"] == "dev":
        return items["dev"][item_id]
    return items[f"pool@{commit or sheet['pool']}"][item_id]


def affected_drafts():
    """Drafts whose item record differs between the first run's pool and the sheet's draw-time pool."""
    items = load_items()
    out = []
    for sheet in SHEETS:
        if sheet["items"] == "dev" or sheet["pool"] == RUN_POOL:
            continue
        for row in jsonl(ROOT / sheet["key"]):
            before, now = item_of(items, sheet, row["item_id"], RUN_POOL), item_of(items, sheet, row["item_id"])
            if before != now:
                out.append({"sheet": sheet["name"], "sheet_no": row["sheet_no"], "item_id": row["item_id"],
                            "fields": sorted(k for k in set(before) | set(now) if before.get(k) != now.get(k)),
                            "bucket": [before.get("bucket"), now.get("bucket")]})
    return out


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
            yield sheet, row, item_of(items, sheet, row["item_id"])


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
        keys = [k for k, _ in questions_for(item_of(items, sheet, c["item_id"]))]
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


def cmd_regrade():
    OUT.mkdir(parents=True, exist_ok=True)
    grader_sha = hashlib.sha256((ROOT / "src" / "calibration" / "grader.py").read_bytes()).hexdigest()
    if GRADER_VERSION != "grader-v13" or grader_sha != GRADER_SHA:
        print(f"grader is not the frozen v13 ({GRADER_VERSION}, {grader_sha}); refusing to run")
        return 1
    replay = json.loads((OUT / "llama-replay.json").read_text(encoding="utf-8"))
    if replay["mismatches"]:
        print("the llama3.1 replay has not reproduced every committed grade under the draw-time pools; run the replay first")
        return 1
    affected = affected_drafts()
    wanted = {(a["sheet"], a["sheet_no"]) for a in affected}
    unloaded = unload_other_models()
    tags = {m["name"]: m for m in httpx.get(f"{BASE_URL}/api/tags", timeout=10).json()["models"]}
    provider = OllamaProvider(model=SECOND_JUDGE, base_url=BASE_URL, cache_dir=CACHE, num_ctx=4096)
    calls, strict_rows, adapted_rows = [], [], []
    started, started_at = time.time(), datetime.now(timezone.utc).isoformat(timespec="seconds")
    todo = [(sheet, row, item) for sheet, row, item in drafts() if (sheet["name"], row["sheet_no"]) in wanted]
    for sheet, row, item in todo:
        context = {"pass": "strict", "stage": "draw-pool regrade", "sheet": sheet["name"], "sheet_no": row["sheet_no"], "item_id": row["item_id"],
                   "draft_key": f"regrade/strict/{sheet['name']}/{row['sheet_no']}"}
        rec = grade(item, row["draft"], judge=RecordingJudge(provider, STRICT_CAP, calls, context), form_hint=form_hint_of(sheet, row))
        rec.update(sheet=sheet["name"], sheet_no=row["sheet_no"], question=row["question"])
        strict_rows.append(rec)
        loaded = [m["name"] for m in httpx.get(f"{BASE_URL}/api/ps", timeout=10).json().get("models", [])]
        if any(name != SECOND_JUDGE for name in loaded):
            print(f"another model is loaded ({loaded}); stopping so the pass stays single-model")
            return 1
        if rec["flag"] == "judge_unparsed":
            context = {**context, "pass": "adapted", "draft_key": f"regrade/adapted/{sheet['name']}/{row['sheet_no']}"}
            with lenient_parser():
                adapted = grade(item, row["draft"], judge=RecordingJudge(provider, ADAPTED_CAP, calls, context), form_hint=form_hint_of(sheet, row))
            adapted.update(sheet=sheet["name"], sheet_no=row["sheet_no"], question=row["question"])
            adapted_rows.append(adapted)
        print(f"{sheet['name']:<6} {row['sheet_no']:>2} {item['bucket']:<14} {rec['decided_by']:<6} llama {row['grade']:<8} mistral {rec['grade']:<8} {rec['flag'] or ''}", flush=True)
    items = load_items()
    for c in calls:
        if c["kind"] == "judge":
            sheet = next(s for s in SHEETS if s["name"] == c["sheet"])
            c["category"] = categorise_reply([k for k, _ in questions_for(item_of(items, sheet, c["item_id"]))], c["reply"], truncated=c["done_reason"] == "length")
    write_jsonl(OUT / "mistral-regrade-strict.jsonl", strict_rows)
    write_jsonl(OUT / "mistral-regrade-adapted.jsonl", adapted_rows)
    write_jsonl(OUT / "mistral-regrade-calls.jsonl", calls)
    regrade = {"judge": SECOND_JUDGE, "digest": tags.get(SECOND_JUDGE, {}).get("digest"), "grader": GRADER_VERSION, "grader_sha256": grader_sha,
               "first_run_pool": RUN_POOL, "draw_pools": {s["name"]: s.get("pool") for s in SHEETS}, "affected": affected,
               "unloaded_before_start": unloaded, "started_at": started_at, "wall_seconds": round(time.time() - started, 1),
               "calls": len(calls), "live_calls": sum(not c["cached"] for c in calls), "adapted_drafts": len(adapted_rows),
               "single_model_guard": "read Ollama's loaded models after every draft; would have stopped if any model other than mistral:latest was loaded"}
    (OUT / "regrade.json").write_text(json.dumps(regrade, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(regrade, indent=1))
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
    run_calls = jsonl(OUT / "mistral-calls.jsonl")
    regrade = json.loads((OUT / "regrade.json").read_text(encoding="utf-8")) if (OUT / "regrade.json").exists() else None
    regraded = set()
    if regrade:
        regraded = {(a["sheet"], a["sheet_no"]) for a in regrade["affected"]}
        for key in regraded:
            adapted.pop(key, None)
        strict.update({(r["sheet"], r["sheet_no"]): r for r in jsonl(OUT / "mistral-regrade-strict.jsonl")})
        adapted.update({(r["sheet"], r["sheet_no"]): r for r in jsonl(OUT / "mistral-regrade-adapted.jsonl")})
    regrade_calls = jsonl(OUT / "mistral-regrade-calls.jsonl") if regrade else []
    calls = [c for c in run_calls if (c["sheet"], c["sheet_no"]) not in regraded] + regrade_calls
    llama_calls = jsonl(OUT / "llama-calls.jsonl")
    run = json.loads((OUT / "run.json").read_text(encoding="utf-8"))
    replay = json.loads((OUT / "llama-replay.json").read_text(encoding="utf-8"))
    load = lambda name: json.loads((OUT / name).read_text(encoding="utf-8")) if (OUT / name).exists() else None
    classification, attribution, verification = load("independent-classification.json"), load("independent-attribution.json"), load("verification.json")
    corrections_check = load("corrections-verification.json")
    regrade_check = load("regrade-verification.json")
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
            rule = cause_by_rule(own[no], llama[(name, no)], strict[(name, no)], item_of(items, s, llama[(name, no)]["item_id"]))
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
    live = [c for c in run_calls if not c["cached"]]
    secs = sorted(c["seconds"] for c in live)
    toks = sorted(c["eval_count"] or 0 for c in live)
    q = lambda xs, f: xs[int(f * (len(xs) - 1))] if xs else None
    run_judge_calls = [c for c in run_calls if c["kind"] == "judge" and c["pass"] == "strict"]
    strict_copy = [c for c in run_calls if c["pass"] == "strict" and c["kind"] == "extraction"]
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
        "calls": {"strict_judge": len(run_judge_calls), "strict_copy": len(strict_copy), "strict_copy_repeated_identical": len(strict_copy) - len({c["user_message"] for c in strict_copy}),
                  "adapted_judge": sum(c["pass"] == "adapted" and c["kind"] == "judge" for c in run_calls), "adapted_copy": sum(c["pass"] == "adapted" and c["kind"] == "extraction" for c in run_calls),
                  "cached": sum(c["cached"] for c in run_calls), "live": len(live), "note": "the first run's calls; the regrade's are under regrade"},
        "regrade": ({**regrade, "judge_calls": sum(c["kind"] == "judge" for c in regrade_calls), "copy_calls": sum(c["kind"] == "extraction" for c in regrade_calls),
                     "grades": {f"{k[0]}/{k[1]}": {"mistral": strict[k]["grade"], "llama": llama[k]["grade"], "decided_by": strict[k]["decided_by"]} for k in sorted(regraded)}}
                    if regrade else None),
        "timing": {"wall_seconds": run["wall_seconds"], "median_seconds": q(secs, 0.5), "p90_seconds": q(secs, 0.9), "median_output_tokens": q(toks, 0.5), "p90_output_tokens": q(toks, 0.9)},
        "single_model_guard": "cmd_run read Ollama's loaded models after every draft and would have stopped if any model other than mistral:latest was loaded; the run log ends with exit 0",
        "harness_lock_in": harness_facts(calls, llama_calls, strict, llama, results),
        "who_ran_the_checks": "The owner's labels are the only human judgement. The readers, analysts, verifier and critic were language-model agents, not people.",
        "run": run, "replay": replay, "independent_classification": classification, "independent_attribution": attribution, "verification": verification,
        "regrade_verification": regrade_check,
        "corrections_verification": ({**{k: v for k, v in corrections_check.items() if k not in ("reviewers", "later_rounds")},
                                      "later_rounds": [{k: v for k, v in r.items() if k != "reviewers"} for r in corrections_check.get("later_rounds", [])],
                                      "later_confirmed": sum(r["confirmed"] for r in corrections_check.get("later_rounds", []))} if corrections_check else None),
    }
    if verification:
        mismatches = []
        regraded_sheets = {k[0] for k in regraded}
        summary["verification_scope"] = {"regraded_sheets": sorted(regraded_sheets), "compared_now": sorted(v["sheet"] for v in verification["sheets"] if v["sheet"] not in regraded_sheets)}
        for v in verification["sheets"]:
            if v["sheet"] in regraded_sheets:
                continue
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


MODEL_RUN = "language-model agents, not people"


def harness_facts(s_calls, l_calls, strict, llama, results):
    """What each judge's copy-the-words replies did on requests that quote a phrase to find, and the echo that cost a grade, from the call logs."""
    def facts(calls):
        extraction = [c for c in calls if c["kind"] == "extraction"]
        echoes, none_quoting, targeted = [], [], {}
        for c in extraction:
            source, instruction = split_extraction_message(c["user_message"])
            kind, target = classify_copy(c["reply"], source, instruction), copy_target(instruction)
            if target:
                targeted.setdefault(c["user_message"], set()).add(kind)
            row = {"sheet": c["sheet"], "sheet_no": c["sheet_no"], "cached": c["cached"], "phrase": target, "reply": c["reply"].strip(), "user_message": c["user_message"]}
            if kind == "echoed":
                echoes.append(row)
            elif kind == "none quoting a phrase":
                none_quoting.append(row)
        return {"calls": len(extraction), "requests": len({c["user_message"] for c in extraction}), "requests_quoting_a_phrase_to_find": len(targeted),
                "echo_calls": len(echoes), "echo_requests": len({e["user_message"] for e in echoes}), "echoes": echoes, "none_quoting_a_phrase": none_quoting,
                "_targeted": targeted}
    m, l = facts([c for c in s_calls if c["pass"] == "strict"]), facts(l_calls)
    where_of = {c["user_message"]: (c["sheet"], c["sheet_no"]) for c in l_calls if c["kind"] == "extraction"}
    both_met = [{"sheet": where_of[u][0], "sheet_no": where_of[u][1], "llama3.1": sorted(l["_targeted"][u]), "mistral": sorted(m["_targeted"][u])}
                for u in sorted(set(m["_targeted"]) & set(l["_targeted"]), key=lambda u: where_of[u])]
    del m["_targeted"], l["_targeted"]
    mistral_only = {(k, d["sheet_no"]): d for k, x in results.items() for d in x["disagreements"] if d["wrong"] == "Mistral only"}
    costly, harmless = [], []
    for e in {e["user_message"]: e for e in m["echoes"]}.values():
        d = mistral_only.get((e["sheet"], e["sheet_no"]))
        if d and d["cause_analysts"] and "grounding_copy_check" in d["cause_analysts"]:
            same_request = [c for c in l_calls if c["kind"] == "extraction" and c["user_message"] == e["user_message"]]
            costly.append({"sheet": e["sheet"], "sheet_no": e["sheet_no"], "phrase": e["phrase"], "mistral_copied": e["reply"],
                           "llama_copied": same_request[0]["reply"].strip() if same_request else None, "owner": d["owner"],
                           "llama_grade": d["llama"], "mistral_grade": d["mistral"], "draft": d["draft"]})
        else:
            harmless.append({"sheet": e["sheet"], "sheet_no": e["sheet_no"], "source": split_extraction_message(e["user_message"])[0]})
    strip = lambda f: {k: ([{kk: vv for kk, vv in e.items() if kk != "user_message"} for e in v] if isinstance(v, list) else v) for k, v in f.items()}
    return {"mistral": strip(m), "llama3.1": strip(l), "requests_both_judges_met": both_met, "costly": costly, "echoes_that_cost_nothing": harmless,
            "note": "echo: the reply gives back the phrase the instruction quotes as the thing to find (give \"X\" as the answer, or state this correction: \"X\"), "
                    "and that phrase is not in the text checked. "
                    "A reply opening with NONE that quotes a phrase in its explanation is counted apart; an earlier version of the classifier counted it as an echo."}


def headline(s):
    r, p, h = s["results"], s["pooled"], s["harness_lock_in"]
    f = r["final"]
    diff = p["paired_difference_llama_minus_mistral"]
    mistral_only = [(k, d) for k in ("final", "sheet1", "sheet2") for d in r[k]["disagreements"] if d["wrong"] == "Mistral only"]
    on_tuned = [(k, d) for k, d in mistral_only if k != "final"]
    by_copy = [(k, d) for k, d in mistral_only if k == "final" and d["cause_analysts"] and "grounding_copy_check" in d["cause_analysts"]]
    first = sum(len(r[k]["overlap"]["first"]) for k in r)
    shared = [(k, d) for k in ("final", "sheet1", "sheet2") for d in r[k]["disagreements"] if d["wrong"] == "both"]
    shared_by_code = [(k, d) for k, d in shared if d.get("decided_by") != "judge"]
    shared_judged = [(k, d) for k, d in shared if d.get("decided_by") == "judge"]
    judging_shared = [(k, d) for k, d in shared_judged if d["cause_analysts"] and "judge_judging" in d["cause_analysts"]]
    name = lambda k, d: f"{k}, draft {d['sheet_no']}"
    out = [
        f"At this size the experiment cannot separate a real difference between the judges from the advantage the harness gives llama3.1. Judge choice measurably "
        f"mattered: across the {p['labelled']} labelled drafts llama3.1 agrees with the owner on {p['llama']}, {share(p['llama_interval'])}, and Mistral on {p['mistral']}, "
        f"{share(p['mistral_interval'])}, a paired difference of {points(diff)}" + (" that excludes zero." if diff[1] > 0 else ".") +
        " What the experiment cannot say is how much of that gap belongs to Mistral and how much to llama3.1's home advantage. "
        f"{word(len(on_tuned)).capitalize()} of Mistral's {word(len(mistral_only))} extra errors fall on sheets 1 and 2, where the rubric was tuned with llama3.1 as the judge."
        + (f" The {'fourth' if len(mistral_only) == 4 else 'remaining one'}, on the final sheet, was taken by the copy-the-words check, a harness step built and tuned "
           "with llama3.1 as the only judge (see Harness lock-in)." if by_copy and len(by_copy) + len(on_tuned) == len(mistral_only) else ""),
        "",
        f"The overlap supports a weaker claim, and no more. Mistral also misgrades every draft llama3.1 misgrades against the owner ({len(shared)} of {first}). "
        + (f"But {word(len(shared_by_code))} of the {word(len(shared))} ({'; '.join(name(k, d) for k, d in shared_by_code)}) was decided by a code rule before any judge "
           "saw it, so the two share it by construction" + (", and the owner later changed that label" if all(d.get("revised_label") for _, d in shared_by_code) else "")
           + ". " if shared_by_code else "")
        + f"The other {word(len(shared_judged))} reached a judge, and {'both' if len(shared_judged) == 2 else 'all ' + word(len(shared_judged))} recur under Mistral. So llama3.1's judged errors are not peculiar to llama3.1: they recur "
        "under an independently trained judge on the same rubric and harness. That does not show the rubric is sound, since Mistral makes errors llama3.1 does not. "
        "Nor does it show that the shared errors are the rubric's"
        + (f"; by the model-run analysts' reading, {word(len(judging_shared))} of the {word(len(shared_judged))} is a judging mistake both judges make." if judging_shared else "."),
        "",
        f"The reading rule fixed before the run was applied as written. On the final sheet, the only one never used to develop the rubric, llama3.1 agrees on "
        f"{k_of(f['llama_owner'])}, {share(f['llama_interval'])}, and Mistral on {k_of(f['mistral_owner'])}, {share(f['mistral_interval'])}; within one draft, so the rule "
        f"reads **{s['verdict_final_sheet']}**. The rule was written to take that as support for rubric over model. This report departs from that reading, a choice "
        "the owner made after seeing the results. The rule looks at twenty drafts while the pooled interval above excludes zero. And only "
        f"{f['judged']} of those {f['drafts']} drafts reach a judge at all (llama3.1 {f['llama_owner_judged'][0]} of {f['judged_labelled']}, Mistral "
        f"{f['mistral_owner_judged'][0]} of {f['judged_labelled']}). The other {f['drafts'] - f['judged']} get the same grade under either judge by construction.",
        "",
        f"Of the 85 drafts, {85 - sum(r[k]['judged'] for k in r)} are decided by code rules or exact match and get the same grade under either judge. Only "
        f"{sum(r[k]['judged'] for k in r)} reach a judge, so a judge swap can move at most that many grades. On those {p['judged_labelled']} labelled drafts llama3.1 "
        f"agrees on {p['llama_judged']} and Mistral on {p['mistral_judged']}.",
        "",
    ]
    return out


def errors_section(s):
    r = s["results"]
    f = r["final"]
    both_final, own_final = f["overlap"]["both"], f["overlap"]["second_only"]
    first = sum(len(r[k]["overlap"]["first"]) for k in r)
    both = sum(len(r[k]["overlap"]["both"]) for k in r)
    first_only = sum(len(r[k]["overlap"]["first_only"]) for k in r)
    second_only = sum(len(r[k]["overlap"]["second_only"]) for k in r)
    by_code = sum(1 for k in r for d in r[k]["disagreements"] if d["wrong"] == "both" and d.get("decided_by") != "judge")
    out = ["## Where the errors fall", "",
           f"On the final sheet the two judges share {count(len(both_final), 'error')} ({drafts_list(both_final)}), and Mistral has {count(len(own_final), 'error')} of its own "
           f"({drafts_list(own_final)}). Over all three sheets Mistral also misgrades every draft llama3.1 misgrades ({both} of {first})"
           + (f", and {word(by_code)} of those {'was' if by_code == 1 else 'were'} decided by a code rule before any judge saw {'it' if by_code == 1 else 'them'}" if by_code else "")
           + f". Mistral adds {count(second_only, 'error')} of its own, while llama3.1 has {count(first_only, 'error')} of its own. That llama3.1 has none is expected on sheets 1 and 2, "
           "where the rubric was revised against llama3.1's disagreements.", ""]
    att = s.get("independent_attribution")
    rows = [(k, d) for k in ("final", "sheet1", "sheet2") for d in r[k]["disagreements"]]
    if att:
        agree_each_other = all(d["analysts_agree"] for d in att["drafts"])
        rule_agrees = sum(1 for _, d in rows if d["rule_agrees_with_analysts"])
        out += [f"Two model-run analysts ({MODEL_RUN}) assigned a cause to each of these {len(rows)} drafts. Each read only the committed records, call logs, owner sheets "
                "and grader source, without seeing this report, the script's rule or the other analyst. They agreed with each other on "
                f"{'every' if agree_each_other else 'not every'} draft. A cause rule written into the script after the run agrees with them on {rule_agrees} of the {len(rows)}, "
                "counting sheet 1, draft 34 as agreement: the rule names the code rule that decided it, the analysts name the label the owner later changed, and both are true. "
                "Where the two differ, this report goes with the analysts. They read the drafts and the replies; the rule reads only flags and answers, assumes that an error "
                "both judges make belongs to the rubric, and cannot tell a defensible answer from a wrong one. Their causes are a model's reading of the records, not a "
                "person's."
                + (" " + later if (later := " ".join(f"{d['sheet'].replace('sheet', 'Sheet ')}, draft {d['sheet_no']} was attributed after the draw-pool regrade by two further "
                                                   "model-run analysts with the same instructions, who read the regraded records and the item as it stood when the sheet was drawn."
                                                   for d in att["drafts"] if d.get("added"))) else ""), "",
                "| sheet | draft | misgraded by | cause, two model-run analysts (not people) | cause, rule written after the run |", "|---|---|---|---|---|"]
        for k, d in rows:
            out.append(f"| {k} | {d['sheet_no']} | {d['wrong']} | {'; '.join(ANALYST_PHRASE[c] for c in (d['cause_analysts'] or []))} | {RULE_PHRASE[d['cause_rule']]} |")
        out.append("")
        shared = [(k, d) for k, d in rows if d["wrong"] == "both"]
        judging_shared = [(k, d) for k, d in shared if d["cause_analysts"] and "judge_judging" in d["cause_analysts"]]
        notes = []
        if judging_shared:
            notes.append(f"By the model-run analysts' reading, an error both judges make is not always the rubric's. {count(len(judging_shared), 'shared error').capitalize()} "
                         f"({', '.join(f'{k}, draft {d["sheet_no"]}' for k, d in judging_shared)}) is a judging mistake the two judges happen to share, which may be a limit "
                         "of judges this size rather than of either one.")
        evidence = {(e["sheet"], e["sheet_no"]): " ".join(e["evidence"]).lower() for e in att["drafts"]}
        for k, d in [(k, d) for k, d in rows if d["wrong"] == "Mistral only" and d["cause_analysts"] and "rubric_or_question_wording" in d["cause_analysts"]]:
            reason = ("padding the draft adds to a right answer, which no judge question asks about and the code's unsupported-claim check, looking only for outside "
                      "names and acronyms, does not catch" if "padding" in evidence.get((k, d["sheet_no"]), "") else "something the judge's questions do not ask about")
            notes.append(f"And one of Mistral's own errors ({k}, draft {d['sheet_no']}) is the rubric's. Both analysts found Mistral's answers defensible and traced the "
                         f"owner's {d['owner']} to {reason}; llama3.1 matched the owner's binary label only by grading the draft {d['llama']}.")
        if notes:
            out += [" ".join(notes), ""]
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
    cls = s.get("independent_classification")
    whole = [e for e in (cls or {}).get("entries", []) if e["type"].startswith("whole")]
    lines = [e for e in (cls or {}).get("entries", []) if not e["type"].startswith("whole")]
    unreadable = sum(v for k, v in cats.items() if k != "parsed")
    out = ["## Unreadable replies: task or format", "",
           f"Mistral's strict grading made {sum(cats.values())} judge calls"
           + (f", {s['regrade']['judge_calls']} of them in the draw-pool regrade" if s.get("regrade") else "")
           + f"; the parser read {cats.get('parsed', 0)}. None stopped at the 200-token cap. "
           f"Every reply is kept verbatim in reports/post-hoc-second-judge/mistral-calls.jsonl"
           + (", and for the regraded draft in mistral-regrade-calls.jsonl" if s.get("regrade") else "") + f". There was only {count(len(s['unreadable_replies']), 'unreadable reply', 'unreadable replies')}, "
           "so the handful asked for is this one:", ""]
    for u in s["unreadable_replies"]:
        out += [f"{u['sheet']}, draft {u['sheet_no']}, second answer order, {u['eval_count']} tokens, stopped normally:", "", "```", u["reply"].strip(), "```", ""]
    out.append("It commits to NO on Q1, qualifies Q3 as \"Yes, in a way\", and gives Q2 no yes or no at all, only \"Implicitly\". The grader needs an answer to every "
               "question, so the draft was graded WRONG. The code's category is a task failure, not a format failure: a lenient reading that strips formatting still "
               "finds no answer to Q2, and the diagnostic regrade at 600 tokens got the same reply."
               + (f" Three model-run readers ({MODEL_RUN}), each shown only the questions and the reply and blind to the code, all called it a task failure."
                  if whole and all(e["votes"].count("task_failure") == 3 for e in whole) else ""))
    out += ["", "How each judge wrote its answer lines over the same drafts, one row per kind of line:", "", "| answer line | llama3.1 | Mistral |", "|---|---|---|"]
    for key in sorted(set(hab["llama3.1"]["answer_lines"]) | set(hab["mistral"]["answer_lines"])):
        out.append(f"| {key} | {hab['llama3.1']['answer_lines'].get(key, 0)} | {hab['mistral']['answer_lines'].get(key, 0)} |")
    out.append("")
    if lines:
        maj = Counter(e["majority"] for e in lines)
        contradictory = [e for e in lines if e["majority"] == "contradictory"]
        split = [e for e in lines if not e["unanimous"]]
        later_lines = [e for e in lines if e.get("added")]
        sentence = (f"The same three model-run readers also read the {len(lines) - len(later_lines)} parsed Mistral answer lines that carry added words, a check added after the run. "
                    + (f"Three further model-run readers, with the same instructions, read the {word(len(later_lines))} such lines from the draw-pool regrade, {len(lines)} in all. "
                       if later_lines else "")
                    + f"By majority {maj.get('clear', 0)} are clear, the added words backing the YES or NO given")
        if contradictory:
            sentence += (f", and {count(len(contradictory), 'is', 'are')} contradictory: "
                         + "; ".join(f"{e['sheet']}, draft {e['sheet_no']}, \"{e['text'].rstrip('.')}.\"" for e in contradictory)
                         + " The parser read the stated answer there, and the owner and both judges graded that draft the same")
        sentence += "."
        if split:
            sentence += f" The readers split on {count(len(split), 'line')}: " + "; ".join(f"{e['sheet']}, draft {e['sheet_no']} ({', '.join(e['votes'])})" for e in split) + "."
        out += [sentence, ""]
    out += [f"Mistral did not fail on format. Its replies parsed under llama3.1's conventions {cats.get('parsed', 0)} times in {sum(cats.values())}"
            + (f", and the {'one reply that did not' if unreadable == 1 else str(unreadable) + ' that did not'} failed the task, not the format." if unreadable else ".")
            + " The parser was not where llama3.1's conventions cost Mistral; the copy check was (see Harness lock-in).", ""]
    return out


def harness_section(s):
    h, r = s["harness_lock_in"], s["results"]
    hab = s["habits"]
    m, l = h["mistral"], h["llama3.1"]
    names = {"copied": "copied words found in the text checked", "echoed": "gave back the phrase the instruction quotes, not in the text",
             "none quoting a phrase": "NONE, quoting a phrase in its explanation", "not found": "other copied words not found in the text", "none": "NONE, or nothing usable"}
    where = lambda es: "; ".join(f"{sheet} draft {no}" + (f", {'twice' if n == 2 else str(n) + ' times'}" if n > 1 else "")
                                  for (sheet, no), n in Counter((e["sheet"], e["sheet_no"]) for e in es).items())
    bare = lambda q: '"' + (q or "").strip().strip('"').rstrip(".") + '"'
    flips = {k: (r[k]["order_flips"]["mistral"], r[k]["order_flips"]["llama"]) for k in ("final", "sheet1", "sheet2")}
    m_cost = sum(r[k]["stricter_order_rule"]["mistral"]["cost"] for k in r)
    m_saved = sum(r[k]["stricter_order_rule"]["mistral"]["saved"] for k in r)
    repeats = m["echo_calls"] - m["echo_requests"]
    out = ["## Harness lock-in: the copy check carries the first judge's habits", "",
           "The grader does not take a judge's YES on trust. It asks the judge to copy the words that back the YES and checks that they are there. For every question "
           "but the one about leaving something out, they must be in the draft; for that one, in the reference. A YES whose copied words cannot be found is turned "
           "into NO. For some questions the instruction quotes the phrase it wants found, for example: Copy the exact words in the text that give \"just prior to the "
           "PDR\" as the answer, in any wording. The check, its instructions and the parser that reads the reply were built and tuned with llama3.1 as the only judge.", "",
           "| copy reply, counted per call | llama3.1 | Mistral |", "|---|---|---|"]
    for key in ("copied", "echoed", "none quoting a phrase", "not found", "none"):
        out.append(f"| {names[key]} | {hab['llama3.1']['copy_replies'].get(key, 0)} | {hab['mistral']['copy_replies'].get(key, 0)} |")
    shared = h["requests_both_judges_met"]
    verb = {"copied": "copied", "echoed": "gave the phrase back", "none quoting a phrase": "replied NONE quoting the phrase", "not found": "copied words not in the text",
            "none": "replied NONE"}
    out += ["",
            "The text checked is the draft, or the reference for the leaves-out question. Only two kinds of instruction quote a phrase to find: give \"X\" as the "
            "answer, and state this correction: \"X\". The other copy calls quote nothing, the question, the draft, or an answer the copied words must go against. Counted by "
            f"distinct request, Mistral met {word(m['requests_quoting_a_phrase_to_find'])} instructions that quote a phrase to find, and llama3.1 met "
            f"{word(l['requests_quoting_a_phrase_to_find'])}. Mistral gave the quoted phrase back as its copy on {word(m['echo_requests'])} of its "
            f"{word(m['requests_quoting_a_phrase_to_find'])} ({where(m['echoes'])}"
            + f")." + (" The repeat is the identical request from the other answer order, served from the cache." if repeats else "")
            + f" llama3.1 did so on {'neither' if l['requests_quoting_a_phrase_to_find'] == 2 and not l['echo_requests'] else word(l['echo_requests'])} of its "
            f"{word(l['requests_quoting_a_phrase_to_find'])}. The two judges met the same such request {'twice' if len(shared) == 2 else count(len(shared), 'time')}"
            + (": " + "; ".join(f"on {x['sheet']} draft {x['sheet_no']} " + (f"both {verb[x['mistral'][0]]}" if x["mistral"] == x["llama3.1"] else
                                          f"llama3.1 {' and '.join(verb[k] for k in x['llama3.1'])} and Mistral {' and '.join(verb[k] for k in x['mistral'])}")
                                 for x in shared) + "." if shared else ".")]
    out += ["",
            "An echo is not in the draft whenever the draft words the answer differently, so the check strikes the YES even when the judge was right."]
    for c in h["costly"]:
        out[-1] += (f" On {c['sheet']} draft {c['sheet_no']} that is what happened. The instruction asked for the words that give \"{c['phrase']}\" as the answer. "
                    f"llama3.1 copied the draft's own words, {bare(c['llama_copied'])}. Mistral replied {bare(c['mistral_copied'])}, the instruction's phrase, which the "
                    f"draft does not contain. The check struck Mistral's YES, and its grade fell to {c['mistral_grade']}, where llama3.1 and the owner have {c['owner']}.")
    for c in h["echoes_that_cost_nothing"]:
        out[-1] += (f" The echo on {c['sheet']} draft {c['sheet_no']} did no harm. The draft reads: \"{c['source'].strip()}\" It accepts the question's premise and never "
                    "states the correction, so there were no words to copy. The check was right to strike the YES, and Mistral's grade there agrees with the owner's.")
    nq = m["none_quoting_a_phrase"]
    if nq:
        out += ["",
                f"On {count(len(nq), 'more call')} ({where(nq)}) Mistral replied NONE and quoted the phrase in its explanation. One of them reads: {nq[0]['reply']} The "
                "grader's parser looks for a quoted phrase before it looks for NONE, so it reads such a reply as a copy of that phrase. None of these phrases was in "
                "the text, so the result was the same as a plain NONE. "
                + ("llama3.1 wrote no reply of this kind." if not l["none_quoting_a_phrase"] else f"llama3.1 wrote {count(len(l['none_quoting_a_phrase']), 'reply', 'replies')} of this kind.")]
    cats = s["reply_categories_strict"]
    out += ["",
            f"This is the most transferable finding in the experiment, and it rests on little: {count(len(h['costly']), 'request')} and "
            f"{count(len(h['costly']), 'grade')}, with the habit behind it seen on {word(m['echo_requests'])}. A verification step that quotes its target inside the prompt passes a judge that copies from the text and fails a "
            "judge that gives the prompt's phrase back, whenever the text words the target differently. A harness built with one judge encodes that judge's habits as "
            "if they were the task, and a second judge's different habits then show up as errors the first judge never makes. Swapping the judge in a grader like "
            f"this one is not free, and the parse rate does not show the cost: Mistral's judge replies parsed {cats.get('parsed', 0)} times in {sum(cats.values())}. "
            "Whether an instruction that does not quote the target would remove the effect was not tested.", "",
            f"A second harness rule, keeping the stricter of two answer orders, met a second difference between the judges. Mistral's grade changed with the answer order "
            f"on {flips['final'][0]}, {flips['sheet1'][0]} and {flips['sheet2'][0]} drafts across the final sheet and sheets 1 and 2, against llama3.1's {flips['final'][1]}, "
            f"{flips['sheet1'][1]} and {flips['sheet2'][1]}; the gap sits mostly on sheet 1, where the rubric was tuned with llama3.1. Here the rule cost Mistral "
            f"{count(m_cost, 'binary agreement')} and saved it {word(m_saved)}, so on these drafts it did not change Mistral's agreement with the owner.", ""]
    return out


def correction_section(s):
    g = s.get("regrade")
    if not g:
        return []
    rows = []
    for a in g["affected"]:
        key = f"{a['sheet']}/{a['sheet_no']}"
        grades = g["grades"][key]
        own = next((d["owner"] for d in s["results"][a["sheet"]]["disagreements"] if d["sheet_no"] == a["sheet_no"]), None)
        rows.append((a, grades, own))
    a, grades, own = rows[0]
    first_run = g["first_run_pool"]
    return ["## Correction, 2026-09-14: sheet 1 graded against the pool it was drawn from", "",
            f"The first version of this report graded sheets 1 and 2 against git {first_run}, the item pool sheet 2 was drawn from. Sheet 1 was drawn at "
            f"{g['draw_pools']['sheet1']}. {count(len(rows), 'item').capitalize()} on it changed between the two. On sheet 1, draft {a['sheet_no']}, a model-run pass over the "
            f"ambiguous items, acting on the owner's blind grade, had moved the item from {a['bucket'][1]} to {a['bucket'][0]}. The owner ruled that each sheet is graded against the pool as it stood when the sheet was drawn and graded, "
            "the rule set before this came up. So the draft was regraded against the item as drawn. llama3.1's grade came from the cache with no live call; Mistral's "
            f"came from a second pass of {g['live_calls']} live calls with only Mistral loaded. "
            + (f"Both judges now grade it {grades['llama']}" if grades["llama"] == grades["mistral"] else f"llama3.1 now grades it {grades['llama']} and Mistral {grades['mistral']}")
            + (f" where the owner has {own}, so it becomes a shared error that reaches a judge." if own else ".")
            + " Every figure below uses each sheet's draw-time pool. The figures that changed, with their old values, are listed in "
            "reports/changed-numbers-2026-09-14.md; see also docs/report.md, measurement integrity, entry 2.", ""]


def checks_section(s):
    out = ["## Independent checks, and who ran them", "",
           f"Every check below was run by code or by {MODEL_RUN}. The only person who graded anything in this experiment is the owner, whose labels are the ones on "
           "the three blind sheets. The readers, analysts and verifier were kept blind in the sense stated for each. The critic and the check of the owner's "
           "corrections were not blind, since reading this report was their job. A reader should weigh all of them as a model's work, not as the human blind checks "
           "reported in the main report.", ""]
    if s.get("verification"):
        mm = s.get("verification_mismatches", [])
        out.append("- A model-run verifier (a language-model agent, not a person) worked from the raw files with its own code, blind to this report and the script. "
                   "It recomputed each sheet's draft, label and judged counts, both judges' binary agreement with the owner, the judges' agreement with each other, the "
                   "misgraded draft numbers and the unreadable count. " + ("Every number matched." if not mm else f"Mismatches: {', '.join(mm)}.")
                   + " It did not recompute the intervals, three-way agreement, order flips or copy-check counts. Added after the run."
                   + (f" It checked the figures from before the draw-pool regrade, so its check is compared here only for {' and '.join(scope['compared_now'])}"
                      + ("; the regraded figures were recounted by a second verifier (see the draw-pool regrade bullet)." if s.get("regrade_verification")
                         else "; the regraded figures have not been independently recounted.")
                      if (scope := s.get("verification_scope")) and scope["regraded_sheets"] else ""))
    if s.get("independent_classification"):
        out.append("- Three model-run readers (language-model agents, not people) classified the unreadable reply, a check planned before the run. After the run they "
                   "also read the answer lines with added words. Each was blind to the code and to the other readers."
                   + (" Three further readers with the same instructions read the lines added by the draw-pool regrade."
                      if any(e.get("added") for e in s["independent_classification"]["entries"]) else ""))
    if s.get("independent_attribution"):
        out.append("- Two model-run analysts (language-model agents, not people) assigned causes to every misgraded draft, blind to the report, the rule and each other, "
                   "added after the run.")
    out.append("- A model-run critic (a language-model agent, not a person) reviewed the first rendering of this report against the owner's requirements and found 26 "
               "defects (reports/post-hoc-second-judge/critic-review.json). The first rendering said the two judges echoed equally often and that echoing was not a "
               "Mistral habit. The critic's first defect called that sentence false against the call logs, though its own echo count was the same undercount. The cause "
               "turned up while that defect was being fixed: a pattern that required a colon missed the instruction shape give \"X\" as the answer. The recount that "
               "followed, 7 calls against 1, was committed and was itself too high. Added after the run; the undercount is the sixth entry in the main report's "
               "measurement-integrity section.")
    cv = s.get("corrections_verification")
    if cv:
        out.append(f"- The owner read the committed report and asked for four corrections. Three more model-run reviewers ({MODEL_RUN}) then checked the corrected "
                   "text, each followed by a model-run agent told to refute its findings (reports/post-hoc-second-judge/corrections-verification.json). "
                   f"{cv['confirmed']} findings survived, several of them found by more than one reviewer, and all are addressed in this version. The recount from the "
                   "raw logs found that 4 of Mistral's 7 counted echoes were NONE replies quoting a phrase, and that llama3.1's 1 was a leaves-out call that copied the "
                   "draft. It also found that the overlap counted a draft no judge saw, and that the critic had been credited with finding the colon bug. A second round of "
                   "the same kind, on the fixed text, found that the recount's denominators included instructions that quote an answer to go against, not a phrase to "
                   f"find. A third round confirmed {word(cv['later_rounds'][-1]['confirmed'])} more findings, none of which changed a number; all {cv['later_confirmed']} later findings "
                   "are fixed and recorded in the same file. The overcount is the seventh entry in the main report's measurement-integrity section, and the classifier has a test for each shape it missed.")
    rv = s.get("regrade_verification")
    g = s.get("regrade")
    if g:
        out.append(f"- The draw-pool regrade (reports/post-hoc-second-judge/regrade.json) is code, with the same single-model guard as the first pass."
                   + (f" A model-run verifier (a language-model agent, not a person), working from the raw files with its own code, then recomputed the regraded sheet 1 and pooled "
                      "figures (reports/post-hoc-second-judge/regrade-verification.json): "
                      + ("every number matched." if not rv.get("mismatches") else f"mismatches: {', '.join(rv['mismatches'])}.") if rv else "")
                   + " Three further model-run readers and two further model-run analysts, with the original instructions, read the new answer lines and the regraded draft.")
    out.append("- The llama3.1 replay and the Mistral pass are code: the replay refused any live model call, and the pass refused to run with any other model loaded.")
    return out + [""]


def render(s):
    r, t, c = s["results"], s["timing"], s["calls"]
    lines = ["# Post hoc: a second judge on the three blind sheets", "",
             "A post hoc experiment, run after the tagged evaluation (v1.0.2). The 85 drafts on the three blind sheets were regraded with grader v13 unchanged and "
             "Mistral 7B Instruct (mistral:latest) as the judge in place of llama3.1 8B, and both judges were compared with the owner's hand labels. No test item "
             "was read and nothing was refit. The plan and the reading rule were committed before the first Mistral call (commit 1514552; docs/decisions.md, "
             "\"Post hoc: a second judge\"). Every number comes from reports/post-hoc-second-judge.json.", "",
             f"Who did what. The owner's hand labels are the only human judgement in this experiment. The two judges are language models. The readers, analysts, "
             f"verifier, critic and reviewers named below are also {MODEL_RUN}, and are called model-run wherever they appear; they are not the human blind checks reported in the "
             "main report. Of these checks only one was planned before the run, the readers' classification of the unreadable reply. The cause rule, the readers' "
             "reading of answer lines with added words, the analysts, the verifier, the critic, the check of the owner's corrections and the checks of the draw-pool "
             "regrade were all added after it.", "",
             "Terms. Binary agreement counts CORRECT against PARTIAL or WRONG; three-way agreement needs the exact grade. 84 of the 85 drafts carry an owner label. "
             "The owner did grade sheet 1, draft 1, CORRECT like both judges. Its grade line is indented and the sheet reader skips it, so it counts as unlabelled "
             "here, as in every earlier figure for that sheet. A draft reaches a judge only when no code rule or exact match decides it first; both judges take the same route "
             "on every draft.", "",
             ]
    lines += correction_section(s)
    lines += ["## Headline", ""]
    lines += headline(s)
    lines += harness_section(s)
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
    g = s.get("regrade")
    if g:
        lines[-2] += (f" The draw-pool regrade was a second, smaller pass with the same guard: {count(len(g['affected']), 'draft')}, {g['judge_calls']} judge "
                      f"{'call' if g['judge_calls'] == 1 else 'calls'} and {word(g['copy_calls']) if g['copy_calls'] else 'no'} copy {'call' if g['copy_calls'] == 1 else 'calls'}, {g['live_calls']} of them live, "
                      f"{g['wall_seconds']:.0f} s.")
    lines += checks_section(s)
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=["replay", "run", "regrade", "report"])
    args = parser.parse_args()
    return {"replay": cmd_replay, "run": cmd_run, "regrade": cmd_regrade, "report": cmd_report}[args.stage]()


if __name__ == "__main__":
    sys.exit(main())
