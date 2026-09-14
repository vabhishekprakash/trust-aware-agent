# Changed numbers, 2026-09-14

Every figure that changed on 2026-09-14, with its old value, for correcting text written from the earlier versions. Part A is the draw-pool regrade of sheet 1. Part B is the measurement-integrity section and the documents that quote it. Part C is the earlier correction commit 6ee42a4, for text written from the first post hoc commit 3524e8b or from tag v1.0.2. Part D lists figures a reader might expect to have moved and that did not. Part E is context that is not a changed figure. The old values are in the named commits; the new ones in the files named.

## A. Draw-pool regrade of sheet 1 (old: 6ee42a4)

The old values are the same in 3524e8b, except rows marked (6ee42a4), which that commit introduced.

Sheet 1 is now graded against git 1cc8664, the pool it was drawn from, instead of 7a2a82d. One draft changed: sheet 1, draft 19, now PARTIAL under both judges where the owner graded CORRECT.

### Grader v13 rubric fidelity, sheet 1 (reports/grader-check-rubric-fidelity-v13.md, docs/annotation-guide.md, docs/decisions.md)

| figure | old | new |
|---|---|---|
| binary agreement | 39 of 39 (100 percent) | 38 of 39 (97 percent) |
| three-way agreement | 36 of 39 (92 percent) | 35 of 39 (90 percent) |
| binary agreement, ambiguous bucket | 3 of 3 | 3 of 4 |
| binary agreement, answerable bucket | 19 of 19 | 18 of 18 |
| binary agreement, with_evidence condition | 13 of 13 | 12 of 13 |
| owner CORRECT, judge CORRECT | 16 | 15 |
| owner CORRECT, judge PARTIAL | 0 | 1 |
| binary disagreements listed | 0 | 1 (sheet 19) |
| sheet 19 record | answerable, exact match, CORRECT | ambiguous, judge, PARTIAL |

### Second judge, pooled over 84 labelled drafts (reports/post-hoc-second-judge.md and .json, docs/report.md)

| figure | old | new |
|---|---|---|
| llama3.1 binary agreement with the owner | 81 of 84, 96% [92, 100] | 80 of 84, 95% [90, 99] |
| Mistral binary agreement with the owner | 77 of 84, 92% [86, 96] | 76 of 84, 90% [84, 96] |
| paired difference, llama3.1 minus Mistral | +4.8 points [+1.2, +9.5] | unchanged, +4.8 points [+1.2, +9.5] |
| Mistral, diagnostic lenient regrade (pooled) | 77 | 76 |
| drafts decided by code rules or exact match | 50 of 85 | 49 of 85 |
| drafts that reach a judge | 35 | 36 |
| llama3.1 agreement on labelled drafts that reach a judge | 33 of 35 | 33 of 36 |
| Mistral agreement on labelled drafts that reach a judge | 29 of 35 | 29 of 36 |
| drafts both judges misgrade (overlap) | 3 of 3 | 4 of 4 |
| of those, decided by a code rule (6ee42a4) | 1 | 1 (unchanged) |
| of those, reaching a judge (6ee42a4) | 2 ("both recur") | 3 ("all three recur") |
| shared judged errors the model-run analysts call a judging mistake (6ee42a4) | one of the two | one of the three |
| misgraded drafts with an assigned cause | 7 | 8 |
| cause rule agrees with the model-run analysts | 5 of 7 | 6 of 8 |
| Mistral strict judge calls, parsed | 69 of 70 | 71 of 72 (2 calls from the regrade) |
| llama3.1 answer lines, bare YES or NO in capitals | 196 | 202 |
| Mistral answer lines with added words, in capitals | 17 | 19 |
| Mistral answer lines, bare YES or NO in capitals | 173 | 177 |
| parsed Mistral answer lines with added words read by model-run readers | 19 | 21 |
| of those, clear by majority | 18 | 20 |
| llama3.1 cache replay, calls | 120 | 122 (still 0 live, 85 of 85 reproduced) |

### Second judge, sheet 1 (39 labelled drafts)

| figure | old | new |
|---|---|---|
| llama3.1 binary agreement | 38 of 39, 97% [92, 100] | 37 of 39, 95% [87, 100] |
| Mistral binary agreement | 37 of 39, 95% [87, 100] | 36 of 39, 92% [82, 100] |
| paired difference | one draft, +2.6 points [0.0, +7.7] | unchanged |
| labelled drafts that reach a judge | 16 | 17 |
| llama3.1 agreement on those | 16 of 16 | 16 of 17 |
| Mistral agreement on those | 15 of 16 | 15 of 17 |
| llama3.1 three-way agreement | 35 of 39 | 34 of 39 |
| Mistral three-way agreement | 34 of 39 | 33 of 39 |
| judges' same binary grade, drafts reaching a judge | 15 of 16 | 16 of 17 |
| judges' same exact grade, drafts reaching a judge | 15 of 16 | 16 of 17 |
| misgraded, llama3.1 | draft 34 | drafts 19 and 34 |
| misgraded, Mistral | drafts 8 and 34 | drafts 8, 19 and 34 |
| misgraded by both | draft 34 | drafts 19 and 34 |
| secondary line with the owner's sheet-34 revision, llama3.1 | 39 of 39 | 38 of 39 |
| secondary line with the owner's sheet-34 revision, Mistral | 38 of 39 | 37 of 39 |
| Mistral, diagnostic lenient regrade | 37 of 39 | 36 of 39 |

New figures with no old value: the regrade pass itself, 1 draft, 2 Mistral judge calls, both live, no copy calls, 34 s.

## B. Measurement integrity and related text (old: 6ee42a4; v1.0.2 where noted)

| figure or statement | where | old | new |
|---|---|---|---|
| number of integrity entries | docs/report.md heading and intro; docs/layman-guide.md | seven (five in v1.0.2) | nine |
| entries caught before any tagged version | docs/report.md intro; docs/layman-guide.md | all seven | six; entry 2's wrong figure stayed in tagged releases, this report's entry 2 among them; entries 8 and 9 not caught at the time |
| entries found by model-run reviews | docs/report.md intro | the last two (6 and 7), against the raw call logs | the rest (6 to 9), against the raw call logs and the git history |
| entry 1 name | docs/report.md | the v9 judge question | the v8 judge question (added in v8, first run on the examples under v9) |
| entry 2, v13 sheet 1 rubric fidelity | docs/report.md | 39 of 39 presented as a pool artefact of a valid rerun | 38 of 39 against the draw-time pool |
| entry 4, what the halving claim fits | docs/report.md | a rank-ordered curve over isotonic ties; 49 [37, 60] to about 40 [26, 57] percent | dropped full vector 34 to 16 [4, 32] percent; confirmed calibrator 34 to 32 [14, 52] percent, decisive stratum, 25 of 50 items; the 49 to 40 figures are for all 70 answered items |
| entry 5, the draft's cells | docs/report.md | pre-reserve figures for unanswerable and false-premise rows | false-premise cells already merged; unanswerable cells matched neither split |
| entry 8 (new) | docs/report.md | none | 27 of 38 and 2 of 8 (pre-reserve, 100 items) against 33 of 50 and 3 of 12 (merged, 134 items) |
| calibrator's pooled AUROC in the policy note (entry 9, new) | reports/m5-policy.md; scripts/policy_apply.py | 0.69 [0.59, 0.78] (v1.0.0 to v1.0.2 and 6ee42a4) | 0.70 [0.61, 0.79] |
| model-run review rounds after the corrections | docs/report.md, Who ran the checks; docs/decisions.md, note after the 2026-09-13 entry | two rounds | three rounds |
| model-run review-round counts (new) | docs/report.md, Iterated model review | none | confirmed 15, 12, 7; distinct 9 to 12, 11, 6; model-run reviewers 3, 2, 2; round 3: 6 distinct, 3 false or self-contradicting, none changed a number |
| model-run verifier's coverage | reports/post-hoc-second-judge.md; docs/report.md | all three sheets matched | final and sheet 2 as it checked them; the regraded sheet 1 and pooled figures, with intervals, matched by a second model-run verifier |
| post hoc: pooled agreement | docs/report.md | 81 and 77 | 80 and 76 |
| post hoc: drafts llama3.1 misgrades, all shared | docs/report.md | three, two reached a judge | four, three reached a judge |
| post hoc: Mistral judge replies parsed | docs/report.md | 69 of 70 | 71 of 72 |
| third model-run review round summary | reports/post-hoc-second-judge.md; docs/decisions.md note | found only wording and test gaps | confirmed seven more findings, none of which changed a number; three of six distinct defects were false or self-contradicting |

## C. The earlier correction commit (old: 3524e8b or v1.0.2; new: 6ee42a4)

These are still current except the integrity count, which is now nine (Part B).

| figure | old | new |
|---|---|---|
| Mistral echoes of the instruction's phrase | 7 calls | 3 calls on 2 distinct requests, of 7 find-shaped requests |
| llama3.1 echoes | 1 call | 0, of 2 find-shaped requests |
| copy replies, llama3.1: found / echoed / not found / none | 30 / 1 / 8 / 11 | 30 / 0 / 9 / 11 |
| copy replies, Mistral: found / echoed / NONE quoting a phrase / not found / none | 37 / 7 / (no row) / 2 / 8 | 37 / 3 / 4 / 2 / 8 |
| what the harness finding rests on | not stated | one request and one grade (the habit seen on two requests) |
| integrity entries | five | seven (now nine) |
| sheet 1 drafts, blind-check table in docs/report.md | 39 graded of 40 (3524e8b and v1.0.2) | 40, one grade line unread |
| sheet 1, draft 1 | never graded | graded CORRECT on an indented line the sheet reader skips |

## D. Checked and unchanged

Final sheet: llama3.1 19 of 20, 95% [85, 100]; Mistral 18 of 20, 90% [75, 100]; paired difference +5.0 [0.0, +15.0]; 9 of 20 drafts reach a judge. Sheet 2: 24 and 22 of 25, paired difference +8.0 [0.0, +20.0]. Pooled and sheet 1 paired differences. Mistral's four extra errors and where they fall. Order flips (Mistral 1, 4, 2; llama3.1 0, 0, 2) and the stricter-order rule's cost 1 and saved 1. Every harness lock-in count in Part C. The unreadable reply. The first run's cost: 719 s, 70 judge and 54 copy calls. Sheet 2's rubric fidelity, 24 of 25. The main evaluation and the test read.

## E. Context, not changed figures

Numbers that reached the owner's own messages before their correction, now five: entry 7's echo count (7 calls against 1); entry 4's first correction, 49 [37, 60] to about 40 [26, 57] percent, quoted for the decisive stratum though it describes all 70 answered items; the second-judge overlap of 3 of 3, which rested on entry 2's pool (now 4 of 4); 0.76, the dropped full vector's stratum AUROC; and 0.69, the plain logistic fit's pooled AUROC, quoted as the calibrator's and still in reports/m5-policy.md until 2026-09-14 (entry 9, Part B). The frozen calibrator's preregistered figures are unchanged: 0.70 [0.61, 0.79] pooled and 0.63 [0.45, 0.80] in the decisive stratum.

Draft 19's item, q0124, was moved from ambiguous to answerable by a model-run pass over the ambiguous items, acting on the owner's blind grade. It was not moved by an owner ruling, as an earlier summary to the owner said.
