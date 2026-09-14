# M8 preregistration: the analysis frozen before the test split is read

Written and committed before any test file is opened. Nothing below is
decided after the read except how to describe what came back. The test
split is data/eval/test.jsonl, SHA-256
3c344521a08865da402a50558c8fbb8eab1b5b0098799b1ba93e84db1f18ad1c, 100
items: 46 answerable, 9 ambiguous, 25 unanswerable, 20 false premise
(reports/split-summary.md, counts recorded at the split, no test item
read). Ambiguous with 9 items is indicative only, as everywhere in this
project.

## The frozen system

- Agent: src/agent/loop.py at commit 85db315, premise check off, k=8, no
  neighbours, seed 42, qwen2.5:3b-instruct on Ollama 0.24, the same
  prompts byte for byte as the dev runs (the cache confirms it).
- Grader: grader-v13, src/calibration/grader.py SHA-256
  a2eb938e82b0b63fa8a00c834e0569924e80b0a966ac1663b2ed9ca4986ad485,
  judge llama3.1:latest, drafts graded exactly as dev was: the response
  with the agent's action as the form hint (scripts/grade_run.py).
- Features: the 39-feature minus_logprobs vector, computed by
  scripts/build_features.py from the trace and the retrieved chunk texts
  only, with the paid signals from scripts/paid_signals.py (verbalized
  confidence with the passages in view; five samples at temperature 0.7,
  seeds 1 to 5). No log-probability call is made on test.
- Calibrator: data/calibrators/minus_logprobs.joblib, SHA-256
  58f3f3d1cba468861b8b5094dae334b270c7fbbdff946fac1a801ad3e1d90116, the
  logistic pipeline fitted on all 134 dev items with the isotonic step
  fitted on their out-of-fold logistic scores. This is the artifact the
  dashboard serves. Test probabilities come from it, uncapped for the
  metrics; the display cap (0.667) applies only to what the page shows.
- Policy: data/calibrators/policy.json, SHA-256
  767fea22e942067807041787901d05347959d921a32c66365fc496b2e3bc3821:
  ANSWER at or above 0.58, ESCALATE below 0.35, VERIFY between. The
  agent's CLARIFY and ABSTAIN pass through.

## The one script

scripts/evaluate_test.py reads test.jsonl exactly once. It runs the
agent, grades, builds the features, scores with the frozen artifact,
applies the frozen policy, fits the two baselines on dev features and
applies them to test, computes every metric below, and writes
reports/m8-test-results.md and .json plus one row per item to
reports/m8-test-rows.jsonl. Those files are committed verbatim. The
script refuses to run a second time once its marker file exists. The
final blind grader check on dev outputs happens before this script runs.

## Metrics, exact definitions, all with intervals

Bootstrap: 1000 resamples of items with replacement, seed 42, 2.5th and
97.5th percentiles, reported as point [lo, hi]. Label: 1 when the grade
is CORRECT, 0 for PARTIAL or WRONG.

- AUROC: rank-based area under the ROC curve of the probability against
  the label, ties averaged (src/calibration/metrics.py auroc).
- Brier: mean squared difference between probability and label.
- ECE: expected calibration error with 10 equal-width bins on [0, 1],
  weighted by bin count (metrics.py ece).
- AURC: area under the risk-coverage curve when items are covered in
  order of decreasing probability, computed as the mean risk over
  coverage steps of one item (metrics.py aurc). Ranking only; ties in
  the isotonic output are broken by index, and the tie-aware view is
  given by the risk-coverage table below.
- Risk-coverage: at every distinct probability used as a threshold, the
  share of items with probability at or above it (coverage) and the error
  rate among them (risk), ties covered together (scripts/policy_curve.py
  step_curve). Reported for the answered population.
- Accuracy at coverage: on the answered population, accuracy among the
  shown items at the tie-aware thresholds nearest 25, 50, 75 and 100
  percent coverage.
- Policy risk and coverage at the frozen thresholds: on the answered
  population, coverage is the share shown (ANSWER or VERIFY), risk the
  error rate among them; also the ANSWER band alone. The deployed
  columns (all items, pass-through counted as shown) carry the standing
  caveat about pass-through abstentions and PARTIAL false-premise
  abstentions.
- Escalation precision and recall: on the answered population, with
  "should be withheld" defined as label 0. Escalate-only: precision is
  the share of ESCALATE items with label 0, recall the share of label-0
  items that were ESCALATE. Flagged (ESCALATE or VERIFY): the same with
  both outcomes counted as withheld or flagged.
- Per-bucket tables: counts next to rates for actions, outcomes and
  grades, as on dev.
- Confounder: accuracy split by whether the evidence chunk was retrieved
  (the recall script's definition), per bucket.

## Strata

- Pooled: all 100 test items.
- Within answerable: the 46 answerable items.
- Decisive: answerable items whose evidence chunk was retrieved at k=8.
  On dev this was 50 of 62 (81 percent); expected on test about 37 of 46.
  The count is reported as found.

Metrics on a stratum are computed on the test probabilities restricted
to it; nothing is refitted per stratum.

## Baselines, exact feature sets

Each baseline is a logistic regression on standardised features plus the
isotonic step, fitted on the 134 dev items with the same 5-fold procedure
for its isotonic (scripts/fit_calibrator.py oof_scores), then applied to
test. Feature sets:

1. Verbalized alone: vc_confidence, vc_parsed, vc_round.
2. Agreement alone: sa_mean_pairwise, sa_min_pairwise, sa_mean_to_draft,
   sa_min_to_draft, sa_max_to_draft, sa_abstain_share, sa_form_agree
   (sa_samples is constant and dropped).
3. The confirmed minus_logprobs vector, 39 features, the frozen artifact
   above.

A fourth reference row, not a baseline: the free signals alone (process
and retrieval-support features, 29), fitted the same way, because the
dev finding that they beat the paid signals is a claim the test read
should be able to confirm or deny.

## Headline and secondary

Headline: for the confirmed vector, AUROC pooled and in the decisive
stratum with intervals, and the policy's risk at the frozen thresholds
against the base rate on the answered population, with intervals.

Secondary: ECE, Brier, AURC, the baselines and the free-signals row, the
risk-coverage table, accuracy at coverage, escalation precision and
recall, per-bucket tables, the confounder split, the final blind grader
check number.

## Expectations, written now

Dev, out of fold, for the confirmed vector with logistic plus isotonic:
AUROC 0.70 [0.61, 0.79] pooled and 0.63 [0.45, 0.80] in the decisive
stratum; the plain logistic fit gave 0.69 and 0.66. (The 0.76 sometimes
quoted for the stratum belongs to the full vector, which was dropped
with its log-probability features; it is not the frozen system's
number.) Policy on the answered population: risk 49 [37, 60] percent
with everything shown, 41 [28, 55] percent at the frozen thresholds at
73 [61, 83] percent coverage.

- Consistent: test point estimates inside the dev intervals, pooled
  AUROC in [0.61, 0.79], decisive in [0.45, 0.80], policy risk at the
  frozen thresholds below the test base risk with overlapping intervals.
- Worse: a point estimate below the dev interval's lower bound, or the
  policy risk at or above the base risk. Reported as such; no refit.
- Suspiciously better: pooled AUROC above 0.85 or decisive above 0.90,
  or policy risk at the frozen thresholds under 25 percent at coverage
  above 60 percent. Such a result triggers a leakage audit of the test
  features before any claim is written: the feature rows are checked for
  ground-truth fields, the traces for item-record reads, and the cache
  for test questions answered before the read.

## Amendment, committed before the read: the response in each band

Decided now so the response is not chosen after seeing the number.

- Consistent: report it. No further analysis, no additional variants.
- Worse: report it as the result. The dev numbers stay in the report as
  dev numbers. No refitting, no new features, no second read.
- Suspiciously better: a leakage audit before any claim, specified here.
  (1) Re-verify the feature provenance list against the test traces: every
  feature name in the test rows is in the provenance lists and none is a
  ground-truth field; the script asserts this and the rows carry the list
  of item-record fields present in each trace, which the features never
  read. (2) Check that no item-record field entered the vector, by name
  and by value: the test feature matrix is recomputed from the traces and
  compared with the stored rows. (3) Near-duplicate questions across the
  dev and test splits, defined below. (4) Confirm the split script's seed
  (42) and stratification by bucket against reports/split-summary.md and
  data/eval/items_locked.jsonl.

Near-duplicate detection runs as part of the read regardless of band,
because both splits came from one drafting pipeline over one corpus and
two questions about the same passage in different splits is a plausible
leak that the seed and stratification would not catch. Definition: for
every test question, the most similar dev question by content-word
Jaccard (the grader's normalise, stopwords and stems) and by bge cosine
of the question texts. A pair is flagged when Jaccard is at least 0.6 or
cosine is at least 0.9, and also when the two items cite the same
evidence page and cosine is at least 0.8. Flagged pairs are listed with
both questions, and the headline metrics are also reported with the
flagged test items removed, labelled as such, whichever band the result
falls in.

## Markers: a crashed run and a completed run are different

The script appends a line to data/eval/TEST_READ_STARTED at every start
and writes data/eval/TEST_READ_ONCE only when it completes. It refuses to
run when TEST_READ_ONCE exists. A crashed run leaves a start line and no
completion marker; the restart replays every model call from the cache
and repeats no generation, and the attempt count is recorded in the
results. Both marker files are committed with the results.

## What happens after the read

Only the description of what came back. No threshold, feature set,
calibrator or grader change is made in response to test numbers. If the
grader's final blind check on dev outputs falls below the bar, that is
reported as a limitation on every test number, not fixed.
