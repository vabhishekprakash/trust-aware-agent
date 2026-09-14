"""The live system: one question in, the agent's answer with its calibrated confidence and reasons out.

Runs exactly what was measured on dev: the agent loop with the premise
check off, the free signals from the trace and the retrieved chunks, the
verbalized-confidence call and five resampled drafts (the calibrator's
vector needs them), the shipped calibrator with its display cap, and the
policy thresholds. Nothing from any item record is read on this path.
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Optional

import numpy as np

from agent.loop import Agent, draft_messages
from agent.provider import OllamaProvider
from agent.retriever import Hit, bge_embedder, load_chunks, load_index
from explain.contributions import DISPLAY_NOTE, Explainer, breakdown
from policy.router import Thresholds, decide, load_thresholds
from signals.agreement import agreement_features
from signals.process import process_features
from signals.retrieval_support import nli_model, support_features
from signals.verbalized import confidence_features, confidence_messages

ROOT = Path(__file__).resolve().parents[2]
SAMPLES = 5
SAMPLE_TEMPERATURE = 0.7

OUTCOME_TEXT = {
    "ANSWER": "Shown as an answer.",
    "VERIFY": "Shown with a flag: check this before relying on it.",
    "ESCALATE": "Withheld. This question goes to a person, with the trace attached.",
    "CLARIFY": "The agent asks which reading is meant before answering.",
    "ABSTAIN": "The agent says the handbook does not answer this.",
}


class LiveSystem:
    def __init__(self, model: str = "qwen2.5:3b-instruct", base_url: str = "http://localhost:11434", k: int = 8,
                 variant: str = "minus_logprobs", cache_dir: Path = ROOT / "data" / "cache", thresholds: Optional[Thresholds] = None):
        self.chunks = load_chunks(ROOT / "data" / "corpus" / "chunks.jsonl")
        self.by_id = {c["id"]: c for c in self.chunks}
        self.embed = bge_embedder()
        self.index = load_index(ROOT / "data" / "index", self.chunks, self.embed)
        if self.index is None:
            raise RuntimeError("no index for the current chunks; run scripts/build_index.py")
        self.vector_of = {c["id"]: self.index.vectors[i] for i, c in enumerate(self.chunks)}
        self.nli = nli_model()
        self.provider = OllamaProvider(model=model, base_url=base_url, cache_dir=cache_dir, num_ctx=4096)
        self.agent = Agent(self.provider, self.index, k=k, premise_check=False)
        self.explainer = Explainer.load(variant)
        self.thresholds = thresholds or load_thresholds()
        self.runs: dict[str, dict] = {}

    def health(self) -> dict:
        try:
            import httpx

            version = httpx.get(f"{self.provider.base_url}/api/version", timeout=3.0).json().get("version")
            ollama = {"reachable": True, "version": version}
        except Exception as e:  # noqa: BLE001 - reported, not hidden
            ollama = {"reachable": False, "error": str(e)}
        return {"ollama": ollama, "model": self.provider.model, "calibrator": self.explainer.variant, "display_cap": self.explainer.display_cap,
                "thresholds": {"answer": self.thresholds.answer, "escalate": self.thresholds.escalate}, "nli_loaded": self.nli is not None,
                "chunks": len(self.chunks)}

    def ask(self, question: str) -> dict:
        timings = {}
        started = time.time()
        trace = self.agent.run(question)
        timings["loop"] = round(time.time() - started, 1)
        hits = [Hit(self.by_id[h["id"]], h["score"]) for h in trace["retrieval"]]
        ids = [h.chunk["id"] for h in hits]
        features = process_features(trace)
        features.update(support_features(trace["response"], [self.by_id[i]["text"] for i in ids], embed=self.embed,
                                         chunk_vectors=np.stack([self.vector_of[i] for i in ids]), nli=self.nli))
        messages = draft_messages(question, hits, False)
        t0 = time.time()
        reply = self.provider.generate(confidence_messages(messages, trace["draft"]["final"]), temperature=0.0, seed=trace["seed"], max_tokens=12).text
        features.update(confidence_features(reply))
        timings["confidence_call"] = round(time.time() - t0, 1)
        t0 = time.time()
        samples = [self.provider.generate(messages, temperature=SAMPLE_TEMPERATURE, seed=s, max_tokens=160).text.strip() for s in range(1, SAMPLES + 1)]
        features.update(agreement_features(samples, trace["draft"]["final"]))
        timings["sampling"] = round(time.time() - t0, 1)
        timings["total"] = round(time.time() - started, 1)

        explanation = self.explainer.explain(features)
        outcome = decide(trace["action"], explanation.probability, self.thresholds)
        run_id = uuid.uuid4().hex[:8]
        result = {
            "run_id": run_id,
            "question": question,
            "agent_action": trace["action"],
            "outcome": outcome,
            "outcome_text": OUTCOME_TEXT[outcome],
            "response": trace["response"],
            "confidence": round(explanation.probability, 3),
            "confidence_uncapped": round(explanation.uncapped_probability, 3),
            "display_cap": explanation.display_cap,
            "note": DISPLAY_NOTE,
            "gated": trace["action"] == "ANSWER",
            "breakdown": breakdown(explanation, outcome=outcome if trace["action"] == "ANSWER" else None),
            "families": [{"family": f, "log_odds": round(v, 3)} for f, v in explanation.by_family()],
            "pushes": [{"feature": c.feature, "phrase": c.phrase, "value": round(c.value, 3), "contribution": round(c.contribution, 3)}
                       for c in explanation.contributions[:8]],
            "passages": [{"rank": i + 1, "page": h.chunk["page_start"], "score": round(h.score, 3), "text": h.chunk["text"][:400]} for i, h in enumerate(hits)],
            "steps": [{"step": c["step"], "seconds": c["seconds"], "cached": c["cached"]} for c in trace["calls"]],
            "readings": trace["readings"]["parsed"],
            "clarify_by": trace["clarify_by"],
            "abstain_by": trace["abstain_by"],
            "samples": samples,
            "stated_confidence": reply.strip(),
            "timings": timings,
        }
        self.runs[run_id] = result
        return result

    def explain(self, run_id: str) -> Optional[dict]:
        r = self.runs.get(run_id)
        if r is None:
            return None
        return {k: r[k] for k in ("run_id", "confidence", "confidence_uncapped", "display_cap", "note", "breakdown", "families", "pushes")}
