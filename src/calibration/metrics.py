"""Calibration and selective-prediction metrics, with bootstrap intervals.

ECE with equal-width bins, Brier score, AUROC, a reliability table, the
risk-coverage curve and its area (AURC). Every summary can be wrapped in a
bootstrap over items, because dev is small and the honest conclusion is
directional.
"""

from __future__ import annotations

from typing import Callable

import numpy as np


def ece(p: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
    edges = np.linspace(0.0, 1.0, bins + 1)
    total = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (p >= lo) & (p < hi) if hi < 1.0 else (p >= lo) & (p <= hi)
        if mask.any():
            total += mask.mean() * abs(p[mask].mean() - y[mask].mean())
    return float(total)


def brier(p: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean((p - y) ** 2))


def auroc(p: np.ndarray, y: np.ndarray) -> float:
    """Rank-based AUROC; 0.5 when one class is absent."""
    pos, neg = p[y == 1], p[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return 0.5
    order = np.argsort(np.concatenate([pos, neg]), kind="mergesort")
    ranks = np.empty(len(order), dtype=float)
    scores = np.concatenate([pos, neg])[order]
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and scores[j + 1] == scores[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2 + 1
        i = j + 1
    return float((ranks[: len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def reliability(p: np.ndarray, y: np.ndarray, bins: int = 10) -> list[dict]:
    edges = np.linspace(0.0, 1.0, bins + 1)
    out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (p >= lo) & (p < hi) if hi < 1.0 else (p >= lo) & (p <= hi)
        out.append({"lo": round(float(lo), 2), "hi": round(float(hi), 2), "n": int(mask.sum()),
                    "confidence": round(float(p[mask].mean()), 3) if mask.any() else None,
                    "accuracy": round(float(y[mask].mean()), 3) if mask.any() else None})
    return out


def risk_coverage(p: np.ndarray, y: np.ndarray) -> list[dict]:
    """Coverage and risk (error rate among the covered) when answering the most confident items first."""
    order = np.argsort(-p, kind="mergesort")
    errors = (1 - y[order]).cumsum()
    n = len(p)
    return [{"coverage": round((i + 1) / n, 3), "risk": round(float(errors[i] / (i + 1)), 3)} for i in range(n)]


def aurc(p: np.ndarray, y: np.ndarray) -> float:
    curve = risk_coverage(p, y)
    return float(np.mean([c["risk"] for c in curve]))


def bootstrap(stat: Callable[[np.ndarray, np.ndarray], float], p: np.ndarray, y: np.ndarray, n: int = 1000, seed: int = 42) -> dict:
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(n):
        idx = rng.integers(0, len(p), len(p))
        values.append(stat(p[idx], y[idx]))
    values = np.array(values)
    return {"point": round(float(stat(p, y)), 4), "lo": round(float(np.percentile(values, 2.5)), 4), "hi": round(float(np.percentile(values, 97.5)), 4), "n": int(len(p))}
