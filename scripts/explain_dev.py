"""Write sample explanations for dev items, one per policy band, for the owner to read.

Usage:
    python scripts/explain_dev.py [--n 2] [--out reports/m6-explanations.md]

Takes the confirmed calibrator artifact (with its isotonic step), the dev
feature rows and the policy thresholds, scores every answered item, and
prints the plain-language breakdown for the first n items of each band
in item order, with the graded label so a reader can check the reasons
against the outcome. Also reports how far the artifact's full-dev
probabilities sit from the out-of-fold ones, since the explanation uses
the former and the metrics the latter. Refuses test.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from explain.contributions import Explainer, breakdown  # noqa: E402
from policy.router import decide, load_thresholds  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--features", default=str(ROOT / "reports" / "features-dev.jsonl"))
    parser.add_argument("--oof", default=str(ROOT / "reports" / "m4-calibration-oof.jsonl"))
    parser.add_argument("--rows", nargs="+", default=[str(ROOT / "reports" / "dev-run-v1b.jsonl"), str(ROOT / "reports" / "dev-run-reserve.jsonl")])
    parser.add_argument("--n", type=int, default=2)
    parser.add_argument("--out", default=str(ROOT / "reports" / "m6-explanations.md"))
    args = parser.parse_args()
    if any("test" in Path(p).name for p in [args.features, args.oof] + args.rows):
        print("refusing to read the test split")
        return 1
    explainer = Explainer.load()
    thresholds = load_thresholds()
    feats = [json.loads(l) for l in Path(args.features).read_text(encoding="utf-8").splitlines() if l.strip()]
    oof = {json.loads(l)["item_id"]: json.loads(l) for l in Path(args.oof).read_text(encoding="utf-8").splitlines() if l.strip()}
    responses = {}
    for path in args.rows:
        for l in Path(path).read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l)
                responses[r["item_id"]] = (r["question"], r["response"])

    diffs = []
    per_band = {"ANSWER": [], "VERIFY": [], "ESCALATE": []}
    for row in feats:
        f = row["features"]
        action = "ANSWER" if f["action_answer"] else ("ABSTAIN" if f["action_abstain"] else "CLARIFY")
        e = explainer.explain(f)
        diffs.append(e.probability - oof[row["item_id"]][explainer.variant]["logistic+isotonic"])
        if action != "ANSWER":
            continue
        outcome = decide(action, e.probability, thresholds)
        if len(per_band[outcome]) < args.n:
            q, resp = responses[row["item_id"]]
            per_band[outcome].append((row, e, outcome, q, resp))

    lines = ["# Sample explanations on dev", "",
             f"Calibrator {explainer.variant}, logistic plus isotonic, the artifact fitted on all of dev. The explanation uses that artifact; the metrics in the "
             f"report use out-of-fold scores. Across the {len(feats)} dev items the artifact's probability differs from the out-of-fold one by "
             f"{np.mean(np.abs(diffs)):.3f} on average (max {np.max(np.abs(diffs)):.3f}), as expected for a model that has now seen every item.", ""]
    for band in ("ANSWER", "VERIFY", "ESCALATE"):
        lines += [f"## {band} band", ""]
        for row, e, outcome, q, resp in per_band[band]:
            lines += [f"### {row['item_id']} ({row['strata']['bucket']}, graded {row['grade']})", "", f"Question: {q}", "", f"Answer: {resp}", "",
                      breakdown(e, outcome=outcome), ""]
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
