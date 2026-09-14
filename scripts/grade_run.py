"""Grade every trace of a dev run with the current grader and keep every draft.

Usage:
    python scripts/grade_run.py [--traces data/traces/dev] [--out reports/dev-run-v1.jsonl]

The graded text is the agent's response, the thing a user would see, with
the agent's action as the form hint. When the response differs from the
final draft (a CLARIFY composed by the rule) the draft is graded as well, so
a later threshold or clarify decision can be judged on what the model would
have said. One row per item goes to the output file with the trace
essentials and the full grade record; a manifest next to it records the
grading wall clock. The test split is refused.
"""

import argparse
import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from agent.provider import OllamaProvider  # noqa: E402
from calibration.grader import GRADER_VERSION, ProviderJudge, grade  # noqa: E402

TRACE_KEYS = ("item_id", "bucket", "question", "model", "k", "abstain_threshold", "action", "clarify_by", "abstain_by", "form",
              "best_score", "retrieval", "retrieval_seconds", "readings", "draft", "response", "evidence", "needs_calculator",
              "spurious_calc", "calls", "seconds", "trace_version")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--split", default=str(ROOT / "data" / "eval" / "dev.jsonl"))
    parser.add_argument("--traces", default=str(ROOT / "data" / "traces" / "dev"))
    parser.add_argument("--out", default=str(ROOT / "reports" / "dev-run-v1.jsonl"))
    parser.add_argument("--judge", default="llama3.1:latest")
    args = parser.parse_args()
    if "test" in Path(args.split).name:
        print("refusing to read the test split")
        return 1

    items = {json.loads(l)["id"]: json.loads(l) for l in Path(args.split).read_text(encoding="utf-8").splitlines() if l.strip()}
    trace_dir = Path(args.traces)
    run = json.loads((trace_dir / "_run.json").read_text(encoding="utf-8"))
    judge = ProviderJudge(OllamaProvider(model=args.judge, cache_dir=ROOT / "data" / "cache", num_ctx=4096))

    started = time.time()
    rows, decided, grades = [], Counter(), Counter()
    for n, item_id in enumerate(run["ids"], start=1):
        item = items[item_id]
        trace = json.loads((trace_dir / f"{item_id}.json").read_text(encoding="utf-8"))
        row = {k: trace.get(k) for k in TRACE_KEYS}
        row["grade"] = grade(item, trace["response"], judge=judge, form_hint=trace["action"])
        row["draft_grade"] = None
        if trace["response"] != trace["draft"]["final"]:
            row["draft_grade"] = grade(item, trace["draft"]["final"], judge=judge)
        rows.append(row)
        decided[row["grade"]["decided_by"]] += 1
        grades[(item["bucket"], row["grade"]["grade"])] += 1
        g = row["grade"]
        print(f"{n:>3} {item_id} {item['bucket']:<14} {trace['action']:<8} {g['decided_by']:<6} {g['grade']:<8} {g['flag'] or ''}", flush=True)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    manifest = {
        "run": run,
        "grader_version": GRADER_VERSION,
        "judge": args.judge,
        "graded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "grading_wall_seconds": round(time.time() - started, 1),
        "decided_by": dict(decided),
        "grades": {f"{b}/{g}": c for (b, g), c in sorted(grades.items())},
    }
    out.with_name(out.stem + "-manifest.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"\n{GRADER_VERSION}: decided by {dict(decided)}; grades {manifest['grades']}\ngrading wall clock {manifest['grading_wall_seconds']:.0f}s -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
