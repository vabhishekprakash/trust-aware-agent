# Decisions

What we picked, what we did not pick, and why. One entry per real choice,
oldest first.

## Model: a small local model, on purpose

Picked: Ollama running qwen2.5:3b-instruct, behind one provider interface.
An OpenAI-compatible client covers both Ollama and hosted services, so the
demo runs with no network and the same code can call a hosted model later.

Rejected: a 7B model, because it does not fit the 4 GB GPU on the development
machine and runs several times slower for the five-sample agreement signal.
Also rejected as the default: a hosted frontier model, because it needs
network access and the Anthropic API does not return token log probabilities.

Why small: this project is about calibration, and calibration needs mistakes
to learn from. A model that is right 95% of the time produces almost no wrong
answers in a 200-item set, so there is nothing for a calibrator to separate.
A weaker model spreads its answers across right and wrong, which is the spread
the calibrator needs.

Log probabilities: Ollama 0.24 returns per-token log probabilities on both its
native endpoint and its OpenAI-compatible endpoint. The script
scripts/check_logprobs.py reruns that check against whichever model and
endpoint you point it at, and its exit code says whether the signal is
available.

Output on 2026-09-08 against the approved model:

    model: qwen2.5:3b-instruct
    reply: 'yes'
    log probabilities: returned for 1 token(s)
      'yes'        logprob=-0.151  alternatives: 'yes'=-0.151, 'Yes'=-1.967, ' yes'=-9.450

That run used the OpenAI-compatible endpoint. The provider in src/agent uses
Ollama's native endpoint, where the log probabilities arrive as a top-level
list, so the script also has a --native flag. On 2026-09-09 it returned the
same token and the same three values from the native endpoint.

## Corpus: the NASA Systems Engineering Handbook

Picked: NASA Systems Engineering Handbook, NASA/SP-2016-6105 Rev 2, as a
single PDF from
https://www.nasa.gov/wp-content/uploads/2018/09/nasa_systems_engineering_handbook_0.pdf
(fetched on 2026-09-08: 3,773,440 bytes, SHA-256 beginning 8eeb4887, pinned
in scripts/fetch_corpus.py and recorded in data/corpus/manifest.json). Page 2
of the PDF states that SP-2016-6105 Rev2 supersedes SP-2007-6105 Rev 1, which
confirms the edition. The extracted text is 297 pages, about 119,000 words,
with the printed page labels preserved.

Licensing: the handbook is a work of the United States government. Under
17 U.S.C. section 105 such works have no copyright protection in the United
States, so the extracted text can live in a public repository. The PDF itself
is fetched by a script rather than committed, to keep the repository small.

Why this corpus: it matches the sponsor's field, engineering research and
development. It is niche enough that a 3B model has not memorised it, so
"answer only from the documents" is a real constraint rather than a formality.
It says little about costs, dates, or mission-specific figures, which makes
unanswerable questions easy to write honestly. It has a glossary and an
acronym appendix, which become a lookup tool, and enough numbers for
calculator questions.

Rejected: Wikipedia articles from SQuAD 2.0, which come with human-written
unanswerable questions but are memorised by every language model, so
abstention would be muddied by recall. A product manual, because licensing for
a public repository is unclear. A fictional company handbook, which has no
leakage but is weak in a review.

## Labeled set: built in-house, grader signed off first

Picked: about 200 questions written over this corpus in four buckets:
70 answerable, 40 answerable but ambiguous, 50 not answerable from the corpus,
and 40 built on a false premise. Every item carries a page or chunk reference
to the passage that supports the label.

Before any item is written, docs/annotation-guide.md defines how an answer is
marked right or wrong. It sets the rubric, what does the grading (a rule, a
model, or a person), and what happens on a partial match. The owner signs off
on graded examples spanning correct, wrong, and borderline before mass
labelling starts.
The correctness labels are what the calibrator trains on, so a sloppy grader
would silently corrupt every number in the report.

Rejected: a public dataset on its own. "Not answerable from the corpus" is a
property of this corpus, and no public set can guarantee it for these
documents.

## Split: 100 dev, 100 test, stratified, seed 42

The split is stratified by bucket with a fixed seed. Thresholds and the
calibrator are fit on the dev half with 5-fold cross-validation. The test half
is read by exactly one script, once, at the end. Test metrics come with
bootstrap confidence intervals, because 100 items is a small sample. If
drafting goes faster than expected, the set grows to 240 and the extra 40 items
go to test.

Rejected: 120 dev and 80 test. That gives the calibrator more to learn from
but a noisier final chart, and the final chart is the deliverable.

## Dashboard: one static page served by FastAPI

Picked: a single HTML page with plain JavaScript, served from the same FastAPI
process as the JSON API. One process, one Docker image, no Node build step,
and Playwright can drive a plain page deterministically for the demo
recording.

Rejected: Streamlit and Gradio, which need a second process and whose re-run
model makes scripted recording flaky. React or similar, because nobody will
maintain a frontend after the project ends.

## Every model call is cached on disk

Each call is stored under data/cache/ keyed by the prompt, the sampling
settings, and the seed. Reruns cost nothing and results are reproducible. The
cache directory is gitignored.

## Git rules enforced by tooling, not memory

A commit-msg hook strips co-author and generator trailers that tools append
to commit messages, so the repository has a single author on record, and it
rejects subjects over 60 characters. A pre-push hook refuses to push unless
ALLOW_PUSH=1 is set on purpose. Copies of the hooks live in scripts/hooks with
an install script, because git does not track .git/hooks and a fresh clone
would otherwise have none.

## Python and compute layout

Development uses Python 3.12 in a virtual environment, with pinned versions in
requirements.txt generated from pyproject.toml. The project itself allows 3.10
or newer. PyTorch is the CPU build: the embedding and entailment models are
small enough for CPU, and the single 4 GB GPU is left to Ollama for the
language model. On Linux the default PyPI wheel is the CUDA build, several
gigabytes the project never uses, so requirements.txt is compiled with the
PyTorch CPU index added. That index also hosts old copies of common packages,
and the first attempt silently pinned a 2022 certificate bundle and older
tqdm, packaging and setuptools from it. The compile command therefore uses
uv's best-match index strategy, which takes the newest version across both
indexes. The exact command is recorded in the file's header. The README
installs from requirements.txt for the same reason.

## License: MIT

Chosen as the default for a student project that should be easy to reuse. It
can be changed before the first release if the owner prefers otherwise.

## Prose hygiene: an ASCII check instead of the cleaning service

Every prose file is meant to pass through a tool that strips invisible
Unicode marks. That tool is a client for a local web service that is not
running on the development machine, and it refuses to work without it. The
files are checked instead by a short script that reports any character
outside printable ASCII, tab, and newline. All prose files pass with zero
hits. That is sufficient because invisible marks are by definition characters
outside that range, so a file that contains none cannot carry them.

## Grader: two orders, forty blind labels, strict partials

The judge model is llama3.1:latest, the 8B model, running locally. It is a
different model family from the model under test, so its blind spots differ,
and grading runs offline and is cached, so its slower speed costs little. The
3B model under test was rejected as judge because it would grade its own
mistakes.

Every draft that reaches the judge is judged twice, with the reference and
candidate in both orders. Disagreements take the stricter grade and are
flagged for review, and the flip rate is reported. Before bulk grading, the
owner hand-labels 40 agent drafts blind to the judge. The agreement figure
goes into the report as a limitation whatever it is; below about 90 percent,
the grader is fixed first.

Partial answers count as wrong for the calibrator. The three-way grade is
kept so the report can show the lenient numbers as a sensitivity check.

## Grader: the judge answers questions, code picks the grade

Three versions of the judge prompt were run over the same worked examples,
and the reports in reports/grader-examples-v1.md to v3.md show them side by
side. The first version asked the judge for CORRECT, PARTIAL or WRONG with a
rubric. On the unanswerable and false-premise buckets it graded the question
instead of the draft. A made-up cost figure was CORRECT because "the handbook
gives no cost". A draft that accepted a false premise was CORRECT, with a
reason saying it had rejected it. Its 0 or 1 label matched the writer's
expectation on 14 of 20 examples.

The second version gave those two buckets a describe-and-classify task
instead and kept the direct grade elsewhere. That fixed them, 17 of 20
labels, but adding the words "judge meaning, not wording" to the other
prompt flipped a correct clarifying question from CORRECT to PARTIAL in both
orders. A small judge asked for a grade is that sensitive to wording.

The third version never asks for a grade. For each bucket the judge answers
two or three yes-or-no reading questions about the draft, and code maps the
answers to a grade; the mapping is in docs/annotation-guide.md. Where a
question concerns a specific text, the answer for a reading or the premise
correction, that text is quoted in the question. That is what made the
false-premise case reliable. Quoting the gold answer in the answerable
questions had the opposite effect. The judge then matched strings and called
paraphrases and a correct calculator answer "not the same", so that bucket
asks about the reference answer without quoting it. On 2026-09-09 the third
version matched the writer's expectation on 19 of 21 grades and on 21 of 21
labels, with 4 order flips in 16 judged drafts. The two grade misses are
both stricter than expected, and both are flagged. Rules decided 5 of the 21
without a model call.

Three rule changes came out of the same review. The exact stage no longer
accepts a short draft that contains the gold answer next to a negation or a
choice ("12, not 17"). The letter A is no longer stripped as an article,
because "Phase A" had normalised to "phase". On the unanswerable and
false-premise buckets an abstention is accepted by rule only when it is the
whole draft. A longer draft that abstains and then speculates goes to the
judge, whose questions catch the hedge.

Open for the owner: a one-sentence abstention that ends in a speculative
figure ("the handbook does not state a figure, but it would run into the
millions") is CORRECT by rule today. Making it PARTIAL means sending every
abstention to the judge.

## Chunking: 200 words, 40 overlap, page tags, bge-small embeddings

The cleaned handbook text is cut into chunks of at most 200 words that
overlap by 40 words. Each cut is snapped back to the nearest sentence end, and
each chunk is tagged with the printed page range it spans. The embedding
model is BAAI/bge-small-en-v1.5, which accepts 512 tokens. That claim was
checked rather than assumed: scripts/build_chunks.py tokenises every chunk
with that model's tokenizer. On 2026-09-09 it produced 773 chunks from 297
pages, 74 to 200 words each with a median of 191, and 181 to 459 tokens each.
The longest, c00760 on pages 280 to 281, is 459 tokens, so no chunk is
truncated. The one short chunk is the tail of the book. The alternative
all-MiniLM-L6-v2 truncates at 256 tokens. Measured with the same tokenizer,
230 of the 773 chunks exceed 256 tokens, and the script prints that count.
That model would have silently cut the tail off roughly a third of the
corpus.

A review of the first build found four cleaning faults, all fixed before the
numbers above were taken. 149 C1 control characters, which the checklists
use as bullets, survived into the text. 33 line breaks after a real hyphen
were joined with a space, giving "require- ments". Drop-cap initials came out
detached, as in "T his handbook". The "References Cited" and "Bibliography"
running headers were spliced into the body on 28 pages. Four pages come out
empty, and that is right: two are chapter divider pages and two are
appendices the handbook marks "Reserved". One side effect is accepted: the
chapter title line is also dropped from a chapter's opening page, because it
matches the running header there too. The numbered section headings in the
body survive, so retrieval loses nothing a question would ask for.

## Owner's rulings on the grader, 2026-09-09

The owner read the v3 report and asked one question before signing off. The
order flips had stayed flat across the three versions, 4 of 15 to 4 of 16,
so did swapping the order ever change the binary label, or only the
three-way grade? Broken down from the report records: in v1 all four flips
changed the label, in v2 all three did, and in v3 one of the four did.
Example 21, a plainly wrong ambiguous draft, was WRONG with the reference
first and CORRECT with the candidate first. In that order the judge said the
draft gave both readings' answers when it named neither. The owner
had ruled in advance that one such flip means v3 is not signed off and
position sensitivity is fixed first. That fix is grader v4, below.

The other rulings, all applied the same day:

A refusal that goes on to offer a figure is PARTIAL, so the strict rule
counts it as label 0. A refusal carrying an invented number is the failure
this project exists to catch, and a user would act on it. It is detected in
code first, so judge exposure stays small. A digit, a number word, a month,
or a capitalised name after the refusal phrase sends the draft to the judge.
A refusal with nothing specific after it is CORRECT by rule. Worked
example 15 changed from CORRECT to PARTIAL under this ruling.

Examples 3 and 19 stay as flagged. Their binary label is unaffected, but the
three-way grade feeds the lenient sensitivity check, so if the strict and
lenient numbers diverge in the final report they come back into scope.

Twenty-one worked examples is fine.

Example item ex-m2 gave its second reading, "program life-cycle phases", the
answer "two", while its own first quote listed Program Pre-Formulation as
well. A gold answer that contradicts its supporting quote teaches the grader
the wrong thing, so the item was reworded. The second reading is now the
top-level NASA life-cycle phases. Its quote is the sentence on page 18 that
names exactly Formulation and Implementation and says they divide into the
seven project phases.

Pushing is the owner's alone. Nothing here sets ALLOW_PUSH or runs git push.

## Grader v4 to v7: every YES is backed by the draft's own words

The binary flip in v3 came from a YES with nothing behind it: in
candidate-first order the judge said the draft gave both readings' answers
when it named neither. The fix is to make every YES carry words from the
draft that code can check. Four versions were needed to get the mechanism
right, and the same 21 worked examples were run under each. The numbers
below are against the expectations as they stand after the owner's rulings,
with example 15 now PARTIAL. That is why v1 and v2 read one lower than in
the morning's report.

    version  grade matches  label matches  order flips  flips that changed the label
    v1       13 of 20       13 of 20       4 of 15      4
    v2       14 of 20       16 of 20       3 of 15      3
    v3       18 of 21       20 of 21       4 of 16      1
    v4       16 of 21       18 of 21       2 of 18      0
    v5       15 of 21       18 of 21       3 of 17      0
    v6       18 of 21       20 of 21       1 of 17      0
    v7       19 of 21       21 of 21       1 of 17      0

v4 asked for the copy in the same reply as the yes-or-no answers. That
removed the binary flips at once, but it made the judge literal. It wrote
"conveys the same meaning" and still answered NO to a paraphrase, because
it could not point at identical words. v5 put a copying hint on every
question and marked the candidate with delimiters. The judge stayed literal,
and a loose matching rule let a copy of the question text pass as a copy of
the draft. v6 separated the two jobs. The yes-or-no call is the v3 prompt
again. Each YES then goes back to the judge as a small copying task,
"copy the exact words in this text that ...", checked by code. Recall came
back and no flip changed a label. v7 lets code settle a YES itself when the
draft contains the claimed answer, an alias, or its acronym. The copying
call had missed "MDR/SDR", and that closed the last label miss.

What is left in v7: example 3 comes out WRONG where the writer expected
PARTIAL, and example 19 flips between PARTIAL and WRONG with the order and
takes WRONG. Both leave the binary label unchanged and both are the cases
the owner ruled to keep flagged. v7 costs about two extra judge calls per
draft. Grading the 21 examples from a cold cache takes about ten minutes.
The owner signed off v7 on that table on 2026-09-09, with the blind grader
check as the gate for mass grading.

## The two blind checks, 2026-09-09

Grader check. Forty drafts by qwen2.5:3b-instruct on verified candidate
items, under three conditions the model did not know it was in (its own
evidence passage, no passage, another item's passage), shuffled. The owner
graded 39 without seeing the judge. Binary agreement: 32 of 39, 82 percent,
below the 90 percent bar, so v7 is not signed off in practice and nothing is
mass graded yet. Per bucket: answerable 17 of 18, ambiguous 3 of 4, false
premise 3 of 4, unanswerable 9 of 13. Per condition: no passage 12 of 13,
own evidence 11 of 13, distractor passage 9 of 13. Where the two disagreed,
the owner was stricter than the judge in six cases and more lenient in one.

Read one by one, the seven disagreements split into one judge error and six
rubric gaps. The judge error: an abstention on an unanswerable item ("the
passage does not provide information about the dollar cost cap...") went to
the judge because a capitalised name followed the refusal. The judge then
answered that the draft offers an answer. The rubric gaps, which the guide
did not settle and the owner's grades did, were four kinds. Three
abstentions were phrased as "the passage does not provide" rather than the
handbook. One of them added a wrong expansion of PDR and one added a false
claim about what the handbook mentions. The owner graded those PARTIAL and
the grader CORRECT. One bare abstention on a false-premise item was CORRECT
by the guide's table and WRONG to the owner. One right answer was padded
with claims from outside the handbook (the Aerospace Industries Association,
defence), CORRECT to the grader and PARTIAL to the owner. One ambiguous item
drew a one-sided answer that the owner graded CORRECT, reading the item as
having a natural answer. Those six were decisions for the owner before the
grader changed; the rulings follow below.

Item check. The owner labelled 40 held-back items from the handbook alone.
Bucket agreement was 37 of 40, 92 percent. Answerable 14 of 14, and the
owner's answer contained the gold answer or an alias every time.
Unanswerable 10 of 10. False premise 8 of 8, with corrections matching the
drafted fix. Ambiguous 5 of 8. The three misses were drafted as ambiguous
and read as answerable. The second reading rested on a distinction the
handbook draws that a user asking the question would not have in mind. The
three were Concept of Operations against Operations Concept, MOEs against
MOPs, and requirements validation against product validation. In two of the three the
owner noted the near-call. That is the failure the guide names: "if one
reading is clearly what any reader would mean, the item is not ambiguous".
It is the bucket to re-read across all candidates during the review.
Unanswerable, which the owner expected to be the shakiest bucket, matched on
every item.

Both figures are measured limitations and go into the final report as they
stand.

## Owner's rulings on the seven disagreements, 2026-09-09

Sheet 18 was a judge defect and is fixed. The specifics trigger after a
refusal now fires only on names and figures the question itself did not
mention, because a capitalised phrase echoed from the question is not an
invented answer.

Sheets 3 and 5 stay PARTIAL, as the owner graded, under a new rule. An
abstention scoped to "the passage" stays CORRECT. An abstention carrying a
positive assertion that is false, including an invented expansion of an
acronym, is PARTIAL.

Sheet 34 the owner withdrew: same scoped wording as sheet 18, so CORRECT.
The owner recorded that the two grades were inconsistent, and the
scoped-versus-positive rule above is what resolves them.

Sheet 32 stays PARTIAL, as the owner graded. Every bucket now asks the judge
one more question, whether the candidate asserts anything the handbook does
not support, and a correct answer padded with outside claims is PARTIAL.

Sheet 16 the owner withdrew: a bare abstention on a false premise fails safe
and stays CORRECT, as the guide's table said. The owner's stricter reading,
that a refusal which neither rejects the premise nor answers should be
WRONG, is recorded here as the alternative. The final report will show the
sensitivity of the results to it.

Sheet 19: the guide's rule stands, one reading without the other is
PARTIAL. The disagreement is an item problem and is handled in the
ambiguous pass below.

The fixed grader is v8. Rerun on the same 40 drafts, and scored against the
owner's grades with the two withdrawals applied, it gives a rubric-fidelity
figure, not a blind one. It measures how faithfully the fixed grader follows
the rubric the owner settled, on the drafts the fix was designed against.
The 82 percent first-pass figure stands as the blind number. A second sheet
of 25 fresh drafts, drawn the same way, gives the honest post-fix agreement
once the owner has graded it blind.

## Grader v9 and v10: the support check moves to code

v8 reached 33 of 39, 85 percent, on the rerun (reports/grader-check-
rubric-fidelity-v8.md). Six disagreements were left. Two were the same
bare-abstention-on-a-false-premise case the owner had ruled on for sheet
16. Sheets 9 and 33 were revised to CORRECT under that rule, and the
revisions file records all four. One, sheet 19, resolves through the item:
q0124 moved to answerable in the ambiguous pass, and there the draft is an
exact match. Three were grader gaps of one kind: the judge sees a single
passage. It cannot tell that "Pre-Development Review" is the wrong
expansion of PDR. It cannot tell that the handbook does discuss the Agency
Baseline Commitment when a draft says it is not mentioned. And it cannot
tell that "the NASA Systems Engineering Handbook" is not the same answer as
"NPR 7120.5" when the only word they share came from the question.

v9 does those three with code and the whole corpus. Appendix A is parsed
into data/corpus/acronyms.json (187 entries, scripts/build_acronyms.py),
and an acronym expanded differently from the table is an unsupported
claim. A claim that the handbook does not mention, cover, discuss, address,
include or contain a term is checked against the full text. Verbs like
"specify" and "define" are left out, because "does not specify where X
happens" is an abstention about a detail. A claim containing a wh-word is
skipped for the same reason. And the words that back a "same answer"
must add something beyond the question's own words. Rerun on the same 40
drafts, v9 gave 38 of 39, 97 percent, rubric fidelity; the one miss was
sheet 19.

Then the 21 worked examples were rerun under v9 and the result was 18 of
21 labels with three order flips that changed the label, after v7 had had
none. The records showed why. v8 had added a fourth question to the judge,
whether the draft asserts anything unsupported. The judge answered YES to
true statements: the correct premise fix in example 17, a sentence the
evidence supports in example 9. Its presence also changed the first three
answers in one order. The sheet-1 gains, meanwhile, had come from the code
checks, not from that question. v10 therefore drops the fourth question,
returns the judge prompt to the v7 form, and keeps every code check. It
adds one more check. A capitalised name or acronym in the draft that is in
neither the question, nor the item's reference and evidence, nor anywhere
in the handbook is a claim brought in from outside. That is the
padded-answer case of sheet 32. The check also runs before the exact stage,
so a short right answer with an outside name attached is not accepted
without the judge.

v10 on the worked examples matches v7 exactly: 19 of 21 grades, 21 of 21
labels, one grade-only flip, none that change the label. Rerun on the
first 40 drafts, v10 gives 38 of 39 binary and 38 of 39 three-way,
97 percent (reports/grader-check-rubric-fidelity.md); the one miss is sheet
19, whose item moved to answerable. This is still not a blind number. The
blind number is 82 percent, and the second sheet (reports/grader-check-
sheet-2.md, 25 fresh drafts graded by v10 into data/eval/grader_check_key-2.
jsonl) is where an honest post-fix figure comes from. Below about 90
percent there, the grader is still not good enough for mass grading.

## Sheet 2 and grader v11, 2026-09-10

The owner graded the second sheet blind. Result for v10: 20 of 25, 80
percent binary agreement. Per bucket: answerable 9 of 9, unanswerable 5 of
6, ambiguous 3 of 4, false premise 3 of 6. Per condition: no passage 8 of
8, distractor 7 of 8, own evidence 5 of 9. That is the honest post-fix number, and it is
below the bar, so v10 is not signed off. The two blind figures now on record
are 82 percent for v7 on sheet 1 and 80 percent for v10 on sheet 2.

The five disagreements, read one by one. Sheet 15 was a grader defect. The
draft "The passage does not specify who wrote the original 1995 edition of
NASA SP-6105" only echoes the question, but "SP-6105" normalises to two
words and the echo check compared them as one. So the draft went to the
judge, whose copying call then answered NONE for an obvious refusal. v11
compares echoed terms word by word and grounds the "abstains" and "flags"
answers with the code's own refusal and clarify patterns instead of a
copying call. Sheets 13, 14 and 17 are bare abstentions on false-premise
items, CORRECT by rule, which the owner graded WRONG. That is the owner's
own ruling on sheet 16 in reverse, and it happened three times out of six
false-premise drafts. The rule has to be settled one way; both the grader
and the sensitivity alternative depend on it. Sheet 10 is q0115, an
ambiguous item whose validation reading the owner treated as the natural
answer, and it is one of the twelve close calls.

v11 numbers. The 21 worked examples are unchanged from v7: 19 of 21
grades, 21 of 21 labels, one grade-only flip. Rubric fidelity on the first
40 stays at 38 of 39. Sheet 2 regraded by v11 after the owner's grades were
seen reads 21 of 25, 84 percent (reports/grader-check-result-2-v11-posthoc.md).
That last figure is not blind and is not the number that gates anything; it
only shows what the sheet-15 fix is worth.

## Ambiguous pass, 2026-09-09

The blind item check put the item problem in the ambiguous bucket, so every
ambiguous candidate was tested against one question: would a person asking
this question have both readings in mind? Of 39 items, 20 hold up. Four
move to answerable: the owner's three blind labels, and q0124, where the
owner's grade on the grader check took the Flight Readiness Review as the
natural answer. Three are duplicates the code check missed and are dropped.
Twelve are close calls left to the owner in reports/ambiguous-calls.md,
since language model verifiers produced the problem and the author of the
pass is one too. The bucket will end between 20 and 32 items depending on
those calls, so the 40-item target for ambiguous is out of reach without
more drafting. The 200-item plan (70/40/50/40) needs either fewer ambiguous
items or a second drafting round for that bucket only.

## The owner's twelve ambiguous calls, 2026-09-10

The owner decided the twelve close calls (their words are kept in
reports/ambiguous-calls.md and data/eval/ambiguous_pass.jsonl). Ten agreed
with the pass's lean; two reversed it, and each reversal carries a rule.
q0095 moves to answerable because the handbook's unqualified sentence, "the
SE engine cycles five times", settles a question that treats the engine as
one object, while the seven is explicitly scoped. The gold is five, with a
scoped seven accepted. q0111 moves because one figure gives both halves of the
answer, so a single two-part answer satisfies every asker; the gold is the
compound. q0104 and q0115 are dropped, q0097, q0106, q0114 and q0123 kept,
and q0108, q0117, q0119 and q0132 moved with the golds the owner named,
including a scoped TRL 5 as an accepted form. q0109 was reworded to name
the ConOps, because the owner moved q0108 ("operations concept") to the
operational team and the two near-identical questions had contradictory
golds. The ambiguous bucket ends at 24 items; the pool is 236: answerable
104, ambiguous 24, unanswerable 59, false premise 49.

The two reversals generalise, and were not applied beyond their items. The
q0095 rule, that an unqualified statement beats a scoped one, fits q0096,
"How many phases make up the NASA life cycle?". There, "NPR 7120.5 defines
the major NASA life cycle phases as Formulation and Implementation" is the
unqualified sentence and the seven are its "incremental pieces". The owner
labelled q0096 ambiguous in the blind check, so it stays until they say
otherwise. The q0111 rule, that one passage giving both halves makes a
compound answer rather than two readings, fits three kept items. q0106 has
both approvers on page 40; the owner kept it narrowly and asked to have it
rewritten. q0118 has both recipients in one sentence on page 106. q0122 has
two adjacent sentences on page 152. The q0104 rule, that two passages
disagreeing is inconsistency and not ambiguity, may fit two more. q0101 has
the ConOps baselined in three different phases across tables, which the
owner called worse than a two-way split. q0125 has verification plans
approved at both CDR and SIR.
The q0132 rule, that the glossary's unqualified line makes one TRL
dominant, fits q0131 (system prototype at TRL 6 or 7). If the owner extends
all of those, the bucket falls from 24 to 17.

## Target for the set, proposed 2026-09-10

Drafted plan: 200 items as 70 answerable, 40 ambiguous, 50 unanswerable,
40 false premise, with 240 if drafting was fast. The pool after the pass
cannot supply 40 ambiguous items and 240 is out of reach. Proposed: 200
items as 86 answerable, 24 ambiguous, 50 unanswerable, 40 false premise.
The 16 items the ambiguous bucket cannot fill go to answerable, which has
the largest surplus and the most reliable labels (14 of 14 in the blind
item check). That leaves 18 answerable, 9 unanswerable and 9 false-premise
items in reserve for fixes and drops from the review sample, and no
ambiguous reserve: any ambiguous item the review drops is replaced from
answerable. The alternative is a second drafting round for ambiguous items
only. The first round kept 24 of 48 drafted after the dominant-reading
pass, so reaching 40 would mean drafting about 35 more and running the
pass again. The proposal awaits the owner's approval; nothing is locked.

## A bare abstention on a false premise is PARTIAL, 2026-09-10

The trail is worth keeping. On the first blind sheet the owner graded a
bare abstention on a false-premise item WRONG (sheet 16). Shown the
disagreement, the owner withdrew it: a bare abstention fails safe and stays
CORRECT, as the guide's table said. On the second blind sheet the owner
then graded three more bare abstentions on false premises WRONG (sheets 13,
14 and 17) on instinct, against that ruling. Asked to settle the rule one
way, the owner settled on PARTIAL: a bare abstention neither acts on the
false premise nor corrects it. Grader v12 applies that by rule when nothing
specific follows the refusal, and through the judge otherwise (a refusal
that neither rejects nor builds is PARTIAL; anything else that neither
rejects nor builds is WRONG). The revisions file keeps only sheet 34, since
the owner's original WRONG grades on sheets 9, 16 and 33 now match PARTIAL
on the binary label.

Effect. The 21 worked examples are unchanged: 19 of 21 grades, 21 of 21
labels, one grade-only flip. The first 40 drafts: binary agreement stays at
38 of 39; three-way agreement falls from 38 to 35 of 39, because the three
bare abstentions the owner graded WRONG are now PARTIAL. Sheet 2 regraded
by v12 after the owner's grades were seen: reported in the next section.

## Sheet 2 in the report: 80 percent blind, decomposed

Sheet 2 stands in the report as 80 percent blind agreement under v10, 20 of
25. It decomposes into three parts. One grader defect, fixed in v11 (sheet
15). One noise flip on an ambiguous item that has since been dropped as a
duplicate (sheet 10, q0115). Three instances of one underspecified rule,
the bare abstention on a false premise, now resolved as PARTIAL (sheets 13,
14 and 17). The 84 percent that v11 reached on the same sheet after the
owner's grades were seen is rubric fidelity, not a blind figure, and is not
presented as one. There is no third sheet now. The grader's signed-off
number will be a final blind check of about 20 real agent outputs at M8,
graded by the owner without seeing the judge on the grader version that
graded the dev set.

## The four generalisations, extended, 2026-09-10

The owner extended all four rules from the twelve calls to the items they
fit. q0096 moved to answerable under the q0095 rule, gold "two: Formulation
and Implementation" with a scoped seven accepted. The owner's blind label
had read q0096 as ambiguous; the owner's later rule disagreed with the
owner's earlier label on that item, and the rule won. q0106, q0118 and
q0122 moved under the q0111 rule with compound golds drawn from both
passages; for q0106 that is the rewrite the owner asked for, done as a
compound gold rather than a new question. q0101 was dropped under the q0104
rule. q0131 moved under the q0132 rule, gold "a relevant environment" with
the TRL 7 space environment accepted when scoped. q0125 was listed under the
q0104 rule and re-read: its two approvals are two versions of the plans,
build-to at CDR and as-built at SIR, like q0102's two plans, not a
disagreement, so it stays ambiguous. The ambiguous bucket ends at 18 items.
The pool is 235: answerable 109, ambiguous 18, unanswerable 59, false
premise 49.

## Target approved: 200, ambiguous as it survives, 2026-09-10

The owner approved 200 items with the ambiguous bucket at whatever
survived and the shortfall going to answerable, and no second drafting
round. That is 92 answerable, 18 ambiguous, 50 unanswerable, 40 false
premise. The limitation goes into the report in these words: genuinely
ambiguous questions proved rare, the bucket ended at 18 against a planned
40, so conclusions about clarification behaviour rest on a small sample.

## Locked and split, 2026-09-10

scripts/lock_and_split.py drew the set from the 235 candidates with seed
42, stratified by bucket: 92 answerable, 18 ambiguous, 50 unanswerable, 40
false premise, 200 in all, then split each bucket in half with the same
seed. dev.jsonl and test.jsonl hold 100 items each: 46 and 46 answerable, 9
and 9 ambiguous, 25 and 25 unanswerable, 20 and 20 false premise. Ten of
the 200 need the calculator. Thirty-five candidates stay in
items_reserve.jsonl for fixes. The 10-per-bucket review sample drawn before
the dominant-reading pass was never used and is retired; the owner's blind
item check and ambiguous calls stood in for it, and the owner locked on
that basis. The test half is now read by exactly one script, once, at the
end of M8, and nothing is tuned on it.

## For the report: the ambiguous bucket is indicative only

The owner's note on confirming the counts, kept here so it is not lost by
M8: the ambiguous bucket has 9 dev and 9 test items. Any claim about
clarification behaviour rests on that, so per-bucket tables at M8 must
show the counts alongside the rates, and the text must say the ambiguous
numbers are indicative only. q0125 stays in the bucket: two versions of a
plan is a real split.

## Retriever built; top-k measured on dev, 2026-09-10

The index is bge-small-en-v1.5 vectors in a flat FAISS index over the 773
chunks (docs/explanations/02-retriever.md, src/agent/retriever.py,
scripts/build_index.py). Embedding the corpus took 127 s on the CPU. The
vectors live in data/index/, which is gitignored and rebuilt by script; the
loader refuses a saved index whose chunk ids differ from chunks.jsonl.

scripts/retrieval_recall.py measured, on the 100 dev items only, how often a
chunk holding the evidence quote sits in the top k. Every evidence quote
was found in some chunk. Recall at k without neighbours: 1 gives 49
percent, 3 gives 63, 5 gives 70, 8 gives 77, 10 gives 79. With one
neighbouring chunk on each side: 3 gives 71, 5 gives 77, 8 gives 80, 10
gives 82. Per bucket at k of 8 without neighbours: answerable 38 of 46,
ambiguous 8 of 9, false premise 17 of 20, unanswerable 14 of 25. For
unanswerable items the target is the closest passage, which the agent does
not need in order to abstain. Average context per question: about 190
words per chunk, so 1,500 words at k of 8 and 2,350 words at k of 5 with
neighbours; tokens run about 1.3 times words. The choice of k is the
owner's; the numbers are recorded here so it is made from measurement.

## M2 design, decided by the owner on 2026-09-10

CLARIFY and ABSTAIN are both a prompt instruction and a rule, so the
behaviour exists even when the model does not produce it, and so the trace
records which path fired. The CLARIFY rule is not a retrieval statistic,
because no statistic means "two readings" and a score-gap rule would fire
on any question that spans sections. It is a readings step: the model lists
the readings the passages answer differently, and code decides CLARIFY when
more than one reading has a different answer. The step will over-list, so
its firing rate on answerable dev items is measured and reported as a
false-clarify rate. Above about a fifth of answerable items, the step gets
a stricter bar before M4. The ABSTAIN rule fires when the best retrieved
chunk scores below a threshold set on dev, or when the draft says the
handbook does not say.

The calculator is narrow: two operands, plus, minus, times, divide and
percent, with dollar signs and M or B suffixes parsed. That is what the
calculator items need (differences of two stated figures, a ratio, a
percentage). There is no expression evaluator.

The OpenAI-compatible backend is not built. The provider is a protocol with
one method, which the Ollama provider satisfies. A second implementation
would be a later file.

Retriever: k of 8, no neighbours, window kept at 4,096 tokens. Measured on
dev it recalls the evidence chunk for 77 percent of items at about 1,500
words of context. The alternative was k of 5 with one neighbour each side,
the same 77 percent overall at 2,360 words, which would have bought
answerable recall of 40 of 46 instead of 38 of 46; the smaller context
leaves margin on the 4 GB card when the judge is loaded.

## M2 must implement CLARIFY and ABSTAIN as real actions

On the grader check the model under test scored 0 of 4 on ambiguous items
and 1 of 4 on false-premise items. Without a clarify action and an abstain
action available to the agent, the ninety-odd items in those two buckets
would measure a missing feature rather than confidence. M2 therefore builds
both as first-class actions of the plan-act loop (ask which reading is
meant; say the handbook does not cover it), before any signal is measured.

## Dev run v1, untuned, 2026-09-10 and 2026-09-11

The first full run of the agent over the 100 dev items, k=8, no abstain
threshold, graded by v12 (reports/dev-run-v1.md, rows in
reports/dev-run-v1.jsonl, one per item with the trace and the grade). The
owner asked for the confounder number from the first run, not derived
later, so the trace records whether a target evidence chunk was retrieved
and at what rank, using the recall script's definition.

Results the next steps rest on. Answerable accuracy is 27 of 38 with the
evidence retrieved and 2 of 8 without it. The false-clarify rate is 6 of 46
(13 percent), under the owner's bar of a fifth; one of the six was a format
slip (the model wrote ONE READING as an answer inside a READING line), and
the parser now drops such lines, which was not rerun. The other five list
a contrast rather than a reading: verification against validation, six
steps against seven, an Event Readiness Review against a Key Decision
Point. The model built on the false premise in 14 of 20 items and never
corrected one; the other 6 abstained (PARTIAL). Spurious CALC lines on 7 of
96 non-calculator items, all uncomputable. The best retrieval score does
not separate correct from incorrect answers (medians 0.755 and 0.752) and
barely separates retrieved from unretrieved evidence (0.748 and 0.727), so
a score threshold would abstain almost at random. The threshold is chosen
with the owner from those distributions, not in this pass.

Grader note, not acted on. Both rule-composed CLARIFY responses on
ambiguous items (q0107, q0126) were graded WRONG by the judge, which
answered NO to "asks which reading is meant" although the guide's rule
grades a CLARIFY that names the two readings CORRECT. A code rule for a
CLARIFY that names both readings would be grader v13; it needs the 21
examples and both rubric-fidelity sheets rerun first. The grades stand as
v12 gave them.

Time. 1,800 s for 100 items, half in the readings step and half in the
draft; retrieval is negligible. Grading was interrupted once by a session
end and once by a dropped connection; the final pass took 710 s with 53
items replayed from the cache, so no clean grading wall clock exists for
this run.

## The retrieval score is a signal, not an abstain trigger, 2026-09-11

The owner dropped the score threshold as an ABSTAIN rule after the first
dev run, on these numbers from reports/dev-run-v1.md: the median best
score was 0.755 for answered items graded CORRECT and 0.752 for answered
items graded otherwise; 0.748 when the evidence chunk was retrieved and
0.727 when it was not; and the unanswerable bucket's median of 0.711 sits
inside the answerable range (0.647 to 0.863). A cut anywhere would abstain
almost at random. ABSTAIN is now the prompt's alone. The score stays in
every trace and goes to M3 as a retrieval-support signal, where a
calibrator can weigh it against the others rather than act on it alone.
Anyone proposing a threshold later starts from those medians.

## Grader v13: a clarifying question that names both readings, 2026-09-11

The judge answered NO to "asks which reading is meant" on both
rule-composed questions of the form "do you mean X, or Y" in the dev run,
against the guide's rule that a CLARIFY naming both readings is CORRECT.
v13 decides that case in code. The draft must contain a "do you mean"
question offering one alternative per reading; each alternative must share
at least two content words with its reading or that reading's answer, and
that pairing must fit better than any other, so two alternatives that only
echo the question do not pass. A question that names one reading, or none,
still goes to the judge. Checked before use: examples 19 of 21 grades, 21 of
21 labels, no binary flip against v12; sheet 1 rubric fidelity 39 of 39
binary (the one change from v12, sheet 19, is the pool snapshot's bucket
for that item, not the rule); sheet 2 rubric fidelity 24 of 25 binary,
unchanged. On the dev run one grade changed, q0107, WRONG to CORRECT. The
composed question on q0126 names one reading (both alternatives describe
the Flight Readiness Review) and stays with the judge, WRONG. Both regrades
of the sheets use scripts/regrade_key.py against the pool snapshot the
sheets were built from (git 7a2a82d), so the drafts are exactly the ones
the owner graded.

## The label distribution before M3, 2026-09-11

On dev v1 the labels are 54 of 100 correct pooled, but two buckets are
nearly constant: unanswerable 23 of 25 correct, false premise 0 of 20. The
action decides the label and the bucket decides the action, so a pooled
calibrator can score well by detecting the bucket. The decisive stratum is
answerable items with the evidence retrieved, 27 right against 11 wrong,
where the model's judgement rather than retrieval decides the outcome.

The owner decided, on 2026-09-11:

- A bucket-detector test is a standing M4 commitment, three checks: predict
  the bucket from the signal vector against the prior; calibration within
  answerable alone; calibration within answerable with evidence retrieved.
  Reported either way. Bootstrap intervals on every reliability diagram
  from the start; with dev at 135 and the decisive stratum near 40 items
  the conclusion is expected to be directional, not precise, and the report
  says so up front.
- A premise-check step in the loop, same shape as the readings step, with a
  grounding gate in code: the model names the assumption and the passage
  that contradicts it, and code accepts the rejection only when the
  assumption comes from the question and the correction's words are in the
  cited passage. Its false-fire rate on answerable and unanswerable dev
  items is measured against the same one-fifth bar as the readings step.
  The report states that the false-premise bucket was zero before the step
  existed. Because the loop changes, the whole dev set is rerun so dev is
  one agent, and the v1 run stays in the report as the before.
- The 35 reserve items (17 answerable, 9 unanswerable, 9 false premise, no
  ambiguous, no calculator) join dev after the premise step, through the
  same code checks, as a labelled second run. Merging the reserve means
  nothing can be swapped in later without a new drafting round; the owner
  accepted that.
- Not done: sampling each item at several retrieval k. The rows would not
  be independent, the variation would be in one signal by construction, and
  the run time triples. It stays available as a separate M4 experiment if
  the calibrator turns out to be a retrieval detector.
- Nothing touches test.

## The premise gate, 2026-09-11

The premise step's first version accepted a rejection when the assumption
shared two words with the question and the correction shared two words
with the cited passage. On the first dev item it fired falsely: the model
put the answer in the ASSUMPTION slot and an unrelated sentence in
CORRECTION, and both shared enough words to pass. The gate now has three
checks. The assumption must be taken from the question: at least two
content words and at least 60 percent of its words occur there, which a
restated answer fails. The correction must be grounded in the cited
passage by at least two words that are not in the question, so an echo of
the question cannot pass for grounding. And the correction must share at
least one word with the assumption, so it is about the same thing. The
run was stopped after that one item and restarted with the gate; the item
is now a test case. The false-fire rate on answerable and unanswerable dev
items is the measure of whether this is enough.

## Dev run v2: the premise step measured, 2026-09-11

The whole dev set was rerun with the premise step (reports/dev-run-v2.md;
v1 kept in it as the labelled before). The step did not do what it was
for. On false-premise items the model claimed a contradiction on 8 of 20,
the gate passed 4, and all 4 were graded WRONG: the "corrections" were
passage sentences unrelated to the assumption, so the bucket stays at 0 of
20 correct. Elsewhere the step cost labels: 6 false REJECTs on answerable
items (13 percent) and 4 on unanswerable (16 percent), under the one-fifth
bar but every one of them wrong, and 5 of 9 ambiguous items went to REJECT
ahead of CLARIFY. The prompt sentence added for the step also changed
drafts: 3 answerable items that were correct in v1 abstained in v2. Net,
correct labels fell from 54 to 41 of 100, with one gain. The step added
1,492 s to the run, more than half the wall clock. Owner's call pending on
whether the step stays, is switched off with prompts identical to v1, or
is reworked. Nothing touched test.

## The premise step is off, 2026-09-11

Owner's decision after run v2: option 1. The step stays in src/agent/loop.py
behind the premise_check flag, off by default, with its tests, and
reports/premise-step.md writes the negative result up for the report body.
With the flag off the answer prompt is the v1 text, checked two ways: a
test holds the v1 prompt copied from commit 799b58a and asserts equality,
and a rerun of all 100 dev items with the flag off drew every one of its
210 model calls from the cache, which only happens when every request is
byte-identical to v1. That rerun differs from v1 in two actions, both from
the ONE READING parser fix made after v1 and never rerun: q0082 CLARIFY to
ABSTAIN and q0126 CLARIFY to ANSWER. Its graded rows (reports/dev-run-v1b.
jsonl) are therefore the current agent's dev rows; v1 stays as the record
of the run before the parser fix. The false-premise bucket stays at zero
and the limitation stands as written.

Reserve: q0118 dropped rather than rewritten, since its gold answer runs
past the 12-word limit the locked items met and the owner's rule is not to
rewrite items. The other 34 join dev as a labelled second run.

Reserve run (reports/dev-run-reserve.md): 843 s for 34 items; answerable 6
of 16 correct, unanswerable 9 of 9, false premise 0 of 9. Merged dev is 134
items, 70 correct (reports/dev-distribution.md); the decisive stratum,
answerable with evidence retrieved, is 33 right against 17 wrong.

## M3 rules, decided by the owner on 2026-09-11

The five M3 positions stand: all five signals, built in cost order (trace
process signals and retrieval support first, log-probabilities, verbalized
confidence, sampling agreement last); agreement with k=5 at temperature
0.7 measured by the grader's own normalise-and-overlap rather than a second
embedding model; both bge cosine and a small NLI cross-encoder for
retrieval support; a single follow-up call for a 0 to 100 confidence; a
binary label, CORRECT against not. Four additions from the owner:

1. Leakage, the most important rule. Anything derived from the item record
   rather than from the run is ground truth and never enters the feature
   vector: the evidence-retrieved flag and rank, bucket membership, the
   gold answer, the expected action, the calculator flag and the spurious
   CALC flag that depends on it. They are stratification variables for
   reporting only. Before anything is fitted at M4, every feature is listed
   with where it comes from and a statement that it is computable at
   inference time on a question with no known answer. A feature that fails
   that test is out. A calibrator that silently sees ground truth looks
   excellent and means nothing.
2. Sampling agreement stores the raw k samples in the trace, so the
   agreement function can change at M4 without a rerun, and measures
   agreement between the graded draft and the k samples as well as among
   the samples, because the label belongs to the graded draft. The report
   notes that token overlap reads paraphrases as disagreement, so the
   signal partly measures lexical variance; the raw samples let M4 check.
3. The verbalized-confidence call sees the retrieved passages as well as
   the question and answer, so it rates a grounded answer rather than
   guessing from memory. The trace records that choice and the raw reply.
4. Build stops after the free signals and retrieval support for a first
   feature table on dev, before the paid ones run.

## First feature table, free signals, 2026-09-11

reports/features-dev.md lists 30 features from the run alone, each with
its provenance and the statement that it exists at inference time, and
the ground-truth fields kept out (evidence flag and rank, bucket, gold,
expected action, calculator flags). Built on the 134 merged dev items.
What the table shows: the pooled label gaps are mostly bucket gaps
(unanswerable items abstain, are short, and score high on NLI
contradiction because "the handbook does not say" contradicts any
passage). In the decisive stratum, answerable with evidence retrieved, 33
right against 17 wrong, the features that separate are the support ones:
lexical support 0.73 against 0.49, cosine to the best chunk 0.77 against
0.71, and the action itself, since every wrong item that clarified or
abstained sits there. NLI entailment does not separate (0.33 against
0.33). One feature is constant on dev, clarify_by_prompt, and is dropped
at M4. The paid signals wait for the owner's read of the table.

## Guard for M4, decided before any fitting, 2026-09-11

The action features separate inside the decisive stratum because every
wrong clarify and abstain lands there. That is partly circular: the action
is downstream of the same model state the signals try to measure. So M4
fits and reports two variants, not one: the full vector, and the full
vector minus the action features (action_answer, action_abstain,
action_clarify, clarify_by_prompt, abstain_by_prompt, response_form_answer,
response_abstain_phrase, readings_fired). If most of the apparent skill
disappears without them, the calibrator is largely an action detector and
the report says so. Recorded now so it is not a decision made after
seeing results. Two smaller rules for the paid signals: the raw token
log-probability sequence is stored per draft, not only mean and min, so a
third summary needs no rerun; and each paid signal's time per item is
recorded and reported, so the report can state what the approach costs.

## Paid signals measured, 2026-09-11 and 2026-09-12

All three paid signals ran on the 134 dev items (reports/features-dev.md,
raw records in reports/paid-signals-dev.jsonl: token sequences, confidence
replies, five samples per item). Cost per item, uncached: log-probabilities
12 to 15 s, verbalized confidence 8 s, sampling with k=5 at 0.7 about 23 s,
so the paid signals add about 45 s to an 18 s answer.

A finding about determinism. The log-probability draft is regenerated at
temperature 0 with the run's seed, and the plain call for the same
messages is served from the cache, yet the regenerated text differed from
the traced draft on 44 of 134 items (37 of 100 and 7 of 34). Ollama's
greedy decoding is not identical across sessions or with logprobs on. The
sequence therefore describes the model's state on the same prompt, not
the graded text's tokens; the mismatch is a feature (lp_same_text) and
the caveat goes in the report.

In the decisive stratum (33 right, 17 wrong): verbalized confidence is 100
on every correct item and 83 on average for wrong ones, with almost every
reply a round number; agreement with the graded draft separates (max
Jaccard 0.85 against 0.70, form agreement 0.95 against 0.77); the
log-probability summaries barely move (first-token -0.16 against -0.28,
mean -0.18 against -0.19, minimum reversed). Nothing is fitted yet.

## M4 on dev: three variants, three strata, the log-probabilities dropped, 2026-09-12

Before fitting: the log-probability mismatch is 44 of 134 pooled and 20 of
50 in the decisive stratum, and on the matched subset the logprob means by
label are flat (reports/logprob-mismatch.md). Fitted as planned
(reports/m4-calibration.md, reading in reports/m4-calibration-reading.md):
out-of-fold AUROC 0.73 pooled and 0.76 decisive for the full vector; the
same without the action features, so the calibrator is not an action
detector; a bucket-detector accuracy of 0.59 against a prior of 0.46,
with discrimination surviving inside the stratum, so not only a bucket
detector. Dropping the logprob features costs 0.04 pooled and 0.10 in the
stratum on point estimates, and a post-hoc diagnostic, labelled as such,
showed the whole gain is lp_tokens, the token count of a regenerated text
that differs from the graded one on 40 percent of the stratum. That is a
length artefact, not a confidence signal, so the logprob features are
dropped and the cost is stated. Recommended: minus_logprobs with logistic
plus isotonic. Artifacts for all three variants, fitted on all of dev with
seed 42 and library versions, are in data/calibrators/. Test untouched.

## Calibrator confirmed, and two reporting rules, 2026-09-12

The owner confirmed minus_logprobs with logistic plus isotonic. Two rules
for the report from now on. Every headline number carries its interval:
no bare point estimate in the abstract, the README or the results
summary, because at 134 items the honest claim is that confidence carries
real but weak information beyond action and bucket, shown inside the
stratum where both are fixed. And the lp_tokens diagnostic is written up
in the results, next to the v9 judge question and the pool-snapshot
episode, as a worked example of a feature that looks predictive and is an
artefact. The report also names the finding that the free support
features beat all three paid signals, which roughly triple the cost per
question; that runs against the usual expectation that sampling-based
uncertainty leads. docs/report.md is the standing draft that carries all
of this.

## M5 policy, decided by the owner on 2026-09-12

VERIFY is a display state: the answer is shown with a flag that it needs
checking, no extra model calls. The problem statement's tool-based
verification loop is therefore not implemented, and the report says so
plainly. Two reasons it was not expected to pay. Retrieval recall on dev
is 77 percent at k=8 and the same at k=10, so re-retrieving at a larger k
buys little, and a second draft on the same model mostly reproduces the
first. And the premise step is the precedent: a second model pass built
to fix a measured gap made every bucket worse (reports/premise-step.md).
A verification loop would need the same measurement before it earned a
place, and there was no budget for another negative result.

ESCALATE withholds the answer and hands the question to a human with the
trace attached. The agent's own CLARIFY and ABSTAIN stand; the policy
decides among ANSWER, VERIFY and ESCALATE only for items the agent
answered, and a confident abstention passes through as the answer "the
handbook does not say". Thresholds are tuned to a target risk, the error
rate among answered items, on the out-of-fold probabilities of the
confirmed calibrator over all 134 dev items, pooled, reported per bucket
and in the decisive stratum. The target is the owner's, chosen from the
risk-coverage curve with its bootstrap band and a table of candidates (10,
15, 20, 25 percent) with the coverage each buys, intervals on both, and
the base rate on the same table. The report states what the policy does
to the unanswerable bucket, 32 of the 70 positives: a policy that keeps
coverage high by passing easy abstentions while escalating everything
hard would score well and be useless, and if that is what happens the
report says so. M5 adds the risk-coverage curve with its band and a
per-bucket table of the policy's actions with counts next to rates.
Nothing is tuned until the owner picks the target. Test is not touched.

## Thresholds chosen, 2026-09-12: a coverage choice, not a risk guarantee

On the out-of-fold probabilities of the confirmed calibrator, no risk
target of 10, 15, 20 or 25 percent among answered items was reachable
with meaningful coverage on dev: the risk stays near 40 percent from 20
to 80 percent coverage and reaches 17 [0, 55] percent only at 9 [3, 16]
percent coverage (reports/m5-risk-coverage.md, thresholds tie-aware). The
owner chose option 2 with a tertile VERIFY band: ANSWER at or above 0.58,
VERIFY from 0.35 to 0.58, ESCALATE below 0.35, recorded in
data/calibrators/policy.json next to the calibrator artifact. Rules for
reporting it: no claim that the policy reduces error, since the intervals
overlap heavily; the point estimate moves in the expected direction and
the interval does not exclude no effect; the claim waits for the single
read of test at M8. The corrected halving figure stays visible as a
measurement-integrity episode. The deployed columns carry the caveat
about 34 pass-through abstentions and 11 PARTIAL false-premise
abstentions wherever they appear. The 20 percent target at threshold
0.846, six of seventy answered items shown, is reported as the
alternative so a reader sees what a risk guarantee would cost.
