# Dev run v1, untuned

Agent: qwen2.5:3b-instruct, k=8, no retrieval-score abstain rule (unset in this run and dropped after it), trace trace-v2. Graded by grader-v13 with judge llama3.1:latest. 100 dev items; the test split was not read. The ambiguous bucket has 9 dev items, so its numbers are indicative only.

Items were drafted and verified by language model agents and graded by a language model judge; human checks so far are the two blind samples recorded in the annotation guide. Every count below comes from reports/dev-run-v1.jsonl.

## Actions per bucket

| bucket | n | ANSWER | REJECT | CLARIFY | ABSTAIN |
|---|---|---|---|---|---|
| answerable | 46 | 29/46 (63%) | 6/46 (13%) | 4/46 (9%) | 7/46 (15%) |
| ambiguous | 9 | 4/9 (44%) | 5/9 (56%) | 0/9 (0%) | 0/9 (0%) |
| unanswerable | 25 | 1/25 (4%) | 4/25 (16%) | 1/25 (4%) | 19/25 (76%) |
| false_premise | 20 | 9/20 (45%) | 4/20 (20%) | 0/20 (0%) | 7/20 (35%) |
| all | 100 | 43/100 (43%) | 19/100 (19%) | 5/100 (5%) | 33/100 (33%) |

Which path fired, over all items (an item can show both a clarify and an abstain path; CLARIFY wins):

- ABSTAIN by prompt: 45
- CLARIFY by rule: 7
- REJECT by rule: 19

## False-clarify rate on answerable items

- CLARIFY action on answerable items: 4/46 (9%). The owner's bar is about a fifth.
- Readings step fired (the rule): 5/46 (11%); the model's own clarifying question (prompt): 0/46 (0%).
- Readings listed on answerable items: n=46 min 0.000 p25 0.000 med 1.000 p75 1.000 max 2.000 (count per item).
- What the draft behind those CLARIFYs would have scored: CORRECT 4, PARTIAL 0, WRONG 0.
- Items where a listed 'answer' was the words ONE READING, a format slip the parser took as a reading: 0.
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
- For contrast, CLARIFY on ambiguous items: 0/9 (0%), readings fired 1/9 (11%).

## Premise step: false-fire rate

- REJECT on answerable and unanswerable items: 10/71 (14%) (answerable 6/46 (13%), unanswerable 4/25 (16%)). The owner's bar is about a fifth.
- The model claimed a contradiction on those items 34/71 (48%); the gate let 10 through.
- On false-premise items: claimed 8/20 (40%), gate passed and REJECT 4/20 (20%), of which graded CORRECT 0.
- Before this step existed (dev run v1) the false-premise bucket had 0 correct answers in 20.
  - false fire q0040 (answerable): The question assumes an example of an enabling product whose use would be acquired during the test phase of a space flight system. The handbook says Because of long development times as well as oversubscribed facilities, it is important to identify enabling products and secure the commitments for them as early in the design phase as possible (page 74).
  - false fire q0047 (answerable): The question assumes Certification is repeated on every flight unit rather than performed once for the design.. The handbook says The final, official verification of the end product should be on a controlled unit (page 256).
  - false fire q0074 (answerable): The question assumes At the successful completion of which review is the allocated baseline normally set?. The handbook says The allocated baseline is typically established at the successful completion of the PDR (page 146).
  - false fire q0090 (answerable): The question assumes Comments from which review need to be folded in before the Verification and Validation Plan is baselined. The handbook says Care should be exercised to ensure that the corrective actions identified to remove validation deficiencies do not conflict with the baselined stakeholder expectations without first coordinating such changes with the appropriate stakeholders (page 104).
  - false fire q0093 (answerable): The question assumes Who is responsible for designating the HSI integrator or team on a program or project?. The handbook says The party or parties responsible for program/project HSI implementation—e.g., an HSI integrator (or team)—should be identified by the program/project manager (page 244).
  - false fire q0119 (answerable): The question assumes all of a project's plans have to comply with. The handbook says any NPR requirements stating that the plans need to be stand-alone document would be too burdensome (page 37).
  - false fire q0147 (unanswerable): The question assumes The Space Shuttle Program flew its last mission.. The handbook says For smaller projects and activities, particularly with short life cycles (i.e., short mission durations), the closeout plans may be contained in the SEMP (page 33).
  - false fire q0163 (unanswerable): The question assumes How many months before the planned end of mission should the Decommissioning Review be scheduled?. The handbook says The DR is normally held near the end of routine mission operations upon accomplishment of planned mission objectives (page 32).
  - false fire q0170 (unanswerable): The question assumes There is a dollar cost cap on projects selected through an Announcement of Opportunity in an uncoupled program.. The handbook says For projects with a Life Cycle Cost (LCC) greater than $250 million, this commitment is made with the Congress and the U.S. Office of Management and Budget (OMB). This external commitment is the Agency Baseline Commitment (ABC) (page 179).
  - false fire q0183 (unanswerable): The question assumes Revision 2 of this handbook was issued by a specific individual serving as NASA Administrator. The handbook says This revision (Rev 2) of SP-6105 maintains that original philosophy while updating the Agency’s systems engineering body of knowledge, providing guidance for insight into current best Agency practices (page viii).

## Calculator lines

- Spurious CALC lines on non-calculator items: 6/96 (6%) (q0043, q0120, q0196, q0229, q0235, q0236).
- CALC lines on the calculator items: 3/4 (75%); calculator items in dev: 4.
- Items whose CALC line could not be computed: 7 (q0022, q0043, q0120, q0196, q0229, q0235, q0236).
  - q0022: calc [('100 - 50; nothing else', None)], action ANSWER, grade WRONG, evidence not retrieved.
  - q0073: calc [('5 - 1', '4')], action ANSWER, grade WRONG, evidence retrieved.
  - q0082: calc [], action ABSTAIN, grade CORRECT, evidence not retrieved.
  - q0083: calc [('34 - 0', '34')], action ANSWER, grade CORRECT, evidence retrieved.

## Grades per bucket

| bucket | n | CORRECT | PARTIAL | WRONG | decided by rules/exact/judge |
|---|---|---|---|---|---|
| answerable | 46 | 23/46 (50%) | 5/46 (11%) | 18/46 (39%) | 7/15/24 |
| ambiguous | 9 | 0/9 (0%) | 1/9 (11%) | 8/9 (89%) | 0/0/9 |
| unanswerable | 25 | 18/25 (72%) | 1/25 (4%) | 6/25 (24%) | 18/0/7 |
| false_premise | 20 | 0/20 (0%) | 6/20 (30%) | 14/20 (70%) | 6/0/14 |

Flagged by the grader (order disagreement or unparsed): 9 (q0013, q0037, q0044, q0093, q0120, q0131, q0134, q0236, q0238).

## Accuracy split by whether the evidence was retrieved

Evidence retrieved means a chunk that covers the evidence page and contains the quote was among the k hits (the same rule as the recall measurement). Items whose quote was not found in any chunk are excluded from the split and counted.

| bucket | evidence retrieved: correct/n | not retrieved: correct/n | no target chunk |
|---|---|---|---|
| answerable | 20/38 (53%) | 3/8 (38%) | 0 |
| ambiguous | 0/8 (0%) | 0/1 (0%) | 0 |
| unanswerable | 9/14 (64%) | 9/11 (82%) | 0 |
| false_premise | 0/17 (0%) | 0/3 (0%) | 0 |
| all | 29/77 (38%) | 12/23 (52%) | 0 |

Evidence rank on answerable items when retrieved: n=38 min 1.000 p25 1.000 med 1.000 p75 2.000 max 6.000.

## Building on a false premise

- Judge said the response builds on the premise (grounded, either order): 13/20 (65%).
- Graded WRONG on false-premise items: 14/20 (70%); PARTIAL 6; CORRECT 0.
- Actions on false-premise items: ANSWER 9, REJECT 4, CLARIFY 0, ABSTAIN 7.

## Grader notes


## Before: trace-v1 run graded by grader-v13

The earlier loop, kept for comparison and labelled; the tables above are the current loop. Different agent, different traces.

| bucket | n | ANSWER | REJECT | CLARIFY | ABSTAIN | correct (label 1) |
|---|---|---|---|---|---|---|
| answerable | 46 | 35/46 (76%) | 0/46 (0%) | 6/46 (13%) | 5/46 (11%) | 29/46 (63%) |
| ambiguous | 9 | 7/9 (78%) | 0/9 (0%) | 2/9 (22%) | 0/9 (0%) | 2/9 (22%) |
| unanswerable | 25 | 0/25 (0%) | 0/25 (0%) | 1/25 (4%) | 24/25 (96%) | 23/25 (92%) |
| false_premise | 20 | 12/20 (60%) | 0/20 (0%) | 0/20 (0%) | 8/20 (40%) | 0/20 (0%) |
| all | 100 | 54/100 (54%) | 0/100 (0%) | 9/100 (9%) | 37/100 (37%) | 54/100 (54%) |

Current loop, same layout:

| bucket | n | ANSWER | REJECT | CLARIFY | ABSTAIN | correct (label 1) |
|---|---|---|---|---|---|---|
| answerable | 46 | 29/46 (63%) | 6/46 (13%) | 4/46 (9%) | 7/46 (15%) | 23/46 (50%) |
| ambiguous | 9 | 4/9 (44%) | 5/9 (56%) | 0/9 (0%) | 0/9 (0%) | 0/9 (0%) |
| unanswerable | 25 | 1/25 (4%) | 4/25 (16%) | 1/25 (4%) | 19/25 (76%) | 18/25 (72%) |
| false_premise | 20 | 9/20 (45%) | 4/20 (20%) | 0/20 (0%) | 7/20 (35%) | 0/20 (0%) |
| all | 100 | 43/100 (43%) | 19/100 (19%) | 5/100 (5%) | 33/100 (33%) | 41/100 (41%) |

## Best retrieval score, for choosing the abstain threshold

Nothing was tuned in this run. Per bucket, then by grade label among items where the agent answered.

- answerable: n=46 min 0.647 p25 0.723 med 0.751 p75 0.795 max 0.863
- ambiguous: n=9 min 0.650 p25 0.720 med 0.724 p75 0.751 max 0.779
- unanswerable: n=25 min 0.612 p25 0.670 med 0.711 p75 0.748 max 0.793
- false_premise: n=20 min 0.673 p25 0.736 med 0.755 p75 0.783 max 0.800
- answered and CORRECT: n=22 min 0.647 p25 0.711 med 0.741 p75 0.779 max 0.841
- answered and not CORRECT: n=21 min 0.661 p25 0.723 med 0.750 p75 0.782 max 0.863
- evidence retrieved: n=77 min 0.630 p25 0.722 med 0.748 p75 0.782 max 0.863
- evidence not retrieved (has target): n=23 min 0.612 p25 0.692 med 0.727 p75 0.751 max 0.784

## Wall clock

- Agent run: 2842 s for 100 items, 28.4 s per item; started 2026-09-11T04:27:55+00:00.
- By step: premise 1492 s (53%), draft 1272 s (45%), draft_after_calc 74 s (3%), retrieval 3 s (0%), readings 1 s (0%).
- Calls served from the cache: {'premise': 3, 'readings': 100, 'draft': 3, 'draft_after_calc': 0}.
- Grading: 1404 s, decided by {'judge': 54, 'rules': 31, 'exact': 15}.
- One uninterrupted grading pass.
