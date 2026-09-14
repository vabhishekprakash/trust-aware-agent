# Dev run v1, untuned

Agent: qwen2.5:3b-instruct, k=8, no retrieval-score abstain rule (unset in this run and dropped after it), trace trace-v1. Graded by grader-v13 with judge llama3.1:latest. 100 dev items; the test split was not read. The ambiguous bucket has 9 dev items, so its numbers are indicative only.

Items were drafted and verified by language model agents and graded by a language model judge; human checks so far are the two blind samples recorded in the annotation guide. Every count below comes from reports/dev-run-v1.jsonl.

## Actions per bucket

| bucket | n | ANSWER | CLARIFY | ABSTAIN |
|---|---|---|---|---|
| answerable | 46 | 35/46 (76%) | 6/46 (13%) | 5/46 (11%) |
| ambiguous | 9 | 7/9 (78%) | 2/9 (22%) | 0/9 (0%) |
| unanswerable | 25 | 0/25 (0%) | 1/25 (4%) | 24/25 (96%) |
| false_premise | 20 | 12/20 (60%) | 0/20 (0%) | 8/20 (40%) |
| all | 100 | 54/100 (54%) | 9/100 (9%) | 37/100 (37%) |

Which path fired, over all items (an item can show both a clarify and an abstain path; CLARIFY wins):

- ABSTAIN by prompt: 39
- CLARIFY by rule: 9

## False-clarify rate on answerable items

- CLARIFY action on answerable items: 6/46 (13%). The owner's bar is about a fifth.
- Readings step fired (the rule): 6/46 (13%); the model's own clarifying question (prompt): 0/46 (0%).
- Readings listed on answerable items: n=46 min 1.000 p25 1.000 med 1.000 p75 1.000 max 2.000 (count per item).
- What the draft behind those CLARIFYs would have scored: CORRECT 5, PARTIAL 1, WRONG 0.
- Items where a listed 'answer' was the words ONE READING, a format slip the parser took as a reading: 1 (q0082). Without them the rate is 5/46 (11%). The parser was fixed after this run and the run was not repeated, so the measured rate is the higher one and the real rate is nearer the lower.
- The readings the model listed on those items:
  - q0009: What does the handbook call the events where the decision authority decides whether a program or project is ready to move into the next life-cycle phase?
    - The readiness of a project's flight system to execute critical events during flight operation => Event Readiness Review
    - An event at which the decision authority determines the readiness of a program/project to progress to the next phase of the life cycle (or to the next KDP) => Key Decision Point
  - q0032: Into how many steps does the handbook break the validation of technical requirements?
    - The handbook breaks validation of technical requirements into six steps => SIX
    - The handbook breaks validation of technical requirements into seven steps => SEVEN
  - q0046: In the comparison of verification and validation testing, which document does validation testing trace back to?
    - Validation relates back to the ConOps document. => The ConOps document
    - Verification relates back to the approved requirements set. => The approved requirements set
  - q0049: When verifying a product, what is the main thing that sets a demonstration apart from a test?
    - Different focus on behavioral capability => Demonstration: Showing stakeholder expectations are met through basic confirmation of behavior, differentiated by lack of detailed data gathering.
    - Use of physical models or mock-ups for validation => Testing involves final end products; demonstration can involve physical models or mock-ups to validate conditions like readability under specific circumstances.
  - q0074: At the successful completion of which review is the allocated baseline normally set?
    - At successful completion of PDR => Passage 2
    - At successful completion of SDR => Passage 3
  - q0082: A Production Readiness Review is held when a project is building or buying more than how many similar systems?
    - The project is developing or acquiring multiple systems greater than three. => MORE THAN ONE
    - Reading 1: The project is building or buying more than one system. => ONE READING
- For contrast, CLARIFY on ambiguous items: 2/9 (22%), readings fired 2/9 (22%).

## Calculator lines

- Spurious CALC lines on non-calculator items: 7/96 (7%) (q0043, q0089, q0174, q0196, q0229, q0235, q0236).
- CALC lines on the calculator items: 3/4 (75%); calculator items in dev: 4.
- Items whose CALC line could not be computed: 7 (q0022, q0043, q0089, q0174, q0229, q0235, q0236).
  - q0022: calc [('100 - 0; The handbook does not say.', None)], action ABSTAIN, grade WRONG, evidence not retrieved.
  - q0073: calc [('5 - 1', '4')], action ANSWER, grade WRONG, evidence retrieved.
  - q0082: calc [], action CLARIFY, grade WRONG, evidence not retrieved.
  - q0083: calc [('34 - 0', '34')], action ANSWER, grade CORRECT, evidence retrieved.

## Grades per bucket

| bucket | n | CORRECT | PARTIAL | WRONG | decided by rules/exact/judge |
|---|---|---|---|---|---|
| answerable | 46 | 29/46 (63%) | 2/46 (4%) | 15/46 (33%) | 10/16/20 |
| ambiguous | 9 | 2/9 (22%) | 3/9 (33%) | 4/9 (44%) | 1/0/8 |
| unanswerable | 25 | 23/25 (92%) | 1/25 (4%) | 1/25 (4%) | 22/0/3 |
| false_premise | 20 | 0/20 (0%) | 6/20 (30%) | 14/20 (70%) | 6/0/14 |

Flagged by the grader (order disagreement or unparsed): 6 (q0013, q0037, q0087, q0126, q0131, q0134).

## Accuracy split by whether the evidence was retrieved

Evidence retrieved means a chunk that covers the evidence page and contains the quote was among the k hits (the same rule as the recall measurement). Items whose quote was not found in any chunk are excluded from the split and counted.

| bucket | evidence retrieved: correct/n | not retrieved: correct/n | no target chunk |
|---|---|---|---|
| answerable | 27/38 (71%) | 2/8 (25%) | 0 |
| ambiguous | 2/8 (25%) | 0/1 (0%) | 0 |
| unanswerable | 13/14 (93%) | 10/11 (91%) | 0 |
| false_premise | 0/17 (0%) | 0/3 (0%) | 0 |
| all | 42/77 (55%) | 12/23 (52%) | 0 |

Evidence rank on answerable items when retrieved: n=38 min 1.000 p25 1.000 med 1.000 p75 2.000 max 6.000.

## Building on a false premise

- Judge said the response builds on the premise (grounded, either order): 14/20 (70%).
- Graded WRONG on false-premise items: 14/20 (70%); PARTIAL 6; CORRECT 0.
- Actions on false-premise items: ANSWER 12, CLARIFY 0, ABSTAIN 8.

## Grader notes

- q0107: the rule's composed CLARIFY was graded CORRECT by the judge, whose answers to 'asks which reading is meant' were []. Response: Do you mean Systems engineer at topmost level of project, or Systems engineer working three or four levels down in PBS?
- q0126: the rule's composed CLARIFY was graded WRONG by the judge, whose answers to 'asks which reading is meant' were [False, False]. Response: Do you mean The readiness review shows system is ready for flight or launch and subsequent operations, or The readiness review confirms the project’s readiness to execute mission critical activities during flight operation?
- The guide grades a CLARIFY that names the two readings CORRECT. The judge did not read the composed question as asking which reading is meant. A code rule for that case is a grader change and needs the 21 examples and both rubric-fidelity sheets rerun before it is used; these grades stand as v12 gave them.

## Regrade: grader-v12 against grader-v13 on the same traces

Same drafts, same actions; only the grader changed. grader-v12 numbers are kept here, labelled, next to grader-v13.

| bucket | n | grader-v12 CORRECT / PARTIAL / WRONG | grader-v13 CORRECT / PARTIAL / WRONG | items changed |
|---|---|---|---|---|
| answerable | 46 | 29 / 2 / 15 | 29 / 2 / 15 | 0 |
| ambiguous | 9 | 1 / 3 / 5 | 2 / 3 / 4 | 1 |
| unanswerable | 25 | 23 / 1 / 1 | 23 / 1 / 1 | 0 |
| false_premise | 20 | 0 / 6 / 14 | 0 / 6 / 14 | 0 |

Items whose grade changed: 1; binary label flips: 1.
- q0107 (ambiguous, CLARIFY): WRONG -> CORRECT, decided by judge then rules. Response: Do you mean Systems engineer at topmost level of project, or Systems engineer working three or four levels down in PBS?

## Best retrieval score, for choosing the abstain threshold

Nothing was tuned in this run. Per bucket, then by grade label among items where the agent answered.

- answerable: n=46 min 0.647 p25 0.723 med 0.751 p75 0.795 max 0.863
- ambiguous: n=9 min 0.650 p25 0.720 med 0.724 p75 0.751 max 0.779
- unanswerable: n=25 min 0.612 p25 0.670 med 0.711 p75 0.748 max 0.793
- false_premise: n=20 min 0.673 p25 0.736 med 0.755 p75 0.783 max 0.800
- answered and CORRECT: n=30 min 0.647 p25 0.721 med 0.755 p75 0.815 max 0.842
- answered and not CORRECT: n=24 min 0.650 p25 0.724 med 0.752 p75 0.782 max 0.863
- evidence retrieved: n=77 min 0.630 p25 0.722 med 0.748 p75 0.782 max 0.863
- evidence not retrieved (has target): n=23 min 0.612 p25 0.692 med 0.727 p75 0.751 max 0.784

## Wall clock

- Agent run: 1800 s for 100 items, 18.0 s per item; started 2026-09-10T15:10:06+00:00.
- By step: draft 886 s (49%), readings 881 s (49%), draft_after_calc 30 s (2%), retrieval 4 s (0%).
- Calls served from the cache: {'readings': 8, 'draft': 8, 'draft_after_calc': 2}.
- Grading: 1 s, decided by {'judge': 45, 'rules': 39, 'exact': 16}.
- Grading under v12 was cut off by a session end at 51 items and a dropped connection at 52, and the cache replayed those items, so no clean grading time exists; the v13 regrade ran from the cache in a second.
