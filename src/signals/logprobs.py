"""Token log-probability signal: summaries of the draft's own token sequence.

The raw sequence is stored with the run so any further summary can be
computed without another model call. The draft is regenerated with
logprobs on, at temperature 0 and the run's seed, and the text is checked
against the draft in the trace; a mismatch is recorded, not hidden.
"""

from __future__ import annotations

import math

PROVENANCE = {
    "lp_mean": "mean token log-probability of the draft (regenerated with logprobs on)",
    "lp_min": "minimum token log-probability of the draft",
    "lp_p10": "10th percentile of the token log-probabilities",
    "lp_share_below_1": "share of tokens with log-probability below -1 (probability under 0.37)",
    "lp_first": "log-probability of the first token",
    "lp_tokens": "number of tokens in the draft",
    "lp_same_text": "1 when the regenerated draft matched the trace's draft exactly",
}


def logprob_features(logprobs: list[float], same_text: bool) -> dict:
    if not logprobs:
        return {"lp_mean": 0.0, "lp_min": 0.0, "lp_p10": 0.0, "lp_share_below_1": 0.0, "lp_first": 0.0, "lp_tokens": 0, "lp_same_text": int(same_text)}
    ordered = sorted(logprobs)
    p10 = ordered[max(0, math.ceil(0.1 * len(ordered)) - 1)]
    return {
        "lp_mean": round(sum(logprobs) / len(logprobs), 4),
        "lp_min": round(min(logprobs), 4),
        "lp_p10": round(p10, 4),
        "lp_share_below_1": round(sum(1 for x in logprobs if x < -1.0) / len(logprobs), 4),
        "lp_first": round(logprobs[0], 4),
        "lp_tokens": len(logprobs),
        "lp_same_text": int(same_text),
    }
