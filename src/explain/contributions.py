"""Per-signal contributions to a confidence score, and a plain-language breakdown.

The calibrator is a logistic regression on standardised features followed
by an isotonic bend. For one item, each feature's contribution is its
coefficient times its standardised value; the contributions plus the
intercept are the log-odds, which the isotonic step maps to the probability
shown. Contributions are exact for the log-odds, not for the probability,
and they describe what moved the score on this run, not what causes
correctness. See docs/explanations/08-explanations.md.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import joblib  # artifacts are written by this project's own scripts into data/calibrators; nothing is loaded from outside the repository
import numpy as np

ARTIFACT_DIR = Path(__file__).resolve().parents[2] / "data" / "calibrators"

# Plain words for each feature, read as "<phrase> (value)". Missing names fall back to the provenance text.
PHRASES = {
    "action_answer": "the agent gave a direct answer",
    "action_abstain": "the agent abstained",
    "action_clarify": "the agent asked a clarifying question",
    "abstain_by_prompt": "the model chose to abstain on its own",
    "readings_count": "readings the model listed for the question",
    "readings_fired": "the readings step found two answers",
    "calc_lines": "calculator lines the draft issued",
    "calc_uncomputable": "calculator lines that could not be computed",
    "calc_round": "a calculator round was needed",
    "response_words": "length of the answer in words",
    "response_content_words": "content words in the answer",
    "response_hedges": "hedge words in the answer (may, about, typically)",
    "response_abstain_phrase": "the answer says the handbook does not say",
    "response_form_answer": "the answer reads as a direct answer",
    "draft_changed_by_calc": "the answer changed after the calculator",
    "best_score": "retrieval score of the best passage",
    "score_gap": "gap between the best and second passage scores",
    "score_mean_k": "mean retrieval score of the passages",
    "score_spread": "spread of retrieval scores across the passages",
    "distinct_pages_k": "distinct pages among the passages",
    "page_span_k": "page span of the passages",
    "top3_same_page": "the top three passages share a page",
    "lexical_support_top1": "share of the answer's words found in the best passage",
    "lexical_support_max": "share of the answer's words found in any passage",
    "cosine_top1": "similarity between the answer and the best passage",
    "cosine_max": "similarity between the answer and the closest passage",
    "nli_entail_top1": "entailment of the answer by the best passage",
    "nli_entail_max": "entailment of the answer by any passage",
    "nli_contradict_max": "contradiction between the answer and a passage",
    "vc_confidence": "the model's own stated confidence, 0 to 100",
    "vc_parsed": "the model gave a usable confidence number",
    "vc_round": "the stated confidence was a round number",
    "sa_mean_pairwise": "agreement among five resampled answers",
    "sa_min_pairwise": "lowest agreement among the resampled answers",
    "sa_mean_to_draft": "agreement of the resampled answers with this answer",
    "sa_min_to_draft": "lowest agreement of a resample with this answer",
    "sa_max_to_draft": "highest agreement of a resample with this answer",
    "sa_abstain_share": "share of resamples that abstained",
    "sa_form_agree": "share of resamples that took the same form as this answer",
    "sa_samples": "number of resamples",
}


# Signal families. Correlated features inside a family take coefficients of opposite sign from the
# logistic fit, so a single feature's push can read backwards; the family sum is the stable quantity.
FAMILIES = {
    "the agent's action": ("action_answer", "action_abstain", "action_clarify", "abstain_by_prompt", "response_form_answer", "response_abstain_phrase"),
    "the readings step": ("readings_count", "readings_fired"),
    "the calculator": ("calc_lines", "calc_uncomputable", "calc_round", "draft_changed_by_calc"),
    "the answer's length and hedging": ("response_words", "response_content_words", "response_hedges"),
    "retrieval scores and spread": ("best_score", "score_gap", "score_mean_k", "score_spread", "distinct_pages_k", "page_span_k", "top3_same_page"),
    "support from the passages": ("lexical_support_top1", "lexical_support_max", "cosine_top1", "cosine_max", "nli_entail_top1", "nli_entail_max", "nli_contradict_max"),
    "the model's stated confidence": ("vc_confidence", "vc_parsed", "vc_round"),
    "agreement among resampled answers": ("sa_mean_pairwise", "sa_min_pairwise", "sa_mean_to_draft", "sa_min_to_draft", "sa_max_to_draft", "sa_abstain_share", "sa_form_agree", "sa_samples"),
    "token log-probabilities": ("lp_mean", "lp_min", "lp_p10", "lp_share_below_1", "lp_first", "lp_tokens", "lp_same_text"),
}


def family_of(feature: str) -> str:
    for family, members in FAMILIES.items():
        if feature in members:
            return family
    return "other"


@dataclass
class Contribution:
    feature: str
    value: float
    dev_mean: float
    dev_sd: float
    coefficient: float
    contribution: float  # log-odds units
    phrase: str


@dataclass
class Explanation:
    probability: float
    logistic_probability: float
    log_odds: float
    intercept: float
    contributions: list[Contribution] = field(default_factory=list)

    def top(self, n: int = 3, sign: int = +1) -> list[Contribution]:
        picked = [c for c in self.contributions if (c.contribution > 0) == (sign > 0) and c.contribution != 0]
        return sorted(picked, key=lambda c: -abs(c.contribution))[:n]

    def by_family(self) -> list[tuple[str, float]]:
        """Family sums of the contributions, largest first; the stable view when features are correlated."""
        sums: dict[str, float] = {}
        for c in self.contributions:
            sums[family_of(c.feature)] = sums.get(family_of(c.feature), 0.0) + c.contribution
        return sorted(sums.items(), key=lambda kv: -abs(kv[1]))


class Explainer:
    """Reads a calibrator artifact and explains one feature vector at a time."""

    def __init__(self, artifact: dict):
        self.features: list[str] = artifact["features"]
        pipeline = artifact["model"]
        scaler = pipeline.named_steps["standardscaler"]
        lr = pipeline.named_steps["logisticregression"]
        self.means = np.asarray(scaler.mean_, dtype=float)
        self.sds = np.asarray(scaler.scale_, dtype=float)
        self.coef = np.asarray(lr.coef_[0], dtype=float)
        self.intercept = float(lr.intercept_[0])
        self.isotonic = artifact.get("isotonic")
        self.variant = artifact.get("variant")

    @classmethod
    def load(cls, variant: str = "minus_logprobs", directory: Path = ARTIFACT_DIR) -> "Explainer":
        return cls(joblib.load(Path(directory) / f"{variant}.joblib"))

    def explain(self, feature_values: dict) -> Explanation:
        x = np.array([float(feature_values[n]) for n in self.features])
        z = (x - self.means) / self.sds
        contribs = self.coef * z
        log_odds = float(self.intercept + contribs.sum())
        p_log = 1.0 / (1.0 + math.exp(-log_odds))
        p = float(self.isotonic.predict([p_log])[0]) if self.isotonic is not None else p_log
        items = [Contribution(n, float(x[i]), float(self.means[i]), float(self.sds[i]), float(self.coef[i]), float(contribs[i]),
                              PHRASES.get(n, n)) for i, n in enumerate(self.features)]
        items.sort(key=lambda c: -abs(c.contribution))
        return Explanation(probability=p, logistic_probability=p_log, log_odds=log_odds, intercept=self.intercept, contributions=items)


def _fmt_value(c: Contribution) -> str:
    if float(c.value).is_integer() and c.dev_sd < 1.5:
        return f"{int(c.value)}"
    return f"{c.value:.2f}"


def _unusual(c: Contribution) -> str:
    if c.dev_sd == 0:
        return ""
    z = (c.value - c.dev_mean) / c.dev_sd
    if abs(z) < 0.5:
        return "about average for this agent"
    return ("well above" if z > 1.5 else "above" if z > 0 else "well below" if z < -1.5 else "below") + " the usual"


def breakdown(explanation: Explanation, outcome: Optional[str] = None, n: int = 3) -> str:
    """A plain-language paragraph: the score, the main pushes up, the main pushes down, the rest, and the limits."""
    pct = round(100 * explanation.probability)
    head = f"Confidence {pct} percent" + (f", so the policy says {outcome}" if outcome else "") + "."
    ups = explanation.top(n, +1)
    downs = explanation.top(n, -1)

    def clause(cs):
        return "; ".join(f"{c.phrase} ({_fmt_value(c)}, {_unusual(c)})" for c in cs)

    parts = [head]
    families = [(f, v) for f, v in explanation.by_family() if abs(v) >= 0.05]
    if families:
        parts.append("By signal family, in log-odds: " + "; ".join(f"{f} {v:+.2f}" for f, v in families[:4]) + ".")
    if ups:
        parts.append("Single features pushing up most: " + clause(ups) + ".")
    if downs:
        parts.append("Pushing down most: " + clause(downs) + ".")
    named = {c.feature for c in ups + downs}
    rest = sum(c.contribution for c in explanation.contributions if c.feature not in named)
    parts.append(f"Everything else together moved the log-odds by {rest:+.2f}; the starting point was {explanation.intercept:+.2f}.")
    parts.append("These amounts are exact for the log-odds, not for the percentage; correlated features inside a family can take opposite signs, "
                 "so the family sums are the steadier reading; and they say what moved the score on this run, not what causes a correct answer.")
    return " ".join(parts)
