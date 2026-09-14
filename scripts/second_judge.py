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
from calibration.judge_compare import (agreement, binary, bootstrap_share, categorise_reply, lenient_parser, overlap,  # noqa: E402
                                       paired_difference)
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
    judge = ProviderJudge(OllamaProvider(model=FIRST_JUDGE, cache_dir=CACHE, transport=refuse_live_call, num_ctx=4096))
    per_sheet, mismatches = Counter(), []
    for sheet, row, item in drafts():
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


def pct(k, n):
    return f"{k} of {n} ({100 * k / n:.0f}%)" if n else "0 of 0"


def interval(hits):
    point, lo, hi = bootstrap_share(hits)
    return f"{100 * point:.0f}% [{100 * lo:.0f}, {100 * hi:.0f}]" if hits else "n/a"


def cmd_report():
    llama = {(s["name"], r["sheet_no"]): r for s in SHEETS for r in jsonl(ROOT / s["key"])}
    strict = {(r["sheet"], r["sheet_no"]): r for r in jsonl(OUT / "mistral-strict.jsonl")}
    adapted = {(r["sheet"], r["sheet_no"]): r for r in jsonl(OUT / "mistral-adapted.jsonl")}
    calls = jsonl(OUT / "mistral-calls.jsonl")
    run = json.loads((OUT / "run.json").read_text(encoding="utf-8"))
    replay = json.loads((OUT / "llama-replay.json").read_text(encoding="utf-8"))
    independent_path = OUT / "independent-classification.json"
    independent = json.loads(independent_path.read_text(encoding="utf-8")) if independent_path.exists() else None
    owner = {s["name"]: read_sheet(ROOT / s["sheet"]) for s in SHEETS}

    results, pooled = {}, {"llama": [], "mistral": [], "adapted": []}
    for s in SHEETS:
        name = s["name"]
        nos = sorted(no for (sh, no) in llama if sh == name)
        labelled = [no for no in nos if no in owner[name]]
        own = owner[name]
        l_hits = [int(binary(llama[(name, no)]["grade"]) == binary(own[no])) for no in labelled]
        m_hits = [int(binary(strict[(name, no)]["grade"]) == binary(own[no])) for no in labelled]
        a_grade = lambda no: (adapted[(name, no)] if (name, no) in adapted else strict[(name, no)])["grade"]
        a_hits = [int(binary(a_grade(no)) == binary(own[no])) for no in labelled]
        pooled["llama"] += l_hits
        pooled["mistral"] += m_hits
        pooled["adapted"] += a_hits
        judged = [no for no in nos if llama[(name, no)]["decided_by"] == "judge"]
        same_route = all(llama[(name, no)]["decided_by"] == strict[(name, no)]["decided_by"] for no in nos)
        parsed_nos = [no for no in labelled if strict[(name, no)]["flag"] != "judge_unparsed"]
        l_wrong = {no for no in labelled if binary(llama[(name, no)]["grade"]) != binary(own[no])}
        m_wrong = {no for no in labelled if binary(strict[(name, no)]["grade"]) != binary(own[no])}
        rev = {}
        if s.get("revisions"):
            revised = dict(own)
            revised.update({int(k): v for k, v in json.loads((ROOT / s["revisions"]).read_text(encoding="utf-8")).items()})
            rev = {"llama": agreement([(llama[(name, no)]["grade"], revised[no]) for no in labelled]),
                   "mistral": agreement([(strict[(name, no)]["grade"], revised[no]) for no in labelled])}
        results[name] = {
            "drafts": len(nos), "labelled": len(labelled), "judged": len(judged), "same_route_for_both_judges": same_route,
            "llama_owner": agreement([(llama[(name, no)]["grade"], own[no]) for no in labelled]),
            "mistral_owner": agreement([(strict[(name, no)]["grade"], own[no]) for no in labelled]),
            "adapted_owner": agreement([(a_grade(no), own[no]) for no in labelled]),
            "llama_owner_3way": agreement([(llama[(name, no)]["grade"], own[no]) for no in labelled], three_way=True),
            "mistral_owner_3way": agreement([(strict[(name, no)]["grade"], own[no]) for no in labelled], three_way=True),
            "llama_interval": bootstrap_share(l_hits), "mistral_interval": bootstrap_share(m_hits),
            "paired_difference_llama_minus_mistral": paired_difference(l_hits, m_hits),
            "judges_all": agreement([(llama[(name, no)]["grade"], strict[(name, no)]["grade"]) for no in nos]),
            "judges_judged": agreement([(llama[(name, no)]["grade"], strict[(name, no)]["grade"]) for no in judged]),
            "judges_judged_3way": agreement([(llama[(name, no)]["grade"], strict[(name, no)]["grade"]) for no in judged], three_way=True),
            "parsed_only": {"n": len(parsed_nos), "llama": agreement([(llama[(name, no)]["grade"], own[no]) for no in parsed_nos]),
                            "mistral": agreement([(strict[(name, no)]["grade"], own[no]) for no in parsed_nos])},
            "overlap": overlap(l_wrong, m_wrong),
            "unparsed": {"llama": sum(llama[(name, no)].get("flag") == "judge_unparsed" for no in nos), "mistral": sum(strict[(name, no)]["flag"] == "judge_unparsed" for no in nos)},
            "position_disagreement": {"llama": sum(llama[(name, no)].get("flag") == "position_disagreement" for no in nos),
                                      "mistral": sum(strict[(name, no)]["flag"] == "position_disagreement" for no in nos)},
            "ungrounded_yes": {"llama": sum(len(u or []) for no in nos for u in (llama[(name, no)].get("judge_ungrounded") or [])),
                               "mistral": sum(len(u or []) for no in nos for u in (strict[(name, no)].get("judge_ungrounded") or []))},
            "revision_applied": rev,
            "disagreements": [{"sheet_no": no, "bucket": llama[(name, no)]["bucket"], "owner": own[no], "llama": llama[(name, no)]["grade"],
                               "mistral": strict[(name, no)]["grade"], "mistral_flag": strict[(name, no)]["flag"], "question": llama[(name, no)]["question"],
                               "draft": llama[(name, no)]["draft"]} for no in sorted(l_wrong | m_wrong)],
        }
    final = results["final"]
    l_final, m_final = final["llama_owner"][0], final["mistral_owner"][0]
    if m_final >= l_final - 1:
        verdict = "about as well"
    else:
        verdict = "noticeably worse"
    judge_calls = [c for c in calls if c["kind"] == "judge" and c["pass"] == "strict"]
    categories = Counter(c["category"] for c in judge_calls)
    unreadable = [c for c in judge_calls if c["category"] != "parsed"]
    adapted_calls = [c for c in calls if c["kind"] == "judge" and c["pass"] == "adapted"]
    live = [c for c in calls if not c["cached"]]
    secs = sorted(c["seconds"] for c in live)
    toks = sorted(c["eval_count"] or 0 for c in live)
    q = lambda xs, f: xs[int(f * (len(xs) - 1))] if xs else None
    summary = {"verdict_final_sheet": verdict, "results": results, "pooled": {
        "labelled": len(pooled["llama"]), "llama": sum(pooled["llama"]), "mistral": sum(pooled["mistral"]), "adapted": sum(pooled["adapted"]),
        "llama_interval": bootstrap_share(pooled["llama"]), "mistral_interval": bootstrap_share(pooled["mistral"]),
        "adapted_interval": bootstrap_share(pooled["adapted"]), "paired_difference_llama_minus_mistral": paired_difference(pooled["llama"], pooled["mistral"]),
        "paired_difference_llama_minus_adapted": paired_difference(pooled["llama"], pooled["adapted"])},
        "reply_categories_strict": dict(categories), "truncated_strict": sum(c["done_reason"] == "length" for c in judge_calls),
        "adapted_reply_categories": dict(Counter(c["category"] for c in adapted_calls)),
        "unreadable_replies": [{k: c[k] for k in ("sheet", "sheet_no", "item_id", "call", "category", "done_reason", "eval_count", "reply")} for c in unreadable],
        "timing": {"wall_seconds": run["wall_seconds"], "calls": run["calls"], "live_calls": len(live), "median_seconds": q(secs, 0.5), "p90_seconds": q(secs, 0.9),
                   "median_output_tokens": q(toks, 0.5), "p90_output_tokens": q(toks, 0.9)},
        "run": run, "replay": replay, "independent_classification": independent}
    (ROOT / "reports" / "post-hoc-second-judge.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    Path(ROOT / "reports" / "post-hoc-second-judge.md").write_text(render(summary), encoding="utf-8", newline="\n")
    print(render(summary))
    return 0


def render(s):
    r, p = s["results"], s["pooled"]
    f = r["final"]
    fmt_int = lambda t: f"{100 * t[0]:.0f}% [{100 * t[1]:.0f}, {100 * t[2]:.0f}]"
    fmt_diff = lambda t: f"{100 * t[0]:+.0f} points [{100 * t[1]:+.0f}, {100 * t[2]:+.0f}]"
    lines = ["# Post hoc: a second judge on the three blind sheets", "",
             "A post hoc experiment run after the tagged evaluation (v1.0.2). It regrades the 85 drafts on the three blind sheets with grader v13 "
             "unchanged and Mistral 7B Instruct (mistral:latest) as the judge in place of llama3.1 8B, and compares both judges with the owner's hand "
             "labels. No test item was read and nothing was refit. The plan and the reading rule were committed before the first Mistral call "
             "(docs/decisions.md, \"Post hoc: a second judge\"). Every number comes from reports/post-hoc-second-judge.json.", "",
             "## Headline", "",
             f"On the final sheet, the only one the rubric was never developed against, Mistral agrees with the owner on {pct(*f['mistral_owner'])} "
             f"and llama3.1 on {pct(*f['llama_owner'])}. By the rule fixed before the run, Mistral agrees **{s['verdict_final_sheet']}** as llama3.1. "
             + ("That supports the claim that the rubric, not the choice of judge, carried the agreement." if s["verdict_final_sheet"] == "about as well"
                else "That weakens the claim that the rubric, not the choice of judge, carried the agreement, and the paper says so."), "",
             f"Pooled over all {p['labelled']} labelled drafts, llama3.1 agrees on {p['llama']} ({fmt_int(p['llama_interval'])}) and Mistral on {p['mistral']} "
             f"({fmt_int(p['mistral_interval'])}); the paired difference, llama3.1 minus Mistral, is {fmt_diff(p['paired_difference_llama_minus_mistral'])}. "
             "The pooled figure includes sheets 1 and 2, where llama3.1 has a home advantage (below).", "",
             f"Structure matters as much as the judge: of the 85 drafts, {85 - sum(r[k]['judged'] for k in r)} are decided by code rules or exact match and get "
             f"the same grade under any judge. Only {sum(r[k]['judged'] for k in r)} reach the judge, so a judge swap can move at most that many grades.", ""]

    def sheet_block(name, heading, caveat):
        x = r[name]
        block = [f"## {heading}", ""]
        if caveat:
            block += [caveat, ""]
        block += ["| measure | llama3.1 | Mistral |", "|---|---|---|",
                  f"| binary agreement with the owner ({x['labelled']} labelled) | {pct(*x['llama_owner'])}, {fmt_int(x['llama_interval'])} | {pct(*x['mistral_owner'])}, {fmt_int(x['mistral_interval'])} |",
                  f"| three-way agreement with the owner | {pct(*x['llama_owner_3way'])} | {pct(*x['mistral_owner_3way'])} |",
                  f"| unreadable judge replies (draft graded WRONG by rule) | {x['unparsed']['llama']} | {x['unparsed']['mistral']} |",
                  f"| grades differing by answer order | {x['position_disagreement']['llama']} | {x['position_disagreement']['mistral']} |",
                  f"| YES answers removed because the copied words did not check out | {x['ungrounded_yes']['llama']} | {x['ungrounded_yes']['mistral']} |",
                  "",
                  f"- Paired difference, llama3.1 minus Mistral: {fmt_diff(x['paired_difference_llama_minus_mistral'])}.",
                  f"- The two judges agree with each other on {pct(*x['judges_all'])} of all {x['drafts']} drafts, and on {pct(*x['judges_judged'])} of the "
                  f"{x['judged']} drafts that reach a judge (three-way {pct(*x['judges_judged_3way'])}). Both judges took the same route (rules, exact, judge) on every draft: {x['same_route_for_both_judges']}.",
                  f"- Drafts graded against the owner: llama3.1 wrong on {len(x['overlap']['first'])}, Mistral wrong on {len(x['overlap']['second'])}, both wrong on "
                  f"{len(x['overlap']['both'])} ({', '.join(map(str, x['overlap']['both'])) or 'none'}); llama3.1 only {', '.join(map(str, x['overlap']['first_only'])) or 'none'}; "
                  f"Mistral only {', '.join(map(str, x['overlap']['second_only'])) or 'none'}.",
                  f"- With Mistral's unreadable drafts set aside ({x['parsed_only']['n']} labelled drafts left): llama3.1 {pct(*x['parsed_only']['llama'])}, Mistral {pct(*x['parsed_only']['mistral'])}.",
                  f"- Diagnostic, not the headline: with the lenient reading and a 600-token cap on the unreadable drafts, Mistral {pct(*x['adapted_owner'])}."]
        if x["revision_applied"]:
            block.append(f"- Secondary line, with the owner's later change to sheet 34 applied: llama3.1 {pct(*x['revision_applied']['llama'])}, Mistral {pct(*x['revision_applied']['mistral'])}.")
        if x["disagreements"]:
            block += ["", "Drafts where either judge's binary grade differs from the owner's:", "", "| draft | bucket | owner | llama3.1 | Mistral | question |", "|---|---|---|---|---|---|"]
            for d in x["disagreements"]:
                flag = f" ({d['mistral_flag']})" if d["mistral_flag"] else ""
                block.append(f"| {d['sheet_no']} | {d['bucket']} | {d['owner']} | {d['llama']} | {d['mistral']}{flag} | {d['question'][:110]} |")
        return block + [""]

    lines += sheet_block("final", "Final sheet: the clean comparison", "Twenty real agent outputs from dev, drawn for the final blind check and graded by the owner without seeing either judge. Grader v13 was frozen before this sheet was drawn, so neither judge had any say in shaping the rubric against it.")
    lines += sheet_block("sheet1", "Sheet 1: home advantage for llama3.1", "Home advantage: grader versions v8 to v13 were developed against this sheet's disagreements with llama3.1 as the judge, so llama3.1's figure here is rubric fidelity, not a blind number (its blind figure under v7 was 82 percent). Mistral had no part in that development.")
    lines += sheet_block("sheet2", "Sheet 2: home advantage for llama3.1", "Home advantage: the v11 to v13 fixes were made after reading this sheet's disagreements with llama3.1 as the judge, so llama3.1's figure here is rubric fidelity, not a blind number (its blind figure under v10 was 80 percent). Mistral had no part in that development.")

    cats = s["reply_categories_strict"]
    lines += ["## Unreadable replies: task or format", "",
              f"Mistral's strict pass made {sum(cats.values())} judge calls. By the code's categories: " + ", ".join(f"{k} {v}" for k, v in sorted(cats.items())) +
              f". Replies that stopped at the 200-token cap: {s['truncated_strict']}. Every unreadable reply is kept verbatim in reports/post-hoc-second-judge/mistral-calls.jsonl.", ""]
    shown = []
    for cat in ("format", "truncated", "task"):
        shown += [u for u in s["unreadable_replies"] if u["category"] == cat][:2]
    for u in s["unreadable_replies"]:
        if len(shown) >= 6:
            break
        if u not in shown:
            shown.append(u)
    for u in shown[:6]:
        lines += [f"{u['sheet']}, draft {u['sheet_no']}, call {u['call']}: code category {u['category']}, stop reason {u['done_reason']}, {u['eval_count']} tokens", "", "```", u["reply"].strip(), "```", ""]
    ind = s.get("independent_classification")
    if ind:
        lines += ["Independent classification. " + ind["summary"], ""]
    lines += ["## Cost", "",
              f"One pass, only Mistral loaded ({', '.join(s['run']['unloaded_before_start']) or 'nothing'} unloaded first). Wall clock {s['timing']['wall_seconds']:.0f} s for "
              f"{s['timing']['calls']} judge and extraction calls ({s['timing']['live_calls']} live). Seconds per live call: median {s['timing']['median_seconds']}, 90th percentile "
              f"{s['timing']['p90_seconds']}. Output tokens per live call: median {s['timing']['median_output_tokens']}, 90th percentile {s['timing']['p90_output_tokens']}. "
              f"llama3.1's grades came from the cache: the replay reproduced {sum(s['replay']['reproduced'].values())} of 85 committed grades exactly, with no live call.", ""]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=["replay", "run", "report"])
    args = parser.parse_args()
    return {"replay": cmd_replay, "run": cmd_run, "report": cmd_report}[args.stage]()


if __name__ == "__main__":
    sys.exit(main())
