"""Tests for the shared evidence definition."""

from agent.evidence import covers, evidence_rank, evidence_record, targets

CHUNKS = [
    {"id": "c1", "page_start": "45", "page_end": "46", "text": "For example, at the topmost level, the customer may be the person or organization that is purchasing the product."},
    {"id": "c2", "page_start": "46", "page_end": "47", "text": "For a systems engineer working three or four levels down in the PBS, the customer may be the leader of the team that takes the element and"},
    {"id": "c3", "page_start": "99", "page_end": "99", "text": "the customer may be the leader of the team, but this page is not the evidence page."},
]
ITEM = {"id": "q", "evidence": [{"page": "46", "quote": "the customer may be the leader of the team that takes the element and integrates it into a larger assembly"}]}


def test_covers_handles_ranges_and_roman_labels():
    assert covers(CHUNKS[0], "46") and covers(CHUNKS[0], "45") and not covers(CHUNKS[0], "47")
    assert covers({"page_start": "xii", "page_end": "xii"}, "xii")
    assert not covers({"page_start": "xii", "page_end": "xii"}, "12")


def test_targets_need_the_page_and_the_quote():
    assert targets(ITEM, CHUNKS) == {"c2"}
    assert targets({"evidence": [{"page": "46", "quote": "words not in any chunk at all here"}]}, CHUNKS) == set()


def test_evidence_rank_and_record():
    assert evidence_rank({"c2"}, ["c1", "c3", "c2"]) == 3
    assert evidence_rank({"c2"}, ["c1", "c3"]) is None
    record = evidence_record(ITEM, CHUNKS, [CHUNKS[0], CHUNKS[2]])
    assert record == {"pages": ["46"], "chunk_ids": ["c2"], "has_target": True, "retrieved": False, "rank": None, "page_retrieved": True}
    record = evidence_record(ITEM, CHUNKS, [CHUNKS[2], CHUNKS[1]])
    assert record["retrieved"] is True and record["rank"] == 2
