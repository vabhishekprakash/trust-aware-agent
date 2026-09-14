"""The feature vector the calibrator sees, and the three variants the owner asked for.

The leakage rule: a feature is admissible only if it comes from the run,
so it exists at inference time for a question with no known answer. The
rows written by scripts/build_features.py keep the ground-truth strata
(bucket, evidence retrieved, rank, calculator flag) in a separate block;
this module asserts that none of those names, and nothing else outside the
provenance lists, is in the vector. Constant features are dropped.

Variants, decided before any fit:
  full            every admissible feature
  minus_actions   without the action features, which are downstream of the
                  same model state the signals measure
  minus_logprobs  without the log-probability features, whose regenerated
                  text differed from the graded draft on a third of items
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from signals.agreement import PROVENANCE as AGREEMENT
from signals.logprobs import PROVENANCE as LOGPROBS
from signals.process import PROVENANCE as PROCESS
from signals.retrieval_support import PROVENANCE as SUPPORT
from signals.verbalized import PROVENANCE as VERBALIZED

PROVENANCE = {**PROCESS, **SUPPORT, **LOGPROBS, **VERBALIZED, **AGREEMENT}
ACTION_FEATURES = ("action_answer", "action_abstain", "action_clarify", "clarify_by_prompt", "abstain_by_prompt",
                   "response_form_answer", "response_abstain_phrase", "readings_fired")
LOGPROB_FEATURES = tuple(LOGPROBS)
GROUND_TRUTH = ("bucket", "evidence_retrieved", "evidence_rank", "needs_calculator", "spurious_calc", "label", "grade",
                "gold_answer", "expected", "premise_fix", "readings")


def load_rows(path: str | Path) -> list[dict]:
    rows = [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]
    if "test" in Path(path).name:
        raise ValueError("refusing to read the test split")
    return rows


def admissible_features(rows: list[dict]) -> list[str]:
    """Feature names present in every row, with a provenance entry, not ground truth, not constant."""
    names = [n for n in rows[0]["features"] if all(n in r["features"] for r in rows)]
    for n in names:
        if n in GROUND_TRUTH:
            raise ValueError(f"ground truth in the feature vector: {n}")
        if n not in PROVENANCE:
            raise ValueError(f"feature without provenance: {n}")
    return [n for n in names if len({r["features"][n] for r in rows}) > 1]


def variant_features(names: list[str], variant: str) -> list[str]:
    if variant == "full":
        return list(names)
    if variant == "minus_actions":
        return [n for n in names if n not in ACTION_FEATURES]
    if variant == "minus_logprobs":
        return [n for n in names if n not in LOGPROB_FEATURES]
    raise ValueError(f"unknown variant {variant!r}")


def matrix(rows: list[dict], names: list[str]) -> tuple[np.ndarray, np.ndarray]:
    X = np.array([[float(r["features"][n]) for n in names] for r in rows], dtype=float)
    y = np.array([int(r["label"]) for r in rows], dtype=int)
    return X, y


def dropped_constant(rows: list[dict]) -> list[str]:
    names = [n for n in rows[0]["features"] if all(n in r["features"] for r in rows)]
    return [n for n in names if len({r["features"][n] for r in rows}) <= 1]
