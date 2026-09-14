"""Tests for the decision policy router."""

import pytest

from policy.router import Thresholds, decide, shown


def test_thresholds_must_be_ordered_probabilities():
    Thresholds(answer=0.7, escalate=0.4)
    with pytest.raises(ValueError):
        Thresholds(answer=0.4, escalate=0.7)
    with pytest.raises(ValueError):
        Thresholds(answer=1.2, escalate=0.1)


def test_answered_items_are_gated_by_the_two_thresholds():
    t = Thresholds(answer=0.7, escalate=0.4)
    assert decide("ANSWER", 0.9, t) == "ANSWER"
    assert decide("ANSWER", 0.7, t) == "ANSWER"
    assert decide("ANSWER", 0.69, t) == "VERIFY"
    assert decide("ANSWER", 0.4, t) == "VERIFY"
    assert decide("ANSWER", 0.39, t) == "ESCALATE"


def test_clarify_and_abstain_pass_through_whatever_the_probability():
    t = Thresholds(answer=0.7, escalate=0.4)
    assert decide("CLARIFY", 0.01, t) == "CLARIFY"
    assert decide("ABSTAIN", 0.01, t) == "ABSTAIN"
    with pytest.raises(ValueError):
        decide("REJECT", 0.5, t)


def test_shown_outcomes():
    assert shown("ANSWER") and shown("VERIFY") and shown("ABSTAIN")
    assert not shown("ESCALATE") and not shown("CLARIFY")
