"""Tests for the flat dense index over chunks, with a fake embedder so no model loads."""

import hashlib

import numpy as np
import pytest

from agent.retriever import Hit, build_index, load_index

CHUNKS = [
    {"id": "c00000", "text": "The Program Manager approves the SEMP.", "page_start": "20", "page_end": "20"},
    {"id": "c00001", "text": "Reviews are held at key decision points.", "page_start": "20", "page_end": "21"},
    {"id": "c00002", "text": "The Critical Design Review precedes fabrication.", "page_start": "21", "page_end": "21"},
    {"id": "c00003", "text": "Validation relates back to the ConOps.", "page_start": "22", "page_end": "22"},
]


def fake_embed(texts):
    """Deterministic unit vectors: a bag of hashed words, so shared words mean nearer vectors."""
    out = np.zeros((len(texts), 64), dtype="float32")
    for i, text in enumerate(texts):
        for word in text.lower().replace(":", " ").split():
            out[i, int(hashlib.md5(word.encode()).hexdigest(), 16) % 64] += 1.0
        norm = np.linalg.norm(out[i]) or 1.0
        out[i] /= norm
    return out


@pytest.fixture
def index():
    return build_index(CHUNKS, fake_embed)


def test_search_returns_the_chunk_sharing_the_most_words_first(index):
    hits = index.search("who approves the SEMP", k=2)
    assert [h.chunk["id"] for h in hits][0] == "c00000"
    assert len(hits) == 2
    assert all(isinstance(h, Hit) and isinstance(h.score, float) for h in hits)


def test_search_caps_k_at_the_number_of_chunks(index):
    assert len(index.search("anything", k=50)) == len(CHUNKS)


def test_expand_adds_neighbours_in_hit_order_without_duplicates(index):
    hits = [Hit(CHUNKS[1], 0.9), Hit(CHUNKS[2], 0.8)]
    ids = [h.chunk["id"] for h in index.expand(hits, neighbours=1)]
    assert ids == ["c00000", "c00001", "c00002", "c00003"]
    ids = [h.chunk["id"] for h in index.expand([Hit(CHUNKS[0], 0.5)], neighbours=1)]
    assert ids == ["c00000", "c00001"]


def test_index_rejects_mismatched_vectors():
    from agent.retriever import Index

    with pytest.raises(ValueError):
        Index(CHUNKS, np.zeros((2, 8), dtype="float32"), fake_embed)


def test_save_and_load_round_trip_and_detect_changed_chunks(index, tmp_path):
    index.save(tmp_path)
    loaded = load_index(tmp_path, CHUNKS, fake_embed)
    assert loaded is not None
    assert [h.chunk["id"] for h in loaded.search("Critical Design Review", k=1)] == ["c00002"]
    assert load_index(tmp_path, CHUNKS[:3], fake_embed) is None
    assert load_index(tmp_path / "missing", CHUNKS, fake_embed) is None
