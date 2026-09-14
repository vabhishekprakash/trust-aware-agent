# Grader check: blind agreement on sheet 2, grader v10

The owner graded the drafts without seeing the judge; the judge's grades were held in a key file.

Grader grader-v10, judge llama3.1:latest, drafts by the model under test.

- drafts graded by the owner: 25 of 25
- binary label agreement (CORRECT against not CORRECT): 20 of 25 (80 percent)
- three-way grade agreement: 18 of 25 (72 percent)
- binary agreement per bucket: ambiguous 3 of 4, answerable 9 of 9, false_premise 3 of 6, unanswerable 5 of 6
- binary agreement per draft condition: distractor 7 of 8, no_passage 8 of 8, with_evidence 5 of 9

Owner grade to judge grade counts:

    CORRECT  -> CORRECT  5
    CORRECT  -> WRONG    2
    PARTIAL  -> WRONG    2
    WRONG    -> CORRECT  3
    WRONG    -> WRONG    13

## Binary disagreements (5)

### sheet 10: owner CORRECT, judge WRONG (decided by judge, position_disagreement)

question: After an end product is built, what does it have to be shown to satisfy before it moves on?

reference: reading 1: Product Verification -> all of its specified requirements (page 90)
reference: reading 2: Product Validation -> stakeholder expectations (MOEs) in the intended operational environment (page 100)

draft: The end product has to be shown to satisfy its stakeholders' expectations within the intended operational environments before moving on.

bucket ambiguous, condition with_evidence, judge reason: judge grades differed by order (PARTIAL vs WRONG); stricter kept: The candidate does not clarify which reading is meant.

### sheet 13: owner WRONG, judge CORRECT (decided by rules)

question: Because the handbook treats an authorized waiver as a minor engineering change to the baseline, whose approval does it need when the waiver touches an external interface?

reference: the question's assumption is false; the handbook says: A waiver is a documented agreement releasing a program or project from meeting a requirement, and authorized waivers do not constitute a change to a baseline.

draft: The NASA Systems Engineering Handbook does not specify whose approval an authorized waiver needs when it touches an external interface.

bucket false_premise, condition with_evidence, judge reason: the draft did not build on the false premise

### sheet 14: owner WRONG, judge CORRECT (decided by rules)

question: The handbook breaks product validation into three major steps. Which of the three involves writing the validation report?

reference: the question's assumption is false; the handbook says: The handbook lists five major steps in the validation process: prepare to conduct validation, perform validation, analyze validation results, prepare a validation report, and capture the validation work products.

draft: The passage does not provide information about breaking product validation into specific steps or which step involves writing a validation report.

bucket false_premise, condition distractor, judge reason: the draft did not build on the false premise

### sheet 15: owner CORRECT, judge WRONG (decided by judge)

question: Who wrote the original 1995 edition of NASA SP-6105?

reference: the handbook does not answer this question

draft: The passage does not specify who wrote the original 1995 edition of NASA SP-6105.

bucket unanswerable, condition with_evidence, judge reason: The passage does provide information relevant to answering the question.

### sheet 17: owner WRONG, judge CORRECT (decided by rules)

question: Because the Physical Configuration Audit has to be finished before the Functional Configuration Audit can begin, what documentation does the FCA verify the product against?

reference: the question's assumption is false; the handbook says: The handbook states the reverse order: the FCA precedes the PCA of the configured product, and the FCA checks test results against the functional baseline documentation approved at PDR and CDR.

draft: The passage does not provide information about what documentation the FCA verifies the product against.

bucket false_premise, condition with_evidence, judge reason: the draft did not build on the false premise


## Grade-only disagreements, same binary label (2)

- sheet 1: owner PARTIAL, judge WRONG; According to the handbook, what are Measures of Performance derived from?
- sheet 4: owner PARTIAL, judge WRONG; What characteristic makes a requirement count as a key driving requirement?
