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
The decision policy above the score escalates about a quarter of answered
items as a coverage choice, not a risk guarantee: the error rate among
shown answers on dev moves from 49 [37, 60] to 41 [28, 55] percent, an
interval that does not exclude no effect. Whether the policy reduces error
is settled by the single read of the test split.

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
- Policy, 70 answered dev items: error among shown answers 49 [37, 60]
  percent with everything shown, 41 [28, 55] percent at the chosen
  threshold (coverage 73 [61, 83] percent). Direction as expected,
  interval includes no effect. A 20 percent risk target would show 6 of
  70.

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

## Measurement integrity: four numbers that looked better than they were

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
4. The halving figure. An earlier reading of the M4 results said that
   answering the most confident half of the decisive stratum roughly
   halved the error rate. That came from a rank-ordered risk-coverage
   curve. The isotonic probabilities carry many ties, and a rank order
   splits a tie at a point no real threshold can reach. The tie-aware
   curve gives 49 [37, 60] to about 40 [26, 57] percent at half coverage
   among answered items. The earlier figure was wrong and is recorded
   here rather than deleted; the authors found it themselves, and the
   rule since then is that every point on a risk-coverage curve must be a
   threshold someone could set.

## The grader's three blind figures

The correctness labels come from a language-model judge inside a staged
grader. Its agreement with the owner was checked blind three times, each
on drafts or outputs the owner graded without seeing the judge's key:

| check | drafts | grader | binary agreement |
|---|---|---|---|
| sheet 1, model drafts under three passage conditions | 39 graded of 40 | v7 | 32 of 39 (82 percent) |
| sheet 2, fresh model drafts | 25 | v10 | 20 of 25 (80 percent) |
| final check, real agent outputs from dev | 20 | v13, the grader that graded dev and test | 19 of 20 (95 percent) |

The final check is the signed-off figure: the same grader version that
produced every label in this report, on the agent's own outputs, 10
answerable, 1 ambiguous, 5 unanswerable, 4 false premise, three-way
agreement 18 of 20. The one binary disagreement is a false-premise output
that states the handbook's correction and then abstains; the owner graded
it CORRECT and the judge WRONG while its own reason called the
interpretation correct. On that item the owner is right and the grader
is not, and the grader was not changed after the check. The later
rubric-fidelity reruns of sheets 1 and 2 (38 of 39 and 24 of 25) are not
blind figures and are reported as such in the annotation guide. Twenty
items give a wide interval on 95 percent; it is a check, not a
certificate.

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

Every metric in this report describes the out-of-fold calibrator: each
dev item scored by a model fitted on the other four fifths. The shipped
artifact is refit on all 134 dev items. Its probabilities differ from the
measured ones by 0.094 on average and up to 0.415, and its own
calibration is unmeasured. The displayed probability is capped at the
isotonic step below the top one, so nothing shows as certain; the cap is
a presentation guard, not a fix, and the page says so.

The explanation layer reports single-feature contributions as the fit
gives them. The correlated retrieval-score features receive opposite
signs from the fit, so individual coefficients are not interpretable as
effects, which is a known consequence of correlated inputs in a linear
model. The breakdown therefore leads with the sums by signal family, the
steadier quantity, and states the caveat every time.

## Decision policy

VERIFY is a flag, not a verification loop. The problem statement's
tool-based verification is not implemented, for two reasons. Retrieval
recall on dev is 77 percent at k=8 and the same at k=10, so re-retrieving
buys little, and a second draft from the same model mostly repeats the
first. The premise step is the precedent: a second model pass built to
fix a measured gap made every bucket worse (reports/premise-step.md).
The agent's own CLARIFY and ABSTAIN stand; the policy gates only the
items the agent answered.

The thresholds are a coverage choice, not a risk guarantee. On the
out-of-fold probabilities no error target of 10, 15, 20 or 25 percent
among answered items was reachable with meaningful coverage: the risk
stays near 40 percent from 20 to 80 percent coverage. The owner chose to
escalate about the bottom quarter of answered items and flag the middle
tertile: ANSWER at or above 0.58, VERIFY from 0.35 to 0.58, ESCALATE
below 0.35 (reports/m5-policy.md).

On the 70 answered dev items, 36 correct, the error rate among shown
answers is 49 [37, 60] percent when everything is shown. At the chosen
threshold it is 41 [28, 55] percent, at 73 [61, 83] percent coverage. The
point estimate moves in the expected direction and the interval does not
exclude no effect. No claim that the policy reduces error is made on
dev; the single read of the test split at M8 is where that is settled.
The alternative is in the same table. A 20 percent risk target needs a
threshold of 0.846 and shows 6 of 70 answered items: 9 [3, 16] percent
coverage at 17 [0, 55] percent risk. That is what a risk guarantee would
cost here.

Outcomes per bucket, counts with rates and the correct count in each
(ambiguous is indicative only):

| bucket | n | ANSWER | VERIFY | ESCALATE | pass-through ABSTAIN, CLARIFY |
|---|---|---|---|---|---|
| answerable | 62 | 16 (26%), 12 correct | 20 (32%), 18 correct | 8 (13%), 5 correct | 12 and 6, 1 correct |
| ambiguous | 9 | 1, 0 correct | 4, 0 correct | 3, 1 correct | 0 and 1, 1 correct |
| unanswerable | 34 | 0 | 0 | 0 | 33 and 1, 32 correct |
| false premise | 29 | 5 (17%), 0 correct | 5 (17%), 0 correct | 8 (28%), 0 correct | 11 and 0, 0 correct |

The bands do not order as a reliable calibrator's would. Accuracy per
band, with bootstrap intervals over the band's items:

| population | ANSWER band | VERIFY band | ESCALATE band |
|---|---|---|---|
| answerable items the agent answered | 12/16 (75% [50, 94]) | 18/20 (90% [75, 100]) | 5/8 (62% [25, 88]) |
| all answered items | 12/22 (55% [32, 77]) | 18/29 (62% [45, 79]) | 6/19 (32% [11, 53]) |

At this sample size the calibrator's ordering is not reliable enough for
the top band to outperform the middle one. That is one finding seen
three ways, not three findings: the band accuracies here, the AUROC of
0.69 [0.59, 0.78], and the flat risk-coverage curve. The intervals cover
the reversal, and the report does not treat it as a separate effect.

The deployed columns, wherever they appear, carry this caveat. Deployed
coverage, 86 [80, 92] percent at the chosen threshold, is flattered by 34
pass-through abstentions on unanswerable items that the policy never
touches, 32 of them correct. Deployed risk, 44 [35, 54] percent, is
punished by 11 false-premise bare abstentions graded PARTIAL and counted
as errors. The answered-population figures are the policy's real work.

## Still to come

M5 policy thresholds on dev; M6 explanations; M7 API and dashboard; M8 the
test split read once, the final blind grader check of about 20 real agent
outputs (the signed-off grader number), baselines, plots.
