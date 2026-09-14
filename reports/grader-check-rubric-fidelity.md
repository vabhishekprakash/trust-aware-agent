# Grader check: rubric fidelity of v10 on the first 40 drafts

This is NOT a blind number. The owner graded the sheet blind once; that figure stands in
reports/grader-check-result.md. Here the grader was changed after the owner's rulings and run
again on the same drafts, and the owner's grades for sheet numbers 9, 16, 33, 34 are the
ones the owner revised on seeing the disagreements. The figure measures how faithfully the
fixed grader follows the rubric the owner settled, on drafts the fix was designed against.

Grader grader-v10, judge llama3.1:latest, drafts by the model under test.

- drafts graded by the owner: 39 of 40 (no grade written for sheet numbers 1)
- binary label agreement (CORRECT against not CORRECT): 38 of 39 (97 percent)
- three-way grade agreement: 38 of 39 (97 percent)
- binary agreement per bucket: ambiguous 3 of 4, answerable 18 of 18, false_premise 4 of 4, unanswerable 13 of 13
- binary agreement per draft condition: distractor 13 of 13, no_passage 13 of 13, with_evidence 12 of 13

Owner grade to judge grade counts:

    CORRECT  -> CORRECT  18
    CORRECT  -> PARTIAL  1
    PARTIAL  -> PARTIAL  3
    WRONG    -> WRONG    17

## Binary disagreements (1)

### sheet 19: owner CORRECT, judge PARTIAL (decided by judge)

question: Which Phase D review signs off that the system is ready?

reference: reading 1: ready to be accepted and shipped to the launch site or operational facility -> the System Acceptance Review (SAR) or pre-Ship Review (page 162)
reference: reading 2: ready for a safe and successful flight or launch -> the Flight Readiness Review (FRR) (Mission Readiness Review for some missions) (page 163)

draft: The FRR (Flight Readiness Review) phase signs off that the system is ready.

bucket ambiguous, condition with_evidence, judge reason: The candidate does not clarify which reading is meant.


## Grade-only disagreements, same binary label (0)

None.
