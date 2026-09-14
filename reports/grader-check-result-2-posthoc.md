# Grader check: sheet 2 regraded by v12 after the owner's grades were seen (rubric fidelity, not blind)

The owner graded the drafts without seeing the judge; the judge's grades were held in a key file.

Grader grader-v12, judge llama3.1:latest, drafts by the model under test.

- drafts graded by the owner: 25 of 25
- binary label agreement (CORRECT against not CORRECT): 24 of 25 (96 percent)
- three-way grade agreement: 19 of 25 (76 percent)
- binary agreement per bucket: ambiguous 3 of 4, answerable 9 of 9, false_premise 6 of 6, unanswerable 6 of 6
- binary agreement per draft condition: distractor 8 of 8, no_passage 8 of 8, with_evidence 8 of 9

Owner grade to judge grade counts:

    CORRECT  -> CORRECT  6
    CORRECT  -> WRONG    1
    PARTIAL  -> WRONG    2
    WRONG    -> PARTIAL  3
    WRONG    -> WRONG    13

## Binary disagreements (1)

### sheet 10: owner CORRECT, judge WRONG (decided by judge, position_disagreement)

question: After an end product is built, what does it have to be shown to satisfy before it moves on?

reference: reading 1: Product Verification -> all of its specified requirements (page 90)
reference: reading 2: Product Validation -> stakeholder expectations (MOEs) in the intended operational environment (page 100)

draft: The end product has to be shown to satisfy its stakeholders' expectations within the intended operational environments before moving on.

bucket ambiguous, condition with_evidence, judge reason: judge grades differed by order (PARTIAL vs WRONG); stricter kept: The candidate does not clarify which reading is meant.


## Grade-only disagreements, same binary label (5)

- sheet 1: owner PARTIAL, judge WRONG; According to the handbook, what are Measures of Performance derived from?
- sheet 4: owner PARTIAL, judge WRONG; What characteristic makes a requirement count as a key driving requirement?
- sheet 13: owner WRONG, judge PARTIAL; Because the handbook treats an authorized waiver as a minor engineering change to the baseline, whose approval does it need when the waiver touches an external interface?
- sheet 14: owner WRONG, judge PARTIAL; The handbook breaks product validation into three major steps. Which of the three involves writing the validation report?
- sheet 17: owner WRONG, judge PARTIAL; Because the Physical Configuration Audit has to be finished before the Functional Configuration Audit can begin, what documentation does the FCA verify the product against?
