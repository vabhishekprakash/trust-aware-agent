"""Comparing two judges on the same drafts: agreement, overlap, and why a reply was unreadable.

Post hoc, after the tagged evaluation. Nothing here changes how the grader
grades; the lenient reading is a diagnostic that tells a format failure
apart from a task failure, because the parser was built around the first
judge's output. See docs/decisions.md, "Post hoc: a second judge".
"""

from __future__ import annotations

import re
from contextlib import contextmanager
from typing import Iterator, Optional

import numpy as np

from calibration import grader

_EMPHASIS = re.compile(r"[*`#]+")
_QUESTION_WORD = re.compile(r"\bQuestion\s*(\d)\b", re.IGNORECASE)
_NUMBERED = re.compile(r"^\s*\(?(\d)[.):]\s+")
_Q_MARK = re.compile(r"^\s*Q(\d)\s*[:.)-]?\s*(.*)$", re.IGNORECASE)
_YES_NO = re.compile(r"\b(YES|NO)\b", re.IGNORECASE)


def lenient_text(text: str) -> str:
    """Rewrite a judge reply so each question's first yes or no sits on a 'Qn: YES' line.

    Strips markdown emphasis, reads 'Question 1' and a line opening '1.' as Q1,
    and takes the first standalone YES or NO on a question's line, or on the
    next line when the question's own line has none.
    """
    lines = [_EMPHASIS.sub("", line) for line in text.translate(grader._QUOTES).splitlines()]
    lines = [_QUESTION_WORD.sub(lambda m: f"Q{m.group(1)}", line) for line in lines]
    lines = [_NUMBERED.sub(lambda m: f"Q{m.group(1)}: ", line) for line in lines]
    out = []
    for i, line in enumerate(lines):
        mark = _Q_MARK.match(line)
        if not mark:
            out.append(line)
            continue
        found = _YES_NO.search(mark.group(2))
        if found is None and i + 1 < len(lines) and not _Q_MARK.match(lines[i + 1]):
            found = _YES_NO.search(lines[i + 1])
        out.append(f"Q{mark.group(1)}: {found.group(1).upper()}" if found else line)
    return "\n".join(out)


def lenient_parse_answers(keys: list[str], text: str):
    """The grader's parser run on the lenient rewrite; None when a question still has no answer."""
    return _STRICT_PARSE(keys, lenient_text(text))


_STRICT_PARSE = grader.parse_answers


@contextmanager
def lenient_parser() -> Iterator[None]:
    """Swap the grader's answer parser for the lenient one, for a labelled diagnostic regrade only."""
    grader.parse_answers = lenient_parse_answers
    try:
        yield
    finally:
        grader.parse_answers = _STRICT_PARSE


def categorise_reply(keys: list[str], text: str, truncated: bool) -> str:
    """parsed, format (a lenient reading recovers every answer), truncated (stopped at the cap), or task."""
    if _STRICT_PARSE(keys, text) is not None:
        return "parsed"
    if lenient_parse_answers(keys, text) is not None:
        return "format"
    return "truncated" if truncated else "task"


def binary(grade: Optional[str]) -> Optional[int]:
    return None if grade is None else int(grade == "CORRECT")


def agreement(pairs: list[tuple[Optional[str], Optional[str]]], three_way: bool = False) -> tuple[int, int]:
    """(agreeing, compared) over pairs where both grades exist."""
    usable = [(a, b) for a, b in pairs if a is not None and b is not None]
    if three_way:
        return sum(a == b for a, b in usable), len(usable)
    return sum(binary(a) == binary(b) for a, b in usable), len(usable)


def bootstrap_share(hits: list[int], n_boot: int = 1000, seed: int = 42) -> tuple[float, float, float]:
    """Share of 1s with a 95 percent bootstrap interval over items."""
    values = np.asarray(hits, dtype=float)
    if values.size == 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    boots = [values[rng.integers(0, values.size, values.size)].mean() for _ in range(n_boot)]
    return float(values.mean()), float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))


def paired_difference(first: list[int], second: list[int], n_boot: int = 1000, seed: int = 42) -> tuple[float, float, float]:
    """Mean of first minus second over the same items, resampled in pairs, with a 95 percent interval."""
    a = np.asarray(first, dtype=float)
    b = np.asarray(second, dtype=float)
    if a.size == 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n_boot):
        idx = rng.integers(0, a.size, a.size)
        boots.append(a[idx].mean() - b[idx].mean())
    return float(a.mean() - b.mean()), float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))


def overlap(first_wrong: set, second_wrong: set) -> dict:
    """How the two judges' disagreements with the owner overlap."""
    return {"first": sorted(first_wrong), "second": sorted(second_wrong), "both": sorted(first_wrong & second_wrong),
            "first_only": sorted(first_wrong - second_wrong), "second_only": sorted(second_wrong - first_wrong)}
