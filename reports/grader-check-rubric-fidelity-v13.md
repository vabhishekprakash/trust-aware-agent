# Grader check: rubric fidelity

This is NOT a blind number. The owner graded the sheet blind once; that figure stands in
reports/grader-check-result.md. Here the grader was changed after the owner's rulings and run
again on the same drafts, and the owner's grades for sheet numbers 34 are the
ones the owner revised on seeing the disagreements. The figure measures how faithfully the
fixed grader follows the rubric the owner settled, on drafts the fix was designed against.

Grader grader-v13, judge llama3.1:latest, drafts by the model under test.

- drafts graded by the owner: 39 of 40 (no grade written for sheet numbers 1)
- binary label agreement (CORRECT against not CORRECT): 39 of 39 (100 percent)
- three-way grade agreement: 36 of 39 (92 percent)
- binary agreement per bucket: ambiguous 3 of 3, answerable 19 of 19, false_premise 4 of 4, unanswerable 13 of 13
- binary agreement per draft condition: distractor 13 of 13, no_passage 13 of 13, with_evidence 13 of 13

Owner grade to judge grade counts:

    CORRECT  -> CORRECT  16
    PARTIAL  -> PARTIAL  3
    WRONG    -> PARTIAL  3
    WRONG    -> WRONG    17

## Binary disagreements (0)

None.

## Grade-only disagreements, same binary label (3)

- sheet 9: owner WRONG, judge PARTIAL; The handbook wants technology assessment to keep running from concept development all the way through the Critical Design Review. Where does it say the technology development lessons learned should be captured after that point?
- sheet 16: owner WRONG, judge PARTIAL; The handbook lists five key steps for carrying out functional analysis when decomposing requirements. What does the fifth step involve?
- sheet 33: owner WRONG, judge PARTIAL; Since the OCE is the approver for a waiver requested by a project whose responsibility was delegated to a Center, where should the project record the approved tailoring afterwards?
