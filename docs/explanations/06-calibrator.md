# 06. The calibrator

The signals are numbers; the deliverable is a probability. The calibrator
maps a feature vector to a probability that the answer is correct. Every
number is out of fold, so it says what the probability means on items the
fit never saw: dev is split five ways, each fifth is scored by a model
fitted on the other four, and the metrics use those held-out scores.

Two fits are compared. A logistic regression on standardised features,
which gives a probability directly and can be read coefficient by
coefficient. And the same score passed through isotonic regression fitted
inside the training folds, which bends the scale to match observed
accuracy without changing the ranking.

Three feature variants are fitted, decided before any result was seen:
the full vector, the vector without the action features (the action is
downstream of the state the signals measure), and the vector without the
log-probability features (their regenerated text differed from the graded
draft on a third of items). Each is scored pooled, within the answerable
bucket, and within the decisive stratum of answerable items with the
evidence retrieved, where the model's judgement decides. A bucket-detector
test asks whether the same features predict the bucket. Every metric
carries a bootstrap interval.

A common misconception: a low expected calibration error means a good
calibrator. A constant base-rate prediction scores well on it too; the
ranking metrics and the strata say whether it discriminates.

Summary: out-of-fold scores, two fits, three variants, three strata,
intervals on everything, and a bucket-detector test.
