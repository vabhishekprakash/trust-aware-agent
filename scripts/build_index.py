"""Embed every chunk with bge-small and save the flat index under data/index/.

Usage:
    python scripts/build_index.py

The vectors are saved as data/index/vectors.npy with the chunk ids beside
them; load_index refuses a saved index whose chunk ids differ from the
current chunks.jsonl, so a rebuild after rechunking cannot be forgotten.
"""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from agent.retriever import EMBEDDING_MODEL, bge_embedder, build_index, load_chunks  # noqa: E402

CHUNKS = ROOT / "data" / "corpus" / "chunks.jsonl"
INDEX = ROOT / "data" / "index"


def main() -> int:
    chunks = load_chunks(CHUNKS)
    start = time.time()
    embed = bge_embedder()
    index = build_index(chunks, embed)
    index.save(INDEX)
    print(f"embedded {len(chunks)} chunks with {EMBEDDING_MODEL} in {time.time() - start:.0f} s; "
          f"vectors {index.vectors.shape} -> {INDEX}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
