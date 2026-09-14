# Post hoc: a second judge on the three blind sheets

A post hoc experiment, run after the tagged evaluation (v1.0.2). The 85 drafts on the three blind sheets were regraded with grader v13 unchanged and Mistral 7B Instruct (mistral:latest) as the judge in place of llama3.1 8B, and both judges were compared with the owner's hand labels. No test item was read and nothing was refit. The plan and the reading rule were committed before the first Mistral call (commit 1514552; docs/decisions.md, "Post hoc: a second judge"). The cause rule, the reading of answer lines with added words, and the two analysts were added after the run and are labelled where they appear. Every number comes from reports/post-hoc-second-judge.json.

Terms. Binary agreement counts CORRECT against PARTIAL or WRONG; three-way agreement needs the exact grade. 84 of the 85 drafts carry an owner label (sheet 1, draft 1 was never graded). A draft reaches a judge only when no code rule or exact match decides it first; both judges take the same route on every draft.

## Headline

On the final sheet, the only one never used to develop the rubric, llama3.1 agrees with the owner on 19 of 20, 95% [85, 100], and Mistral on 18 of 20, 90% [75, 100]. By the rule fixed before the run, a result within one draft of llama3.1 counts as agreeing about as well, so Mistral agrees **about as well**. That supports the claim that the rubric carried the agreement more than the choice of judge.

That support is thin in two ways. Only 9 of the 20 final-sheet drafts reach a judge; the other 11 get the same grade under either judge by construction, and on the 9 that do, llama3.1 agrees with the owner on 8 and Mistral on 7. And the prompts, the answer parser and the copy-the-words check were all built with llama3.1 as the judge, so even this sheet carries some general advantage for llama3.1.

Across all 84 labelled drafts llama3.1 agrees on 81, 96% [92, 100], and Mistral on 77, 92% [86, 96]: four drafts apart, a paired difference of +4.8 points [+1.2, +9.5], an interval that excludes zero. Mistral agreed less on every sheet, by 1, 1 and 2 drafts. Three of Mistral's four extra errors are on sheets 1 and 2, where the rubric was tuned with llama3.1 in the loop, so the pooled gap mixes that home advantage with any real difference between the judges, and these drafts cannot separate the two. On the 35 judged drafts alone, llama3.1 agrees on 33 and Mistral on 29.

Of the 85 drafts, 50 are decided by code rules or exact match and get the same grade under either judge. Only 35 reach a judge, so a judge swap can move at most that many grades.

## Where the errors fall

On the final sheet the two judges share one error (draft 10), and Mistral has one error of its own (draft 5). Over all three sheets Mistral also misgrades every draft llama3.1 misgrades (3 of 3) and adds four errors of its own, while llama3.1 has no errors of its own. That llama3.1 has none is expected on sheets 1 and 2, where the rubric was revised until its disagreements there were fixed.

Two analysts assigned a cause to each of these 7 drafts, blind to this report, the script's rule and each other. They agreed with each other on every draft. A cause rule written into the script after the run agrees with them on 5 of the 7, counting sheet 1, draft 34 as agreement: the rule names the code rule that decided it, the analysts name the label the owner later changed, and both are true. Where the two differ, this report goes with the analysts. They read the drafts and the replies; the rule reads only flags and answers, assumes that an error both judges make belongs to the rubric, and cannot tell a defensible answer from a wrong one.

| sheet | draft | misgraded by | cause, two blind analysts | cause, rule written after the run |
|---|---|---|---|---|
| final | 5 | Mistral only | the copy check removed a YES the judge had right | the copy check removed a YES the judge had right |
| final | 10 | both | the judge's own yes or no answers were wrong | shared by both judges, so the rubric or question wording |
| sheet1 | 8 | Mistral only | order sensitivity: the stricter of two differing orders was kept | order sensitivity |
| sheet1 | 34 | both | the owner later changed this blind label | a code rule decided it |
| sheet2 | 2 | Mistral only | the judge's own yes or no answers were wrong | the judge's own answers |
| sheet2 | 4 | Mistral only | the rubric or question wording: the judge's answers were defensible | the judge's own answers |
| sheet2 | 10 | both | the rubric or question wording: the judge's answers were defensible | shared by both judges, so the rubric or question wording |

So an error both judges make is not always the rubric's. One shared error (final, draft 10) is a judging mistake the two judges happen to share, which may be a limit of judges this size rather than of either one. And one of Mistral's own errors (sheet2, draft 4) is the rubric's. Both analysts found Mistral's answers defensible and traced the owner's PARTIAL to padding the draft adds to a right answer, which no judge question asks about and the code's unsupported-claim check, looking only for outside names and acronyms, does not catch; llama3.1 matched the owner's binary label only by grading the draft WRONG.

## Final sheet: the clean comparison

Twenty real agent outputs from dev, drawn for the final blind check after grader v13 was frozen, and graded by the owner without seeing either judge. No rubric change was made against this sheet. The prompts, parser and copy-the-words check were still built with llama3.1 as the judge, so some general advantage for llama3.1 remains even here.

| measure | llama3.1 | Mistral |
|---|---|---|
| binary agreement with the owner, 20 labelled drafts | 19 of 20, 95% [85, 100] | 18 of 20, 90% [75, 100] |
| binary agreement on the 9 labelled drafts that reach a judge | 8 of 9 | 7 of 9 |
| three-way agreement with the owner | 18 of 20 | 17 of 20 |
| drafts whose two answer orders gave different grades | 0 | 1 |
| YES answers removed by the copy check, counted per question per answer order | 2 | 5 |
| unreadable judge replies | 0 | 0 |

- Paired difference, llama3.1 minus Mistral: one draft, +5.0 points [0.0, +15.0].
- The two judges give the same binary grade on 19 of the 20 drafts, and on 8 of the 9 that reach a judge (8 of 9 on the exact grade). Both judges took the same route, code rule, exact match or judge, on every draft.
- Misgraded against the owner: llama3.1 draft 10; Mistral drafts 5 and 10; both draft 10.
- Keeping the stricter of two answer orders, where the orders disagreed, cost llama3.1 0 and saved it 0 binary agreements; for Mistral it cost 0 and saved 0.
- No unreadable replies on this sheet.

| draft | bucket | owner | llama3.1 | Mistral | question |
|---|---|---|---|---|---|
| 5 | ambiguous | CORRECT | CORRECT | PARTIAL | When in the life cycle is the Technology Maturity Assessment carried out? |
| 10 | false_premise | CORRECT | WRONG | WRONG (orders differed) | The handbook's definition of life cycle cost leaves out the launch vehicle; where does it say the launch cost should be accounted for instead? |

## Sheet 1: home advantage for llama3.1

Home advantage: grader versions v8 to v13 were developed against this sheet's disagreements with llama3.1 as the judge, so llama3.1's figures below are rubric fidelity, not a blind number. Its blind figure on this sheet, under v7, was 32 of 39. Mistral had no part in that development.

| measure | llama3.1 | Mistral |
|---|---|---|
| binary agreement with the owner, 39 labelled drafts | 38 of 39, 97% [92, 100] | 37 of 39, 95% [87, 100] |
| binary agreement on the 16 labelled drafts that reach a judge | 16 of 16 | 15 of 16 |
| three-way agreement with the owner | 35 of 39 | 34 of 39 |
| drafts whose two answer orders gave different grades | 0 | 4 |
| YES answers removed by the copy check, counted per question per answer order | 14 | 15 |
| unreadable judge replies | 0 | 0 |

- Paired difference, llama3.1 minus Mistral: one draft, +2.6 points [0.0, +7.7].
- The two judges give the same binary grade on 39 of the 40 drafts, and on 15 of the 16 that reach a judge (15 of 16 on the exact grade). Both judges took the same route, code rule, exact match or judge, on every draft.
- Misgraded against the owner: llama3.1 draft 34; Mistral drafts 8 and 34; both draft 34.
- Keeping the stricter of two answer orders, where the orders disagreed, cost llama3.1 0 and saved it 0 binary agreements; for Mistral it cost 1 and saved 1.
- No unreadable replies on this sheet.
- Secondary line, with the owner's later label change applied (draft 34, PARTIAL to CORRECT): llama3.1 39 of 39, Mistral 38 of 39.

| draft | bucket | owner | llama3.1 | Mistral | question |
|---|---|---|---|---|---|
| 8 | unanswerable | CORRECT | CORRECT | PARTIAL (orders differed) | Which commercial software package does the handbook recommend purchasing for configuration status accounting? |
| 34 | unanswerable | PARTIAL | CORRECT | CORRECT | Which commercial space flight mishaps supplied the lessons learned that fed the Office of the Chief Engineer's systems engineering initiative? |

## Sheet 2: home advantage for llama3.1

Home advantage: the v11 to v13 fixes were made after reading this sheet's disagreements with llama3.1 as the judge, so llama3.1's figures below are rubric fidelity, not a blind number. Its blind figure on this sheet, under v10, was 20 of 25. Mistral had no part in that development.

| measure | llama3.1 | Mistral |
|---|---|---|
| binary agreement with the owner, 25 labelled drafts | 24 of 25, 96% [88, 100] | 22 of 25, 88% [72, 100] |
| binary agreement on the 10 labelled drafts that reach a judge | 9 of 10 | 7 of 10 |
| three-way agreement with the owner | 19 of 25 | 18 of 25 |
| drafts whose two answer orders gave different grades | 2 | 2 |
| YES answers removed by the copy check, counted per question per answer order | 7 | 6 |
| unreadable judge replies | 0 | 1 |

- Paired difference, llama3.1 minus Mistral: two drafts, +8.0 points [0.0, +20.0].
- The two judges give the same binary grade on 23 of the 25 drafts, and on 8 of the 10 that reach a judge (7 of 10 on the exact grade). Both judges took the same route, code rule, exact match or judge, on every draft.
- Misgraded against the owner: llama3.1 draft 10; Mistral drafts 2, 4 and 10; both draft 10.
- Keeping the stricter of two answer orders, where the orders disagreed, cost llama3.1 0 and saved it 0 binary agreements; for Mistral it cost 0 and saved 0.
- Mistral had one unreadable reply here, graded WRONG by the grader's rule. A diagnostic regrade of those drafts with a lenient reading and a 600-token cap, not part of the headline, gives Mistral 22 of 25.

| draft | bucket | owner | llama3.1 | Mistral | question |
|---|---|---|---|---|---|
| 2 | answerable | WRONG | WRONG | CORRECT | NPR 7123.1 groups its common technical processes into three sets. What are they? |
| 4 | answerable | PARTIAL | WRONG | CORRECT | What characteristic makes a requirement count as a key driving requirement? |
| 10 | ambiguous | CORRECT | WRONG (orders differed) | PARTIAL | After an end product is built, what does it have to be shown to satisfy before it moves on? |

## Unreadable replies: task or format

Mistral's strict pass made 70 judge calls; the parser read 69. None stopped at the 200-token cap. Every reply is kept verbatim in reports/post-hoc-second-judge/mistral-calls.jsonl. There was only one unreadable reply, so the handful asked for is this one:

sheet2, draft 5, second answer order, 78 tokens, stopped normally:

```
REASON: The candidate does not directly address the assumption but provides information that contradicts it.
Q1: NO
Q2: Implicitly, as they provide information that contradicts the assumption without explicitly stating it.
Q3: Yes, in a way, as their answer suggests that the systems engineer focuses on different tasks than what was assumed in the question.
```

It commits to NO on Q1, qualifies Q3 as "Yes, in a way", and gives Q2 no yes or no at all, only "Implicitly". The grader needs an answer to every question, so the draft was graded WRONG. The code's category is a task failure, not a format failure: a lenient reading that strips formatting still finds no answer to Q2, and the diagnostic regrade at 600 tokens got the same reply. Three readers who saw only the questions and the reply, blind to the code, all called it a task failure.

How each judge wrote its answer lines over the same drafts, one row per kind of line:

| answer line | llama3.1 | Mistral |
|---|---|---|
| YES or NO with added words, in capitals | 0 | 17 |
| YES or NO with added words, not all capitals | 0 | 3 |
| bare YES or NO, in capitals | 196 | 173 |
| bare YES or NO, not all capitals | 0 | 2 |

Three blind readers also read the 19 parsed Mistral answer lines that carry added words, a check added after the run. By majority 18 are clear, the added words backing the YES or NO given, and one is contradictory: sheet1, draft 4, "Q2: No, the candidate does not state that the handbook does not contain the answer or could not find one. Instead, they acknowledge that the handbook does not answer the question directly." The parser read the stated answer there, and the owner and both judges graded that draft the same. The readers split on one line: sheet2, draft 5 (clear, hedged, clear).

What each judge's copy-the-words replies did, one row per kind of reply, counted per call:

| copy reply | llama3.1 | Mistral |
|---|---|---|
| copied words found in the draft | 30 | 37 |
| echoed the instruction's own phrase | 1 | 7 |
| copied words not found in the draft | 8 | 2 |
| NONE, or nothing usable | 11 | 8 |

Mistral did not fail on format. Its replies parsed under llama3.1's conventions 69 times in 70, and the one reply that did not failed the task, not the format. The harness still carried llama3.1's conventions, and they cost Mistral, through the copy check rather than the parser. That instruction quotes the phrase it wants found, and Mistral echoed the phrase back instead of copying the draft's words on seven calls, against llama3.1's one. On one draft (final, draft 5) that echo removed a YES Mistral had right and cost the grade. A judge swap is not free: a harness built around the first judge's habits turns a second judge's different habits into errors the first judge never makes. Mistral's grade also changed with the answer order more often, on 1, 4 and 2 drafts across the final sheet and sheets 1 and 2, against llama3.1's 0, 0 and 2; the gap sits mostly on sheet 1, where the rubric was tuned with llama3.1. Keeping the stricter order cost Mistral one binary agreement and saved it one, so on these drafts the order sensitivity did not change its agreement with the owner.

## Cost

One pass, one model: the run read Ollama's loaded models after every draft and would have stopped if any model other than Mistral had been loaded, and it finished normally. Wall clock 719 s. The strict pass made 70 judge calls and 54 copy-the-words calls, 13 of which repeated the identical request from the other answer order and came from the cache; the diagnostic pass made 2 judge calls and 1 copy call. Live calls took a median 6.1 s, 90th percentile 10.49 s, with a median 34 output tokens, 90th percentile 59. llama3.1's grades were replayed from the cache: all 85 matched the committed grades exactly, over 120 calls, none of them live.

## Independent checks

- A verifier, blind to this report and the script, recomputed each sheet's draft, label and judged counts, both judges' binary agreement with the owner, the judges' agreement with each other, the misgraded draft numbers and the unreadable count from the raw files with its own code. Every number matched.
- Three readers classified the unreadable reply (planned before the run) and the answer lines with added words (added after the run), blind to the code.
- Two analysts assigned causes to every misgraded draft, blind to the report, the rule and each other (added after the run).
- A critic reviewed the first rendering of this report against the owner's requirements and found 26 defects (reports/post-hoc-second-judge/critic-review.json). The most serious was a bug in the echo count: a pattern that required a colon missed the instruction shape "give \"X\" as the answer", so the first rendering said Mistral and llama3.1 echoed equally often and that echoing was not a Mistral habit. The corrected count is the one above, the pattern has a test, and every other defect is addressed in this version.

