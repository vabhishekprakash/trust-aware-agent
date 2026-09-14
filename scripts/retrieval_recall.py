"""Measure, on the dev items only, how often the evidence chunk is among the top k.

Usage:
    python scripts/retrieval_recall.py [--split data/eval/dev.jsonl]

For each dev item the target chunks are those whose page range covers the
evidence page and whose text contains the quote (matched on letters and
digits only, and accepting the quote's first or last twelve words, because a
quote can straddle a chunk boundary). An item counts as recalled at k when
any target chunk is in the top k. Reported for several k, with and without
one neighbouring chunk on each side, per bucket, with the average context
cost in words. The test split is never read by this script.
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from agent.evidence import targets  # noqa: E402
from agent.retriever import bge_embedder, load_chunks, load_index  # noqa: E402

KS = [1, 3, 5, 8, 10]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--split", default=str(ROOT / "data" / "eval" / "dev.jsonl"))
    args = parser.parse_args()
    if "test" in Path(args.split).name:
        print("refusing to read the test split")
        return 1

    chunks = load_chunks(ROOT / "data" / "corpus" / "chunks.jsonl")
    embed = bge_embedder()
    index = load_index(ROOT / "data" / "index", chunks, embed)
    if index is None:
        print("no index for the current chunks; run scripts/build_index.py first")
        return 1
    items = [json.loads(l) for l in Path(args.split).read_text(encoding="utf-8").splitlines() if l.strip()]

    rows = []
    for item in items:
        wanted = targets(item, chunks)
        hits = index.search(item["question"], k=max(KS))
        rows.append((item, wanted, hits))
    no_target = [it["id"] for it, wanted, _ in rows if not wanted]

    buckets = sorted({it["bucket"] for it, _, _ in rows})
    print(f"items: {len(rows)}; items whose evidence quote was not found in any chunk: {len(no_target)} {no_target}")
    print("\nrecall at k (any target chunk in the top k), per bucket; 'n' counts items with a target")
    header = f"{'k':>3} {'nbr':>4} " + " ".join(f"{b[:12]:>14}" for b in buckets) + f" {'all':>10} {'words':>7}"
    print(header)
    for neighbours in (0, 1):
        for k in KS:
            cells, total_hit, total_n, words = [], 0, 0, []
            for b in buckets:
                hit = n = 0
                for it, wanted, hits in rows:
                    if it["bucket"] != b or not wanted:
                        continue
                    chosen = index.expand(hits[:k], neighbours) if neighbours else hits[:k]
                    n += 1
                    hit += any(h.chunk["id"] in wanted for h in chosen)
                cells.append(f"{hit:>3}/{n:<3} {100 * hit / n if n else 0:>5.0f}%")
                total_hit += hit
                total_n += n
            for it, wanted, hits in rows:
                chosen = index.expand(hits[:k], neighbours) if neighbours else hits[:k]
                words.append(sum(h.chunk["word_count"] for h in chosen))
            print(f"{k:>3} {neighbours:>4} " + " ".join(f"{c:>14}" for c in cells) + f" {100 * total_hit / total_n:>9.0f}% {sum(words) / len(words):>7.0f}")
    print("\nwords is the average context handed to the model per question; tokens are about 1.3 times words for this text.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
