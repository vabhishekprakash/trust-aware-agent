# Dev label distribution

Label 1 is a CORRECT grade; PARTIAL and WRONG are 0. Sources: locked 100 from dev-run-v1b.jsonl; reserve 34 from dev-run-reserve.jsonl.

### locked 100

| bucket | n | correct | actions (count) |
|---|---|---|---|
| answerable | 46 | 30/46 (65%) | ABSTAIN 6, ANSWER 35, CLARIFY 5 |
| ambiguous | 9 | 2/9 (22%) | ANSWER 8, CLARIFY 1 |
| unanswerable | 25 | 23/25 (92%) | ABSTAIN 24, CLARIFY 1 |
| false_premise | 20 | 0/20 (0%) | ABSTAIN 8, ANSWER 12 |
| all | 100 | 55/100 (55%) | ABSTAIN 38, ANSWER 55, CLARIFY 7 |

Decisive stratum, answerable with evidence retrieved: 27/38 (71%) correct, 11 wrong.

### reserve 34

| bucket | n | correct | actions (count) |
|---|---|---|---|
| answerable | 16 | 6/16 (38%) | ABSTAIN 6, ANSWER 9, CLARIFY 1 |
| ambiguous | 0 | 0/0 |  |
| unanswerable | 9 | 9/9 (100%) | ABSTAIN 9 |
| false_premise | 9 | 0/9 (0%) | ABSTAIN 3, ANSWER 6 |
| all | 34 | 15/34 (44%) | ABSTAIN 18, ANSWER 15, CLARIFY 1 |

Decisive stratum, answerable with evidence retrieved: 6/12 (50%) correct, 6 wrong.

### merged

| bucket | n | correct | actions (count) |
|---|---|---|---|
| answerable | 62 | 36/62 (58%) | ABSTAIN 12, ANSWER 44, CLARIFY 6 |
| ambiguous | 9 | 2/9 (22%) | ANSWER 8, CLARIFY 1 |
| unanswerable | 34 | 32/34 (94%) | ABSTAIN 33, CLARIFY 1 |
| false_premise | 29 | 0/29 (0%) | ABSTAIN 11, ANSWER 18 |
| all | 134 | 70/134 (52%) | ABSTAIN 56, ANSWER 70, CLARIFY 8 |

Decisive stratum, answerable with evidence retrieved: 33/50 (66%) correct, 17 wrong.

The ambiguous bucket is small and its numbers are indicative only. The false-premise bucket has no positive examples; see reports/premise-step.md and the limitations in docs/annotation-guide.md.
