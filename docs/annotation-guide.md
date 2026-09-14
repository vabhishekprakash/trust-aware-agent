# Annotation guide

How the labeled question set is written, and how an answer is marked right or
wrong. Nothing in data/eval is labeled until the grader described here has
been signed off by the owner on the worked examples.

The corpus is the NASA Systems Engineering Handbook (NASA/SP-2016-6105 Rev 2).
Every label below means "according to the handbook", never "according to the
world". A question the handbook does not answer is unanswerable here even if
the answer is common knowledge.

## The item record

Items live in data/eval as one JSON object per line. Fields:

    id            string, q0001 and up
    bucket        answerable | ambiguous | unanswerable | false_premise
    question      the question as a user would type it
    gold_answer   short answer string; null for unanswerable and false_premise
    gold_aliases  other acceptable short forms; may be empty
    readings      ambiguous only: list of {reading, answer, page}
    premise_fix   false_premise only: what the handbook actually says
    expected      answer | clarify | abstain
    evidence      list of {page, quote}; at least one entry in every bucket
    notes         why the item is in its bucket; anything that could fool the grader
    split         dev | test; set once by the split script, never by hand

Evidence is mandatory in every bucket. For answerable items it is the passage
that states the answer. For ambiguous items it is one passage per reading. For
false premise items it is the passage the premise contradicts. For
unanswerable items it is the closest passage, the one a reader would expect to
hold the answer, so a reviewer can see that the handbook was searched.

Page numbers are the printed page numbers of the handbook, and quotes are
copied from the extracted text so they can be found again with a search.

## The four buckets

### Answerable (target 70)

The handbook states the answer in one passage, or in two passages that sit
together. Answering needs reading, and sometimes one arithmetic step, but no
outside knowledge. Some items are built for the calculator tool: the handbook
gives the numbers and the question asks for a sum, difference, or percentage.

Writing rules: paraphrase rather than copy the sentence that holds the answer.
Avoid yes or no questions. Keep the gold answer short, a phrase or a number.
List aliases for every reasonable short form, including the acronym and the
spelled-out term.

### Ambiguous (target 40)

The question has two readings, and the handbook answers each reading
differently. The right response is to ask which reading is meant, or to answer
both. Ambiguity must be real: a term the handbook uses in two senses, a step
that exists in more than one phase, a role that appears in more than one
process. "Which review comes before implementation?" is ambiguous if the
handbook has several reviews before several implementation stages.

Writing rules: record both readings, both answers, and a page for each in the
readings field. If one reading is clearly what any reader would mean, the
item is not ambiguous; move it to answerable.

### Unanswerable (target 50)

The question uses the handbook's vocabulary and sounds like it belongs, but the
handbook does not contain the answer. Good sources of such questions: costs,
dates, named people, numbers the handbook does not give, comparisons with
other organisations, and details of specific missions.

Writing rules: before labelling, search the extracted text for the key terms
of the question and write in notes what was searched and what was found. The
question must not be answerable by combining passages either. A question that
is merely hard is not unanswerable.

### False premise (target 40)

The question asserts something the handbook contradicts, then asks about it.
"Since the handbook requires two key decision points per phase, which one
comes first?" is a false premise item if the handbook gives a different
number. The right response is to reject or correct the premise, or at least
to refuse to build on it.

Writing rules: the false part must be checkable against the text, with the
contradicting passage as evidence and the correction in premise_fix. If the
handbook is merely silent on the premise, the item is unanswerable, not false
premise.

## How an answer is graded

The agent always produces a draft response, even when that draft is "I could
not find this in the handbook" or a question back to the user. The grader
judges the draft. Its output is a grade of CORRECT, PARTIAL, or WRONG, and a
binary label, 1 or 0, which is what the calibrator trains on.

The grader runs in stages, and the first stage that reaches a decision wins.

Stage 1, normalise. Lowercase, strip punctuation, collapse whitespace, and
drop the thousands separators in numbers so that "1,000" and "1000" compare
equal. The articles "the" and "an" are stripped anywhere, and "a" only at the
start of the text. Elsewhere the letter A is kept, because "Phase A", "KDP A"
and "Appendix A" are labels in this handbook and stripping it would turn
"Phase A" into "phase".

Stage 2, classify the form of the draft. A draft is a CLARIFY if it ends with
a question mark and contains a clarifying cue such as "do you mean" or "which
of these". Otherwise it is an ABSTAIN if it says the handbook does not contain
the answer, and a CLARIFY again if the whole draft is one short question.
Anything else is an ANSWER. The patterns handle the clear cases; the judge in
stage 4 reads the unclear ones. On the unanswerable and false-premise buckets
the rules accept an ABSTAIN only when nothing specific follows the refusal
phrase that the question itself did not mention. The trigger is a digit, a
number word such as "million", a month, or a capitalised name mid-sentence,
and only when the question did not already mention it. Such a draft may be
a refusal carrying an invented answer, so it goes to the judge instead. A
name or figure echoed from the question is not an invented answer. A
refusal that goes on to offer a figure is PARTIAL, which the strict rule
turns into label 0. A user would act on that figure, and it is the failure
this project exists to catch. A refusal scoped to "the passage" the agent
was given, with nothing added, is CORRECT. A refusal that carries a positive
assertion that is false or unsupported is PARTIAL. An invented expansion of
an acronym, or a claim about what the handbook does or does not cover,
counts. These are the owner's rulings of 2026-09-09.

Stage 3, exact check. For an ANSWER draft with a gold answer, if the
normalised draft equals the gold answer or an alias, the grade is CORRECT and
no model is called. The same holds if the draft is under 30 words and contains
the gold answer or an alias. A negation or a choice next to it ("12, not 17";
"17 or 12") cancels that, and the judge reads the draft. Longer drafts go to
the judge, because a long draft can contain the right answer and a
contradicting one. An ABSTAIN draft on an answerable item that still names
the gold answer also goes to the judge.

Stage 4, judge. A language model reads the question, the evidence quote, the
draft, and the reference material for the bucket. That material is the gold
answer and its aliases, the two readings and their answers, or the premise
correction. It does not choose a grade. It answers a fixed list of yes-or-no questions about
what the draft does, and code maps the answers to a grade.

    bucket          questions the judge answers about the draft
    answerable      gives the same answer? states a different or contradicting one?
                    leaves out a part that carries meaning?
    ambiguous       asks which reading is meant? gives the answer for reading 1?
                    for reading 2?
    unanswerable    offers any answer, figure, estimate, name or date, even a
                    hedged one? says the handbook does not contain the answer?
    false_premise   says the assumption is wrong or states the correction?
                    doubts it without correcting it? answers as if it were true?

One more check applies in every bucket: does the draft assert anything the
handbook does not support? The judge is not asked it. Asked as a fourth
question, it said YES to true statements, such as a correct premise fix or
a sentence the evidence supports. Its presence also changed the other
answers in one order, which brought binary flips back on the worked
examples. Code makes
the check with the whole corpus instead. An acronym expanded differently
from Appendix A (data/corpus/acronyms.json) counts as unsupported. So does
a claim that the handbook does not mention, cover, discuss, address,
include or contain a term the text does contain. So does a capitalised
name or acronym that appears in neither the question, nor the item's
reference and evidence, nor anywhere in the handbook: a claim brought in
from outside. A claim about a detail ("does not specify where X happens")
is an abstention, not an existence claim, and is left alone. The check also
runs before the exact stage, so a short right answer padded with an outside
name is not accepted without the judge.

Every YES must be backed by words from the draft. When the draft contains
the claimed answer, an alias, or its acronym, code settles that itself.
Otherwise the judge gets a second, smaller call: copy the exact words in the
draft that do what the question says. Code checks that the copied words
occur in the draft. For the "leaves out" question they must occur in the
reference answer and not in the draft. Where the question claims the draft
gives an answer, they must name that answer. A YES that cannot be backed
becomes NO, and the record lists which answers were turned. Asking for the
copy inside the yes-or-no question itself made the judge read "same answer"
as "same words" and fail plain paraphrases, so the copy is asked for
afterwards. The check is what keeps the two orders in step. Without it the
judge said YES, in candidate-first order, to answers the draft never gave,
and one binary label flipped with the order.

    bucket          mapping from answers to grade
    answerable      a different answer: PARTIAL if the right one is there too,
                    else WRONG. A part left out: PARTIAL. The same answer and
                    nothing against it: CORRECT. Otherwise WRONG.
    ambiguous       asks which reading, or answers both: CORRECT. Answers one:
                    PARTIAL. Neither: WRONG.
    unanswerable    says there is no answer and gives none: CORRECT. Gives one
                    while saying so: PARTIAL. Gives one: WRONG. Neither: WRONG.
    false_premise   rejects or doubts the assumption and does not answer on it:
                    CORRECT. Rejects or doubts it but still answers on it:
                    PARTIAL. Answers on it: WRONG. Neither: WRONG.
    every bucket    a grade that would be CORRECT becomes PARTIAL when the
                    draft asserts something unsupported. Lower grades stand.

Where a question is about a specific piece of text, the answer for a reading
or the premise correction, that text is quoted in the question. For the
answerable bucket the gold answer is not quoted, because quoting it made the
judge match strings instead of meaning. The prompt is fixed and versioned,
temperature is zero, the seed is fixed, and every call is cached, so grading
is repeatable. The judge sees the evidence quote so that it reads against the
handbook and not against its own memory.

Why questions rather than a grade: the first two versions of the grader asked
the local judge for CORRECT, PARTIAL or WRONG directly. On the unanswerable and
false-premise buckets it graded the question instead of the draft. Adding
three words to the prompt flipped a correct clarifying question from CORRECT
to PARTIAL in both orders. Narrow reading questions were answered steadily.
The worked examples were run under all three versions and the report shows
them side by side.

The judge runs twice for every draft it sees: once with the reference before
the candidate, and once with the candidate before the reference. Language
model judges are sensitive to position, and running both orders measures
that. If the two grades differ, the stricter one is used, the record is
flagged for the owner's review, and the flip rate is reported. A reply the
parser cannot read is flagged, graded WRONG, and counts as label 0 until a
person reads it.

Stage 5, the partial rule. PARTIAL becomes label 0. An answer that is half
right is one a user would act on and be misled by, so it counts as a failure
for calibration. The PARTIAL grade is kept in the record so the report can
say how many items fall there and can rerun the metrics under the lenient
rule as a sensitivity check.

Stage 6, human override. When the owner reviews an item and disagrees with
the grader, the owner's verdict replaces it and the record says so.

### What counts as correct, by bucket

    bucket          draft form      grade
    answerable      ANSWER          judged against gold_answer and aliases; PARTIAL if
                                    right but padded with claims the handbook does not
                                    support
    answerable      ABSTAIN         WRONG: the answer was there and was missed
    answerable      CLARIFY         WRONG
    ambiguous       CLARIFY         CORRECT if it names or resolves the two readings
    ambiguous       ANSWER          CORRECT if it covers both readings, PARTIAL if one
    ambiguous       ABSTAIN         WRONG
    unanswerable    ABSTAIN         CORRECT, also when scoped to the passage the agent
                                    was given; PARTIAL if it goes on to offer a figure,
                                    name or date, or asserts something false or
                                    unsupported, such as an invented acronym expansion
    unanswerable    ANSWER          WRONG, even if the claim happens to be true elsewhere;
                                    PARTIAL if it also says the handbook has no answer
    unanswerable    CLARIFY         WRONG
    false_premise   ABSTAIN         CORRECT: a bare refusal fails safe; better still if
                                    it states the correction; WRONG if it goes on to
                                    build on the premise
    false_premise   ANSWER          CORRECT if it rejects the premise, PARTIAL if it
                                    rejects or doubts it but still answers on it,
                                    WRONG if it builds on it
    false_premise   CLARIFY         WRONG unless the question exposes the false premise

An abstention on an answerable question is a miss for correctness. Coverage,
meaning how often the system chooses to answer at all, is measured
separately in the risk-coverage analysis, so this rule does not punish
caution twice.

### What every grade record stores

    grader_version   version string of the rules and the judge prompt
    form             ANSWER | ABSTAIN | CLARIFY
    decided_by       exact | rules | judge | human
    grade            CORRECT | PARTIAL | WRONG
    label            1 | 0
    judge_model      model name, when the judge ran
    judge_grades     the two grades, reference first then candidate first
    judge_answers    the two sets of yes-or-no answers, keyed by question, after the check
    judge_quotes     the words that back each YES, found by code or copied by the judge
    judge_ungrounded the answers turned from YES to NO because no backing words were found
    judge_outputs    the two raw judge replies
    flag             null | position_disagreement | judge_unparsed
    machine_grade    the grade before a human override, when one was applied
    reason           one sentence

## Review procedure

Before mass labelling, twenty-one worked examples are graded and shown to the
owner. They are real questions from the handbook with hand-written drafts
that are plainly correct, plainly wrong, partial, and borderline, spread
across the four buckets. They live in data/eval/grader_examples.jsonl, and
scripts/grade_examples.py writes the report to reports/. The owner signs off
on the rules or changes them. The sign-off and any changes are recorded at
the end of this file with the date.

Before the agent's drafts on the dev set are graded in bulk, the owner
hand-labels 40 of them without seeing the judge's verdicts. Agreement between
the owner and the judge on those 40 goes into the final report as a
limitation, whatever the number is. If agreement is below about 90 percent,
the grader is fixed and re-checked before the remaining drafts are graded.

Two blind checks by the owner, kept separate, gate the next steps. The item
check: 40 drafted items, held back with their labels hidden, which the owner
labels from the handbook alone; agreement with the drafted bucket and answer
is reported. The grader check: about 40 drafts written by the model under
test, spanning correct, wrong and borderline, which the owner grades CORRECT,
PARTIAL or WRONG without seeing the judge. Agreement with the judge on the
binary label is reported. Below about 90 percent the grader is not good
enough for mass grading.

Stated plainly: the items are drafted by language model agents, checked by
other language model agents, and the agent's answers are graded by a
language model judge. The only human checks are the owner's two 40-item
samples. Every number built on this set carries that limitation, and the
final report says so.

A second limitation is a confounder, not a footnote. In the grader check the
model under test was right on every answerable item when its own evidence
passage was in front of it, 6 of 6. Without it, it was right on 1 of 8.
Whether the agent answers correctly is therefore decided mostly by whether
retrieval found the right passage. Much of the variance the calibrator sees,
and much of what the confidence signals pick up, is retrieval quality rather
than the model's judgement of its own answer. The final report must separate
the two where it can, for example by reporting calibration with retrieval
quality held fixed, and must say so where it cannot.

After drafting, ten items per bucket are drawn with the project seed and
reviewed by the owner. Each is marked keep, fix, or drop. Fixes are applied
before the split is made. Nothing is locked, and no split is made, until the
owner has returned both blind sheets and the review sample.

The split into dev and test is made once, by script, stratified by bucket,
with seed 42. The test half is not read again until the final evaluation.

## Sign-off record

2026-09-09. The owner reviewed the v3 report and ruled as follows. v3 is
accepted on the condition that no order flip changes the binary label. A
refusal that goes on to offer a figure is PARTIAL, detected in code first.
Examples 3 and 19 stay as flagged. 21 examples is fine. Example item ex-m2
is reworded so its second reading matches its quote. Pushing is the owner's
alone. v3 failed the condition on one example (21), so position sensitivity
was fixed before anything else. On the same 21 examples grader v7 has no
order flip that changes the binary label; its one flip, example 19, is
grade-only. It matches the expected label on 21 of 21 and the expected grade
on 19 of 21, and its two grade misses are examples 3 and 19.

2026-09-09, later. The owner signed off grader v7 on the version table below.
Grade and label matches are against the writer's expected grade for the
worked examples, as they stand after the rulings above; flips are order
flips among the drafts the judge saw.

    version  grade matches  label matches  order flips  flips that changed the label
    v1       13 of 20       13 of 20       4 of 15      4
    v2       14 of 20       16 of 20       3 of 15      3
    v3       18 of 21       20 of 21       4 of 16      1
    v4       16 of 21       18 of 21       2 of 18      0
    v5       15 of 21       18 of 21       3 of 17      0
    v6       18 of 21       20 of 21       1 of 17      0
    v7       19 of 21       21 of 21       1 of 17      0

Sign-off on the examples is not the last word. Mass grading is gated on the
blind grader check in reports/grader-check-sheet.md reaching about 90
percent agreement with the owner on the binary label. Below that the grader
is fixed first, whatever the table says. Nothing in data/eval is locked and
no split is made until the owner has returned both blind sheets and the
review sample.

2026-09-09, blind checks returned. Grader check: the owner graded 39 of 40
model drafts and agreed with the judge on the binary label on 32 of 39, 82
percent (reports/grader-check-result.md). That is below the bar, so grader
v7 is not signed off in practice and mass grading waits. One of the seven
disagreements is a judge error (an abstention on an unanswerable item
graded as an answer). The other six were rubric questions the owner's
grades raised and this guide did not then settle. They were four. An
abstention that refers to "the passage" rather than the handbook, or adds an
invented detail. A bare abstention on a false-premise question. A right
answer padded with claims from outside the handbook. One ambiguous item the
owner read as having one natural answer. The rulings that settled them are in stage 2
and stage 4 above and in docs/decisions.md. Item check: the owner's bucket
matched the drafted bucket on 37 of 40 items, 92 percent
(reports/item-check-result.md). Answerable 14 of 14, with the owner's answer
matching the gold or an alias every time; unanswerable 10 of 10; false
premise 8 of 8; ambiguous 5 of 8. The three misses were drafted as ambiguous
and read as answerable by the owner. Both figures go into the final report
as measured limitations.

2026-09-09, evening. The owner's rulings on the seven disagreements are in
stage 2, stage 4 and the bucket table above, and in docs/decisions.md. The
grader is now v10. It keeps the v7 judge questions and adds the
question-aware specifics trigger. The unsupported-assertion check is done
in code with the whole corpus. It covers acronym expansions against
Appendix A, claims that the handbook does not mention a term it contains,
names and acronyms from outside the handbook, and a "same answer" that
must add something beyond the question. On the 21 worked examples v10 matches v7: 19 of 21 grades,
21 of 21 labels, one grade-only order flip, none that change the label.
Rerun on the first 40 drafts and scored against the owner's grades, with
the four rule-based revisions applied (sheets 9, 16, 33 and 34), v10 agrees
on the binary label on 38 of 39. That is 97 percent. It is rubric fidelity,
not blind agreement: the fixes were built against those drafts, and the one
miss, sheet 19, is an item that has since moved to answerable. The blind
figure remains 82 percent. The second sheet, reports/grader-check-sheet-2.md,
holds 25 fresh drafts the owner has not seen; its blind agreement, once
graded, is the post-fix figure that gates mass grading. Nothing is locked
and no split is made.

2026-09-10. Sheet 2, the blind post-fix check. The owner graded all 25
fresh drafts without seeing the judge, and v10 agreed on the binary label
on 20 of 25, 80 percent (reports/grader-check-result-2.md). That is the
honest post-fix number. It sits next to the first blind figure, 32 of 39,
82 percent for v7, and both are below the bar, so v10 is not signed off.
Of the five disagreements, one was a grader defect and is fixed in v11: an
abstention that only echoed the question's own "NASA SP-6105" went to the
judge because a two-word term was matched as one word, and the judge's
copying call then failed on a plain refusal. Refusal phrases now ground
themselves. Regraded after the fact by v11, sheet 2 reads 21 of 25, 84
percent; that is not a blind number and is reported only as the effect of
the fix. Three of the remaining four are bare abstentions on false-premise
items that the owner graded WRONG, against the owner's own ruling on sheet
16 that a bare abstention on a false premise fails safe and stays CORRECT.
The owner is asked to settle that rule one way, because it decides both
the grader check and the sensitivity alternative. The last is an ambiguous
item (q0115) whose validation reading the owner treated as the natural
answer; it is one of the twelve close calls. v11 leaves the 21 worked
examples where v7 had them: 21 of 21 labels, no flip that changes a label.
