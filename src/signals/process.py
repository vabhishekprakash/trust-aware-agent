"""Process and retrieval-shape signals read from a trace. No model calls, no item record.

Every feature here is computed from what the agent wrote while answering,
so it exists at inference time for a question with no known answer. The
trace also carries fields derived from the item record (the evidence block,
the bucket, the calculator flags); those are never read here.
"""

from __future__ import annotations

import re

from calibration.grader import _ABSTAIN, classify_form, content_words

HEDGES = re.compile(r"\b(may|might|typically|usually|generally|approximately|about|around|likely|possibly|perhaps|seems?)\b", re.IGNORECASE)
_PAGE = re.compile(r"^\d+$")

PROVENANCE = {
    "action_answer": "trace.action == ANSWER",
    "action_abstain": "trace.action == ABSTAIN",
    "action_clarify": "trace.action == CLARIFY",
    "clarify_by_prompt": "trace.clarify_by is prompt or both: the model asked on its own",
    "abstain_by_prompt": "trace.abstain_by is prompt or both",
    "readings_count": "trace.readings.parsed, how many readings the readings step listed",
    "readings_fired": "trace.readings.fired",
    "calc_lines": "trace.draft.calc, how many CALC lines the draft issued",
    "calc_uncomputable": "trace.draft.calc, how many of them the calculator refused",
    "calc_round": "trace.calls has a draft_after_calc step",
    "response_words": "word count of trace.response",
    "response_content_words": "content words in trace.response after the grader's normalise and stopword drop",
    "response_hedges": "count of hedge words in trace.response (may, typically, about, ...)",
    "response_abstain_phrase": "trace.response matches the grader's abstain pattern",
    "response_form_answer": "grader classify_form of trace.response is ANSWER (text only, no hint)",
    "draft_changed_by_calc": "trace.draft.raw differs from trace.draft.final",
    "best_score": "trace.retrieval[0].score, cosine of the query to the best chunk",
    "score_gap": "best score minus the second score",
    "score_mean_k": "mean score over the k hits",
    "score_spread": "best score minus the kth score",
    "distinct_pages_k": "number of distinct start pages among the k hits",
    "page_span_k": "max minus min numeric start page among the k hits (0 when fewer than two numeric)",
    "top3_same_page": "the top three hits share one start page",
}


def process_features(trace: dict) -> dict:
    hits = trace["retrieval"]
    scores = [h["score"] for h in hits]
    response = trace["response"]
    calc = trace["draft"]["calc"]
    pages = [h["page_start"] for h in hits]
    numeric = [int(p) for p in pages if _PAGE.match(str(p))]
    return {
        "action_answer": int(trace["action"] == "ANSWER"),
        "action_abstain": int(trace["action"] == "ABSTAIN"),
        "action_clarify": int(trace["action"] == "CLARIFY"),
        "clarify_by_prompt": int(trace.get("clarify_by") in ("prompt", "both")),
        "abstain_by_prompt": int(trace.get("abstain_by") in ("prompt", "both")),
        "readings_count": len(trace["readings"]["parsed"]),
        "readings_fired": int(bool(trace["readings"]["fired"])),
        "calc_lines": len(calc),
        "calc_uncomputable": sum(1 for c in calc if c["result"] is None),
        "calc_round": int(any(c["step"] == "draft_after_calc" for c in trace["calls"])),
        "response_words": len(response.split()),
        "response_content_words": len(content_words(response)),
        "response_hedges": len(HEDGES.findall(response)),
        "response_abstain_phrase": int(bool(_ABSTAIN.search(response))),
        "response_form_answer": int(classify_form(response) == "ANSWER"),
        "draft_changed_by_calc": int(trace["draft"]["raw"] != trace["draft"]["final"]),
        "best_score": round(scores[0], 4) if scores else 0.0,
        "score_gap": round(scores[0] - scores[1], 4) if len(scores) > 1 else 0.0,
        "score_mean_k": round(sum(scores) / len(scores), 4) if scores else 0.0,
        "score_spread": round(scores[0] - scores[-1], 4) if scores else 0.0,
        "distinct_pages_k": len(set(pages)),
        "page_span_k": (max(numeric) - min(numeric)) if len(numeric) > 1 else 0,
        "top3_same_page": int(len(set(pages[:3])) == 1) if len(pages) >= 3 else 0,
    }


def leaked_fields(trace: dict) -> list[str]:
    """Trace fields that come from the item record; listed so a feature builder can prove it did not read them."""
    return [f for f in ("evidence", "bucket", "needs_calculator", "spurious_calc") if f in trace]


def stratum(trace: dict) -> dict:
    """Ground-truth variables kept next to the features for reporting only, never inside them."""
    ev = trace.get("evidence") or {}
    return {"bucket": trace.get("bucket"), "evidence_retrieved": ev.get("retrieved"), "evidence_rank": ev.get("rank"),
            "needs_calculator": trace.get("needs_calculator")}
