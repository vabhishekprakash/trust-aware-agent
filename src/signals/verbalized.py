"""Verbalized self-confidence: one follow-up call asking for a number from 0 to 100.

The follow-up continues the draft conversation, so the model still sees
the passages and its own answer; it rates a grounded answer rather than
guessing from memory. The raw reply is stored; a reply with no number
parses as missing and is recorded as such.
"""

from __future__ import annotations

import re
from typing import Optional

QUESTION = ("How likely is it that your answer above is correct, given the passages? "
            "Reply with a single number from 0 to 100 and nothing else.")
_NUMBER = re.compile(r"(\d{1,3})(?:\.\d+)?\s*%?")

PROVENANCE = {
    "vc_confidence": "the number the model gave when asked, with the passages and its answer in view, how likely its answer is correct (0 to 100; 50 when it gave none)",
    "vc_parsed": "1 when the reply held a number from 0 to 100",
    "vc_round": "1 when the number is a multiple of 10, the clustering small models show",
}


def confidence_messages(draft_messages: list[dict], draft: str) -> list[dict]:
    return draft_messages + [{"role": "assistant", "content": draft}, {"role": "user", "content": QUESTION}]


def parse_confidence(reply: str) -> Optional[int]:
    match = _NUMBER.search(reply)
    if not match:
        return None
    value = int(match.group(1))
    return value if 0 <= value <= 100 else None


def confidence_features(reply: str) -> dict:
    value = parse_confidence(reply)
    return {"vc_confidence": value if value is not None else 50, "vc_parsed": int(value is not None),
            "vc_round": int(value is not None and value % 10 == 0)}
