"""Draw the report's figures from the committed JSON, dev and test side by side. No hand edits.

Usage:
    python scripts/make_plots.py [--out docs/assets]

Inputs: reports/m4-calibration.json (dev, out of fold), reports/m5-risk-coverage.json
and reports/m5-policy.json (dev policy), reports/m8-test-results.json (test),
reports/m8-dev-baselines.json (dev baselines, out of fold). Outputs four PNGs:
reliability, risk-coverage, per-bucket outcomes, baselines.
"""

import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BUCKETS = ("answerable", "ambiguous", "unanswerable", "false_premise")
OUTCOMES = ("ANSWER", "VERIFY", "ESCALATE", "ABSTAIN", "CLARIFY")
COLORS = {"ANSWER": "#1b6e3a", "VERIFY": "#9a6a00", "ESCALATE": "#a1261f", "ABSTAIN": "#3b5b8a", "CLARIFY": "#7a7a7a"}


def load(name):
    return json.loads((ROOT / "reports" / name).read_text(encoding="utf-8"))


def reliability_plot(dev, test, out):
    fig, axes = plt.subplots(1, 2, figsize=(9, 4), sharey=True)
    for ax, stratum in zip(axes, ("pooled", "decisive")):
        for label, table, color in (("dev, out of fold", dev[stratum], "C0"), ("test, single read", test[stratum], "C3")):
            xs = [b["confidence"] for b in table if b["n"]]
            ys = [b["accuracy"] for b in table if b["n"]]
            ns = [b["n"] for b in table if b["n"]]
            ax.plot(xs, ys, "o-", color=color, label=label)
            for x, y_, n in zip(xs, ys, ns):
                ax.annotate(str(n), (x, y_), textcoords="offset points", xytext=(4, 4), fontsize=7, color=color)
        ax.plot([0, 1], [0, 1], ":", color="grey")
        ax.set_title(f"{stratum} stratum")
        ax.set_xlabel("mean predicted probability (bin)")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
    axes[0].set_ylabel("observed accuracy")
    axes[0].legend(fontsize=8)
    fig.suptitle("Reliability, 10 equal-width bins, bin counts printed; sparse bins are noise, not curve")
    fig.tight_layout()
    fig.savefig(out / "reliability.png", dpi=130)


def risk_coverage_plot(dev_curve, test_curve, thresholds, out):
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    for label, pts, color in (("dev, out of fold (70 answered)", dev_curve, "C0"), ("test, single read (54 answered)", test_curve, "C3")):
        g = np.array([r["coverage"] for r in pts])
        c = np.array([r["risk"] for r in pts])
        lo = np.array([r["risk_lo"] for r in pts])
        hi = np.array([r["risk_hi"] for r in pts])
        ax.step(g, c, where="post", color=color, label=label)
        ax.fill_between(g, lo, hi, step="post", color=color, alpha=0.15)
        for thr, name in thresholds.items():
            near = min(pts, key=lambda r: abs(r["threshold"] - thr))
            ax.plot(near["coverage"], near["risk"], marker="s" if name == "escalate" else "^", color=color, markersize=7)
    ax.set_xlabel("coverage (share of answered items shown)")
    ax.set_ylabel("risk (error rate among shown)")
    ax.set_ylim(0, 1)
    ax.set_title("Risk against coverage, tie-aware thresholds, 95% bootstrap bands\nsquares: escalate threshold 0.35; triangles: answer threshold 0.58")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "risk-coverage.png", dpi=130)


def buckets_plot(dev_pb, test_pb, out):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    for ax, (label, pb) in zip(axes, (("dev (134)", dev_pb), ("test (100)", test_pb))):
        bottoms = np.zeros(len(BUCKETS))
        for o in OUTCOMES:
            vals = np.array([pb[b][o]["n"] for b in BUCKETS], dtype=float)
            corr = np.array([pb[b][o]["correct"] for b in BUCKETS], dtype=float)
            ax.bar(BUCKETS, vals, bottom=bottoms, color=COLORS[o], label=o)
            for i, (v, c) in enumerate(zip(vals, corr)):
                if v:
                    ax.text(i, bottoms[i] + v / 2, f"{int(v)} ({int(c)} ok)", ha="center", va="center", fontsize=7, color="white")
            bottoms += vals
        ax.set_title(label)
        ax.tick_params(axis="x", labelrotation=15)
    axes[0].set_ylabel("items")
    axes[1].legend(fontsize=8)
    fig.suptitle("Policy outcomes per bucket, counts with the correct count in each; ambiguous is indicative only")
    fig.tight_layout()
    fig.savefig(out / "buckets.png", dpi=130)


def baselines_plot(dev_b, test_b, out):
    names = ["verbalized alone", "agreement alone", "free signals alone", "confirmed minus_logprobs"]
    test_names = {"confirmed minus_logprobs": "confirmed minus_logprobs (frozen artifact)"}
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    for ax, stratum in zip(axes, ("pooled", "decisive")):
        x = np.arange(len(names))
        for shift, (label, src, keymap, color) in enumerate((("dev, out of fold", dev_b, {}, "C0"), ("test, single read", test_b, test_names, "C3"))):
            pts, err_lo, err_hi = [], [], []
            for n in names:
                r = src[keymap.get(n, n)][stratum]["auroc"]
                pts.append(r["point"])
                err_lo.append(r["point"] - r["lo"])
                err_hi.append(r["hi"] - r["point"])
            ax.errorbar(x + (shift - 0.5) * 0.25, pts, yerr=[err_lo, err_hi], fmt="o", color=color, capsize=3, label=label)
        ax.axhline(0.5, color="grey", linestyle=":")
        ax.set_xticks(x)
        ax.set_xticklabels([n.replace(" alone", "").replace("confirmed ", "") for n in names], rotation=15)
        ax.set_title(f"AUROC, {stratum}")
        ax.set_ylim(0.2, 1.0)
    axes[0].legend(fontsize=8)
    fig.suptitle("Baselines and the confirmed vector, AUROC with 95% bootstrap intervals")
    fig.tight_layout()
    fig.savefig(out / "baselines.png", dpi=130)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=str(ROOT / "docs" / "assets"))
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    m4 = load("m4-calibration.json")
    m5c = load("m5-risk-coverage.json")
    m5p = load("m5-policy.json")
    m8 = load("m8-test-results.json")
    devb = load("m8-dev-baselines.json")
    dev_rel = m4["results"]["minus_logprobs"]["fits"]["logistic+isotonic"]["reliability"]
    test_rel = {s: m8["metrics"][s]["reliability"] for s in ("pooled", "decisive")}
    reliability_plot(dev_rel, test_rel, out)
    risk_coverage_plot(m5c["curves"]["answered"], m8["policy"]["risk_coverage"], {0.35: "escalate", 0.58: "answer"}, out)
    buckets_plot(m5p["per_bucket"], m8["policy"]["outcomes_per_bucket"], out)
    baselines_plot(devb, m8["baselines"], out)
    print("wrote", ", ".join(p.name for p in sorted(out.glob("*.png"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
