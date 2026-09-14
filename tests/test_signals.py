"""Tests for the free signals: process features from a trace and retrieval support without real models."""

import numpy as np

from signals.process import PROVENANCE, leaked_fields, process_features, stratum
from signals.retrieval_support import PROVENANCE as SUPPORT_PROVENANCE
from signals.retrieval_support import cosine, lexical_support, support_features

TRACE = {
    "action": "ANSWER", "clarify_by": None, "abstain_by": None,
    "readings": {"raw": "ONE READING", "parsed": [], "fired": False},
    "draft": {"raw": "CALC: 500 - 100", "calc": [{"expression": "500 - 100", "result": "400"}], "final": "The gap is about $400M."},
    "calls": [{"step": "readings", "cached": True, "seconds": 0}, {"step": "draft", "cached": True, "seconds": 0}, {"step": "draft_after_calc", "cached": True, "seconds": 0}],
    "response": "The gap is about $400M.",
    "retrieval": [{"id": "c1", "page_start": "38", "page_end": "38", "score": 0.80}, {"id": "c2", "page_start": "38", "page_end": "38", "score": 0.70},
                  {"id": "c3", "page_start": "38", "page_end": "39", "score": 0.65}, {"id": "c4", "page_start": "xii", "page_end": "xii", "score": 0.60}],
    "evidence": {"retrieved": True, "rank": 1}, "bucket": "answerable", "needs_calculator": True, "spurious_calc": False,
}


def test_process_features_come_from_the_run_only():
    f = process_features(TRACE)
    assert f["action_answer"] == 1 and f["action_abstain"] == 0 and f["action_clarify"] == 0
    assert f["calc_lines"] == 1 and f["calc_uncomputable"] == 0 and f["calc_round"] == 1 and f["draft_changed_by_calc"] == 1
    assert f["response_words"] == 5 and f["response_hedges"] == 1 and f["response_abstain_phrase"] == 0 and f["response_form_answer"] == 1
    assert f["best_score"] == 0.8 and f["score_gap"] == 0.1 and f["score_spread"] == 0.2 and f["score_mean_k"] == 0.6875
    assert f["distinct_pages_k"] == 2 and f["page_span_k"] == 0 and f["top3_same_page"] == 1
    assert set(f) == set(PROVENANCE)
    for name in ("evidence", "bucket", "needs_calculator", "spurious_calc", "retrieved", "rank"):
        assert name not in f


def test_leaked_fields_and_stratum_are_kept_apart():
    assert leaked_fields(TRACE) == ["evidence", "bucket", "needs_calculator", "spurious_calc"]
    assert stratum(TRACE) == {"bucket": "answerable", "evidence_retrieved": True, "evidence_rank": 1, "needs_calculator": True}


def test_abstain_and_clarify_traces():
    t = dict(TRACE, action="ABSTAIN", abstain_by="prompt", response="The handbook does not say.", calls=TRACE["calls"][:2],
             draft={"raw": "The handbook does not say.", "calc": [], "final": "The handbook does not say."})
    f = process_features(t)
    assert f["action_abstain"] == 1 and f["abstain_by_prompt"] == 1 and f["response_abstain_phrase"] == 1 and f["response_form_answer"] == 0
    assert f["calc_round"] == 0 and f["draft_changed_by_calc"] == 0
    t = dict(t, action="CLARIFY", clarify_by="rule", readings={"raw": "", "parsed": [{"reading": "a", "answer": "x"}, {"reading": "b", "answer": "y"}], "fired": True},
             response="Do you mean a, or b?")
    f = process_features(t)
    assert f["action_clarify"] == 1 and f["clarify_by_prompt"] == 0 and f["readings_count"] == 2 and f["readings_fired"] == 1


def test_lexical_support_and_cosine():
    assert lexical_support("The Program Manager approves the SEMP.", "The SEMP is approved by the Program Manager.") == 1.0
    assert lexical_support("Costs are capped at $500M.", "The SEMP is approved by the Program Manager.") == 0.0
    assert cosine(np.array([1.0, 0.0]), np.array([1.0, 0.0])) == 1.0
    assert cosine(np.array([1.0, 0.0]), np.array([0.0, 1.0])) == 0.0


def test_support_features_without_models_and_with_a_fake_embedder():
    chunks = ["The SEMP is approved by the Program Manager.", "Type C projects cost up to $500M."]
    f = support_features("The Program Manager approves the SEMP.", chunks)
    assert set(f) == {"lexical_support_top1", "lexical_support_max"} and f["lexical_support_top1"] == 1.0

    def embed(texts):
        return np.array([[1.0, 0.0] if "SEMP" in t else [0.0, 1.0] for t in texts])

    f = support_features("The Program Manager approves the SEMP.", chunks, embed=embed)
    assert f["cosine_top1"] == 1.0 and f["cosine_max"] == 1.0
    f = support_features("Type C costs $500M.", chunks, embed=embed, chunk_vectors=embed(chunks))
    assert f["cosine_top1"] == 0.0 and f["cosine_max"] == 1.0
    assert set(SUPPORT_PROVENANCE) >= set(f)
