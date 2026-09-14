"""Add the isotonic bend to a calibrator artifact, fitted on the dev out-of-fold logistic scores.

Usage:
    python scripts/finalize_calibrator.py [--variant minus_logprobs]

The artifact written by scripts/fit_calibrator.py holds the logistic
pipeline fitted on all of dev. The confirmed fit is logistic plus
isotonic, and the isotonic step must be fitted on scores the logistic
model did not train on, so it is fitted here on the out-of-fold logistic
probabilities from reports/m4-calibration-oof.jsonl and stored in the
same artifact under "isotonic". Refuses test.
"""

import argparse
import json
import sys
from pathlib import Path

import joblib  # artifacts are written by this project's own scripts into data/calibrators; nothing is loaded from outside the repository
import numpy as np
from sklearn.isotonic import IsotonicRegression

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--variant", default="minus_logprobs")
    parser.add_argument("--oof", default=str(ROOT / "reports" / "m4-calibration-oof.jsonl"))
    parser.add_argument("--artifacts", default=str(ROOT / "data" / "calibrators"))
    args = parser.parse_args()
    if "test" in Path(args.oof).name:
        print("refusing to read the test split")
        return 1
    rows = [json.loads(l) for l in Path(args.oof).read_text(encoding="utf-8").splitlines() if l.strip()]
    scores = np.array([r[args.variant]["logistic"] for r in rows])
    labels = np.array([r["label"] for r in rows])
    iso = IsotonicRegression(out_of_bounds="clip").fit(scores, labels)
    path = Path(args.artifacts) / f"{args.variant}.joblib"
    artifact = joblib.load(path)
    artifact["isotonic"] = iso
    artifact["isotonic_fitted_on"] = f"{len(rows)} out-of-fold logistic scores from {Path(args.oof).name}"
    joblib.dump(artifact, path)
    print(f"{path}: isotonic added, fitted on {len(rows)} out-of-fold scores; knots {len(iso.X_thresholds_)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
