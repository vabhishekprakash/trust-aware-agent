# Trust-aware agent

A question-answering agent that retrieves from a fixed document set, uses
tools, and estimates a calibrated probability that each answer is right before
showing it. When that probability is low it verifies, asks a clarifying
question, or hands the case to a person, and every score comes with a
plain-language breakdown of the signals behind it.

Built for L&T Technology Services problem statement Tech2607 (Techgium).

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
    pip install -e ".[dev]"
    sh scripts/hooks/install-hooks.sh
    ollama pull qwen2.5:3b-instruct
    python scripts/check_logprobs.py
    pytest

The hook install step matters. It copies the commit-msg and pre-push hooks into
.git/hooks, which git does not track. The commit-msg hook strips co-author
trailers and rejects subjects over 60 characters. The pre-push hook refuses to
push unless ALLOW_PUSH=1 is set, so nothing leaves the machine by accident.

The last script confirms that the model provider returns token log
probabilities, which one of the confidence signals depends on.

## Running the evaluation

Not available yet. This section will hold the commands that build the index,
run the agent over the development set, train the calibrator, and score the
held-out test set once those parts exist.

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

None yet. See docs/decisions.md for the choices made so far and why.

## License

MIT. See LICENSE.
