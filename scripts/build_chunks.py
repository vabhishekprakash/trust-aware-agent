"""Cut the extracted handbook pages into chunks and measure their token lengths.

Reads data/corpus/pages.jsonl, writes data/corpus/chunks.jsonl, and reports
word and token statistics. Token counts use the tokenizer of the embedding
model so the report says whether any chunk would be truncated at that model's
input limit rather than assuming it.

Usage:
    python scripts/build_chunks.py [--size 200] [--overlap 40] [--model BAAI/bge-small-en-v1.5]
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from agent.chunking import chunk_pages  # noqa: E402

PAGES = ROOT / "data" / "corpus" / "pages.jsonl"
CHUNKS = ROOT / "data" / "corpus" / "chunks.jsonl"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--size", type=int, default=200)
    parser.add_argument("--overlap", type=int, default=40)
    parser.add_argument("--model", default="BAAI/bge-small-en-v1.5")
    parser.add_argument("--no-tokens", action="store_true", help="skip the tokenizer measurement")
    args = parser.parse_args()

    pages = [json.loads(line) for line in PAGES.read_text(encoding="utf-8").splitlines() if line.strip()]
    chunks = chunk_pages(pages, size=args.size, overlap=args.overlap)
    with CHUNKS.open("w", encoding="utf-8", newline="\n") as out:
        for c in chunks:
            out.write(json.dumps(c.__dict__, ensure_ascii=False) + "\n")

    words = [c.word_count for c in chunks]
    print(f"chunks: {len(chunks)} from {len(pages)} pages")
    print(f"words per chunk: min {min(words)} median {sorted(words)[len(words) // 2]} max {max(words)}")
    print(f"written: {CHUNKS}")

    if args.no_tokens:
        return 0
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    limit = tokenizer.model_max_length
    lengths = [len(tokenizer(c.text, add_special_tokens=True)["input_ids"]) for c in chunks]
    longest = max(range(len(chunks)), key=lambda i: lengths[i])
    over = sum(1 for n in lengths if n > limit)
    print(f"tokenizer: {args.model}, input limit {limit} tokens")
    print(f"tokens per chunk: min {min(lengths)} median {sorted(lengths)[len(lengths) // 2]} max {max(lengths)}")
    print(f"longest chunk: {chunks[longest].id} pages {chunks[longest].page_start}-{chunks[longest].page_end}, "
          f"{chunks[longest].word_count} words, {lengths[longest]} tokens")
    print(f"chunks over the limit: {over}")
    print(f"chunks over 256 tokens, the all-MiniLM-L6-v2 limit: {sum(1 for n in lengths if n > 256)}")
    return 0 if over == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
