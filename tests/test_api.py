"""API tests with a stub system: no model, no index."""

import json

from fastapi.testclient import TestClient

from api.app import create_app, load_gallery


class StubExplainer:
    display_cap = 0.67


class StubSystem:
    explainer = StubExplainer()

    def __init__(self):
        self.runs = {}

    def health(self):
        return {"ollama": {"reachable": False, "error": "stub"}, "model": "stub", "calibrator": "minus_logprobs", "display_cap": 0.67}

    def ask(self, question):
        r = {"run_id": "abc12345", "question": question, "agent_action": "ANSWER", "outcome": "VERIFY", "outcome_text": "Shown with a flag.",
             "response": "The Program Manager.", "confidence": 0.57, "confidence_uncapped": 0.57, "display_cap": 0.67, "note": "This system does not report certainty.",
             "gated": True, "breakdown": "Confidence 57 percent, so the policy says VERIFY.", "families": [{"family": "support from the passages", "log_odds": 0.4}],
             "pushes": [], "passages": [{"rank": 1, "page": "20", "score": 0.8, "text": "The SEMP is approved by the Program Manager."}],
             "steps": [{"step": "readings", "seconds": 9.0, "cached": False}], "readings": [], "clarify_by": None, "abstain_by": None,
             "samples": ["The Program Manager."] * 5, "stated_confidence": "80", "timings": {"loop": 20.0, "confidence_call": 8.0, "sampling": 23.0, "total": 51.0}}
        self.runs[r["run_id"]] = r
        return r

    def explain(self, run_id):
        r = self.runs.get(run_id)
        return None if r is None else {"run_id": run_id, "breakdown": r["breakdown"]}


def test_health_ask_and_explain():
    client = TestClient(create_app(StubSystem()))
    assert client.get("/health").json()["display_cap"] == 0.67
    r = client.post("/ask", json={"question": "Who approves the SEMP?"})
    assert r.status_code == 200
    body = r.json()
    assert body["outcome"] == "VERIFY" and body["confidence"] == 0.57 and "certainty" in body["note"]
    assert client.get(f"/explain/{body['run_id']}").json()["breakdown"].startswith("Confidence")
    assert client.get("/explain/nope").status_code == 404
    assert client.post("/ask", json={"question": "x"}).status_code == 422


def test_page_and_gallery(tmp_path):
    client = TestClient(create_app(StubSystem()))
    page = client.get("/")
    assert page.status_code == 200 and "Calibrated confidence that the answer is correct" in page.text and "capped" in page.text
    policy = tmp_path / "m5-policy.json"
    policy.write_text(json.dumps({"rows": [{"item_id": "q1", "bucket": "answerable", "agent_action": "ANSWER", "probability": 0.9, "outcome": "ANSWER", "label": 1}]}), encoding="utf-8")
    rows = tmp_path / "rows.jsonl"
    rows.write_text(json.dumps({"item_id": "q1", "question": "Q?", "response": "A.", "grade": {"grade": "CORRECT", "label": 1}}) + "\n", encoding="utf-8")
    items = load_gallery(policy_path=policy, oof_path=tmp_path / "none.jsonl", rows_paths=(rows,), cap=0.67)
    assert items == [{"item_id": "q1", "bucket": "answerable", "agent_action": "ANSWER", "outcome": "ANSWER", "confidence": 0.67, "grade": "CORRECT", "question": "Q?", "response": "A."}]
    gallery = client.get("/dev").json()
    assert "ground truth" in gallery["note"] and isinstance(gallery["items"], list)
