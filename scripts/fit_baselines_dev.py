"""Dev out-of-fold numbers for the preregistered baselines, so dev and test sit side by side.

Usage:
    python scripts/fit_baselines_dev.py [--out reports/m8-dev-baselines.json]

Descriptive only, computed after the test read for the report's side-by-side
tables; the baselines themselves were preregistered and their test numbers
are in reports/m8-test-results.json. Same folds, same fit (logistic plus
nested isotonic), same strata as the M4 fit. Refuses test.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.model_selection import StratifiedKFold

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from calibration.features import admissible_features, load_rows, matrix  # noqa: E402
from calibration.metrics import auroc, bootstrap, brier  # noqa: E402
from fit_calibrator import FOLDS, SEED, oof_scores  # noqa: E402
from signals.process import PROVENANCE as PP  # noqa: E402
from signals.retrieval_support import PROVENANCE as SP  # noqa: E402

SETS = {
    "verbalized alone": ["vc_confidence", "vc_parsed", "vc_round"],
    "agreement alone": ["sa_mean_pairwise", "sa_min_pairwise", "sa_mean_to_draft", "sa_min_to_draft", "sa_max_to_draft", "sa_abstain_share", "sa_form_agree"],
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--features", default=str(ROOT / "reports" / "features-dev.jsonl"))
    parser.add_argument("--out", default=str(ROOT / "reports" / "m8-dev-baselines.json"))
    args = parser.parse_args()
    rows = load_rows(args.features)
    names = admissible_features(rows)
    y = np.array([r["label"] for r in rows])
    strata = {"pooled": np.ones(len(rows), bool), "answerable": np.array([r["strata"]["bucket"] == "answerable" for r in rows]),
              "decisive": np.array([r["strata"]["bucket"] == "answerable" and bool(r["strata"]["evidence_retrieved"]) for r in rows])}
    folds = list(StratifiedKFold(n_splits=FOLDS, shuffle=True, random_state=SEED).split(np.zeros(len(y)), y))
    sets = dict(SETS)
    sets["free signals alone"] = [n for n in names if n in PP or n in SP]
    m4 = json.load(open(ROOT / "reports" / "m4-calibration.json", encoding="utf-8"))
    out = {}
    for label, feats in sets.items():
        feats = [f for f in feats if f in names]
        X, _ = matrix(rows, feats)
        _, p_iso = oof_scores(X, y, folds)
        out[label] = {s: {"auroc": bootstrap(auroc, p_iso[m], y[m]), "brier": bootstrap(brier, p_iso[m], y[m])} for s, m in strata.items()}
        out[label]["n_features"] = len(feats)
    conf = m4["results"]["minus_logprobs"]["fits"]["logistic+isotonic"]
    out["confirmed minus_logprobs"] = {s: {"auroc": conf[s]["auroc"], "brier": conf[s]["brier"]} for s in strata}
    out["confirmed minus_logprobs"]["n_features"] = len(m4["results"]["minus_logprobs"]["features"])
    Path(args.out).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    for label, r in out.items():
        print(f"{label:<28} pooled {r['pooled']['auroc']['point']:.3f} [{r['pooled']['auroc']['lo']:.3f}, {r['pooled']['auroc']['hi']:.3f}]  "
              f"decisive {r['decisive']['auroc']['point']:.3f} [{r['decisive']['auroc']['lo']:.3f}, {r['decisive']['auroc']['hi']:.3f}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
