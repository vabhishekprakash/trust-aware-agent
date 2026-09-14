"""Run the dashboard on localhost.

Usage:
    python scripts/serve.py [--port 8000] [--model qwen2.5:3b-instruct]

Needs Ollama running with the model pulled, the corpus and index built
(scripts/fetch_corpus.py, scripts/build_chunks.py, scripts/build_index.py)
and the calibrator artifact in data/calibrators. A live question takes
about 50 seconds on a 4 GB card: the loop, the confidence call, five
resampled drafts.
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--model", default="qwen2.5:3b-instruct")
    parser.add_argument("--base-url", default="http://localhost:11434")
    args = parser.parse_args()
    import uvicorn

    from api.app import create_app
    from api.live import LiveSystem

    system = LiveSystem(model=args.model, base_url=args.base_url)
    print(f"health: {system.health()}", flush=True)
    uvicorn.run(create_app(system), host="127.0.0.1", port=args.port, log_level="info")
    return 0


if __name__ == "__main__":
    sys.exit(main())
