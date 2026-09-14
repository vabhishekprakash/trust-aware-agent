# Dev run v1, untuned

Agent: qwen2.5:3b-instruct, k=8, no retrieval-score abstain rule (unset in this run and dropped after it), trace trace-v2. Graded by grader-v13 with judge llama3.1:latest. 34 dev items; the test split was not read. The ambiguous bucket has 0 dev items, so its numbers are indicative only.

Related: the labelled second dev run: the 34 reserve items, same loop as reports/dev-run-v1b.jsonl (premise check off).

Items were drafted and verified by language model agents and graded by a language model judge; human checks so far are the two blind samples recorded in the annotation guide. Every count below comes from reports/dev-run-v1.jsonl.

## Actions per bucket

| bucket | n | ANSWER | REJECT | CLARIFY | ABSTAIN |
|---|---|---|---|---|---|
| answerable | 16 | 9/16 (56%) | 0/16 (0%) | 1/16 (6%) | 6/16 (38%) |
| ambiguous | 0 | 0/0 | 0/0 | 0/0 | 0/0 |
| unanswerable | 9 | 0/9 (0%) | 0/9 (0%) | 0/9 (0%) | 9/9 (100%) |
| false_premise | 9 | 6/9 (67%) | 0/9 (0%) | 0/9 (0%) | 3/9 (33%) |
| all | 34 | 15/34 (44%) | 0/34 (0%) | 1/34 (3%) | 18/34 (53%) |

Which path fired, over all items (an item can show both a clarify and an abstain path; CLARIFY wins):

- ABSTAIN by prompt: 18
- CLARIFY by rule: 1

## False-clarify rate on answerable items

- CLARIFY action on answerable items: 1/16 (6%). The owner's bar is about a fifth.
- Readings step fired (the rule): 1/16 (6%); the model's own clarifying question (prompt): 0/16 (0%).
- Readings listed on answerable items: n=16 min 0.000 p25 0.000 med 1.000 p75 1.000 max 2.000 (count per item).
- What the draft behind those CLARIFYs would have scored: CORRECT 1, PARTIAL 0, WRONG 0.
- Items where a listed 'answer' was the words ONE READING, a format slip the parser took as a reading: 0.
- The readings the model listed on those items:
  - q0077: Who normally approves a change to project information that is held under configuration control?
    - The change is proposed by an Originator and reviewed by Propose reviewers => Configuration Control Board (CCB) or equivalent authority
    - The change is proposed by an Originator and reviewed by CM Function Reviewers => CCB or equivalent authority
- For contrast, CLARIFY on ambiguous items: 0/0, readings fired 0/0.

## Calculator lines

- Spurious CALC lines on non-calculator items: 1/34 (3%) (q0057).
- CALC lines on the calculator items: 0/0; calculator items in dev: 0.
- Items whose CALC line could not be computed: 1 (q0057).

## Grades per bucket

| bucket | n | CORRECT | PARTIAL | WRONG | decided by rules/exact/judge |
|---|---|---|---|---|---|
| answerable | 16 | 6/16 (38%) | 2/16 (12%) | 8/16 (50%) | 7/4/5 |
| ambiguous | 0 | 0/0 | 0/0 | 0/0 | 0/0/0 |
| unanswerable | 9 | 9/9 (100%) | 0/9 (0%) | 0/9 (0%) | 9/0/0 |
| false_premise | 9 | 0/9 (0%) | 2/9 (22%) | 7/9 (78%) | 2/0/7 |

Flagged by the grader (order disagreement or unparsed): 1 (q0031).

## Accuracy split by whether the evidence was retrieved

Evidence retrieved means a chunk that covers the evidence page and contains the quote was among the k hits (the same rule as the recall measurement). Items whose quote was not found in any chunk are excluded from the split and counted.

| bucket | evidence retrieved: correct/n | not retrieved: correct/n | no target chunk |
|---|---|---|---|
| answerable | 6/12 (50%) | 0/4 (0%) | 0 |
| ambiguous | 0/0 | 0/0 | 0 |
| unanswerable | 5/5 (100%) | 4/4 (100%) | 0 |
| false_premise | 0/9 (0%) | 0/0 | 0 |
| all | 11/26 (42%) | 4/8 (50%) | 0 |

Evidence rank on answerable items when retrieved: n=12 min 1.000 p25 1.000 med 1.000 p75 2.000 max 5.000.

## Building on a false premise

- Judge said the response builds on the premise (grounded, either order): 7/9 (78%).
- Graded WRONG on false-premise items: 7/9 (78%); PARTIAL 2; CORRECT 0.
- Actions on false-premise items: ANSWER 6, REJECT 0, CLARIFY 0, ABSTAIN 3.

## Grader notes


## Best retrieval score, for choosing the abstain threshold

Nothing was tuned in this run. Per bucket, then by grade label among items where the agent answered.

- answerable: n=16 min 0.621 p25 0.706 med 0.739 p75 0.773 max 0.810
- ambiguous: n=0
- unanswerable: n=9 min 0.589 p25 0.637 med 0.729 p75 0.751 max 0.760
- false_premise: n=9 min 0.739 p25 0.762 med 0.775 p75 0.821 max 0.854
- answered and CORRECT: n=6 min 0.688 p25 0.700 med 0.724 p75 0.773 max 0.809
- answered and not CORRECT: n=9 min 0.738 p25 0.739 med 0.766 p75 0.791 max 0.836
- evidence retrieved: n=26 min 0.670 p25 0.734 med 0.761 p75 0.784 max 0.854
- evidence not retrieved (has target): n=8 min 0.589 p25 0.609 med 0.711 p75 0.752 max 0.758

## Wall clock

- Agent run: 843 s for 34 items, 24.8 s per item; started 2026-09-11T05:54:07+00:00.
- By step: readings 435 s (52%), draft 402 s (48%), draft_after_calc 6 s (1%), retrieval 1 s (0%).
- Calls served from the cache: {'readings': 0, 'draft': 0, 'draft_after_calc': 0}.
- Grading: 364 s, decided by {'judge': 12, 'rules': 18, 'exact': 4}.
- One uninterrupted grading pass.
