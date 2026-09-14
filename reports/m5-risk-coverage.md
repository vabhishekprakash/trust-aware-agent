# Risk and coverage on dev, before any threshold is chosen

Out-of-fold probabilities of minus_logprobs with logistic+isotonic, 134 dev items, bootstrap bands over items with 1000 resamples. Risk is the error rate among the covered items; coverage is the share covered. Nothing is tuned here.

Answered items: 70 (the population the thresholds act on), of which 36 correct, base risk 49 percent. Pass-through items: 56 ABSTAIN and 8 CLARIFY, of which 34 correct.

## Risk-coverage curve, answered population

Every row is a threshold that can actually be set (ties covered together).

| threshold | coverage % | risk % |
|---|---|---|
| 1.000 | 1 [0, 4] | 0 [0, 0] |
| 0.882 | 4 [0, 10] | 33 [0, 100] |
| 0.846 | 9 [3, 16] | 17 [0, 55] |
| 0.686 | 13 [6, 20] | 33 [0, 67] |
| 0.680 | 20 [11, 30] | 36 [11, 64] |
| 0.652 | 21 [13, 31] | 40 [15, 67] |
| 0.649 | 23 [13, 33] | 38 [15, 63] |
| 0.625 | 24 [14, 34] | 35 [13, 59] |
| 0.600 | 31 [21, 41] | 46 [25, 67] |
| 0.577 | 41 [30, 53] | 41 [24, 61] |
| 0.577 | 43 [31, 54] | 43 [26, 62] |
| 0.571 | 47 [36, 59] | 39 [23, 58] |
| 0.532 | 49 [37, 60] | 41 [26, 60] |
| 0.517 | 53 [41, 64] | 40 [26, 57] |
| 0.500 | 59 [47, 70] | 39 [25, 55] |
| 0.429 | 64 [53, 74] | 40 [26, 56] |
| 0.418 | 66 [54, 77] | 41 [28, 57] |
| 0.400 | 67 [56, 79] | 40 [27, 56] |
| 0.389 | 69 [57, 79] | 40 [26, 55] |
| 0.375 | 70 [60, 80] | 41 [26, 55] |
| 0.364 | 73 [61, 83] | 41 [28, 55] |
| 0.348 | 74 [63, 84] | 42 [28, 57] |
| 0.348 | 79 [69, 87] | 40 [26, 54] |
| 0.341 | 80 [69, 89] | 41 [28, 55] |
| 0.333 | 86 [77, 93] | 43 [31, 57] |
| 0.294 | 89 [80, 96] | 45 [32, 58] |
| 0.273 | 90 [83, 97] | 46 [33, 59] |
| 0.250 | 91 [84, 97] | 47 [34, 59] |
| 0.176 | 97 [93, 100] | 48 [37, 61] |
| 0.000 | 100 [100, 100] | 49 [37, 60] |

## Risk-coverage curve, deployed population

Every row is a threshold that can actually be set (ties covered together).

| threshold | coverage % | risk % |
|---|---|---|
| 1.000 | 48 [40, 57] | 46 [34, 59] |
| 0.882 | 50 [41, 59] | 46 [34, 59] |
| 0.846 | 52 [42, 60] | 44 [33, 56] |
| 0.686 | 55 [46, 63] | 45 [34, 56] |
| 0.680 | 58 [49, 66] | 45 [33, 55] |
| 0.652 | 59 [50, 67] | 46 [34, 56] |
| 0.649 | 60 [51, 67] | 45 [34, 56] |
| 0.625 | 60 [52, 68] | 44 [33, 55] |
| 0.600 | 64 [56, 72] | 46 [35, 57] |
| 0.577 | 69 [61, 77] | 45 [35, 55] |
| 0.577 | 70 [62, 78] | 46 [35, 56] |
| 0.571 | 72 [65, 79] | 44 [34, 54] |
| 0.532 | 73 [66, 80] | 45 [35, 55] |
| 0.517 | 75 [68, 82] | 45 [35, 55] |
| 0.500 | 78 [71, 84] | 44 [34, 54] |
| 0.429 | 81 [75, 87] | 44 [34, 54] |
| 0.418 | 82 [75, 88] | 44 [35, 54] |
| 0.400 | 83 [76, 89] | 44 [35, 54] |
| 0.389 | 84 [77, 90] | 44 [34, 53] |
| 0.375 | 84 [78, 90] | 44 [35, 54] |
| 0.364 | 86 [80, 92] | 44 [35, 54] |
| 0.348 | 87 [81, 92] | 45 [36, 54] |
| 0.348 | 89 [84, 94] | 44 [35, 53] |
| 0.341 | 90 [84, 94] | 44 [35, 53] |
| 0.333 | 92 [88, 96] | 45 [36, 54] |
| 0.294 | 94 [90, 98] | 46 [37, 55] |
| 0.273 | 95 [91, 98] | 46 [38, 55] |
| 0.250 | 96 [92, 98] | 47 [38, 56] |
| 0.176 | 98 [96, 100] | 48 [40, 56] |
| 0.000 | 100 [100, 100] | 48 [40, 56] |

## Candidate targets, error among answered items

Threshold is the lowest out-of-fold probability whose covered error rate on dev is at most the target. Coverage is the share of answered items shown; intervals are bootstrap over items at that fixed threshold. The deployed columns count CLARIFY and ABSTAIN as covered with their own labels.

| target | threshold | answered: coverage % | answered: risk % | deployed: coverage % | deployed: risk % |
|---|---|---|---|---|---|
| base rate (answer everything) | 0.000 | 100 [100, 100] | 49 [37, 60] | 100 [100, 100] | 48 [40, 56] |
| 10% | 1.000 | 1 [0, 4] | 0 [0, 0] | 49 [40, 57] | 46 [34, 59] |
| 15% | 1.000 | 1 [0, 4] | 0 [0, 0] | 49 [40, 57] | 46 [34, 59] |
| 20% | 0.846 | 9 [3, 16] | 17 [0, 55] | 52 [43, 60] | 44 [33, 56] |
| 25% | 0.846 | 9 [3, 16] | 17 [0, 55] | 52 [43, 60] | 44 [33, 56] |

## What each candidate does per bucket

Counts of items shown (ANSWER by the policy, plus pass-through ABSTAIN and CLARIFY) and withheld (below the threshold), with the correct count among the shown. The unanswerable bucket is where a policy can look good by passing easy abstentions.

Target 10%, threshold 1.000:

| bucket | n | shown | correct among shown | withheld | correct among withheld |
|---|---|---|---|---|---|
| answerable | 62 | 19 (18 pass-through) | 2 | 43 | 34 |
| ambiguous | 9 | 1 (1 pass-through) | 1 | 8 | 1 |
| unanswerable | 34 | 34 (34 pass-through) | 32 | 0 | 0 |
| false_premise | 29 | 11 (11 pass-through) | 0 | 18 | 0 |

Target 15%, threshold 1.000:

| bucket | n | shown | correct among shown | withheld | correct among withheld |
|---|---|---|---|---|---|
| answerable | 62 | 19 (18 pass-through) | 2 | 43 | 34 |
| ambiguous | 9 | 1 (1 pass-through) | 1 | 8 | 1 |
| unanswerable | 34 | 34 (34 pass-through) | 32 | 0 | 0 |
| false_premise | 29 | 11 (11 pass-through) | 0 | 18 | 0 |

Target 20%, threshold 0.846:

| bucket | n | shown | correct among shown | withheld | correct among withheld |
|---|---|---|---|---|---|
| answerable | 62 | 23 (18 pass-through) | 6 | 39 | 30 |
| ambiguous | 9 | 1 (1 pass-through) | 1 | 8 | 1 |
| unanswerable | 34 | 34 (34 pass-through) | 32 | 0 | 0 |
| false_premise | 29 | 12 (11 pass-through) | 0 | 17 | 0 |

Target 25%, threshold 0.846:

| bucket | n | shown | correct among shown | withheld | correct among withheld |
|---|---|---|---|---|---|
| answerable | 62 | 23 (18 pass-through) | 6 | 39 | 30 |
| ambiguous | 9 | 1 (1 pass-through) | 1 | 8 | 1 |
| unanswerable | 34 | 34 (34 pass-through) | 32 | 0 | 0 |
| false_premise | 29 | 12 (11 pass-through) | 0 | 17 | 0 |

Unanswerable bucket on its own: 34 items, 34 pass through as abstentions or clarifications (32 correct), 0 answered. The thresholds never touch the pass-through items, so this bucket's contribution to deployed coverage and to the positives is the same at every target. That is stated so a reader can subtract it: the answered-population columns above are the policy's real work.

Figure: m5-risk-coverage.png
