# The decision policy on dev

Thresholds chosen by the owner on 2026-09-12: ANSWER at or above 0.58, ESCALATE below 0.35, VERIFY between. a coverage choice on dev, not a risk guarantee: escalate about the bottom quarter of answered items, flag the middle tertile; no risk target of 10 to 25 percent was reachable with meaningful coverage (reports/m5-risk-coverage.md). Probabilities are out of fold from minus_logprobs with logistic+isotonic; 134 dev items. VERIFY is a flag, not a verification loop.

## Outcomes per bucket, counts with rates, and the correct count in each

| bucket | n | ANSWER | VERIFY | ESCALATE | ABSTAIN | CLARIFY |
|---|---|---|---|---|---|---|
| answerable | 62 | 16/62 (26%), 12 correct | 20/62 (32%), 18 correct | 8/62 (13%), 5 correct | 12/62 (19%), 1 correct | 6/62 (10%), 0 correct |
| ambiguous | 9 | 1/9 (11%), 0 correct | 4/9 (44%), 0 correct | 3/9 (33%), 1 correct | 0/9 (0%), 0 correct | 1/9 (11%), 1 correct |
| unanswerable | 34 | 0/34 (0%), 0 correct | 0/34 (0%), 0 correct | 0/34 (0%), 0 correct | 33/34 (97%), 32 correct | 1/34 (3%), 0 correct |
| false_premise | 29 | 5/29 (17%), 0 correct | 5/29 (17%), 0 correct | 8/29 (28%), 0 correct | 11/29 (38%), 0 correct | 0/29 (0%), 0 correct |
| all | 134 | 22/134 (16%), 12 correct | 29/134 (22%), 18 correct | 19/134 (14%), 6 correct | 56/134 (42%), 33 correct | 8/134 (6%), 1 correct |

## The answered population: the policy's real work

70 items the agent answered, 36 correct. Coverage is the share shown (ANSWER or VERIFY); risk is the error rate among the shown. Intervals are bootstrap over items at the fixed threshold.

| operating point | threshold | coverage % | risk % |
|---|---|---|---|
| base rate, show everything | 0.000 | 100 [100, 100] | 49 [37, 60] |
| chosen: escalate below | 0.350 | 73 [61, 83] | 41 [28, 55] |
| shown without a flag (ANSWER band only) | 0.580 | 31 [21, 41] | 45 [25, 67] |
| alternative, risk target 20 percent | 0.846 | 9 [3, 16] | 17 [0, 55] |

The point estimate moves in the expected direction and the interval does not exclude no effect. No claim that the policy reduces error is made on dev; the single read of the test split at M8 is where that is settled. The alternative row shows what a risk guarantee would cost here: 6 of 70 answered items shown.

## Deployed columns, with their caveat

All 134 items, with the agent's 64 ABSTAIN and CLARIFY outputs counted as shown with their own labels.

| operating point | threshold | coverage % | risk % |
|---|---|---|---|
| base rate | 0.000 | 100 [100, 100] | 48 [40, 56] |
| chosen: escalate below | 0.350 | 86 [80, 92] | 44 [35, 54] |

Caveat: deployed coverage is flattered by 34 pass-through abstentions on unanswerable items that the policy never touches (32 correct), and deployed risk is punished by 11 false-premise bare abstentions graded PARTIAL and counted as errors. The answered-population table above is the policy's real work.

