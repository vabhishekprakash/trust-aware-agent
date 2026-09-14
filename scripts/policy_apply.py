"""Apply the chosen thresholds to dev and report the policy's actions per bucket.

Usage:
    python scripts/policy_apply.py [--policy data/calibrators/policy.json] [--out reports/m5-policy]

Uses the out-of-fold probabilities of the confirmed calibrator, so every
item is scored by a model that never saw it. Reports, with counts next to
rates: the outcome per bucket (ANSWER, VERIFY, ESCALATE, and the agent's
own ABSTAIN and CLARIFY passing through) and the correct count in each;
coverage and risk on the answered population at the escalate threshold,
against the base rate and against the recorded risk-target alternative;
and the deployed columns with their caveat. Refuses test.
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from policy.router import Thresholds, decide  # noqa: E402

SEED = 42
BUCKETS = ("answerable", "ambiguous", "unanswerable", "false_premise")
OUTCOMES = ("ANSWER", "VERIFY", "ESCALATE", "ABSTAIN", "CLARIFY")


def pct(a, n):
    return f"{a}/{n} ({100 * a / n:.0f}%)" if n else "0/0"


def cov_risk(p, y, thr):
    covered = p >= thr
    return covered.mean(), ((1 - y[covered]).mean() if covered.any() else float("nan"))


def boot(p, y, thr, n=1000):
    rng = np.random.default_rng(SEED)
    cs, rs = [], []
    for _ in range(n):
        idx = rng.integers(0, len(p), len(p))
        c, r = cov_risk(p[idx], y[idx], thr)
        cs.append(c)
        rs.append(r)
    return (np.percentile(cs, 2.5), np.percentile(cs, 97.5)), (np.nanpercentile(rs, 2.5), np.nanpercentile(rs, 97.5))


def line(label, p, y, thr):
    c, r = cov_risk(p, y, thr)
    (clo, chi), (rlo, rhi) = boot(p, y, thr)
    return f"| {label} | {thr:.3f} | {100 * c:.0f} [{100 * clo:.0f}, {100 * chi:.0f}] | {100 * r:.0f} [{100 * rlo:.0f}, {100 * rhi:.0f}] |"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--policy", default=str(ROOT / "data" / "calibrators" / "policy.json"))
    parser.add_argument("--oof", default=str(ROOT / "reports" / "m4-calibration-oof.jsonl"))
    parser.add_argument("--features", default=str(ROOT / "reports" / "features-dev.jsonl"))
    parser.add_argument("--out", default=str(ROOT / "reports" / "m5-policy"))
    args = parser.parse_args()
    if any("test" in Path(p).name for p in (args.oof, args.features)):
        print("refusing to read the test split")
        return 1
    policy = json.loads(Path(args.policy).read_text(encoding="utf-8"))
    t = Thresholds(answer=policy["thresholds"]["answer"], escalate=policy["thresholds"]["escalate"])
    oof = {json.loads(l)["item_id"]: json.loads(l) for l in Path(args.oof).read_text(encoding="utf-8").splitlines() if l.strip()}
    feats = {json.loads(l)["item_id"]: json.loads(l) for l in Path(args.features).read_text(encoding="utf-8").splitlines() if l.strip()}
    ids = list(oof)
    p = np.array([oof[i][policy["variant"]][policy["fit"]] for i in ids])
    y = np.array([oof[i]["label"] for i in ids])
    bucket = np.array([oof[i]["strata"]["bucket"] for i in ids])
    action = np.array(["ANSWER" if feats[i]["features"]["action_answer"] else ("ABSTAIN" if feats[i]["features"]["action_abstain"] else "CLARIFY") for i in ids])
    outcome = np.array([decide(a, float(pr), t) for a, pr in zip(action, p)])
    answered = action == "ANSWER"

    rows = [{"item_id": i, "bucket": b, "agent_action": a, "probability": round(float(pr), 4), "outcome": o, "label": int(l)}
            for i, b, a, pr, o, l in zip(ids, bucket, action, p, outcome, y)]
    lines = ["# The decision policy on dev", "",
             f"Thresholds chosen by the owner on 2026-09-12: ANSWER at or above {t.answer}, ESCALATE below {t.escalate}, VERIFY between. "
             f"{policy['basis']}. Probabilities are out of fold from {policy['variant']} with {policy['fit']}; {len(ids)} dev items. "
             "VERIFY is a flag, not a verification loop.", "",
             "## Outcomes per bucket, counts with rates, and the correct count in each", "",
             "| bucket | n | " + " | ".join(OUTCOMES) + " |", "|---|---|" + "---|" * len(OUTCOMES)]
    per_bucket = {}
    for b in BUCKETS + ("all",):
        m = np.ones(len(ids), dtype=bool) if b == "all" else bucket == b
        cells = []
        per_bucket[b] = {}
        for o in OUTCOMES:
            mo = m & (outcome == o)
            cells.append(f"{pct(int(mo.sum()), int(m.sum()))}, {int(y[mo].sum())} correct")
            per_bucket[b][o] = {"n": int(mo.sum()), "correct": int(y[mo].sum())}
        lines.append(f"| {b} | {int(m.sum())} | " + " | ".join(cells) + " |")

    pa, ya = p[answered], y[answered]
    lines += ["", "## The answered population: the policy's real work", "",
              f"{int(answered.sum())} items the agent answered, {int(ya.sum())} correct. Coverage is the share shown (ANSWER or VERIFY); "
              "risk is the error rate among the shown. Intervals are bootstrap over items at the fixed threshold.", "",
              "| operating point | threshold | coverage % | risk % |", "|---|---|---|---|",
              line("base rate, show everything", pa, ya, 0.0),
              line("chosen: escalate below", pa, ya, t.escalate),
              line("shown without a flag (ANSWER band only)", pa, ya, t.answer),
              line(f"alternative, risk target {int(100 * policy['alternative_recorded']['target_risk'])} percent", pa, ya, policy["alternative_recorded"]["threshold"]),
              "",
              "The point estimate moves in the expected direction and the interval does not exclude no effect. No claim that the policy reduces error "
              "is made on dev; the single read of the test split at M8 is where that is settled. The alternative row shows what a risk guarantee would "
              f"cost here: {policy['alternative_recorded']['coverage_of_answered']} answered items shown.", ""]

    # accuracy per band, with intervals: the confident band should beat the flagged one and here it does not
    def band_acc(mask, n=1000):
        k = int(mask.sum())
        if k == 0:
            return "0/0"
        rng = np.random.default_rng(SEED)
        vals = y[mask]
        boots = [rng.choice(vals, k, replace=True).mean() for _ in range(n)]
        return f"{int(vals.sum())}/{k} ({100 * vals.mean():.0f}% [{100 * np.percentile(boots, 2.5):.0f}, {100 * np.percentile(boots, 97.5):.0f}])"

    lines += ["## Accuracy per band, with intervals", "",
              "If the calibrator's ordering were reliable, the ANSWER band would be more accurate than the VERIFY band. Intervals are bootstrap over the band's items.", "",
              "| population | ANSWER band | VERIFY band | ESCALATE band |", "|---|---|---|---|"]
    for label, m in (("answerable items the agent answered", answered & (bucket == "answerable")), ("all answered items", answered)):
        lines.append(f"| {label} | " + " | ".join(band_acc(m & (outcome == o)) for o in ("ANSWER", "VERIFY", "ESCALATE")) + " |")
    lines += ["", "At this sample size the calibrator's ordering is not reliable enough for the top band to outperform the middle one. "
              "That is one finding seen three ways: the band accuracies here, the AUROC of 0.70 [0.61, 0.79], and the flat risk-coverage curve. "  # corrected 2026-09-14: was the plain logistic fit's 0.69
              "The intervals cover the reversal; the report does not treat it as a separate effect.", ""]

    passthrough = ~answered
    pd = np.where(answered, p, 1.0)
    lines += ["## Deployed columns, with their caveat", "",
              f"All {len(ids)} items, with the agent's {int(passthrough.sum())} ABSTAIN and CLARIFY outputs counted as shown with their own labels.", "",
              "| operating point | threshold | coverage % | risk % |", "|---|---|---|---|",
              line("base rate", pd, y, 0.0), line("chosen: escalate below", pd, y, t.escalate), "",
              f"Caveat: deployed coverage is flattered by {int((bucket == 'unanswerable') & passthrough).sum() if False else int(((bucket == 'unanswerable') & passthrough).sum())} "
              f"pass-through abstentions on unanswerable items that the policy never touches ({int(y[(bucket == 'unanswerable') & passthrough].sum())} correct), "
              f"and deployed risk is punished by {int(((bucket == 'false_premise') & passthrough & (y == 0)).sum())} false-premise bare abstentions graded PARTIAL and counted as errors. "
              "The answered-population table above is the policy's real work.", ""]

    Path(args.out).with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    Path(args.out).with_suffix(".json").write_text(json.dumps({"policy": policy, "per_bucket": per_bucket, "rows": rows}, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
