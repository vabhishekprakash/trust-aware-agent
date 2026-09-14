# Trust-aware agent: report (draft, dev results only)

This is the standing draft of the final report. Sections fill in as the
milestones complete; the test split is read once, at M8, and its numbers
replace nothing here, they are added next to the dev numbers. Every
headline number carries its 95 percent bootstrap interval. The reader
should assume every claim is directional at this data size.

## Abstract

A retrieval question-answering agent over the NASA Systems Engineering
Handbook, built on a 3B local model, outputs a calibrated probability that
its answer is correct and chooses among answering, asking which reading is
meant, and abstaining. On 134 development items the out-of-fold
probability separates right from wrong answers with an AUROC of 0.70
[0.61, 0.79] pooled and 0.63 [0.45, 0.80] inside the decisive stratum.
That stratum is the answerable questions whose evidence was retrieved,
where bucket and retrieval are held fixed and the model's judgement
decides. The confidence carries real but weak information beyond the action taken and
the question's bucket. The free signals computed from the agent's own
trace outperform three paid signals that roughly triple the cost per
question. A premise-check step built to move the false-premise bucket off
zero made every bucket worse and is reported as a negative result.

## Results summary (dev, out of fold, 5-fold, seed 42)

Calibrator: logistic regression plus isotonic on 39 features (the vector
without log-probabilities, see the integrity section), confirmed by the
owner on 2026-09-12. Base rate: 70 of 134 correct.

| stratum | n | AUROC | ECE | Brier | AURC (base rate) |
|---|---|---|---|---|---|
| pooled | 134 | 0.70 [0.61, 0.79] | 0.10 [0.07, 0.19] | 0.22 [0.19, 0.25] | 0.31 [0.23, 0.42] (0.40) |
| answerable | 62 | 0.62 [0.47, 0.76] | 0.13 [0.08, 0.26] | 0.24 [0.20, 0.29] | 0.31 [0.18, 0.47] (0.38) |
| decisive | 50 | 0.63 [0.45, 0.80] | 0.18 [0.12, 0.31] | 0.22 [0.18, 0.26] | 0.24 [0.11, 0.42] (0.33) |

The action features, removed as a planned variant, change nothing:
pooled AUROC 0.73 [0.64, 0.81] without them against 0.73 [0.64, 0.82]
for the full vector. The calibrator is not an action detector. The same
features predict the bucket at 0.59 [0.50, 0.67] against a prior of
0.46, so it is partly a bucket detector. But the discrimination survives
inside the decisive stratum, where bucket and retrieval are fixed.
Per-bucket action and label tables are in reports/dev-distribution.md;
the ambiguous bucket (9 items) is indicative only.

## Named finding: the free signals beat the paid ones

The usual expectation is that sampling-based uncertainty leads. Here it
did not. In the decisive stratum the widest gap by label is lexical
support, the share of the answer's words found in the best retrieved
chunk. It is 0.73 for correct answers against 0.49 for wrong ones, and it
is computed from the trace at no cost. Verbalized confidence saturated at 100 on
every correct item and averaged 83 on wrong ones, a round-number habit
rather than a scale. Sampling agreement with the graded draft separated
(maximum Jaccard 0.85 against 0.70), agreement among the samples alone
did not (0.53 against 0.54), and the log-probability summaries were flat
where they described the graded text. The three paid signals cost 12 to
15 s, 8 s and 23 s per item on top of an 18 s answer. Read as a design
result: on a small model over a niche corpus, whether the answer's words
are in the passage tells you more than asking the model how sure it is.

## Measurement integrity: three features that looked predictive and were artefacts

The grader, the item pool and the feature vector each produced one
episode where a number improved for a reason that had nothing to do with
what it claimed to measure. They are reported together because the
pattern is the same and a reader should expect more of it.

1. The v9 judge question. Adding a fourth yes-or-no question to the judge
   ("does the draft assert anything unsupported?") produced YES on true
   statements and flipped three binary labels on the 21 worked examples.
   The question was removed and the support check moved into code that
   reads the corpus. Rule since then: no judge prompt changes without
   rerunning the examples.
2. The pool snapshot. A rerun of grader v13 on the first blind sheet
   showed 39 of 39 against 38 of 39 for v12. The one changed row was
   sheet 19, whose item sits as answerable in the pool snapshot and as
   ambiguous in the pool the v12 rerun used; the new rule never touched
   it. Rule since then: a rubric-fidelity rerun grades against the exact
   pool the sheet was drawn from, by a script that takes the snapshot as
   an argument and regenerates nothing.
3. The lp_tokens feature. The full feature vector beat the vector without
   log-probabilities by 0.04 AUROC pooled and 0.10 in the decisive
   stratum. A post-hoc diagnostic, labelled as such, showed the entire
   gain was lp_tokens, the token count of a draft regenerated with
   log-probabilities on. That text differs from the graded draft on 40
   percent of the stratum. Adding that one feature back restored the full
   result; the five probability summaries alone added nothing, and on the
   matched subset their means by label were flat. The coefficient paired
   with a negative one on the response's own length: a length difference
   between two generations, not a confidence signal, and one that would
   not transfer. The log-probability features were dropped and the cost
   is stated above.

## Limitations

The standing limitations are in docs/annotation-guide.md. In short:

- Items were drafted and verified by language model agents and graded by
  a language model judge. Human checks: two blind samples, 82 percent
  under v7 on sheet 1 and 80 percent under v10 on sheet 2. Later figures
  are rubric fidelity, not blind.
- The retrieval confounder: answerable items were correct 27 of 38 times
  with the evidence retrieved and 2 of 8 without.
- The false-premise bucket is at 0 of 29 with the premise step switched
  off (reports/premise-step.md).
- The ambiguous bucket has 9 dev items; its numbers are indicative only.
- Sensitivity alternatives carried to M8: the owner's earlier WRONG and
  CORRECT readings of a bare false-premise abstention, and the lenient
  three-way grade.

## Still to come

M5 policy thresholds on dev; M6 explanations; M7 API and dashboard; M8 the
test split read once, the final blind grader check of about 20 real agent
outputs (the signed-off grader number), baselines, plots.
