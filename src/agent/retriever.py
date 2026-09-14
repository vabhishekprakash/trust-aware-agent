"""Dense retrieval over the handbook chunks: bge-small embeddings in a flat FAISS index.

build_index embeds every chunk once; Index.search embeds a question and
returns the nearest chunks by inner product on normalised vectors, which is
cosine similarity. expand adds the chunks on either side of each hit, in the
order of the hits, without duplicates, because answers can straddle a chunk
boundary. The embedding function is injectable so the index logic is tested
without loading the model.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import numpy as np

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

Embed = Callable[[list[str]], np.ndarray]


@dataclass
class Hit:
    chunk: dict
    score: float


def load_chunks(path: str | Path) -> list[dict]:
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]


def bge_embedder(model_name: str = EMBEDDING_MODEL) -> Embed:
    """The real embedder: sentence-transformers on CPU, unit-normalised vectors."""
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name, device="cpu")

    def embed(texts: list[str]) -> np.ndarray:
        return np.asarray(model.encode(texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False), dtype="float32")

    return embed


class Index:
    def __init__(self, chunks: list[dict], vectors: np.ndarray, embed: Embed):
        import faiss

        if len(chunks) != len(vectors):
            raise ValueError("one vector per chunk is required")
        self.chunks = chunks
        self.vectors = np.ascontiguousarray(vectors, dtype="float32")
        self.embed = embed
        self.faiss = faiss.IndexFlatIP(self.vectors.shape[1])
        self.faiss.add(self.vectors)
        self._position = {c["id"]: i for i, c in enumerate(chunks)}

    def search(self, query: str, k: int = 5) -> list[Hit]:
        vector = self.embed([QUERY_PREFIX + query])
        scores, positions = self.faiss.search(np.ascontiguousarray(vector, dtype="float32"), min(k, len(self.chunks)))
        return [Hit(self.chunks[p], float(s)) for s, p in zip(scores[0], positions[0]) if p >= 0]

    def expand(self, hits: list[Hit], neighbours: int = 1) -> list[Hit]:
        """Each hit plus its neighbours on either side, hits first, no duplicates."""
        seen, out = set(), []
        for hit in hits:
            for offset in range(-neighbours, neighbours + 1):
                pos = self._position[hit.chunk["id"]] + offset
                if 0 <= pos < len(self.chunks) and pos not in seen:
                    seen.add(pos)
                    out.append(hit if offset == 0 else Hit(self.chunks[pos], hit.score))
        return out

    def save(self, directory: str | Path) -> None:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        np.save(directory / "vectors.npy", self.vectors)
        (directory / "chunk_ids.json").write_text(json.dumps([c["id"] for c in self.chunks]), encoding="utf-8", newline="\n")


def build_index(chunks: list[dict], embed: Embed) -> Index:
    return Index(chunks, embed([c["text"] for c in chunks]), embed)


def load_index(directory: str | Path, chunks: list[dict], embed: Embed) -> Optional[Index]:
    """The saved index, or None when it is missing or was built from different chunks."""
    directory = Path(directory)
    if not (directory / "vectors.npy").exists() or not (directory / "chunk_ids.json").exists():
        return None
    ids = json.loads((directory / "chunk_ids.json").read_text(encoding="utf-8"))
    if ids != [c["id"] for c in chunks]:
        return None
    return Index(chunks, np.load(directory / "vectors.npy"), embed)
