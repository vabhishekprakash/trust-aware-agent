"""The agent's tools: a narrow calculator and an acronym lookup.

The calculator does one operation on two numbers, which is all the
calculator items need: a difference of two stated figures, a ratio, a
percentage. It parses dollar signs, commas, percent signs and K, M or B
suffixes, and refuses anything else; there is no expression evaluator. The
lookup returns the handbook's own expansion of an acronym from Appendix A.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
ACRONYMS_PATH = ROOT / "data" / "corpus" / "acronyms.json"

CALC_LINE = re.compile(r"^\s*CALC\s*:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
_NUMBER = re.compile(r"^\$?\s*(-?\d[\d,]*(?:\.\d+)?)\s*([kKmMbB]|%)?$")
_EXPRESSION = re.compile(r"^(.+?)\s*([-+*/x])\s*(.+?)$")
_SUFFIX = {"k": 1e3, "m": 1e6, "b": 1e9}


def parse_number(text: str) -> Optional[float]:
    match = _NUMBER.match(text.strip())
    if not match:
        return None
    value = float(match.group(1).replace(",", ""))
    suffix = (match.group(2) or "").lower()
    if suffix in _SUFFIX:
        value *= _SUFFIX[suffix]
    return value


def calculate(expression: str) -> Optional[float]:
    """One operation on two numbers, or None when the text is not that."""
    match = _EXPRESSION.match(expression.strip())
    if not match:
        return None
    left, op, right = parse_number(match.group(1)), match.group(2), parse_number(match.group(3))
    if left is None or right is None:
        return None
    if op == "+":
        return left + right
    if op == "-":
        return left - right
    if op in "*x":
        return left * right
    if right == 0:
        return None
    return left / right


def format_number(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return f"{int(round(value)):,}"
    return f"{value:,.4f}".rstrip("0").rstrip(".")


def calc_lines(text: str) -> list[str]:
    return [m.group(1) for m in CALC_LINE.finditer(text)]


_ACRONYMS: Optional[dict] = None


def lookup_acronym(term: str, table: Optional[dict] = None) -> list[str]:
    """The handbook's expansions of an acronym, or an empty list."""
    global _ACRONYMS
    if table is None:
        if _ACRONYMS is None:
            _ACRONYMS = json.loads(ACRONYMS_PATH.read_text(encoding="utf-8")) if ACRONYMS_PATH.exists() else {}
        table = _ACRONYMS
    return list(table.get(term.strip().upper(), []) or table.get(term.strip(), []))
