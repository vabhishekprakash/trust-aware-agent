"""Tests for the paid-signal feature functions; no model calls."""

from agent.loop import draft_messages
from agent.retriever import Hit
from signals.agreement import agreement_features, jaccard
from signals.logprobs import logprob_features
from signals.verbalized import confidence_features, confidence_messages, parse_confidence


def test_logprob_summaries_and_the_mismatch_flag():
    f = logprob_features([-0.1, -2.0, -0.5, -0.05], same_text=True)
    assert f["lp_mean"] == -0.6625 and f["lp_min"] == -2.0 and f["lp_first"] == -0.1 and f["lp_tokens"] == 4
    assert f["lp_share_below_1"] == 0.25 and f["lp_p10"] == -2.0 and f["lp_same_text"] == 1
    assert logprob_features([], same_text=False)["lp_same_text"] == 0


def test_confidence_parsing_and_features():
    assert parse_confidence("85") == 85 and parse_confidence("About 70%.") == 70 and parse_confidence("100") == 100
    assert parse_confidence("I cannot say.") is None and parse_confidence("150") is None
    assert confidence_features("90") == {"vc_confidence": 90, "vc_parsed": 1, "vc_round": 1}
    assert confidence_features("83") == {"vc_confidence": 83, "vc_parsed": 1, "vc_round": 0}
    assert confidence_features("no idea") == {"vc_confidence": 50, "vc_parsed": 0, "vc_round": 0}


def test_confidence_follow_up_keeps_the_passages_in_view():
    hits = [Hit({"id": "c1", "text": "The SEMP is approved by the Program Manager.", "page_start": "20", "page_end": "20", "word_count": 8}, 0.8)]
    base = draft_messages("Who approves the SEMP?", hits)
    messages = confidence_messages(base, "The Program Manager.")
    assert messages[:2] == base and "The SEMP is approved" in messages[1]["content"]
    assert messages[2] == {"role": "assistant", "content": "The Program Manager."}
    assert messages[3]["role"] == "user" and "0 to 100" in messages[3]["content"]


def test_agreement_among_samples_and_against_the_draft():
    assert jaccard("The Program Manager approves the SEMP.", "The SEMP is approved by the Program Manager.") == 1.0
    samples = ["The Program Manager approves it.", "The Program Manager.", "The handbook does not say."]
    f = agreement_features(samples, "The Program Manager approves the SEMP.")
    assert f["sa_samples"] == 3 and f["sa_abstain_share"] == 0.3333 and f["sa_form_agree"] == 0.6667
    assert f["sa_max_to_draft"] > f["sa_min_to_draft"] == 0.0
    assert 0 < f["sa_mean_pairwise"] < 1 and f["sa_min_pairwise"] == 0.0
    assert agreement_features([], "x")["sa_samples"] == 0
