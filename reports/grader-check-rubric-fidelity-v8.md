# Grader check: rubric fidelity of v8 on the first 40 drafts

This is NOT a blind number. The owner graded the sheet blind once; that figure stands in
reports/grader-check-result.md. Here the grader was changed after the owner's rulings and run
again on the same drafts, and the owner's grades for sheet numbers 16, 34 are the
ones the owner revised on seeing the disagreements. The figure measures how faithfully the
fixed grader follows the rubric the owner settled, on drafts the fix was designed against.

Grader grader-v8, judge llama3.1:latest, drafts by the model under test.

- drafts graded by the owner: 39 of 40 (no grade written for sheet numbers 1)
- binary label agreement (CORRECT against not CORRECT): 33 of 39 (85 percent)
- three-way grade agreement: 32 of 39 (82 percent)
- binary agreement per bucket: ambiguous 3 of 4, answerable 17 of 18, false_premise 2 of 4, unanswerable 11 of 13
- binary agreement per draft condition: distractor 10 of 13, no_passage 12 of 13, with_evidence 11 of 13

Owner grade to judge grade counts:

    CORRECT  -> CORRECT  16
    CORRECT  -> WRONG    1
    PARTIAL  -> CORRECT  2
    PARTIAL  -> WRONG    1
    WRONG    -> CORRECT  3
    WRONG    -> WRONG    16

## Binary disagreements (6)

### sheet 3: owner PARTIAL, judge CORRECT (decided by judge)

question: What joint cost and schedule confidence level must the Agency Baseline Commitment be funded to at KDP C?

reference: the handbook does not answer this question

draft: The passage does not provide information about joint cost and schedule confidence levels, nor does it mention anything related to Agency Baseline Commitments or KDP C.

bucket unanswerable, condition distractor, judge reason: The candidate answer is accurate and correctly identifies that the handbook does not provide information on joint cost and schedule confidence levels for Agency Baseline Commitments at KDP C.

### sheet 5: owner PARTIAL, judge CORRECT (decided by judge)

question: What minimum mass margin percentage should a hardware project be holding at PDR?

reference: the handbook does not answer this question

draft: The passage does not provide information about the minimum mass margin percentage or any details related to PDR (Pre-Development Review) for hardware projects.

bucket unanswerable, condition distractor, judge reason: The candidate answer is accurate and concise.

### sheet 9: owner WRONG, judge CORRECT (decided by rules)

question: The handbook wants technology assessment to keep running from concept development all the way through the Critical Design Review. Where does it say the technology development lessons learned should be captured after that point?

reference: the question's assumption is false; the handbook says: The handbook says technology assessment should play a role from concept development through the Preliminary Design Review (PDR), not the Critical Design Review; the lessons learned are captured in the final phase of the program.

draft: The NASA Systems Engineering Handbook does not specify where technology development lessons learned should be captured after the Critical Design Review.

bucket false_premise, condition distractor, judge reason: the draft did not build on the false premise

### sheet 10: owner WRONG, judge CORRECT (decided by judge)

question: Which NASA requirements document says data management planning has to appear either in the program/project plan, in the CM plan, or as a standalone document?

reference: reference answer: NPR 7120.5
reference: acceptable forms: NPR7120.5; 7120.5; NASA Procedural Requirements 7120.5

draft: The NASA Systems Engineering Handbook (SEH) requires that data management planning be included in the Program/Project Plan, the Configuration Management Plan, or as a separate document. This is outlined in the SEH guidelines for ensuring comprehensive and integrated project management practices.

bucket answerable, condition no_passage, judge reason: The candidate answer is generally consistent with the reference answer but lacks specificity.

### sheet 19: owner CORRECT, judge WRONG (decided by judge)

question: Which Phase D review signs off that the system is ready?

reference: reading 1: ready to be accepted and shipped to the launch site or operational facility -> the System Acceptance Review (SAR) or pre-Ship Review (page 162)
reference: reading 2: ready for a safe and successful flight or launch -> the Flight Readiness Review (FRR) (Mission Readiness Review for some missions) (page 163)

draft: The FRR (Flight Readiness Review) phase signs off that the system is ready.

bucket ambiguous, condition with_evidence, judge reason: The candidate answer is incomplete and does not address both possible readings of the question.

### sheet 33: owner WRONG, judge CORRECT (decided by rules)

question: Since the OCE is the approver for a waiver requested by a project whose responsibility was delegated to a Center, where should the project record the approved tailoring afterwards?

reference: the question's assumption is false; the handbook says: For a program or project delegated to a Center, the Center Director or designee approves the waiver or deviation; the OCE approves Center-level tailoring for standard use at the Center.

draft: The passage does not provide information on where the project should record the approved tailoring after it has been requested and approved by the OCE.

bucket false_premise, condition with_evidence, judge reason: the draft did not build on the false premise


## Grade-only disagreements, same binary label (1)

- sheet 32: owner PARTIAL, judge WRONG; What is AS9100 and which industry was it created for?
