# Trust-aware agent

A question-answering agent that retrieves from a fixed document set, uses
tools, and estimates a calibrated probability that each answer is right before
showing it. When that probability is low it verifies, asks a clarifying
question, or hands the case to a person, and every score comes with a
plain-language breakdown of the signals behind it.

Built for L&T Technology Services problem statement Tech2607 (Techgium).

![Demo: a confident answer with its capped confidence, an escalated one, and the explanation panel](docs/assets/demo.gif)

The GIF is speeded up. A live question costs about 50 seconds on a 4 GB
card: the agent loop (retrieval, readings step, draft) about 20 s, the
confidence call about 8 s, and five resampled drafts about 23 s. The
calibrator was fitted with those paid signals in its vector, so the
dashboard runs the system that was measured rather than a cheaper
stand-in. The counterpoint is the project's main finding: the free
signals read from the trace carried more of the usable signal than any of
the paid ones, so a cheaper deployment would start there.

Status: early scaffolding. There are no results yet. The evaluation arrives in
milestone M8, and every number that appears in this file will come from a run
you can repeat.

## Quickstart

You need Python 3.10 or newer, git, and Ollama (https://ollama.com) for the
local model.

    git clone <this repository>
    cd trust-aware-agent
    python -m venv .venv
    .venv\Scripts\activate          # Windows
    source .venv/bin/activate       # macOS or Linux
    pip install -r requirements.txt
    pip install -e . --no-deps
    sh scripts/hooks/install-hooks.sh
    ollama pull qwen2.5:3b-instruct
    python scripts/check_logprobs.py
    pytest

Install from requirements.txt rather than from the package alone. It pins the
CPU build of PyTorch. On Linux the default wheel is the CUDA build, several
gigabytes this project never uses.

The hook install step matters. It copies the commit-msg and pre-push hooks into
.git/hooks, which git does not track. The commit-msg hook strips co-author
trailers and rejects subjects over 60 characters. The pre-push hook refuses to
push unless ALLOW_PUSH=1 is set, so nothing leaves the machine by accident.

The last script confirms that the model provider returns token log
probabilities, which one of the confidence signals depends on.

## Running the dashboard

With Ollama running and the model pulled (ollama pull qwen2.5:3b-instruct):

    python scripts/fetch_corpus.py
    python scripts/build_chunks.py
    python scripts/build_index.py
    python scripts/serve.py

Then open http://127.0.0.1:8000. The health tab says whether Ollama
answers. The dev gallery tab lists the 134 development items with their
outcome, confidence, grade and bucket, read from the committed reports.
The demo GIF is recorded with scripts/demo/record_gif.py, which needs
Playwright (uv pip install playwright; python -m playwright install
chromium); it is not in requirements.txt because the served app does not
need it.

## Running the evaluation

The development-set pipeline, in order: scripts/run_agent.py (traces),
scripts/grade_run.py (grader v13 with the local judge),
scripts/build_features.py with scripts/paid_signals.py (features),
scripts/fit_calibrator.py and scripts/finalize_calibrator.py (the
calibrator), scripts/policy_curve.py and scripts/policy_apply.py (the
thresholds). Every model call is cached under data/cache, so reruns are
cheap. The test split is read by one script, once, at the end; that
script arrives with milestone M8.

## Layout

    src/agent/         base agent, tools, tracing
    src/signals/       one module per confidence signal
    src/calibration/   training, thresholds, persistence
    src/policy/        the four-action router
    src/explain/       score breakdown in plain language
    src/api/           FastAPI app
    src/ui/            dashboard
    data/corpus/       source documents (extracted text; the PDF is fetched)
    data/eval/         labeled question sets, dev and test
    models/            trained calibrator artifacts
    reports/           plots, metrics tables, the evaluation report
    tests/
    scripts/hooks/     git hooks and their install script
    scripts/demo/      the scripted run used for the demo gif
    docs/              layman guide, numbered explainers, decisions

## Results

Development set only so far, 134 items, every number out of fold with a
95 percent bootstrap interval. The calibrated probability separates right
from wrong answers with an AUROC of 0.70 [0.61, 0.79] pooled and 0.63
[0.45, 0.80] inside the stratum where bucket and retrieval are held
fixed. The honest claim is that confidence carries real but weak
information beyond the action taken and the question's bucket. The free
signals read from the agent's trace beat the three paid signals, which
roughly triple the cost per question. The test split has not been read.
Full draft: docs/report.md; the choices and why: docs/decisions.md.

## License

MIT. See LICENSE.
