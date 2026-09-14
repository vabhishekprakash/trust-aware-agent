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
again, and each YES then goes back to the judge as a small copying task,
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
the judge because a capitalised name followed the refusal, and the judge
answered that the draft offers an answer. The rubric gaps, which the guide
does not settle and the owner's grades do: three abstentions phrased as
"the passage does not provide" rather than the handbook, one of them adding
a wrong expansion of PDR and one adding a false claim about what the
handbook mentions, which the owner graded PARTIAL and the grader CORRECT;
one bare abstention on a false-premise item, CORRECT by the guide's table
and WRONG to the owner; one right answer padded with claims from outside
the handbook (the Aerospace Industries Association, defence), CORRECT to
the grader and PARTIAL to the owner; and one ambiguous item whose one-sided
answer the owner graded CORRECT, reading the item as having a natural
answer. Those six are decisions for the owner before the grader changes.

Item check. The owner labelled 40 held-back items from the handbook alone.
Bucket agreement 37 of 40, 92 percent: answerable 14 of 14, and the owner's
answer contained the gold answer or an alias every time; unanswerable 10 of
10; false premise 8 of 8, corrections matching the drafted fix; ambiguous 5
of 8. The three misses were drafted as ambiguous and read as answerable:
the second reading rested on a distinction the handbook draws (Concept of
Operations against Operations Concept, MOEs against MOPs, requirements
validation against product validation) that a user asking the question
would not have in mind. In two of the three the owner noted the near-call.
That is the failure the guide names, "if one reading is clearly what any
reader would mean, the item is not ambiguous", and it is the bucket to
re-read across all candidates during the review. Unanswerable, which the
owner expected to be the shakiest bucket, matched on every item.

Both figures are measured limitations and go into the final report as they
stand.
