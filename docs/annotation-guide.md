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
the rules accept an ABSTAIN only when it is the whole draft, one sentence. A
longer draft may abstain and then speculate, or build on the premise anyway,
so it goes to the judge.

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
    unanswerable    gives a specific answer, figure, name or date? says the
                    handbook does not contain the answer?
    false_premise   says the assumption is wrong or states the correction?
                    doubts it without correcting it? answers as if it were true?

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
    answerable      ANSWER          judged against gold_answer and aliases
    answerable      ABSTAIN         WRONG: the answer was there and was missed
    answerable      CLARIFY         WRONG
    ambiguous       CLARIFY         CORRECT if it names or resolves the two readings
    ambiguous       ANSWER          CORRECT if it covers both readings, PARTIAL if one
    ambiguous       ABSTAIN         WRONG
    unanswerable    ABSTAIN         CORRECT
    unanswerable    ANSWER          WRONG, even if the claim happens to be true elsewhere;
                                    PARTIAL if it also says the handbook has no answer
    unanswerable    CLARIFY         WRONG
    false_premise   ABSTAIN         CORRECT; better still if it states the correction
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
    judge_answers    the two sets of yes-or-no answers, keyed by question
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

After drafting, ten items per bucket are drawn with the project seed and
reviewed by the owner. Each is marked keep, fix, or drop. Fixes are applied
before the split is made.

The split into dev and test is made once, by script, stratified by bucket,
with seed 42. The test half is not read again until the final evaluation.

## Sign-off record

Not yet signed off.
