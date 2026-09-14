"""Which chunks hold an item's evidence, and whether retrieval found one.

One definition, shared by the recall measurement and the agent run, so the
confounder numbers rest on a single rule. A target chunk covers the evidence
page and contains the quote, matched on letters and digits only, accepting
the quote's first or last twelve words because a quote can straddle a chunk
boundary. Retrieval found the evidence when any target chunk is in the hits.
"""

from __future__ import annotations

import re
from typing import Optional


def key(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def page_number(label) -> Optional[int]:
    return int(label) if str(label).isdigit() else None


def covers(chunk: dict, page) -> bool:
    p, a, b = page_number(page), page_number(chunk["page_start"]), page_number(chunk["page_end"])
    if p is None or a is None or b is None:
        return str(page) in (str(chunk["page_start"]), str(chunk["page_end"]))
    return a <= p <= b


def targets(item: dict, chunks: list[dict]) -> set:
    found = set()
    for ev in item.get("evidence", []):
        words = ev["quote"].split()
        probes = [key(ev["quote"]), key(" ".join(words[:12])), key(" ".join(words[-12:]))]
        for c in chunks:
            if covers(c, ev["page"]) and any(len(p) >= 20 and p in key(c["text"]) for p in probes):
                found.add(c["id"])
    return found


def evidence_rank(target_ids: set, retrieved_ids: list[str]) -> Optional[int]:
    """1-based rank of the first target chunk among the hits, or None."""
    for rank, cid in enumerate(retrieved_ids, start=1):
        if cid in target_ids:
            return rank
    return None


def page_retrieved(item: dict, retrieved_chunks: list[dict]) -> bool:
    """Looser than a target chunk: any hit whose page range covers an evidence page."""
    return any(covers(c, ev["page"]) for ev in item.get("evidence", []) for c in retrieved_chunks)


def evidence_record(item: dict, chunks: list[dict], retrieved_chunks: list[dict]) -> dict:
    """The block the runner writes into a trace."""
    wanted = targets(item, chunks)
    rank = evidence_rank(wanted, [c["id"] for c in retrieved_chunks])
    return {
        "pages": sorted({str(ev["page"]) for ev in item.get("evidence", [])}),
        "chunk_ids": sorted(wanted),
        "has_target": bool(wanted),
        "retrieved": rank is not None,
        "rank": rank,
        "page_retrieved": page_retrieved(item, retrieved_chunks),
    }
