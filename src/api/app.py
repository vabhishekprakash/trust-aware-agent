"""FastAPI app: health, ask, explain, the dev gallery, and the static dashboard page.

The app takes the live system as an argument so tests can pass a stub;
the real one is built by scripts/serve.py. Localhost only, no
authentication; the health endpoint says whether Ollama answers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
PAGE = Path(__file__).resolve().parents[1] / "ui" / "index.html"


class Question(BaseModel):
    question: str = Field(min_length=3, max_length=500)


def load_gallery(policy_path: Path = ROOT / "reports" / "m5-policy.json", oof_path: Path = ROOT / "reports" / "m4-calibration-oof.jsonl",
                 rows_paths: tuple = (ROOT / "reports" / "dev-run-v1b.jsonl", ROOT / "reports" / "dev-run-reserve.jsonl"), cap: Optional[float] = None) -> list[dict]:
    """The 134 dev items with outcome, out-of-fold confidence (capped for display), grade and bucket: ground truth for review only."""
    if not policy_path.exists():
        return []
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    responses = {}
    for p in rows_paths:
        if p.exists():
            for l in p.read_text(encoding="utf-8").splitlines():
                if l.strip():
                    r = json.loads(l)
                    responses[r["item_id"]] = {"question": r["question"], "response": r["response"], "grade": r["grade"]["grade"]}
    out = []
    for row in policy["rows"]:
        r = responses.get(row["item_id"], {})
        conf = row["probability"] if cap is None else min(row["probability"], cap)
        out.append({"item_id": row["item_id"], "bucket": row["bucket"], "agent_action": row["agent_action"], "outcome": row["outcome"],
                    "confidence": round(conf, 3), "grade": r.get("grade"), "question": r.get("question"), "response": r.get("response")})
    return out


def create_app(system: Any) -> FastAPI:
    app = FastAPI(title="Trust-aware agent", version="0.1")

    @app.get("/", response_class=HTMLResponse)
    def page():
        return PAGE.read_text(encoding="utf-8")

    @app.get("/health")
    def health():
        return system.health()

    @app.post("/ask")
    def ask(q: Question):
        return system.ask(q.question.strip())

    @app.get("/explain/{run_id}")
    def explain(run_id: str):
        r = system.explain(run_id)
        if r is None:
            raise HTTPException(status_code=404, detail="no such run")
        return r

    @app.get("/dev")
    def dev():
        cap = getattr(getattr(system, "explainer", None), "display_cap", None)
        return {"items": load_gallery(cap=cap), "note": "Bucket and grade are ground truth from the item records, shown here for review only; the live path never reads them. "
                                                       "Confidence is the out-of-fold probability the report measured, capped for display."}

    return app
