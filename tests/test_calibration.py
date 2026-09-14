"""Tests for the feature manifest (no leakage) and the calibration metrics."""

import numpy as np
import pytest

from calibration.features import ACTION_FEATURES, LOGPROB_FEATURES, admissible_features, dropped_constant, matrix, variant_features
from calibration.metrics import auroc, aurc, bootstrap, brier, ece, reliability, risk_coverage


def rows_with(features_list):
    return [{"item_id": f"q{i}", "label": i % 2, "strata": {"bucket": "answerable"}, "features": f} for i, f in enumerate(features_list)]


def test_admissible_features_drop_constants_and_refuse_ground_truth():
    rows = rows_with([{"best_score": 0.7, "clarify_by_prompt": 0, "action_answer": 1}, {"best_score": 0.8, "clarify_by_prompt": 0, "action_answer": 0}])
    assert admissible_features(rows) == ["best_score", "action_answer"]
    assert dropped_constant(rows) == ["clarify_by_prompt"]
    with pytest.raises(ValueError, match="ground truth"):
        admissible_features(rows_with([{"best_score": 0.7, "evidence_retrieved": 1}, {"best_score": 0.8, "evidence_retrieved": 0}]))
    with pytest.raises(ValueError, match="provenance"):
        admissible_features(rows_with([{"best_score": 0.7, "mystery": 1}, {"best_score": 0.8, "mystery": 0}]))


def test_variants_remove_the_right_features():
    names = ["best_score", "action_answer", "lp_mean", "sa_max_to_draft", "readings_fired", "lp_first"]
    assert variant_features(names, "full") == names
    assert variant_features(names, "minus_actions") == ["best_score", "lp_mean", "sa_max_to_draft", "lp_first"]
    assert variant_features(names, "minus_logprobs") == ["best_score", "action_answer", "sa_max_to_draft", "readings_fired"]
    assert set(ACTION_FEATURES) & set(LOGPROB_FEATURES) == set()
    with pytest.raises(ValueError):
        variant_features(names, "other")


def test_matrix_shapes():
    rows = rows_with([{"a": 1, "b": 2.5}, {"a": 0, "b": 1.0}])
    X, y = matrix(rows, ["a", "b"])
    assert X.shape == (2, 2) and list(y) == [0, 1] and X[0, 1] == 2.5


def test_metrics_on_known_cases():
    p = np.array([0.9, 0.8, 0.2, 0.1])
    y = np.array([1, 1, 0, 0])
    assert auroc(p, y) == 1.0
    # a perfect ranking still covers the two wrong items last: risks 0, 0, 1/3, 1/2
    assert aurc(p, y) == pytest.approx((0 + 0 + 1 / 3 + 1 / 2) / 4, abs=1e-3)
    assert aurc(p, y) < aurc(np.array([0.1, 0.2, 0.8, 0.9]), y)
    assert brier(p, y) == pytest.approx(0.025)  # (0.01 + 0.04 + 0.04 + 0.01) / 4
    assert ece(p, y) == pytest.approx(0.15)
    assert auroc(np.array([0.5, 0.5]), np.array([1, 0])) == 0.5
    perfect = np.array([1.0, 1.0, 0.0, 0.0])
    assert ece(perfect, y) == 0.0
    curve = risk_coverage(p, np.array([1, 0, 1, 0]))
    assert curve[0] == {"coverage": 0.25, "risk": 0.0} and curve[1] == {"coverage": 0.5, "risk": 0.5}
    table = reliability(p, y, bins=2)
    assert table[0]["n"] == 2 and table[0]["accuracy"] == 0.0 and table[1]["confidence"] == 0.85
    b = bootstrap(brier, p, y, n=200)
    assert b["lo"] <= b["point"] <= b["hi"] and b["n"] == 4
