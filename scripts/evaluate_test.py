"""The one script that reads the test split, once. Preregistered in reports/m8-preregistration.md.

Usage:
    python scripts/evaluate_test.py --dry-run          # the same pipeline on dev, writes reports/m8-dryrun-*
    python scripts/evaluate_test.py                    # the single test read; refuses if the marker exists

Runs the frozen agent on every test item, grades with grader-v13, builds
the 39-feature vector with the paid signals, scores with the frozen
calibrator artifact and applies the frozen policy, fits the preregistered
baselines on dev features and applies them, and computes every
preregistered metric with bootstrap intervals. Writes <out>.md, <out>.json
and <out>-rows.jsonl verbatim, and a marker file that stops a second run.
Nothing is decided after the read except how to describe what came back.
"""

import argparse
import hashlib
import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import joblib  # the artifact is this project's own file in data/calibrators
import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.model_selection import StratifiedKFold

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from agent.evidence import evidence_record  # noqa: E402
from agent.loop import Agent, draft_messages  # noqa: E402
from agent.provider import OllamaProvider  # noqa: E402
from agent.retriever import Hit, bge_embedder, load_chunks, load_index  # noqa: E402
from calibration.features import GROUND_TRUTH, PROVENANCE, admissible_features, matrix, variant_features  # noqa: E402
from calibration.grader import content_words  # noqa: E402
from calibration.grader import GRADER_VERSION, ProviderJudge, grade  # noqa: E402
from calibration.metrics import auroc, aurc, bootstrap, brier, ece, reliability  # noqa: E402
from fit_calibrator import FOLDS, SEED, logistic, oof_scores  # noqa: E402
from policy.router import Thresholds, decide  # noqa: E402
from policy_curve import at_threshold, bootstrap_at, step_curve  # noqa: E402
from signals.agreement import agreement_features  # noqa: E402
from signals.process import leaked_fields, process_features, stratum  # noqa: E402
from signals.retrieval_support import nli_model, support_features  # noqa: E402
from signals.verbalized import confidence_features, confidence_messages  # noqa: E402

MARKER = ROOT / "data" / "eval" / "TEST_READ_ONCE"  # written only when a run completes
STARTED = ROOT / "data" / "eval" / "TEST_READ_STARTED"  # one line appended per attempt; a crash leaves it without the completion marker
DUP_JACCARD = 0.6
DUP_COSINE = 0.9
DUP_SAME_PAGE_COSINE = 0.8
BUCKETS = ("answerable", "ambiguous", "unanswerable", "false_premise")
BASELINES = {
    "verbalized alone": ["vc_confidence", "vc_parsed", "vc_round"],
    "agreement alone": ["sa_mean_pairwise", "sa_min_pairwise", "sa_mean_to_draft", "sa_min_to_draft", "sa_max_to_draft", "sa_abstain_share", "sa_form_agree"],
    "free signals alone": None,  # filled from the provenance lists: process and support features
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fmt(b: dict) -> str:
    return f"{b['point']:.3f} [{b['lo']:.3f}, {b['hi']:.3f}]"


def pct(a, n):
    return f"{a}/{n} ({100 * a / n:.0f}%)" if n else "0/0"


def fit_baseline(dev_rows, names):
    X, y = matrix(dev_rows, names)
    p_log, _ = oof_scores(X, y, list(StratifiedKFold(n_splits=FOLDS, shuffle=True, random_state=SEED).split(np.zeros(len(y)), y)))
    model = logistic().fit(X, y)
    iso = IsotonicRegression(out_of_bounds="clip").fit(p_log, y)
    return model, iso


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="run the whole pipeline on dev instead; touches nothing in test")
    parser.add_argument("--model", default="qwen2.5:3b-instruct")
    parser.add_argument("--judge", default="llama3.1:latest")
    args = parser.parse_args()
    if args.dry_run:
        split = ROOT / "data" / "eval" / "dev.jsonl"
        out = ROOT / "reports" / "m8-dryrun"
        trace_dir = ROOT / "data" / "traces" / "m8-dryrun"
    else:
        if MARKER.exists():
            print(f"{MARKER} exists: the test split has been read once already; this script does not run twice")
            return 1
        split = ROOT / "data" / "eval" / "test.jsonl"
        out = ROOT / "reports" / "m8-test-results"
        trace_dir = ROOT / "data" / "traces" / "test"
        with STARTED.open("a", encoding="utf-8", newline="\n") as f:
            f.write(f"attempt started {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n")
    attempts = len(STARTED.read_text(encoding="utf-8").splitlines()) if (not args.dry_run and STARTED.exists()) else 0
    trace_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()

    items = [json.loads(l) for l in split.read_text(encoding="utf-8").splitlines() if l.strip()]
    chunks = load_chunks(ROOT / "data" / "corpus" / "chunks.jsonl")
    by_id = {c["id"]: c for c in chunks}
    embed = bge_embedder()
    index = load_index(ROOT / "data" / "index", chunks, embed)
    vector_of = {c["id"]: index.vectors[i] for i, c in enumerate(chunks)}
    nli = nli_model()
    provider = OllamaProvider(model=args.model, cache_dir=ROOT / "data" / "cache", num_ctx=4096)
    judge = ProviderJudge(OllamaProvider(model=args.judge, cache_dir=ROOT / "data" / "cache", num_ctx=4096))
    agent = Agent(provider, index, k=8, premise_check=False)
    artifact = joblib.load(ROOT / "data" / "calibrators" / "minus_logprobs.joblib")
    policy = json.loads((ROOT / "data" / "calibrators" / "policy.json").read_text(encoding="utf-8"))
    thresholds = Thresholds(answer=policy["thresholds"]["answer"], escalate=policy["thresholds"]["escalate"])
    frozen = {"agent_commit": "85db315", "artifact_sha256": sha(ROOT / "data" / "calibrators" / "minus_logprobs.joblib"),
              "policy_sha256": sha(ROOT / "data" / "calibrators" / "policy.json"), "split_sha256": sha(split), "grader": GRADER_VERSION,
              "grader_sha256": sha(ROOT / "src" / "calibration" / "grader.py")}

    # 1. run, grade, features
    rows = []
    timings = Counter()
    for n, item in enumerate(items, start=1):
        t0 = time.time()
        trace = agent.run(item["question"], item_id=item["id"])
        trace["bucket"] = item["bucket"]
        trace["evidence"] = evidence_record(item, chunks, [by_id[h["id"]] for h in trace["retrieval"]])
        trace["needs_calculator"] = bool(item.get("needs_calculator"))
        timings["loop"] += time.time() - t0
        hits = [Hit(by_id[h["id"]], h["score"]) for h in trace["retrieval"]]
        ids = [h.chunk["id"] for h in hits]
        features = process_features(trace)
        features.update(support_features(trace["response"], [by_id[i]["text"] for i in ids], embed=embed, chunk_vectors=np.stack([vector_of[i] for i in ids]), nli=nli))
        messages = draft_messages(item["question"], hits, False)
        t0 = time.time()
        reply = provider.generate(confidence_messages(messages, trace["draft"]["final"]), temperature=0.0, seed=trace["seed"], max_tokens=12).text
        features.update(confidence_features(reply))
        timings["confidence"] += time.time() - t0
        t0 = time.time()
        samples = [provider.generate(messages, temperature=0.7, seed=s, max_tokens=160).text.strip() for s in range(1, 6)]
        features.update(agreement_features(samples, trace["draft"]["final"]))
        timings["sampling"] += time.time() - t0
        t0 = time.time()
        form_hint = "ANSWER" if trace["action"] == "REJECT" else trace["action"]
        record = grade(item, trace["response"], judge=judge, form_hint=form_hint)
        timings["grading"] += time.time() - t0
        trace["paid"] = {"verbalized": reply.strip(), "samples": samples}
        (trace_dir / f"{item['id']}.json").write_text(json.dumps(trace, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        rows.append({"item_id": item["id"], "label": record["label"], "grade": record["grade"], "decided_by": record["decided_by"], "action": trace["action"],
                     "response": trace["response"], "question": item["question"], "strata": stratum(trace), "features": features,
                     "leaked_fields_present_in_trace": leaked_fields(trace)})
        print(f"{n:>3} {item['id']} {item['bucket']:<14} {trace['action']:<8} {record['grade']:<8} {time.time() - started:.0f}s", flush=True)

    # 1b. audits that run regardless of band: provenance, no ground truth in the vector, near-duplicates across the splits
    for r in rows:
        for k in r["features"]:
            assert k in PROVENANCE, f"feature without provenance: {k}"
            assert k not in GROUND_TRUTH, f"ground truth in the feature vector: {k}"
    dev_items = [json.loads(l) for l in (ROOT / "data" / "eval" / "dev.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    dev_q = [d["question"] for d in dev_items]
    dev_pages = [{str(e["page"]) for e in d.get("evidence", [])} for d in dev_items]
    dev_vec = embed(dev_q)
    test_vec = embed([it["question"] for it in items])
    dev_vec = dev_vec / np.linalg.norm(dev_vec, axis=1, keepdims=True)
    test_vec = test_vec / np.linalg.norm(test_vec, axis=1, keepdims=True)
    sims = test_vec @ dev_vec.T
    for i, it in enumerate(items):  # in the dry run the items are the dev items; a question is not its own duplicate
        for k, d in enumerate(dev_items):
            if d["id"] == it["id"]:
                sims[i, k] = -1.0
    flagged_pairs = []
    for i, it in enumerate(items):
        words = content_words(it["question"])
        pages = {str(e["page"]) for e in it.get("evidence", [])}
        j = int(np.argmax(sims[i]))
        best_cos = float(sims[i, j])
        jac_all = [0.0 if d["id"] == it["id"] else (len(words & content_words(q)) / len(words | content_words(q)) if (words | content_words(q)) else 0.0)
                   for q, d in zip(dev_q, dev_items)]
        jj = int(np.argmax(jac_all))
        reasons = []
        if jac_all[jj] >= DUP_JACCARD:
            reasons.append(f"jaccard {jac_all[jj]:.2f} with {dev_items[jj]['id']}")
        if best_cos >= DUP_COSINE:
            reasons.append(f"cosine {best_cos:.2f} with {dev_items[j]['id']}")
        same_page = [k for k in range(len(dev_items)) if pages & dev_pages[k] and sims[i, k] >= DUP_SAME_PAGE_COSINE]
        if same_page:
            reasons.append("same evidence page and cosine >= 0.8 with " + ", ".join(dev_items[k]["id"] for k in same_page))
        rows[i]["nearest_dev"] = {"id": dev_items[j]["id"], "cosine": round(best_cos, 3), "jaccard_best": round(max(jac_all), 3), "jaccard_id": dev_items[jj]["id"]}
        rows[i]["duplicate_flag"] = bool(reasons)
        if reasons:
            flagged_pairs.append({"test_id": it["id"], "test_question": it["question"], "dev_id": dev_items[j]["id"], "dev_question": dev_q[j], "reasons": reasons})
    split_check = {"seed": 42, "source": "scripts/lock_and_split.py, stratified by bucket, halves per bucket",
                   "test_counts_found": dict(Counter(it["bucket"] for it in items)), "expected": {"answerable": 46, "ambiguous": 9, "unanswerable": 25, "false_premise": 20}}

    # 2. score with the frozen artifact, apply the policy
    names = artifact["features"]
    X = np.array([[float(r["features"][k]) for k in names] for r in rows])
    p_log = artifact["model"].predict_proba(X)[:, 1]
    p = artifact["isotonic"].predict(p_log)
    y = np.array([r["label"] for r in rows])
    bucket = np.array([r["strata"]["bucket"] for r in rows])
    answered = np.array([r["action"] == "ANSWER" for r in rows])
    outcome = np.array([decide(r["action"], float(pi), thresholds) for r, pi in zip(rows, p)])
    for r, pi, pl, o in zip(rows, p, p_log, outcome):
        r["probability"] = round(float(pi), 4)
        r["probability_logistic"] = round(float(pl), 4)
        r["outcome"] = o
    strata = {"pooled": np.ones(len(rows), bool), "answerable": bucket == "answerable",
              "decisive": (bucket == "answerable") & np.array([bool(r["strata"]["evidence_retrieved"]) for r in rows])}

    # 3. baselines fitted on dev features
    dev_rows = [json.loads(l) for l in (ROOT / "reports" / "features-dev.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    dev_names = admissible_features(dev_rows)
    from signals.process import PROVENANCE as PP
    from signals.retrieval_support import PROVENANCE as SP
    BASELINES["free signals alone"] = [n_ for n_ in dev_names if n_ in PP or n_ in SP]
    baseline_probs = {}
    for name, feats in BASELINES.items():
        feats = [f for f in feats if f in dev_names]
        model, iso = fit_baseline(dev_rows, feats)
        Xb = np.array([[float(r["features"][k]) for k in feats] for r in rows])
        baseline_probs[name] = iso.predict(model.predict_proba(Xb)[:, 1])
    baseline_probs["confirmed minus_logprobs (frozen artifact)"] = p

    # 4. metrics
    def block(pp, yy):
        return {"auroc": bootstrap(auroc, pp, yy), "brier": bootstrap(brier, pp, yy), "ece": bootstrap(ece, pp, yy), "aurc": bootstrap(aurc, pp, yy)}

    results = {"frozen": frozen, "attempts": attempts, "n": len(rows), "strata_counts": {s: int(m.sum()) for s, m in strata.items()},
               "audit": {"provenance_ok": True, "ground_truth_in_vector": False, "near_duplicates": flagged_pairs, "split": split_check},
               "label_rate": {s: int(y[m].sum()) for s, m in strata.items()}, "metrics": {}, "baselines": {}, "policy": {}, "timings": {k: round(v, 1) for k, v in timings.items()}}
    for s, m in strata.items():
        results["metrics"][s] = block(p[m], y[m])
        results["metrics"][s]["reliability"] = reliability(p[m], y[m])
    for name, pb in baseline_probs.items():
        results["baselines"][name] = {s: {"auroc": bootstrap(auroc, pb[m], y[m]), "brier": bootstrap(brier, pb[m], y[m])} for s, m in strata.items()}
    pa, ya = p[answered], y[answered]
    curve = step_curve(pa, ya)
    cov_b, risk_b = bootstrap_at(pa, ya, 0.0)
    cov_e, risk_e = bootstrap_at(pa, ya, thresholds.escalate)
    cov_a, risk_a = bootstrap_at(pa, ya, thresholds.answer)
    esc = answered & (outcome == "ESCALATE")
    flagged = answered & ((outcome == "ESCALATE") | (outcome == "VERIFY"))
    wrong = answered & (y == 0)

    def pr(mask):
        prec = (y[mask] == 0).mean() if mask.any() else float("nan")
        rec = (mask & wrong).sum() / wrong.sum() if wrong.any() else float("nan")
        return {"precision": round(float(prec), 3), "recall": round(float(rec), 3), "n": int(mask.sum())}

    results["policy"] = {"answered": int(answered.sum()), "answered_correct": int(ya.sum()),
                         "base": {"coverage": 1.0, "risk": round(float(1 - ya.mean()), 3), "risk_ci": [round(float(risk_b[0]), 3), round(float(risk_b[1]), 3)]},
                         "escalate_threshold": {"coverage": round(float(at_threshold(pa, ya, thresholds.escalate)[0]), 3), "coverage_ci": [round(float(cov_e[0]), 3), round(float(cov_e[1]), 3)],
                                                "risk": round(float(at_threshold(pa, ya, thresholds.escalate)[1]), 3), "risk_ci": [round(float(risk_e[0]), 3), round(float(risk_e[1]), 3)]},
                         "answer_threshold": {"coverage": round(float(at_threshold(pa, ya, thresholds.answer)[0]), 3), "coverage_ci": [round(float(cov_a[0]), 3), round(float(cov_a[1]), 3)],
                                              "risk": round(float(at_threshold(pa, ya, thresholds.answer)[1]), 3), "risk_ci": [round(float(risk_a[0]), 3), round(float(risk_a[1]), 3)]},
                         "risk_coverage": curve, "escalation": {"escalate_only": pr(esc), "flagged": pr(flagged)},
                         "outcomes_per_bucket": {b: {o: {"n": int(((bucket == b) & (outcome == o)).sum()), "correct": int(y[(bucket == b) & (outcome == o)].sum())}
                                                     for o in ("ANSWER", "VERIFY", "ESCALATE", "ABSTAIN", "CLARIFY")} for b in BUCKETS}}
    acc_at = {}
    for target in (0.25, 0.5, 0.75, 1.0):
        nearest = min(curve, key=lambda r: abs(r["coverage"] - target))
        acc_at[str(target)] = {"threshold": nearest["threshold"], "coverage": nearest["coverage"], "accuracy": round(1 - nearest["risk"], 3),
                               "accuracy_ci": [round(1 - nearest["risk_hi"], 3), round(1 - nearest["risk_lo"], 3)]}
    results["policy"]["accuracy_at_coverage"] = acc_at
    conf = {}
    for b in BUCKETS + ("all",):
        m = np.ones(len(rows), bool) if b == "all" else bucket == b
        got = m & np.array([bool(r["strata"]["evidence_retrieved"]) for r in rows])
        conf[b] = {"retrieved": {"n": int(got.sum()), "correct": int(y[got].sum())}, "not_retrieved": {"n": int((m & ~got).sum()), "correct": int(y[m & ~got].sum())}}
    results["confounder"] = conf
    results["per_bucket"] = {b: {"n": int((bucket == b).sum()), "actions": dict(Counter(r["action"] for r in rows if r["strata"]["bucket"] == b)),
                                 "grades": dict(Counter(r["grade"] for r in rows if r["strata"]["bucket"] == b))} for b in BUCKETS}
    results["wall_seconds"] = round(time.time() - started, 1)
    keep = np.array([not r["duplicate_flag"] for r in rows])
    results["metrics_without_flagged"] = {s: block(p[m & keep], y[m & keep]) for s, m in strata.items()} if (~keep).any() else None

    # 5. write everything verbatim
    with open(str(out) + "-rows.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    Path(str(out) + ".json").write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8", newline="\n")
    if not args.dry_run:
        MARKER.write_text(f"test.jsonl read once by scripts/evaluate_test.py; completed {datetime.now(timezone.utc).isoformat(timespec='seconds')} after {attempts} attempt(s)\n", encoding="utf-8")

    title = "Dry run on dev (not the test read)" if args.dry_run else "Test split results, read once"
    lines = [f"# {title}", "", f"Preregistered in reports/m8-preregistration.md. Frozen: {json.dumps(frozen)}.",
             f"{len(rows)} items; strata counts {results['strata_counts']}; correct per stratum {results['label_rate']}. Wall clock {results['wall_seconds']:.0f} s "
             f"(loop {timings['loop']:.0f}, confidence {timings['confidence']:.0f}, sampling {timings['sampling']:.0f}, grading {timings['grading']:.0f}).", "",
             f"Attempts (a crashed attempt leaves a start line and replays from the cache): {attempts}.", "",
             "## Audit, run regardless of band", "",
             f"- Provenance: every feature name in the rows is in the provenance lists and none is a ground-truth field (asserted).",
             f"- Split: seed {split_check['seed']}, {split_check['source']}; test counts found {split_check['test_counts_found']}, expected {split_check['expected']}.",
             f"- Near-duplicates across dev and test (Jaccard >= {DUP_JACCARD}, cosine >= {DUP_COSINE}, or same evidence page with cosine >= {DUP_SAME_PAGE_COSINE}): {len(flagged_pairs)} flagged.",
             *[f"  - {fp['test_id']} / {fp['dev_id']} ({'; '.join(fp['reasons'])}): \"{fp['test_question']}\" against \"{fp['dev_question']}\"" for fp in flagged_pairs],
             "", "## Headline: the confirmed vector", "", "| stratum | n | correct | AUROC | Brier | ECE (10 bins) | AURC |", "|---|---|---|---|---|---|---|"]
    for s, m in strata.items():
        r_ = results["metrics"][s]
        lines.append(f"| {s} | {int(m.sum())} | {int(y[m].sum())} | {fmt(r_['auroc'])} | {fmt(r_['brier'])} | {fmt(r_['ece'])} | {fmt(r_['aurc'])} |")
    if results["metrics_without_flagged"]:
        lines += ["", "With the flagged near-duplicate items removed:", "", "| stratum | AUROC | Brier |", "|---|---|---|"]
        for s, r_ in results["metrics_without_flagged"].items():
            lines.append(f"| {s} | {fmt(r_['auroc'])} | {fmt(r_['brier'])} |")
    pol = results["policy"]
    lines += ["", f"Policy on the {pol['answered']} answered items ({pol['answered_correct']} correct):", "",
              "| operating point | coverage % | risk % |", "|---|---|---|",
              f"| show everything | 100 | {100 * pol['base']['risk']:.0f} [{100 * pol['base']['risk_ci'][0]:.0f}, {100 * pol['base']['risk_ci'][1]:.0f}] |",
              f"| frozen thresholds, escalate below {thresholds.escalate} | {100 * pol['escalate_threshold']['coverage']:.0f} [{100 * pol['escalate_threshold']['coverage_ci'][0]:.0f}, {100 * pol['escalate_threshold']['coverage_ci'][1]:.0f}] | {100 * pol['escalate_threshold']['risk']:.0f} [{100 * pol['escalate_threshold']['risk_ci'][0]:.0f}, {100 * pol['escalate_threshold']['risk_ci'][1]:.0f}] |",
              f"| ANSWER band only, at or above {thresholds.answer} | {100 * pol['answer_threshold']['coverage']:.0f} [{100 * pol['answer_threshold']['coverage_ci'][0]:.0f}, {100 * pol['answer_threshold']['coverage_ci'][1]:.0f}] | {100 * pol['answer_threshold']['risk']:.0f} [{100 * pol['answer_threshold']['risk_ci'][0]:.0f}, {100 * pol['answer_threshold']['risk_ci'][1]:.0f}] |",
              "", "## Baselines (fitted on dev, applied here)", "", "| system | pooled AUROC | answerable AUROC | decisive AUROC | pooled Brier |", "|---|---|---|---|---|"]
    for name, r_ in results["baselines"].items():
        lines.append(f"| {name} | {fmt(r_['pooled']['auroc'])} | {fmt(r_['answerable']['auroc'])} | {fmt(r_['decisive']['auroc'])} | {fmt(r_['pooled']['brier'])} |")
    lines += ["", "## Escalation precision and recall (answered items; wrong = label 0)", "",
              f"- ESCALATE only: precision {pol['escalation']['escalate_only']['precision']}, recall {pol['escalation']['escalate_only']['recall']}, n {pol['escalation']['escalate_only']['n']}.",
              f"- Flagged (ESCALATE or VERIFY): precision {pol['escalation']['flagged']['precision']}, recall {pol['escalation']['flagged']['recall']}, n {pol['escalation']['flagged']['n']}.",
              "", "## Accuracy at coverage (answered items, tie-aware thresholds nearest the target)", "", "| target | threshold | coverage | accuracy |", "|---|---|---|---|"]
    for t, r_ in acc_at.items():
        lines.append(f"| {t} | {r_['threshold']:.3f} | {r_['coverage']:.2f} | {r_['accuracy']:.2f} [{r_['accuracy_ci'][0]:.2f}, {r_['accuracy_ci'][1]:.2f}] |")
    lines += ["", "## Risk-coverage, answered population (every reachable threshold)", "", "| threshold | coverage % | risk % |", "|---|---|---|"]
    for r_ in curve:
        lines.append(f"| {r_['threshold']:.3f} | {100 * r_['coverage']:.0f} [{100 * r_['cov_lo']:.0f}, {100 * r_['cov_hi']:.0f}] | {100 * r_['risk']:.0f} [{100 * r_['risk_lo']:.0f}, {100 * r_['risk_hi']:.0f}] |")
    lines += ["", "## Per bucket: actions, grades, policy outcomes (counts next to rates; ambiguous indicative only)", "",
              "| bucket | n | actions | grades | outcomes (n, correct) |", "|---|---|---|---|---|"]
    for b in BUCKETS:
        pb = results["per_bucket"][b]
        outs = ", ".join(f"{o} {v['n']}/{v['correct']}" for o, v in pol["outcomes_per_bucket"][b].items() if v["n"])
        lines.append(f"| {b} | {pb['n']} | {pb['actions']} | {pb['grades']} | {outs} |")
    lines += ["", "## Confounder: accuracy by whether the evidence chunk was retrieved", "", "| bucket | retrieved: correct/n | not retrieved: correct/n |", "|---|---|---|"]
    for b, c in conf.items():
        lines.append(f"| {b} | {pct(c['retrieved']['correct'], c['retrieved']['n'])} | {pct(c['not_retrieved']['correct'], c['not_retrieved']['n'])} |")
    lines += ["", "## Reliability, pooled (10 bins)", "", "| bin | n | mean confidence | accuracy |", "|---|---|---|---|"]
    for b_ in results["metrics"]["pooled"]["reliability"]:
        lines.append(f"| {b_['lo']:.1f} to {b_['hi']:.1f} | {b_['n']} | {b_['confidence'] if b_['confidence'] is not None else ''} | {b_['accuracy'] if b_['accuracy'] is not None else ''} |")
    Path(str(out) + ".md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
