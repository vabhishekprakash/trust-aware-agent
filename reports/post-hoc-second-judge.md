# Post hoc: a second judge on the three blind sheets

A post hoc experiment, run after the tagged evaluation (v1.0.2). The 85 drafts on the three blind sheets were regraded with grader v13 unchanged and Mistral 7B Instruct (mistral:latest) as the judge in place of llama3.1 8B, and both judges were compared with the owner's hand labels. No test item was read and nothing was refit. The plan and the reading rule were committed before the first Mistral call (commit 1514552; docs/decisions.md, "Post hoc: a second judge"). Every number comes from reports/post-hoc-second-judge.json.

Who did what. The owner's hand labels are the only human judgement in this experiment. The two judges are language models. The readers, analysts, verifier, critic and reviewers named below are also language-model agents, not people, and are called model-run wherever they appear; they are not the human blind checks reported in the main report. Of these checks only one was planned before the run, the readers' classification of the unreadable reply. The cause rule, the readers' reading of answer lines with added words, the analysts, the verifier, the critic and the check of the owner's corrections were all added after it.

Terms. Binary agreement counts CORRECT against PARTIAL or WRONG; three-way agreement needs the exact grade. 84 of the 85 drafts carry an owner label. The owner did grade sheet 1, draft 1, CORRECT like both judges. Its grade line is indented and the sheet reader skips it, so it counts as unlabelled here, as in every earlier figure for that sheet. A draft reaches a judge only when no code rule or exact match decides it first; both judges take the same route on every draft.

## Headline

At this size the experiment cannot separate a real difference between the judges from the advantage the harness gives llama3.1. Judge choice measurably mattered: across the 84 labelled drafts llama3.1 agrees with the owner on 81, 96% [92, 100], and Mistral on 77, 92% [86, 96], a paired difference of +4.8 points [+1.2, +9.5] that excludes zero. What the experiment cannot say is how much of that gap belongs to Mistral and how much to llama3.1's home advantage. Three of Mistral's four extra errors fall on sheets 1 and 2, where the rubric was tuned with llama3.1 as the judge. The fourth, on the final sheet, was taken by the copy-the-words check, a harness step built and tuned with llama3.1 as the only judge (see Harness lock-in).

The overlap supports a weaker claim, and no more. Mistral also misgrades every draft llama3.1 misgrades against the owner (3 of 3). But one of the three (sheet1, draft 34) was decided by a code rule before any judge saw it, so the two share it by construction, and the owner later changed that label. The other two reached a judge, and both recur under Mistral. So llama3.1's judged errors are not peculiar to llama3.1: they recur under an independently trained judge on the same rubric and harness. That does not show the rubric is sound, since Mistral makes errors llama3.1 does not. Nor does it show that the shared errors are the rubric's; by the model-run analysts' reading, one of the two is a judging mistake both judges make.

The reading rule fixed before the run was applied as written. On the final sheet, the only one never used to develop the rubric, llama3.1 agrees on 19 of 20, 95% [85, 100], and Mistral on 18 of 20, 90% [75, 100]; within one draft, so the rule reads **about as well**. The rule was written to take that as support for rubric over model. This report departs from that reading, a choice the owner made after seeing the results. The rule looks at twenty drafts while the pooled interval above excludes zero. And only 9 of those 20 drafts reach a judge at all (llama3.1 8 of 9, Mistral 7 of 9). The other 11 get the same grade under either judge by construction.

Of the 85 drafts, 50 are decided by code rules or exact match and get the same grade under either judge. Only 35 reach a judge, so a judge swap can move at most that many grades. On those 35 labelled drafts llama3.1 agrees on 33 and Mistral on 29.

## Harness lock-in: the copy check carries the first judge's habits

The grader does not take a judge's YES on trust. It asks the judge to copy the words that back the YES and checks that they are there. For every question but the one about leaving something out, they must be in the draft; for that one, in the reference. A YES whose copied words cannot be found is turned into NO. For some questions the instruction quotes the phrase it wants found, for example: Copy the exact words in the text that give "just prior to the PDR" as the answer, in any wording. The check, its instructions and the parser that reads the reply were built and tuned with llama3.1 as the only judge.

| copy reply, counted per call | llama3.1 | Mistral |
|---|---|---|
| copied words found in the text checked | 30 | 37 |
| gave back the phrase the instruction quotes, not in the text | 0 | 3 |
| NONE, quoting a phrase in its explanation | 0 | 4 |
| other copied words not found in the text | 9 | 2 |
| NONE, or nothing usable | 11 | 8 |

The text checked is the draft, or the reference for the leaves-out question. Only two kinds of instruction quote a phrase to find: give "X" as the answer, and state this correction: "X". The other copy calls quote nothing, the question, the draft, or an answer the copied words must go against. Counted by distinct request, Mistral met seven instructions that quote a phrase to find, and llama3.1 met two. Mistral gave the quoted phrase back as its copy on two of its seven (final draft 5, twice; sheet2 draft 20). The repeat is the identical request from the other answer order, served from the cache. llama3.1 did so on neither of its two. The two judges met the same such request twice: on final draft 5 llama3.1 copied and Mistral gave the phrase back; on sheet2 draft 10 both copied.

An echo is not in the draft whenever the draft words the answer differently, so the check strikes the YES even when the judge was right. On final draft 5 that is what happened. The instruction asked for the words that give "just prior to the PDR" as the answer. llama3.1 copied the draft's own words, "Just prior to the Preliminary Design Review (PDR)". Mistral replied "just prior to the PDR", the instruction's phrase, which the draft does not contain. The check struck Mistral's YES, and its grade fell to PARTIAL, where llama3.1 and the owner have CORRECT. The echo on sheet2 draft 20 did no harm. The draft reads: "The NASA Systems Engineering Handbook states that while the project plan is a subordinate document to the System Engineering Management Plan (SEMP), it can define specific project-specific tasks and activities not covered by the broader SEMP." It accepts the question's premise and never states the correction, so there were no words to copy. The check was right to strike the YES, and Mistral's grade there agrees with the owner's.

On four more calls (sheet1 draft 38, twice; sheet2 draft 9; sheet2 draft 10) Mistral replied NONE and quoted the phrase in its explanation. One of them reads: NONE (The given text does not contain the phrase "Operational Readiness Review (ORR)".) The grader's parser looks for a quoted phrase before it looks for NONE, so it reads such a reply as a copy of that phrase. None of these phrases was in the text, so the result was the same as a plain NONE. llama3.1 wrote no reply of this kind.

This is the most transferable finding in the experiment, and it rests on little: one request and one grade, with the habit behind it seen on two. A verification step that quotes its target inside the prompt passes a judge that copies from the text and fails a judge that gives the prompt's phrase back, whenever the text words the target differently. A harness built with one judge encodes that judge's habits as if they were the task, and a second judge's different habits then show up as errors the first judge never makes. Swapping the judge in a grader like this one is not free, and the parse rate does not show the cost: Mistral's judge replies parsed 69 times in 70. Whether an instruction that does not quote the target would remove the effect was not tested.

A second harness rule, keeping the stricter of two answer orders, met a second difference between the judges. Mistral's grade changed with the answer order on 1, 4 and 2 drafts across the final sheet and sheets 1 and 2, against llama3.1's 0, 0 and 2; the gap sits mostly on sheet 1, where the rubric was tuned with llama3.1. Here the rule cost Mistral one binary agreement and saved it one, so on these drafts it did not change Mistral's agreement with the owner.

## Where the errors fall

On the final sheet the two judges share one error (draft 10), and Mistral has one error of its own (draft 5). Over all three sheets Mistral also misgrades every draft llama3.1 misgrades (3 of 3), and one of those was decided by a code rule before any judge saw it. Mistral adds four errors of its own, while llama3.1 has no errors of its own. That llama3.1 has none is expected on sheets 1 and 2, where the rubric was revised until its disagreements there were fixed.

Two model-run analysts (language-model agents, not people) assigned a cause to each of these 7 drafts. Each read only the committed records, call logs, owner sheets and grader source, without seeing this report, the script's rule or the other analyst. They agreed with each other on every draft. A cause rule written into the script after the run agrees with them on 5 of the 7, counting sheet 1, draft 34 as agreement: the rule names the code rule that decided it, the analysts name the label the owner later changed, and both are true. Where the two differ, this report goes with the analysts. They read the drafts and the replies; the rule reads only flags and answers, assumes that an error both judges make belongs to the rubric, and cannot tell a defensible answer from a wrong one. Their causes are a model's reading of the records, not a person's.

| sheet | draft | misgraded by | cause, two model-run analysts (not people) | cause, rule written after the run |
|---|---|---|---|---|
| final | 5 | Mistral only | the copy check removed a YES the judge had right | the copy check removed a YES the judge had right |
| final | 10 | both | the judge's own yes or no answers were wrong | shared by both judges, so the rubric or question wording |
| sheet1 | 8 | Mistral only | order sensitivity: the stricter of two differing orders was kept | order sensitivity |
| sheet1 | 34 | both | the owner later changed this blind label | a code rule decided it |
| sheet2 | 2 | Mistral only | the judge's own yes or no answers were wrong | the judge's own answers |
| sheet2 | 4 | Mistral only | the rubric or question wording: the judge's answers were defensible | the judge's own answers |
| sheet2 | 10 | both | the rubric or question wording: the judge's answers were defensible | shared by both judges, so the rubric or question wording |

By the model-run analysts' reading, an error both judges make is not always the rubric's. One shared error (final, draft 10) is a judging mistake the two judges happen to share, which may be a limit of judges this size rather than of either one. And one of Mistral's own errors (sheet2, draft 4) is the rubric's. Both analysts found Mistral's answers defensible and traced the owner's PARTIAL to padding the draft adds to a right answer, which no judge question asks about and the code's unsupported-claim check, looking only for outside names and acronyms, does not catch; llama3.1 matched the owner's binary label only by grading the draft WRONG.

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

It commits to NO on Q1, qualifies Q3 as "Yes, in a way", and gives Q2 no yes or no at all, only "Implicitly". The grader needs an answer to every question, so the draft was graded WRONG. The code's category is a task failure, not a format failure: a lenient reading that strips formatting still finds no answer to Q2, and the diagnostic regrade at 600 tokens got the same reply. Three model-run readers (language-model agents, not people), each shown only the questions and the reply and blind to the code, all called it a task failure.

How each judge wrote its answer lines over the same drafts, one row per kind of line:

| answer line | llama3.1 | Mistral |
|---|---|---|
| YES or NO with added words, in capitals | 0 | 17 |
| YES or NO with added words, not all capitals | 0 | 3 |
| bare YES or NO, in capitals | 196 | 173 |
| bare YES or NO, not all capitals | 0 | 2 |

The same three model-run readers also read the 19 parsed Mistral answer lines that carry added words, a check added after the run. By majority 18 are clear, the added words backing the YES or NO given, and one is contradictory: sheet1, draft 4, "Q2: No, the candidate does not state that the handbook does not contain the answer or could not find one. Instead, they acknowledge that the handbook does not answer the question directly." The parser read the stated answer there, and the owner and both judges graded that draft the same. The readers split on one line: sheet2, draft 5 (clear, hedged, clear).

Mistral did not fail on format. Its replies parsed under llama3.1's conventions 69 times in 70, and the one reply that did not failed the task, not the format. The parser was not where llama3.1's conventions cost Mistral; the copy check was (see Harness lock-in).

## Cost

One pass, one model: the run read Ollama's loaded models after every draft and would have stopped if any model other than Mistral had been loaded, and it finished normally. Wall clock 719 s. The strict pass made 70 judge calls and 54 copy-the-words calls, 13 of which repeated the identical request from the other answer order and came from the cache; the diagnostic pass made 2 judge calls and 1 copy call. Live calls took a median 6.1 s, 90th percentile 10.49 s, with a median 34 output tokens, 90th percentile 59. llama3.1's grades were replayed from the cache: all 85 matched the committed grades exactly, over 120 calls, none of them live.

## Independent checks, and who ran them

Every check below was run by code or by language-model agents, not people. The only person who graded anything in this experiment is the owner, whose labels are the ones on the three blind sheets. The readers, analysts and verifier were kept blind in the sense stated for each. The critic and the check of the owner's corrections were not blind, since reading this report was their job. A reader should weigh all of them as a model's work, not as the human blind checks reported in the main report.

- A model-run verifier (a language-model agent, not a person) worked from the raw files with its own code, blind to this report and the script. It recomputed each sheet's draft, label and judged counts, both judges' binary agreement with the owner, the judges' agreement with each other, the misgraded draft numbers and the unreadable count. Every number matched. It did not recompute the intervals, three-way agreement, order flips or copy-check counts. Added after the run.
- Three model-run readers (language-model agents, not people) classified the unreadable reply, a check planned before the run. After the run they also read the answer lines with added words. Each was blind to the code and to the other readers.
- Two model-run analysts (language-model agents, not people) assigned causes to every misgraded draft, blind to the report, the rule and each other, added after the run.
- A model-run critic (a language-model agent, not a person) reviewed the first rendering of this report against the owner's requirements and found 26 defects (reports/post-hoc-second-judge/critic-review.json). The first rendering said the two judges echoed equally often and that echoing was not a Mistral habit. The critic's first defect called that sentence false against the call logs, though its own echo count was the same undercount. The cause turned up while that defect was being fixed: a pattern that required a colon missed the instruction shape give "X" as the answer. The recount that followed, 7 calls against 1, was committed and was itself too high. Added after the run; the undercount is the sixth entry in the main report's measurement-integrity section.
- The owner read the committed report and asked for four corrections. Three more model-run reviewers (language-model agents, not people) then checked the corrected text, each followed by a model-run agent told to refute its findings (reports/post-hoc-second-judge/corrections-verification.json). 15 findings survived, several of them found by more than one reviewer, and all are addressed in this version. The recount from the raw logs found that 4 of Mistral's 7 counted echoes were NONE replies quoting a phrase, and that llama3.1's 1 was a leaves-out call that copied the draft. It also found that the overlap counted a draft no judge saw, and that the critic had been credited with finding the colon bug. A second round of the same kind, on the fixed text, found that the recount's denominators included instructions that quote an answer to go against, not a phrase to find. A third round found only wording and test gaps; all 19 later findings are fixed and recorded in the same file. The overcount is the seventh entry in the main report's measurement-integrity section, and the classifier has a test for each shape it missed.
- The llama3.1 replay and the Mistral pass are code: the replay refused any live model call, and the pass refused to run with any other model loaded.

