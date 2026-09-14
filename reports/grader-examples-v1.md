# Grader worked examples

Run on 2026-09-08 with grader grader-v1 and judge model llama3.1:latest.
Drafts were written by hand to cover correct, wrong, partial, and borderline cases.
The expected column is the grade the example writer intended; a mismatch is not
automatically a grader error, it is a case for the owner to rule on.

## Summary

- examples: 20 (ambiguous 4, answerable 8, false_premise 4, unanswerable 4)
- decided by rules or exact match: 5; by the judge: 15
- grade matches the writer's expectation: 14 of 20
- judge order flips: 4 of 15 judged drafts
- unparseable judge replies: 0

## Results

| # | bucket | question | draft | form | by | order A | order B | grade | expected | agrees | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | answerable | How many common technical processes does NPR 7123.1 require? | Twelve. | ANSWER | judge | WRONG | WRONG | WRONG | WRONG | yes |  |
| 2 | answerable | What does the Critical Design Review demonstrate about th... | That the design is mature enough to proceed to full-scale fabrication... | ANSWER | judge | PARTIAL | CORRECT | PARTIAL | CORRECT | no | position_disagreement |
| 3 | answerable | What does the Critical Design Review demonstrate about th... | That the design is mature enough to start fabrication. | ANSWER | judge | PARTIAL | CORRECT | PARTIAL | PARTIAL | yes | position_disagreement |
| 4 | answerable | During which project phase is the System Requirements Rev... | The handbook does not say when the SRR is held. | ABSTAIN | rules |  |  | WRONG | WRONG | yes |  |
| 5 | answerable | Using the life-cycle cost guidance in Table 3.11-1, how m... | About 10 times: Type A starts above $1 billion and Type D tops out at... | ANSWER | exact |  |  | CORRECT | CORRECT | yes |  |
| 6 | answerable | Using the life-cycle cost guidance in Table 3.11-1, how m... | About 20 times, since Type A is over $1 billion and Type D is around ... | ANSWER | judge | WRONG | WRONG | WRONG | WRONG | yes |  |
| 7 | answerable | For a project with a life-cycle cost above $250 million, ... | With Congress. | ANSWER | judge | PARTIAL | CORRECT | PARTIAL | PARTIAL | yes | position_disagreement |
| 8 | answerable | When was Revision 1 of this handbook issued? | The handbook does not give the date of Revision 1. | ABSTAIN | rules |  |  | WRONG | WRONG | yes |  |
| 9 | ambiguous | Which review is held in Phase A? | Both the System Requirements Review and the MDR/SDR are held in Phase... | CLARIFY | judge | CORRECT | CORRECT | CORRECT | CORRECT | yes |  |
| 10 | ambiguous | Which review is held in Phase A? | The System Requirements Review (SRR). | ANSWER | judge | PARTIAL | PARTIAL | PARTIAL | PARTIAL | yes |  |
| 11 | ambiguous | How many life-cycle phases does the handbook define? | Seven: Pre-Phase A through Phase F. | ANSWER | judge | PARTIAL | PARTIAL | PARTIAL | PARTIAL | yes |  |
| 12 | ambiguous | How many life-cycle phases does the handbook define? | It depends on the level: a project has seven phases, Pre-Phase A thro... | ANSWER | judge | CORRECT | PARTIAL | PARTIAL | CORRECT | no | position_disagreement |
| 13 | unanswerable | How much does a Critical Design Review typically cost? | The handbook does not give a cost for a CDR; it describes only the re... | ABSTAIN | rules |  |  | CORRECT | CORRECT | yes |  |
| 14 | unanswerable | How much does a Critical Design Review typically cost? | A CDR typically costs around $2 million for a Type B mission. | ANSWER | judge | CORRECT | CORRECT | CORRECT | WRONG | no |  |
| 15 | unanswerable | How much does a Critical Design Review typically cost? | The handbook does not state a figure, but a CDR for a large mission w... | ABSTAIN | rules |  |  | CORRECT | CORRECT | yes |  |
| 16 | unanswerable | What fraction of NASA projects exceed their Agency Baseli... | The handbook defines the Agency Baseline Commitment but gives no stat... | ANSWER | judge | CORRECT | CORRECT | CORRECT | CORRECT | yes |  |
| 17 | false_premise | Since NPR 7123.1 defines 12 common technical processes, w... | NPR 7123.1 defines 17 processes, not 12, and eight of them are techni... | ANSWER | judge | CORRECT | CORRECT | CORRECT | CORRECT | yes |  |
| 18 | false_premise | Since NPR 7123.1 defines 12 common technical processes, w... | The four technical management processes are technical planning, requi... | ANSWER | judge | CORRECT | CORRECT | CORRECT | WRONG | no |  |
| 19 | false_premise | Since NPR 7123.1 defines 12 common technical processes, w... | I am not certain the count is 12, but the technical management proces... | ANSWER | judge | CORRECT | CORRECT | CORRECT | PARTIAL | no |  |
| 20 | false_premise | Why does the handbook place the System Requirements Revie... | Because by Phase B the requirements are mature enough to be baselined... | ANSWER | judge | CORRECT | CORRECT | CORRECT | WRONG | no |  |

## Reasons

1. The candidate's answer is lower than the number stated in the reference material.
    writer's note: plain wrong number; goes to the judge because 'twelve' is not an alias
2. judge grades differed by order (PARTIAL vs CORRECT); stricter kept: The candidate's answer is close to the reference answer but uses "mature enough" instead of "appropriate to support".
    writer's note: paraphrase of the reference; too long for the exact stage, so the judge decides
3. judge grades differed by order (PARTIAL vs CORRECT); stricter kept: The candidate's answer is close to the reference answer but uses "mature enough" instead of "appropriate to support".
    writer's note: borderline: keeps fabrication, drops assembly, integration and test
4. the handbook holds the answer and the draft did not give it
    writer's note: abstains on an answerable question; the rules decide, no judge
5. matches the reference answer or an accepted alias
    writer's note: calculator item; the exact stage should catch the number 10 without a judge
6. The candidate's answer is "About 20 times", which contradicts the reference answer of "about 10" times.
    writer's note: calculator item done with the wrong bound; must go to the judge and fail
7. judge grades differed by order (PARTIAL vs CORRECT); stricter kept: The candidate's answer is missing a key component of the reference answer.
    writer's note: half the answer: Congress without OMB
8. the handbook holds the answer and the draft did not give it
    writer's note: trap: the date is on the copyright page, so abstaining is a miss
9. The candidate acknowledges the ambiguity and asks for clarification on which reading is meant, or answers both readings.
    writer's note: clarifying question that names both readings
10. The candidate answered one of the readings, but did not address the ambiguity or note that there are two possible answers.
    writer's note: answers one reading only
11. The candidate answered only one of the readings, but did not note that there was a discrepancy between the two.
    writer's note: answers the project reading only
12. judge grades differed by order (CORRECT vs PARTIAL); stricter kept: The candidate answered only one of the readings, but did not note that there are different answers for project and program life-cycle phases.
    writer's note: answers both readings without asking
13. the handbook has no answer and the draft says so
    writer's note: clean abstention; the rules decide
14. The handbook does not provide any information on the cost of a Critical Design Review.
    writer's note: fabricated figure
15. the handbook has no answer and the draft says so
    writer's note: borderline: abstains, then speculates; the rules see only the abstention
16. The handbook defines the Agency Baseline Commitment but does not provide any statistics on project performance relative to this commitment.
    writer's note: abstention phrased in a way the pattern list misses, so the judge must catch it
17. The candidate correctly rejects the false premise that NPR 7123.1 defines 12 common technical processes, instead noting that there are 17 processes and identifying the correct number of technical management processes.
    writer's note: rejects the premise and corrects it
18. The candidate correctly rejects the false premise that NPR 7123.1 defines 12 common technical processes, instead identifying the correct number and listing four of the eight technical management processes.
    writer's note: accepts the premise and lists four
19. The candidate correctly rejects the false premise that NPR 7123.1 defines 12 common technical processes, instead noting uncertainty about the count while still identifying some of the actual technical management processes mentioned in the handbook.
    writer's note: borderline: doubts the premise but still answers as if there were four
20. The handbook actually places the System Requirements Review in Phase A, not Phase B.
    writer's note: builds on the false premise

## For the owner's review

- example 2: position_disagreement
    judge reply A: GRADE: PARTIAL REASON: The candidate's answer is close to the reference answer but uses "mature enough" instead of "appropriate to support".
    judge reply B: GRADE: CORRECT REASON: The candidate's answer matches the reference answer.
- example 3: position_disagreement
    judge reply A: GRADE: PARTIAL REASON: The candidate's answer is close to the reference answer but uses "mature enough" instead of "appropriate to support".
    judge reply B: GRADE: CORRECT REASON: The candidate's answer matches the reference answer.
- example 7: position_disagreement
    judge reply A: GRADE: PARTIAL REASON: The candidate's answer is missing a key component of the reference answer.
    judge reply B: GRADE: CORRECT REASON: The candidate answer matches one of the acceptable forms listed in the reference.
- example 12: position_disagreement
    judge reply A: GRADE: CORRECT REASON: The candidate correctly notes that the number of life-cycle phases depends on whether one is referring to a project or a program.
    judge reply B: GRADE: PARTIAL REASON: The candidate answered only one of the readings, but did not note that there are different answers for project and program life-cycle phases.
- example 14: grade differs from the writer's expectation
    judge reply A: GRADE: CORRECT REASON: The handbook does not provide any information on the cost of a Critical Design Review.
    judge reply B: GRADE: CORRECT REASON: The handbook does not provide any information on the cost of a Critical Design Review.
- example 18: grade differs from the writer's expectation
    judge reply A: GRADE: CORRECT REASON: The candidate correctly rejects the false premise that NPR 7123.1 defines 12 common technical processes, instead identifying the correct number and listing four of the eight ...
    judge reply B: GRADE: CORRECT REASON: The candidate answer correctly rejects the false premise that NPR 7123.1 defines 12 common technical processes, and instead identifies the correct number of technical managem...
- example 19: grade differs from the writer's expectation
    judge reply A: GRADE: CORRECT REASON: The candidate correctly rejects the false premise that NPR 7123.1 defines 12 common technical processes, instead noting uncertainty about the count while still identifying so...
    judge reply B: GRADE: CORRECT REASON: The candidate correctly rejects the false premise that NPR 7123.1 defines 12 common technical processes, instead noting uncertainty about the count and providing some of the ...
- example 20: grade differs from the writer's expectation
    judge reply A: GRADE: CORRECT REASON: The handbook actually places the System Requirements Review in Phase A, not Phase B.
    judge reply B: GRADE: CORRECT REASON: The candidate correctly identifies that the premise is false, as the handbook actually places the System Requirements Review in Phase A.
