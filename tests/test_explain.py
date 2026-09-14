"""Tests for the explanation layer, on a small fitted pipeline built in the test."""

import math

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from explain.contributions import FAMILIES, PHRASES, Explainer, breakdown, family_of


def make_artifact(with_isotonic=True):
    rng = np.random.default_rng(0)
    X = rng.normal(size=(200, 3))
    y = (X[:, 0] - 0.5 * X[:, 1] + rng.normal(scale=0.5, size=200) > 0).astype(int)
    model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)).fit(X, y)
    artifact = {"variant": "test", "features": ["lexical_support_top1", "readings_count", "response_words"], "model": model}
    if with_isotonic:
        artifact["isotonic"] = IsotonicRegression(out_of_bounds="clip").fit(model.predict_proba(X)[:, 1], y)
    return artifact


def test_contributions_add_up_to_the_log_odds_and_the_probability_follows():
    ex = Explainer(make_artifact(with_isotonic=False))
    e = ex.explain({"lexical_support_top1": 1.2, "readings_count": -0.3, "response_words": 0.1})
    assert math.isclose(e.intercept + sum(c.contribution for c in e.contributions), e.log_odds, abs_tol=1e-9)
    assert math.isclose(1 / (1 + math.exp(-e.log_odds)), e.logistic_probability, abs_tol=1e-9)
    assert e.probability == e.logistic_probability  # no isotonic step
    assert e.contributions[0].feature == "lexical_support_top1"  # the strongest signal in the synthetic data


def test_isotonic_step_keeps_order():
    ex = Explainer(make_artifact(with_isotonic=True))
    low = ex.explain({"lexical_support_top1": -2.0, "readings_count": 1.0, "response_words": 0.0})
    high = ex.explain({"lexical_support_top1": 2.0, "readings_count": -1.0, "response_words": 0.0})
    assert high.log_odds > low.log_odds and high.probability >= low.probability
    assert 0.0 <= low.probability <= 1.0


def test_breakdown_is_plain_language_with_the_limits_stated():
    ex = Explainer(make_artifact())
    e = ex.explain({"lexical_support_top1": 2.0, "readings_count": 2.0, "response_words": 0.0})
    text = breakdown(e, outcome="VERIFY", n=2)
    assert text.startswith("Confidence ") and "policy says VERIFY" in text
    assert "share of the answer's words found in the best passage" in text
    assert "readings the model listed" in text
    assert "not what causes a correct answer" in text
    assert "lexical_support_top1" not in text  # names, not identifiers
    assert all(name in PHRASES for name in ex.features)


def test_top_selection_by_sign():
    ex = Explainer(make_artifact(with_isotonic=False))
    e = ex.explain({"lexical_support_top1": 2.0, "readings_count": 2.0, "response_words": 0.0})
    assert all(c.contribution > 0 for c in e.top(3, +1))
    assert all(c.contribution < 0 for c in e.top(3, -1))


def test_family_sums_partition_the_contributions():
    ex = Explainer(make_artifact(with_isotonic=False))
    e = ex.explain({"lexical_support_top1": 1.0, "readings_count": 1.0, "response_words": 1.0})
    fam = dict(e.by_family())
    assert math.isclose(sum(fam.values()), sum(c.contribution for c in e.contributions), abs_tol=1e-9)
    assert set(fam) == {"support from the passages", "the readings step", "the answer's length and hedging"}
    assert family_of("cosine_max") == "support from the passages" and family_of("mystery") == "other"
    members = [m for ms in FAMILIES.values() for m in ms]
    assert len(members) == len(set(members))
    assert "By signal family" in breakdown(e)
