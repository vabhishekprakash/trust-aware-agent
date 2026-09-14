"""Risk-coverage curve with a bootstrap band, and candidate risk targets, on dev.

Usage:
    python scripts/policy_curve.py [--variant minus_logprobs] [--fit logistic+isotonic] [--out reports/m5-risk-coverage]

Nothing is tuned here. The out-of-fold probabilities of the confirmed
calibrator are sorted, and for each coverage the risk (error rate among
the covered) is computed, with a 95 percent bootstrap band over items.
Two populations are shown: the answered items, where the thresholds act,
and the deployed population, all items with CLARIFY and ABSTAIN passing
through as covered outputs. For candidate targets (10, 15, 20, 25 percent
error among answered items) the table gives the threshold, the coverage
it buys and intervals on both, next to the base rate. The unanswerable
bucket is reported on its own. Writes <out>.md, <out>.json and <out>.png.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

SEED = 42
TARGETS = (0.10, 0.15, 0.20, 0.25)
BUCKETS = ("answerable", "ambiguous", "unanswerable", "false_premise")


def fmt(point, lo, hi, pct=True):
    scale = 100 if pct else 1
    return f"{point * scale:.0f} [{lo * scale:.0f}, {hi * scale:.0f}]" if pct else f"{point:.3f} [{lo:.3f}, {hi:.3f}]"


def step_curve(p: np.ndarray, y: np.ndarray, n_boot=1000, seed=SEED) -> list[dict]:
    """Coverage and risk at every distinct probability used as a threshold (ties covered together), with bootstrap intervals.

    Isotonic probabilities carry many ties, so a rank-ordered curve would split a tie and
    overstate what any real threshold can do. Every point here is reachable by a threshold.
    """
    rng = np.random.default_rng(seed)
    boots = [rng.integers(0, len(p), len(p)) for _ in range(n_boot)]
    out = []
    for thr in sorted(set(p.tolist()), reverse=True):
        cov, risk = at_threshold(p, y, thr)
        covs = np.array([at_threshold(p[b], y[b], thr)[0] for b in boots])
        risks = np.array([at_threshold(p[b], y[b], thr)[1] for b in boots])
        out.append({"threshold": round(float(thr), 4), "coverage": round(float(cov), 3), "risk": round(float(risk), 3),
                    "cov_lo": round(float(np.percentile(covs, 2.5)), 3), "cov_hi": round(float(np.percentile(covs, 97.5)), 3),
                    "risk_lo": round(float(np.nanpercentile(risks, 2.5)), 3), "risk_hi": round(float(np.nanpercentile(risks, 97.5)), 3)})
    return out


def at_threshold(p, y, thr):
    covered = p >= thr
    cov = covered.mean()
    risk = (1 - y[covered]).mean() if covered.any() else np.nan
    return cov, risk


def threshold_for_target(p, y, target):
    """The lowest distinct probability whose covered error rate (ties included) is at most the target; None if none."""
    best = None
    for thr in sorted(set(p.tolist()), reverse=True):
        _, risk = at_threshold(p, y, thr)
        if risk <= target:
            best = float(thr)
    return best


def bootstrap_at(p, y, thr, n_boot=1000, seed=SEED):
    rng = np.random.default_rng(seed)
    covs, risks = [], []
    for _ in range(n_boot):
        idx = rng.integers(0, len(p), len(p))
        c, r = at_threshold(p[idx], y[idx], thr)
        covs.append(c)
        risks.append(r)
    return (np.percentile(covs, 2.5), np.percentile(covs, 97.5)), (np.nanpercentile(risks, 2.5), np.nanpercentile(risks, 97.5))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--oof", default=str(ROOT / "reports" / "m4-calibration-oof.jsonl"))
    parser.add_argument("--features", default=str(ROOT / "reports" / "features-dev.jsonl"))
    parser.add_argument("--variant", default="minus_logprobs")
    parser.add_argument("--fit", default="logistic+isotonic")
    parser.add_argument("--out", default=str(ROOT / "reports" / "m5-risk-coverage"))
    args = parser.parse_args()
    if any("test" in Path(p).name for p in (args.oof, args.features)):
        print("refusing to read the test split")
        return 1
    oof = {json.loads(l)["item_id"]: json.loads(l) for l in Path(args.oof).read_text(encoding="utf-8").splitlines() if l.strip()}
    feats = {json.loads(l)["item_id"]: json.loads(l) for l in Path(args.features).read_text(encoding="utf-8").splitlines() if l.strip()}
    ids = list(oof)
    p_all = np.array([oof[i][args.variant][args.fit] for i in ids])
    y_all = np.array([oof[i]["label"] for i in ids])
    bucket = np.array([oof[i]["strata"]["bucket"] for i in ids])
    action = np.array(["ANSWER" if feats[i]["features"]["action_answer"] else ("ABSTAIN" if feats[i]["features"]["action_abstain"] else "CLARIFY") for i in ids])
    answered = action == "ANSWER"
    p, y = p_all[answered], y_all[answered]

    lines = ["# Risk and coverage on dev, before any threshold is chosen", "",
             f"Out-of-fold probabilities of {args.variant} with {args.fit}, {len(ids)} dev items, bootstrap bands over items with 1000 resamples. "
             "Risk is the error rate among the covered items; coverage is the share covered. Nothing is tuned here.", "",
             f"Answered items: {int(answered.sum())} (the population the thresholds act on), of which {int(y.sum())} correct, base risk {100 * (1 - y.mean()):.0f} percent. "
             f"Pass-through items: {int((action == 'ABSTAIN').sum())} ABSTAIN and {int((action == 'CLARIFY').sum())} CLARIFY, "
             f"of which {int(y_all[~answered].sum())} correct.", ""]

    # curves at every reachable threshold
    results = {}
    fig_data = {}
    for name in ("answered", "deployed"):
        pp = p if name == "answered" else np.where(answered, p_all, 1.0)
        yy = y if name == "answered" else y_all
        pts = step_curve(pp, yy)
        results[name] = pts
        fig_data[name] = pts
        lines += [f"## Risk-coverage curve, {name} population", "", "Every row is a threshold that can actually be set (ties covered together).", "",
                  "| threshold | coverage % | risk % |", "|---|---|---|"]
        for r in pts:
            lines.append(f"| {r['threshold']:.3f} | {fmt(r['coverage'], r['cov_lo'], r['cov_hi'])} | {fmt(r['risk'], r['risk_lo'], r['risk_hi'])} |")
        lines.append("")

    # candidate targets on the answered population
    lines += ["## Candidate targets, error among answered items", "",
              "Threshold is the lowest out-of-fold probability whose covered error rate on dev is at most the target. Coverage is the share of "
              "answered items shown; intervals are bootstrap over items at that fixed threshold. The deployed columns count CLARIFY and ABSTAIN as covered with their own labels.", "",
              "| target | threshold | answered: coverage % | answered: risk % | deployed: coverage % | deployed: risk % |", "|---|---|---|---|---|---|"]
    cov_b, risk_b = bootstrap_at(p, y, 0.0)
    cov_d, risk_d = bootstrap_at(np.where(answered, p_all, 1.0), y_all, 0.0)
    lines.append(f"| base rate (answer everything) | 0.000 | {fmt(1.0, *cov_b)} | {fmt(1 - y.mean(), *risk_b)} | {fmt(1.0, *cov_d)} | {fmt(1 - y_all.mean(), *risk_d)} |")
    candidates = {}
    for target in TARGETS:
        thr = threshold_for_target(p, y, target)
        if thr is None:
            lines.append(f"| {int(target * 100)}% | none reachable | | | | |")
            continue
        cov, risk = at_threshold(p, y, thr)
        (clo, chi), (rlo, rhi) = bootstrap_at(p, y, thr)
        pd = np.where(answered, p_all, 1.0)
        covd, riskd = at_threshold(pd, y_all, thr)
        (cdlo, cdhi), (rdlo, rdhi) = bootstrap_at(pd, y_all, thr)
        candidates[str(target)] = {"threshold": round(thr, 4), "answered": {"coverage": round(float(cov), 3), "risk": round(float(risk), 3)},
                                   "deployed": {"coverage": round(float(covd), 3), "risk": round(float(riskd), 3)}}
        lines.append(f"| {int(target * 100)}% | {thr:.3f} | {fmt(cov, clo, chi)} | {fmt(risk, rlo, rhi)} | {fmt(covd, cdlo, cdhi)} | {fmt(riskd, rdlo, rdhi)} |")

    # the unanswerable bucket, and what each candidate does per bucket
    lines += ["", "## What each candidate does per bucket", "",
              "Counts of items shown (ANSWER by the policy, plus pass-through ABSTAIN and CLARIFY) and withheld (below the threshold), with the correct count among the shown. "
              "The unanswerable bucket is where a policy can look good by passing easy abstentions.", ""]
    for target, cand in candidates.items():
        thr = cand["threshold"]
        lines += [f"Target {int(float(target) * 100)}%, threshold {thr:.3f}:", "", "| bucket | n | shown | correct among shown | withheld | correct among withheld |", "|---|---|---|---|---|---|"]
        for b in BUCKETS:
            m = bucket == b
            show = m & (~answered | (p_all >= thr))
            hold = m & answered & (p_all < thr)
            lines.append(f"| {b} | {int(m.sum())} | {int(show.sum())} ({int((show & ~answered).sum())} pass-through) | {int(y_all[show].sum())} | {int(hold.sum())} | {int(y_all[hold].sum())} |")
        lines.append("")
    una = bucket == "unanswerable"
    lines += ["Unanswerable bucket on its own: " + f"{int(una.sum())} items, {int((una & ~answered).sum())} pass through as abstentions or clarifications "
              f"({int(y_all[una & ~answered].sum())} correct), {int((una & answered).sum())} answered. The thresholds never touch the pass-through items, so this "
              "bucket's contribution to deployed coverage and to the positives is the same at every target. That is stated so a reader can subtract it: the answered-population "
              "columns above are the policy's real work.", ""]

    # figure
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(6, 4))
        for name, color in (("answered", "C0"), ("deployed", "C1")):
            pts = fig_data[name]
            g = np.array([r["coverage"] for r in pts]); c = np.array([r["risk"] for r in pts])
            lo = np.array([r["risk_lo"] for r in pts]); hi = np.array([r["risk_hi"] for r in pts])
            ax.step(g, c, where="post", color=color, label=f"{name} population")
            ax.fill_between(g, lo, hi, step="post", color=color, alpha=0.2)
        ax.axhline(1 - y.mean(), color="C0", linestyle=":", label="base risk, answered")
        for target in TARGETS:
            ax.axhline(target, color="grey", linewidth=0.5, linestyle="--")
        ax.set_xlabel("coverage")
        ax.set_ylabel("risk (error among covered)")
        ax.set_title("Dev risk-coverage, out of fold, 95% bootstrap band")
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(Path(args.out).with_suffix(".png"), dpi=120)
        lines.append(f"Figure: {Path(args.out).with_suffix('.png').name}")
    except Exception as e:  # noqa: BLE001
        lines.append(f"No figure: {e}")

    Path(args.out).with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    Path(args.out).with_suffix(".json").write_text(json.dumps({"variant": args.variant, "fit": args.fit, "curves": results, "candidates": candidates}, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
