"""Clean extracted handbook pages and cut them into overlapping word chunks.

Each PDF page comes with a running header (page label, chapter title, handbook
title, or "References Cited" and "Bibliography" in the back matter),
soft-hyphen line breaks, and a few control characters left by the extraction,
including the C1 range that the checklists use as bullets. clean_page removes
those. It also joins hard-hyphen line breaks, keeping the hyphen because
"top-\\nlevel" is a real compound while "require-\\nments" is not, and
re-attaches drop-cap initials ("T\\nhis" becomes "This"). chunk_pages then
walks the whole book as one stream of words, cutting chunks of roughly `size`
words that overlap by `overlap` words, snapping each cut back to the nearest
sentence end, and tagging every chunk with the printed page range it came
from.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

HANDBOOK_TITLE = "NASA SYSTEMS ENGINEERING HANDBOOK"
_PAGE_LABEL = re.compile(r"^(?:\d{1,3}|[ivxlc]{1,6})$", re.IGNORECASE)
_CHAPTER_HEADER = re.compile(r"^(?:\d+\.0\s|Appendix [A-Z]:)")
_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")
_SENTENCE_END = (".", "?", "!", '."', '?"', '!"')
_HEADER_LINES = 3
_SECTION_HEADERS = {"References Cited", "Bibliography"}
_HARD_HYPHEN_BREAK = re.compile(r"(\w)-\n(?=[a-z])")
_DROP_CAP = re.compile(r"(?m)^([A-Z])\n(?=[a-z])")


@dataclass
class Chunk:
    id: str
    text: str
    word_count: int
    page_start: str
    page_end: str
    pdf_page_start: int
    pdf_page_end: int


def _is_header_line(line: str) -> bool:
    return bool(
        _PAGE_LABEL.match(line)
        or line.upper() == HANDBOOK_TITLE
        or _CHAPTER_HEADER.match(line)
        or line in _SECTION_HEADERS
    )


def clean_page(text: str) -> str:
    text = text.replace("\xad\n", "").replace("\xad", "")
    text = _HARD_HYPHEN_BREAK.sub(r"\1-", text)
    text = _DROP_CAP.sub(r"\1", text)
    text = text.replace("\u2002", " ").replace("\u00a0", " ")
    text = _CONTROL.sub("", text)
    lines = [" ".join(line.split()) for line in text.split("\n")]
    lines = [line for line in lines if line]
    kept = 0
    while kept < min(_HEADER_LINES, len(lines)) and _is_header_line(lines[kept]):
        kept += 1
    return " ".join(lines[kept:])


def chunk_pages(pages: list[dict], size: int = 200, overlap: int = 40) -> list[Chunk]:
    words: list[tuple[str, dict]] = []
    for page in pages:
        for word in clean_page(page["text"]).split():
            words.append((word, page))

    chunks: list[Chunk] = []
    lookback = max(1, size // 4)
    start = 0
    while start < len(words):
        end = min(start + size, len(words))
        if end < len(words):
            for candidate in range(end, max(end - lookback, start + 1), -1):
                if words[candidate - 1][0].endswith(_SENTENCE_END):
                    end = candidate
                    break
        piece = words[start:end]
        first, last = piece[0][1], piece[-1][1]
        chunks.append(
            Chunk(
                id=f"c{len(chunks):05d}",
                text=" ".join(word for word, _ in piece),
                word_count=len(piece),
                page_start=first.get("printed_page") or str(first["page"]),
                page_end=last.get("printed_page") or str(last["page"]),
                pdf_page_start=first["page"],
                pdf_page_end=last["page"],
            )
        )
        if end >= len(words):
            break
        start = max(end - overlap, start + 1)
    return chunks
