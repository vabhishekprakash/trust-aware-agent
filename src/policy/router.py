"""The decision policy: ANSWER, VERIFY or ESCALATE from a calibrated probability.

The agent's own CLARIFY and ABSTAIN actions stand. For an item the agent
answered, the probability that the answer is correct is compared with two
thresholds tuned on dev to a target risk: at or above the upper one the
answer is shown (ANSWER); below the lower one it is withheld and handed to
a person (ESCALATE); between them it is shown with a flag (VERIFY). VERIFY
is a display state, not a verification loop; see
docs/explanations/07-policy.md for why the loop was not built.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

OUTCOMES = ("ANSWER", "VERIFY", "ESCALATE", "CLARIFY", "ABSTAIN")
POLICY_PATH = Path(__file__).resolve().parents[2] / "data" / "calibrators" / "policy.json"


@dataclass(frozen=True)
class Thresholds:
    answer: float  # show the answer at or above this probability
    escalate: float  # withhold below this probability

    def __post_init__(self):
        if not 0.0 <= self.escalate <= self.answer <= 1.0:
            raise ValueError("need 0 <= escalate <= answer <= 1")


def load_thresholds(path: str | Path = POLICY_PATH) -> Thresholds:
    """The thresholds the owner chose on dev, kept next to the calibrator artifact."""
    record = json.loads(Path(path).read_text(encoding="utf-8"))
    return Thresholds(answer=float(record["thresholds"]["answer"]), escalate=float(record["thresholds"]["escalate"]))


def decide(agent_action: str, probability: float, thresholds: Thresholds) -> str:
    """The policy outcome for one item.

    CLARIFY and ABSTAIN pass through untouched: a clarifying question is not
    an answer to gate, and a confident abstention is the answer "the
    handbook does not say".
    """
    if agent_action in ("CLARIFY", "ABSTAIN"):
        return agent_action
    if agent_action != "ANSWER":
        raise ValueError(f"unknown agent action {agent_action!r}")
    if probability >= thresholds.answer:
        return "ANSWER"
    if probability < thresholds.escalate:
        return "ESCALATE"
    return "VERIFY"


def shown(outcome: str) -> bool:
    """Whether the user sees an answer (flagged or not) rather than a withheld one."""
    return outcome in ("ANSWER", "VERIFY", "ABSTAIN")
