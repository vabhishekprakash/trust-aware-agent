"""Report the log-probability text mismatch before any fit.

Usage:
    python scripts/logprob_mismatch.py [--features reports/features-dev.jsonl] [--out reports/logprob-mismatch.md]

The log-probability draft is regenerated with logprobs on; when its text
differs from the graded draft, the logprob features describe a different
output than the label. This reports the mismatch rate pooled, per bucket
and in the decisive stratum, then feature means by label on the matched
subset alone, so the flat logprob result can be checked where the
sequence really does describe the graded text.
"""

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUCKETS = ("answerable", "ambiguous", "unanswerable", "false_premise")
LOGPROB = ("lp_mean", "lp_min", "lp_p10", "lp_share_below_1", "lp_first", "lp_tokens")
OTHERS = ("lexical_support_top1", "cosine_top1", "vc_confidence", "sa_max_to_draft", "sa_form_agree", "action_answer")


def pct(a, n):
    return f"{a}/{n} ({100 * a / n:.0f}%)" if n else "0/0"


def mean_sd(values):
    if not values:
        return "n=0"
    if len(values) == 1:
        return f"{values[0]:.3f}"
    return f"{statistics.mean(values):.3f} (sd {statistics.stdev(values):.3f}, n={len(values)})"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--features", default=str(ROOT / "reports" / "features-dev.jsonl"))
    parser.add_argument("--out", default=str(ROOT / "reports" / "logprob-mismatch.md"))
    args = parser.parse_args()
    if "test" in Path(args.features).name:
        print("refusing to read the test split")
        return 1
    rows = [json.loads(l) for l in Path(args.features).read_text(encoding="utf-8").splitlines() if l.strip()]
    matched = [r for r in rows if r["features"]["lp_same_text"] == 1]
    decisive = [r for r in rows if r["strata"]["bucket"] == "answerable" and r["strata"]["evidence_retrieved"]]
    dec_matched = [r for r in decisive if r["features"]["lp_same_text"] == 1]

    lines = ["# Log-probability text mismatch, before any fit", "",
             "The draft was regenerated at temperature 0 with logprobs on. When its text differs from the graded draft, the "
             "logprob features describe a different output than the label does.", "",
             "## Mismatch rate", "",
             f"- Pooled: {pct(len(rows) - len(matched), len(rows))} of items mismatched.",
             f"- Decisive stratum (answerable, evidence retrieved): {pct(len(decisive) - len(dec_matched), len(decisive))} mismatched; "
             f"matched subset there is {sum(r['label'] for r in dec_matched)} right against {len(dec_matched) - sum(r['label'] for r in dec_matched)} wrong.",
             "- Per bucket: " + ", ".join(f"{b} {pct(sum(1 for r in rows if r['strata']['bucket'] == b and r['features']['lp_same_text'] == 0), sum(1 for r in rows if r['strata']['bucket'] == b))}" for b in BUCKETS) + ".",
             "", "## Feature means by label on the matched subset alone", "",
             "Pooled matched subset, then the matched part of the decisive stratum. Log-probability features first, then a few others for scale.", "",
             "| feature | matched, label 1 | matched, label 0 | decisive matched, label 1 | decisive matched, label 0 |", "|---|---|---|---|---|"]
    for name in LOGPROB + OTHERS:
        cols = []
        for subset in (matched, dec_matched):
            by = defaultdict(list)
            for r in subset:
                by[r["label"]].append(float(r["features"][name]))
            cols += [mean_sd(by[1]), mean_sd(by[0])]
        lines.append(f"| {name} | " + " | ".join(cols) + " |")
    lines += ["", "## For comparison, all items, decisive stratum", "", "| feature | label 1 | label 0 |", "|---|---|---|"]
    for name in LOGPROB:
        by = defaultdict(list)
        for r in decisive:
            by[r["label"]].append(float(r["features"][name]))
        lines.append(f"| {name} | {mean_sd(by[1])} | {mean_sd(by[0])} |")
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
