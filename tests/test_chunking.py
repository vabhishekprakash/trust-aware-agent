"""Tests for page cleaning and chunking of the extracted handbook text."""

from agent.chunking import chunk_pages, clean_page

HEADER_PAGE = (
    "37\n"
    "3.0  NASA Program/Project Life Cycle\n"
    "NASA SYSTEMS ENGINEERING HANDBOOK\n"
    "Depending on the project, some relief on \n"
    "the scope may be appropriate.\n"
)


def test_clean_page_removes_running_header_lines():
    text = clean_page(HEADER_PAGE)
    assert text.startswith("Depending on the project")
    assert "SYSTEMS ENGINEERING HANDBOOK" not in text


def test_clean_page_removes_back_matter_running_headers():
    assert clean_page("265\nNASA SYSTEMS ENGINEERING HANDBOOK\nBibliography\nSmith, J. 2001.") == "Smith, J. 2001."
    assert clean_page("261\nReferences Cited\nNASA SYSTEMS ENGINEERING HANDBOOK\nNPR 7120.5.") == "NPR 7120.5."


def test_clean_page_keeps_body_when_no_header_present():
    assert clean_page("Just a body line.\nAnother line.") == "Just a body line. Another line."


def test_clean_page_joins_soft_hyphen_line_breaks():
    assert clean_page("types of mis\xad\nsions that can") == "types of missions that can"


def test_clean_page_joins_hard_hyphen_line_breaks_keeping_the_hyphen():
    assert clean_page("the top-\nlevel requirements") == "the top-level requirements"
    assert clean_page("Define technical require-\nments in") == "Define technical require-ments in"


def test_clean_page_reattaches_drop_cap_initials():
    assert clean_page("1.1 Purpose\nT\nhis handbook is intended") == "1.1 Purpose This handbook is intended"


def test_clean_page_normalises_special_spaces_and_control_chars():
    assert clean_page("3.11.4.2  \x07Adjusting the Scope") == "3.11.4.2 Adjusting the Scope"
    assert clean_page("Use of Correct Terms \x86 \x86 Shall = requirement") == "Use of Correct Terms Shall = requirement"


def _pages(words_per_page, n_pages, sentence_every=None):
    pages, counter = [], 0
    for i in range(n_pages):
        words = []
        for _ in range(words_per_page):
            counter += 1
            word = f"w{counter}"
            if sentence_every and counter % sentence_every == 0:
                word += "."
            words.append(word)
        pages.append({"page": i + 1, "printed_page": str(i + 1), "text": " ".join(words)})
    return pages


def test_chunks_respect_size_and_overlap_without_sentences():
    chunks = chunk_pages(_pages(250, 2), size=100, overlap=20)
    assert len(chunks) > 1
    for c in chunks:
        assert c.word_count <= 100
    first, second = chunks[0].text.split(), chunks[1].text.split()
    assert first[-20:] == second[:20]


def test_every_word_appears_in_some_chunk():
    pages = _pages(130, 3)
    chunks = chunk_pages(pages, size=100, overlap=20)
    seen = {w for c in chunks for w in c.text.split()}
    expected = {w for p in pages for w in p["text"].split()}
    assert expected <= seen


def test_chunk_records_page_range_it_spans():
    chunks = chunk_pages(_pages(60, 2), size=100, overlap=20)
    assert chunks[0].page_start == "1"
    assert chunks[0].page_end == "2"
    assert chunks[0].pdf_page_start == 1
    assert chunks[0].pdf_page_end == 2


def test_chunk_boundary_snaps_back_to_sentence_end():
    chunks = chunk_pages(_pages(300, 1, sentence_every=23), size=100, overlap=20)
    assert chunks[0].text.endswith(".")
    assert chunks[0].word_count < 100


def test_chunk_ids_are_sequential():
    chunks = chunk_pages(_pages(250, 1), size=100, overlap=20)
    assert [c.id for c in chunks] == [f"c{i:05d}" for i in range(len(chunks))]


def test_empty_pages_are_skipped():
    pages = _pages(50, 1) + [{"page": 2, "printed_page": "2", "text": "   \n"}]
    chunks = chunk_pages(pages, size=100, overlap=20)
    assert len(chunks) == 1
    assert chunks[0].page_end == "1"
