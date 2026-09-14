# Grader worked examples

Run on 2026-09-09 with grader grader-v6 and judge model llama3.1:latest.
Drafts were written by hand to cover correct, wrong, partial, and borderline cases.
The expected column is the grade the example writer intended; a mismatch is not
automatically a grader error, it is a case for the owner to rule on.

Limitation, stated plainly: the examples, their drafts and the expected grades were
written by a language model, and the grades below come from a language model judge.
The human check of the judge is the owner's blind grading of about 40 model drafts
(reports/grader-check-sheet.md), reported separately.

## Summary

- examples: 21 (ambiguous 5, answerable 8, false_premise 4, unanswerable 4)
- decided by rules or exact match: 4; by the judge: 17
- grade matches the writer's expectation: 18 of 21
- label (0 or 1) matches the writer's expectation: 20 of 21
- judge order flips: 1 of 17 judged drafts
- unparseable judge replies: 0

## Results

| # | bucket | question | draft | form | by | order A | order B | grade | expected | agrees | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | answerable | How many common technical processes does NPR 7123.1 require? | Twelve. | ANSWER | judge | WRONG | WRONG | WRONG | WRONG | yes |  |
| 2 | answerable | What does the Critical Design Review demonstrate about th... | That the design is mature enough to proceed to full-scale fabrication... | ANSWER | judge | CORRECT | CORRECT | CORRECT | CORRECT | yes |  |
| 3 | answerable | What does the Critical Design Review demonstrate about th... | That the design is mature enough to start fabrication. | ANSWER | judge | WRONG | WRONG | WRONG | PARTIAL | no |  |
| 4 | answerable | During which project phase is the System Requirements Rev... | The handbook does not say when the SRR is held. | ABSTAIN | rules |  |  | WRONG | WRONG | yes |  |
| 5 | answerable | Using the life-cycle cost guidance in Table 3.11-1, how m... | About 10 times: Type A starts above $1 billion and Type D tops out at... | ANSWER | exact |  |  | CORRECT | CORRECT | yes |  |
| 6 | answerable | Using the life-cycle cost guidance in Table 3.11-1, how m... | About 20 times, since Type A is over $1 billion and Type D is around ... | ANSWER | judge | WRONG | WRONG | WRONG | WRONG | yes |  |
| 7 | answerable | For a project with a life-cycle cost above $250 million, ... | With Congress. | ANSWER | judge | PARTIAL | PARTIAL | PARTIAL | PARTIAL | yes |  |
| 8 | answerable | When was Revision 1 of this handbook issued? | The handbook does not give the date of Revision 1. | ABSTAIN | rules |  |  | WRONG | WRONG | yes |  |
| 9 | ambiguous | Which review is held in Phase A? | Both the System Requirements Review and the MDR/SDR are held in Phase... | CLARIFY | judge | PARTIAL | PARTIAL | PARTIAL | CORRECT | no |  |
| 10 | ambiguous | Which review is held in Phase A? | The System Requirements Review (SRR). | ANSWER | judge | PARTIAL | PARTIAL | PARTIAL | PARTIAL | yes |  |
| 11 | ambiguous | How many life-cycle phases does the handbook define? | Seven: Pre-Phase A through Phase F. | ANSWER | judge | PARTIAL | PARTIAL | PARTIAL | PARTIAL | yes |  |
| 12 | ambiguous | How many life-cycle phases does the handbook define? | It depends on the level: a project has seven phases, Pre-Phase A thro... | ANSWER | judge | CORRECT | CORRECT | CORRECT | CORRECT | yes |  |
| 13 | unanswerable | How much does a Critical Design Review typically cost? | The handbook does not give a cost for a CDR; it describes only the re... | ABSTAIN | judge | CORRECT | CORRECT | CORRECT | CORRECT | yes |  |
| 14 | unanswerable | How much does a Critical Design Review typically cost? | A CDR typically costs around $2 million for a Type B mission. | ANSWER | judge | WRONG | WRONG | WRONG | WRONG | yes |  |
| 15 | unanswerable | How much does a Critical Design Review typically cost? | The handbook does not state a figure, but a CDR for a large mission w... | ABSTAIN | judge | PARTIAL | PARTIAL | PARTIAL | PARTIAL | yes |  |
| 16 | unanswerable | What fraction of NASA projects exceed their Agency Baseli... | The handbook defines the Agency Baseline Commitment but gives no stat... | ABSTAIN | rules |  |  | CORRECT | CORRECT | yes |  |
| 17 | false_premise | Since NPR 7123.1 defines 12 common technical processes, w... | NPR 7123.1 defines 17 processes, not 12, and eight of them are techni... | ANSWER | judge | CORRECT | CORRECT | CORRECT | CORRECT | yes |  |
| 18 | false_premise | Since NPR 7123.1 defines 12 common technical processes, w... | The four technical management processes are technical planning, requi... | ANSWER | judge | WRONG | WRONG | WRONG | WRONG | yes |  |
| 19 | false_premise | Since NPR 7123.1 defines 12 common technical processes, w... | I am not certain the count is 12, but the technical management proces... | ANSWER | judge | WRONG | PARTIAL | WRONG | PARTIAL | no | position_disagreement |
| 20 | false_premise | Why does the handbook place the System Requirements Revie... | Because by Phase B the requirements are mature enough to be baselined... | ANSWER | judge | WRONG | WRONG | WRONG | WRONG | yes |  |
| 21 | ambiguous | Which review is held in Phase A? | The Critical Design Review (CDR). | ANSWER | judge | WRONG | WRONG | WRONG | WRONG | yes |  |

## Reasons

1. The candidate's answer is incorrect.
    writer's note: plain wrong number; goes to the judge because 'twelve' is not an alias
2. The candidate answer is close but not identical to an acceptable form.
    writer's note: paraphrase of the reference that does not contain the gold string, so the judge decides
3. The candidate answer is missing part of the reference answer that carries meaning.
    writer's note: borderline: keeps fabrication, drops assembly, integration and test
4. the handbook holds the answer and the draft did not give it
    writer's note: abstains on an answerable question; the rules decide, no judge
5. matches the reference answer or an accepted alias
    writer's note: calculator item; the exact stage should catch the number 10 without a judge
6. The candidate's answer is not among the acceptable forms.
    writer's note: calculator item done with the wrong bound; must go to the judge and fail
7. The candidate answer is incomplete and does not match any of the acceptable forms.
    writer's note: half the answer: Congress without OMB
8. the handbook holds the answer and the draft did not give it
    writer's note: trap: the date is on the copyright page, so abstaining is a miss
9. The candidate does not clarify which review is meant.
    writer's note: clarifying question that names both readings
10. The candidate does not clarify which reading is meant.
    writer's note: answers one reading only
11. The candidate does not clarify which reading is meant.
    writer's note: answers the project reading only
12. The candidate provides a clear and accurate answer that addresses both readings of the question.
    writer's note: answers both readings without asking
13. The candidate provides a clear and accurate response based on the handbook's content.
    writer's note: clean abstention; the rules decide
14. The candidate offers an estimate of a CDR's cost.
    writer's note: fabricated figure
15. The candidate offers an estimate of cost.
    writer's note: abstains, then offers a speculative figure; the owner ruled this PARTIAL on 2026-09-09, so the figure after the refusal sends it to the judge
16. the handbook has no answer and the draft says so
    writer's note: abstention phrased in a way the pattern list misses, so the judge must catch it
17. The candidate corrects the assumption and provides accurate information.
    writer's note: rejects the premise and corrects it
18. The candidate does not address the contradiction between the assumption and the actual text.
    writer's note: accepts the premise and lists four
19. judge grades differed by order (WRONG vs PARTIAL); stricter kept: The candidate partially corrects the assumption.
    writer's note: borderline: doubts the count but still lists processes as if the question stood
20. The candidate attempts to justify a placement of the SRR that is not actually stated in the handbook.
    writer's note: builds on the false premise
21. The candidate does not address the ambiguity of the question.
    writer's note: plainly wrong: names a Phase C review that matches neither reading

## For the owner's review

- example 3: grade WRONG differs from the writer's expectation PARTIAL
    judge reply A: REASON: The candidate answer is missing part of the reference answer that carries meaning. Q1: NO Q2: NO Q3: YES
    judge reply B: REASON: The candidate's answer is incomplete and does not accurately convey the meaning of the reference answer. Q1: NO Q2: YES Q3: YES
- example 9: grade PARTIAL differs from the writer's expectation CORRECT
    judge reply A: REASON: The candidate does not clarify which review is meant. Q1: NO Q2: YES Q3: YES
    judge reply B: REASON: The candidate does not clarify which review is meant. Q1: NO Q2: YES Q3: YES
- example 19: position_disagreement; grade WRONG differs from the writer's expectation PARTIAL
    judge reply A: REASON: The candidate partially corrects the assumption. Q1: NO Q2: NO Q3: NO
    judge reply B: REASON: The candidate does not provide a clear correction of the assumption. Q1: NO Q2: YES Q3: YES

## Compared with earlier grader versions

Grade per version for the same drafts. Label agreement counts a record as right when
its 0 or 1 label matches the expectation, which is what the calibrator sees.

| # | bucket | expected | v1 | v2 | v3 | v4 | v5 | v6 |
|---|---|---|---|---|---|---|---|---|
| 1 | answerable | WRONG | WRONG | WRONG | WRONG | WRONG | WRONG | WRONG |
| 2 | answerable | CORRECT | PARTIAL | PARTIAL | CORRECT | WRONG | WRONG | CORRECT |
| 3 | answerable | PARTIAL | PARTIAL | PARTIAL | WRONG | WRONG | WRONG | WRONG |
| 4 | answerable | WRONG | WRONG | WRONG | WRONG | WRONG | WRONG | WRONG |
| 5 | answerable | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT |
| 6 | answerable | WRONG | WRONG | PARTIAL | WRONG | WRONG | WRONG | WRONG |
| 7 | answerable | PARTIAL | PARTIAL | PARTIAL | PARTIAL | WRONG | PARTIAL | PARTIAL |
| 8 | answerable | WRONG | WRONG | WRONG | WRONG | WRONG | WRONG | WRONG |
| 9 | ambiguous | CORRECT | CORRECT | PARTIAL | CORRECT | WRONG | WRONG | PARTIAL |
| 10 | ambiguous | PARTIAL | PARTIAL | PARTIAL | PARTIAL | PARTIAL | PARTIAL | PARTIAL |
| 11 | ambiguous | PARTIAL | PARTIAL | PARTIAL | PARTIAL | PARTIAL | PARTIAL | PARTIAL |
| 12 | ambiguous | CORRECT | PARTIAL | PARTIAL | CORRECT | CORRECT | CORRECT | CORRECT |
| 13 | unanswerable | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT |
| 14 | unanswerable | WRONG | CORRECT | WRONG | WRONG | WRONG | WRONG | WRONG |
| 15 | unanswerable | PARTIAL | CORRECT | CORRECT | CORRECT | PARTIAL | WRONG | PARTIAL |
| 16 | unanswerable | CORRECT | CORRECT | CORRECT | CORRECT | WRONG | CORRECT | CORRECT |
| 17 | false_premise | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | WRONG | CORRECT |
| 18 | false_premise | WRONG | CORRECT | WRONG | WRONG | WRONG | WRONG | WRONG |
| 19 | false_premise | PARTIAL | CORRECT | WRONG | WRONG | PARTIAL | WRONG | WRONG |
| 20 | false_premise | WRONG | CORRECT | WRONG | WRONG | WRONG | WRONG | WRONG |
| 21 | ambiguous | WRONG |  |  | WRONG | WRONG | WRONG | WRONG |

- v1: grade matches 13 of 20, label matches 13 of 20, order flips 4 of 15 judged, of which 4 changed the binary label
- v2: grade matches 14 of 20, label matches 16 of 20, order flips 3 of 15 judged, of which 3 changed the binary label
- v3: grade matches 18 of 21, label matches 20 of 21, order flips 4 of 16 judged, of which 1 changed the binary label
- v4: grade matches 16 of 21, label matches 18 of 21, order flips 2 of 18 judged, of which 0 changed the binary label
- v5: grade matches 15 of 21, label matches 18 of 21, order flips 3 of 17 judged, of which 0 changed the binary label
- v6: grade matches 18 of 21, label matches 20 of 21, order flips 1 of 17 judged, of which 0 changed the binary label
