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
marked right or wrong: the rubric, what does the grading (a rule, a model, or a
person), and what happens on a partial match. The owner signs off on 20 graded
examples spanning correct, wrong, and borderline before mass labelling starts.
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
or newer. PyTorch is the CPU build from PyPI: the embedding and entailment
models are small enough for CPU, and the single 4 GB GPU is left to Ollama for
the language model.

## License: MIT

Chosen as the default for a student project that should be easy to reuse. It
can be changed before the first release if the owner prefers otherwise.
