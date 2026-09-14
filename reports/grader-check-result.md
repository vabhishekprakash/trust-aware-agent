# Blind grader check: result

Grader grader-v7, judge llama3.1:latest, drafts by the model under test.
The owner graded the drafts without seeing the judge; the judge's grades were held in a key file.

- drafts graded by the owner: 39 of 40 (no grade written for sheet numbers 1)
- binary label agreement (CORRECT against not CORRECT): 32 of 39 (82 percent)
- three-way grade agreement: 32 of 39 (82 percent)
- binary agreement per bucket: ambiguous 3 of 4, answerable 17 of 18, false_premise 3 of 4, unanswerable 9 of 13
- binary agreement per draft condition: distractor 9 of 13, no_passage 12 of 13, with_evidence 11 of 13

Owner grade to judge grade counts:

    CORRECT  -> CORRECT  13
    CORRECT  -> PARTIAL  1
    CORRECT  -> WRONG    1
    PARTIAL  -> CORRECT  4
    WRONG    -> CORRECT  1
    WRONG    -> WRONG    19

## Binary disagreements (7)

### sheet 3: owner PARTIAL, judge CORRECT (decided by judge)

question: What joint cost and schedule confidence level must the Agency Baseline Commitment be funded to at KDP C?

reference: the handbook does not answer this question

draft: The passage does not provide information about joint cost and schedule confidence levels, nor does it mention anything related to Agency Baseline Commitments or KDP C.

bucket unanswerable, condition distractor, judge reason: The candidate correctly states that the handbook does not provide information on the topic.

### sheet 5: owner PARTIAL, judge CORRECT (decided by judge)

question: What minimum mass margin percentage should a hardware project be holding at PDR?

reference: the handbook does not answer this question

draft: The passage does not provide information about the minimum mass margin percentage or any details related to PDR (Pre-Development Review) for hardware projects.

bucket unanswerable, condition distractor, judge reason: The candidate provides a clear and accurate answer based on the information given.

### sheet 16: owner WRONG, judge CORRECT (decided by rules)

question: The handbook lists five key steps for carrying out functional analysis when decomposing requirements. What does the fifth step involve?

reference: the question's assumption is false; the handbook says: The handbook gives three key steps for functional analysis: translating top-level requirements into functions, decomposing and allocating the functions to lower levels of the product breakdown structure, and identifying and describing functional and subsystem interfaces.

draft: The passage provided does not contain information about functional analysis or any specific steps involved in it.

bucket false_premise, condition distractor, judge reason: the draft did not build on the false premise

### sheet 18: owner CORRECT, judge WRONG (decided by judge)

question: What is the dollar cost cap on projects selected through an Announcement of Opportunity in an uncoupled program?

reference: the handbook does not answer this question

draft: The passage does not provide information about the dollar cost cap on projects selected through an Announcement of Opportunity in an uncoupled program.

bucket unanswerable, condition with_evidence, judge reason: The candidate provides a clear and direct answer based on the information provided.

### sheet 19: owner CORRECT, judge PARTIAL (decided by judge)

question: Which Phase D review signs off that the system is ready?

reference: reading 1: ready to be accepted and shipped to the launch site or operational facility -> the System Acceptance Review (SAR) or pre-Ship Review (page 162)
reference: reading 2: ready for a safe and successful flight or launch -> the Flight Readiness Review (FRR) (Mission Readiness Review for some missions) (page 163)

draft: The FRR (Flight Readiness Review) phase signs off that the system is ready.

bucket ambiguous, condition with_evidence, judge reason: The candidate does not clarify which reading is meant.

### sheet 32: owner PARTIAL, judge CORRECT (decided by judge)

question: What is AS9100 and which industry was it created for?

reference: reference answer: a quality management system developed for the commercial aerospace industry
reference: acceptable forms: a widely adopted and standardized quality management system for the commercial aerospace industry; quality management system; commercial aerospace industry; aerospace quality management system; a quality management system (QMS) developed for the commercial aerospace industry; a QMS for the commercial aerospace industry; QMS; commercial aerospace industry

draft: AS9100, developed by the Aerospace Industries Association (AIA), is a quality management system standard specifically tailored for the aerospace and defense industries to ensure product safety and reliability.

bucket answerable, condition no_passage, judge reason: The candidate's answer is very similar to the reference answer but includes an additional detail.

### sheet 34: owner PARTIAL, judge CORRECT (decided by rules)

question: Which commercial space flight mishaps supplied the lessons learned that fed the Office of the Chief Engineer's systems engineering initiative?

reference: the handbook does not answer this question

draft: The passage does not say anything about commercial space flight mishaps or lessons learned from such incidents. Therefore, it cannot answer which specific mishaps supplied those lessons.

bucket unanswerable, condition distractor, judge reason: the handbook has no answer and the draft says so


## Grade-only disagreements, same binary label (0)

None.
