"""Fit and evaluate the calibrator on dev: three variants, two fits, three strata, bootstrap intervals.

Usage:
    python scripts/fit_calibrator.py [--features reports/features-dev.jsonl] [--out reports/m4-calibration]

Everything is out of fold: stratified 5-fold CV with seed 42, each fold
scored by a model fitted on the other four. Fits: logistic regression on
standardised features (L2, C=1), and the same score passed through
isotonic regression fitted inside the training folds. Variants: full,
minus_actions, minus_logprobs. Strata: pooled, answerable, decisive
(answerable with evidence retrieved; the strata are read from the rows'
strata block, never from the features). Metrics: ECE, Brier, AUROC, AURC,
each with a 1000-resample bootstrap interval; reliability tables; a
bucket-detector test. Writes <out>.md, <out>-oof.jsonl (out-of-fold
probabilities per item and variant) and a calibrator artifact per variant
fitted on all of dev, with seed and library versions. Refuses test.
"""

import argparse
import json
import platform
import sys
from collections import Counter
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from calibration.features import ACTION_FEATURES, LOGPROB_FEATURES, PROVENANCE, admissible_features, dropped_constant, load_rows, matrix, variant_features  # noqa: E402
from calibration.metrics import auroc, aurc, bootstrap, brier, ece, reliability, risk_coverage  # noqa: E402

SEED = 42
FOLDS = 5
VARIANTS = ("full", "minus_actions", "minus_logprobs")
BUCKETS = ("answerable", "ambiguous", "unanswerable", "false_premise")


def logistic():
    return make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=2000, random_state=SEED))


def oof_scores(X, y, folds) -> tuple[np.ndarray, np.ndarray]:
    """Out-of-fold probabilities for the logistic fit and for logistic plus isotonic (isotonic fitted on inner OOF scores)."""
    p_log = np.zeros(len(y))
    p_iso = np.zeros(len(y))
    for train, test in folds:
        model = logistic().fit(X[train], y[train])
        p_log[test] = model.predict_proba(X[test])[:, 1]
        # isotonic on the training part's own out-of-fold scores, so it never sees the test fold
        inner = StratifiedKFold(n_splits=FOLDS, shuffle=True, random_state=SEED)
        inner_scores = np.zeros(len(train))
        for itr, ite in inner.split(X[train], y[train]):
            m = logistic().fit(X[train][itr], y[train][itr])
            inner_scores[ite] = m.predict_proba(X[train][ite])[:, 1]
        iso = IsotonicRegression(out_of_bounds="clip").fit(inner_scores, y[train])
        p_iso[test] = iso.predict(p_log[test])
    return p_log, p_iso


def metric_block(p, y) -> dict:
    return {"ece": bootstrap(ece, p, y), "brier": bootstrap(brier, p, y), "auroc": bootstrap(auroc, p, y), "aurc": bootstrap(aurc, p, y)}


def fmt(b: dict) -> str:
    return f"{b['point']:.3f} [{b['lo']:.3f}, {b['hi']:.3f}]"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--features", default=str(ROOT / "reports" / "features-dev.jsonl"))
    parser.add_argument("--out", default=str(ROOT / "reports" / "m4-calibration"))
    parser.add_argument("--artifacts", default=str(ROOT / "data" / "calibrators"))
    args = parser.parse_args()
    rows = load_rows(args.features)
    names_all = admissible_features(rows)
    y_all = np.array([int(r["label"]) for r in rows])
    strata = {
        "pooled": np.ones(len(rows), dtype=bool),
        "answerable": np.array([r["strata"]["bucket"] == "answerable" for r in rows]),
        "decisive": np.array([r["strata"]["bucket"] == "answerable" and bool(r["strata"]["evidence_retrieved"]) for r in rows]),
    }
    folds = list(StratifiedKFold(n_splits=FOLDS, shuffle=True, random_state=SEED).split(np.zeros(len(y_all)), y_all))

    results = {}
    oof = {r["item_id"]: {"label": int(r["label"]), "strata": r["strata"]} for r in rows}
    for variant in VARIANTS:
        names = variant_features(names_all, variant)
        X, y = matrix(rows, names)
        p_log, p_iso = oof_scores(X, y, folds)
        results[variant] = {"features": names, "fits": {}}
        for fit, p in (("logistic", p_log), ("logistic+isotonic", p_iso)):
            results[variant]["fits"][fit] = {s: metric_block(p[m], y[m]) for s, m in strata.items()}
            results[variant]["fits"][fit]["reliability"] = {s: reliability(p[m], y[m]) for s, m in strata.items()}
            results[variant]["fits"][fit]["risk_coverage_pooled"] = risk_coverage(p, y)[::max(1, len(y) // 10)]
            for r, pl, pi in zip(rows, p_log, p_iso):
                oof[r["item_id"]].setdefault(variant, {})["logistic"] = round(float(pl), 4)
                oof[r["item_id"]][variant]["logistic+isotonic"] = round(float(pi), 4)
        # the base rate as the floor every fit must beat
        base = np.full(len(y), y.mean())
        results[variant]["base_rate"] = {s: metric_block(base[m], y[m]) for s, m in strata.items()}
        # coefficients of the full-dev fit, and the artifact
        model = logistic().fit(X, y)
        coef = model.named_steps["logisticregression"].coef_[0]
        results[variant]["coefficients"] = sorted(((n, round(float(c), 3)) for n, c in zip(names, coef)), key=lambda t: -abs(t[1]))
        Path(args.artifacts).mkdir(parents=True, exist_ok=True)
        joblib.dump({"variant": variant, "features": names, "model": model, "seed": SEED, "folds": FOLDS,
                     "versions": {"python": platform.python_version(), "scikit-learn": sklearn.__version__, "numpy": np.__version__},
                     "trained_on": str(Path(args.features).name), "n": int(len(y))}, Path(args.artifacts) / f"{variant}.joblib")

    # bucket-detector test: can the bucket be predicted from the full vector?
    X, _ = matrix(rows, names_all)
    buckets = np.array([r["strata"]["bucket"] for r in rows])
    prior = Counter(buckets).most_common(1)[0][1] / len(buckets)
    pred = np.empty(len(buckets), dtype=object)
    for train, test in folds:
        clf = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=2000, random_state=SEED)).fit(X[train], buckets[train])
        pred[test] = clf.predict(X[test])
    detector = {"accuracy": round(float((pred == buckets).mean()), 3), "prior": round(float(prior), 3),
                "per_bucket_recall": {b: round(float((pred[buckets == b] == b).mean()), 3) for b in BUCKETS},
                "confusion": {b: dict(Counter(pred[buckets == b])) for b in BUCKETS}}
    acc_boot = []
    rng = np.random.default_rng(SEED)
    for _ in range(1000):
        idx = rng.integers(0, len(buckets), len(buckets))
        acc_boot.append(float((pred[idx] == buckets[idx]).mean()))
    detector["accuracy_interval"] = [round(float(np.percentile(acc_boot, 2.5)), 3), round(float(np.percentile(acc_boot, 97.5)), 3)]

    out = Path(args.out)
    with out.with_name(out.name + "-oof.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for item_id, rec in oof.items():
            f.write(json.dumps({"item_id": item_id, **rec}) + "\n")
    out.with_suffix(".json").write_text(json.dumps({"results": results, "bucket_detector": detector, "dropped_constant": dropped_constant(rows),
                                                    "seed": SEED, "folds": FOLDS, "n": len(rows)}, indent=1) + "\n", encoding="utf-8", newline="\n")

    n_dec = int(strata["decisive"].sum())
    lines = ["# M4 calibration on dev", "",
             f"{len(rows)} dev items, stratified {FOLDS}-fold cross-validation with seed {SEED}; every number is out of fold. "
             f"Intervals are 95 percent bootstrap over items, 1000 resamples. Strata: pooled ({len(rows)}), answerable "
             f"({int(strata['answerable'].sum())}), decisive ({n_dec}: answerable with the evidence chunk retrieved, "
             f"{int(y_all[strata['decisive']].sum())} right against {n_dec - int(y_all[strata['decisive']].sum())} wrong). "
             "The decisive stratum is the real test: retrieval is held fixed there and the model's judgement decides the outcome. "
             "With dev this size the conclusions are directional, not precise. The test split was not read.",
             "", "## Leakage list", "",
             "Features admitted, all computed from the run (trace and retrieved chunk texts), each computable at inference time on a question "
             "with no known answer. Ground truth kept out: bucket, evidence retrieved and rank, calculator flags, gold answer, expected action. "
             f"Constant on dev and dropped: {', '.join(dropped_constant(rows)) or 'none'}.", ""]
    for n in names_all:
        tags = []
        if n in ACTION_FEATURES:
            tags.append("action")
        if n in LOGPROB_FEATURES:
            tags.append("logprob")
        lines.append(f"- {n}{' [' + ', '.join(tags) + ']' if tags else ''}: {PROVENANCE[n]}")
    lines += ["", "## Results, out of fold", "", "Lower is better for ECE, Brier and AURC; higher for AUROC. The base rate row is a constant prediction at the dev label rate.", ""]
    for variant in VARIANTS:
        res = results[variant]
        lines += [f"### {variant} ({len(res['features'])} features)", "", "| fit | stratum | ECE | Brier | AUROC | AURC |", "|---|---|---|---|---|---|"]
        for s in strata:
            b = res["base_rate"][s]
            lines.append(f"| base rate | {s} | {fmt(b['ece'])} | {fmt(b['brier'])} | {fmt(b['auroc'])} | {fmt(b['aurc'])} |")
        for fit in ("logistic", "logistic+isotonic"):
            for s in strata:
                m = res["fits"][fit][s]
                lines.append(f"| {fit} | {s} | {fmt(m['ece'])} | {fmt(m['brier'])} | {fmt(m['auroc'])} | {fmt(m['aurc'])} |")
        lines += ["", "Largest coefficients of the full-dev logistic fit (standardised features): " + ", ".join(f"{n} {c:+.2f}" for n, c in res["coefficients"][:8]) + ".", ""]
    lines += ["## Reliability, logistic+isotonic, full variant", ""]
    for s in strata:
        lines += [f"{s}:", "", "| bin | n | mean confidence | accuracy |", "|---|---|---|---|"]
        for b in results["full"]["fits"]["logistic+isotonic"]["reliability"][s]:
            lines.append(f"| {b['lo']:.1f} to {b['hi']:.1f} | {b['n']} | {b['confidence'] if b['confidence'] is not None else ''} | {b['accuracy'] if b['accuracy'] is not None else ''} |")
        lines.append("")
    lines += ["## Bucket-detector test", "",
              f"A multinomial logistic fit from the full feature vector to the bucket, out of fold: accuracy {detector['accuracy']} "
              f"[{detector['accuracy_interval'][0]}, {detector['accuracy_interval'][1]}] against a majority-bucket prior of {detector['prior']}. "
              "Per-bucket recall: " + ", ".join(f"{b} {v}" for b, v in detector["per_bucket_recall"].items()) + ".",
              "", "If the features predict the bucket well and the pooled calibration numbers do not survive inside the decisive stratum, the calibrator is a bucket detector.", ""]
    out.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
