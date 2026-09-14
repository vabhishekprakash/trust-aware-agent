# Reading the M4 calibration results

The numbers are in reports/m4-calibration.md (generated, every figure out
of fold with a 95 percent bootstrap interval). This note says what they
mean and records the one post-hoc diagnostic that was run, labelled as
such. Dev has 134 items; the decisive stratum has 50. The conclusions are
directional, as planned.

## Does the calibrator discriminate?

Yes, weakly. The full vector with a logistic fit reaches an out-of-fold
AUROC of 0.73 [0.64, 0.82] pooled and 0.76 [0.62, 0.90] in the decisive
stratum, against 0.50 for the base rate. Answering the most confident
items first cuts the risk: AURC 0.30 against 0.40 pooled, 0.18 against
0.33 in the stratum. The intervals are wide; the lower bounds sit above
chance pooled and touch it in the stratum.

## Is it an action detector?

No. Removing the eight action features barely moves anything: pooled
AUROC 0.73 against 0.73, decisive 0.73 against 0.76, AURC unchanged. The
skill does not live in "did the agent answer". The features that carry it
are agreement with the graded draft, readings count and the support
features, with the log-probability token count discussed below.

## Is it a bucket detector?

Partly. The same features predict the bucket at 0.59 [0.50, 0.67] against
a majority prior of 0.46, so they know something about the bucket. But
the discrimination survives inside the decisive stratum, where the bucket
is fixed and retrieval is fixed, so the calibrator is not only a bucket
detector. Pooled ECE is flattered by the constant buckets, as expected:
the base rate itself scores 0.00 pooled.

## Should the log-probability features stay?

No. Dropping them costs on the point estimates, pooled AUROC 0.73 to 0.69
and decisive 0.76 to 0.66, which is why the question needed a diagnostic
rather than a rule. The diagnostic, run after the three planned variants
and reported as post hoc, refits the logistic model with single features
moved in or out:

| vector | pooled AUROC | decisive AUROC |
|---|---|---|
| full | 0.73 [0.64, 0.82] | 0.76 [0.62, 0.90] |
| full minus lp_tokens | 0.70 [0.61, 0.79] | 0.71 [0.55, 0.85] |
| minus_logprobs | 0.69 [0.59, 0.78] | 0.66 [0.47, 0.81] |
| minus_logprobs plus lp_tokens alone | 0.73 [0.64, 0.82] | 0.75 [0.61, 0.89] |
| the six logprob features alone | 0.65 [0.54, 0.74] | 0.59 [0.42, 0.75] |

The whole gain is lp_tokens: the token count of the regenerated draft.
Adding that one feature back to the minus_logprobs vector restores the
full result; the five probability summaries add nothing, and on the
matched subset, where the sequence does describe the graded text, their
means by label are flat (reports/logprob-mismatch.md). A token count of a
text that differs from the graded one on 40 percent of the stratum is not
a confidence signal, it is a length feature with noise, and its
coefficient pairs with a negative one on the response's own length. That
is a pattern that would not transfer. The log-probability features are
dropped, the cost is stated, and the recommended vector is minus_logprobs.

## Which fit?

Logistic plus isotonic, on the minus_logprobs vector: pooled ECE 0.10
[0.07, 0.19] against 0.14 for the plain logistic fit, Brier 0.22 against
0.24, the same ranking. Inside the decisive stratum the ECE is 0.18
[0.12, 0.31] on 50 items across ten bins, so the reliability table there
is a sketch, not a curve.

## What this means for the report

The confidence score carries real but weak information about correctness
that is not explained by the action taken or the bucket, and it is
usable for a selective policy: answering the top half by confidence in
the decisive stratum roughly halves the error rate. It is not a precise
probability at this data size. The test split, read once at M8, will say
whether even the directional claim holds.
