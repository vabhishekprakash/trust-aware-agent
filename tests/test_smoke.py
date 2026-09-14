"""Smoke test: the package skeleton imports."""

import importlib

PACKAGES = ["agent", "signals", "calibration", "policy", "explain", "api", "ui"]


def test_packages_import():
    for name in PACKAGES:
        importlib.import_module(name)
