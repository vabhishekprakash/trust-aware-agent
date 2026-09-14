# Integrity entry 4: the halving figure, recounted

Post hoc, 2026-09-14, dev only, from reports/m4-calibration-oof.jsonl. Nothing refit, no test item read.

Population: decisive stratum: answerable items with the evidence retrieved, dev, out-of-fold probabilities. 50 items, 17 errors, base error 34 percent. The most confident half is 25 items.

| vector | fit | distinct values | rank-ordered top half: errors, error % | tie-aware threshold nearest half: covered, errors, error % [95% interval] |
|---|---|---|---|---|
| full | logistic | 50 | 4 of 25, 16 | 25, 4, 16 [4, 32] |
| full | logistic+isotonic | 22 | 6 of 25, 24 | 22, 4, 18 [4, 36] |
| minus_logprobs | logistic | 50 | 8 of 25, 32 | 25, 8, 32 [14, 52] |
| minus_logprobs | logistic+isotonic | 23 | 8 of 25, 32 | 25, 8, 32 [14, 52] |

Rank-ordered splits ties in file order, which no threshold can do; tie-aware covers every item tied at the boundary.
The confirmed calibrator is minus_logprobs with logistic+isotonic. The bootstrap resamples items (1000, seed 42) at the fixed threshold.
