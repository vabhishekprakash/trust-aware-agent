"""Fetch the NASA Systems Engineering Handbook and extract its text per page.

Downloads the PDF (a US government work, public domain) into data/corpus/,
verifies its SHA-256 when one is pinned below, and writes one JSON object per
page to data/corpus/pages.jsonl plus a small manifest. The PDF itself is
gitignored; the extracted text is committed.

Usage:
    python scripts/fetch_corpus.py            # download if missing, extract
    python scripts/fetch_corpus.py --force    # re-download

Exit codes: 0 ok, 1 hash mismatch, 2 download failed.
"""

import argparse
import datetime as dt
import hashlib
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

URL = "https://www.nasa.gov/wp-content/uploads/2018/09/nasa_systems_engineering_handbook_0.pdf"
EXPECTED_SHA256 = "8eeb4887a4dc57a23049da7dd2ed556833cf98e214b240468d987873164ff688"  # verified 2026-09-08
ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "corpus"
PDF = CORPUS / "nasa_se_handbook_rev2.pdf"
PAGES = CORPUS / "pages.jsonl"
MANIFEST = CORPUS / "manifest.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(force: bool) -> None:
    if PDF.exists() and not force:
        print(f"pdf already present: {PDF}")
        return
    CORPUS.mkdir(parents=True, exist_ok=True)
    print(f"downloading {URL}")
    request = urllib.request.Request(URL, headers={"User-Agent": "trust-aware-agent/0.1"})
    with urllib.request.urlopen(request, timeout=120) as response, PDF.open("wb") as out:
        while True:
            chunk = response.read(1 << 20)
            if not chunk:
                break
            out.write(chunk)
    print(f"saved {PDF.stat().st_size:,} bytes")


def extract() -> dict:
    import pymupdf

    doc = pymupdf.open(PDF)
    count = 0
    empty = 0
    with PAGES.open("w", encoding="utf-8", newline="\n") as out:
        for index, page in enumerate(doc, start=1):
            text = page.get_text("text")
            label = page.get_label() or ""
            if not text.strip():
                empty += 1
            record = {"page": index, "printed_page": label, "text": text}
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
    return {
        "pages": count,
        "empty_pages": empty,
        "pymupdf_version": pymupdf.version[0],
        "title_page_snippet": doc[0].get_text("text")[:400].strip(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--force", action="store_true", help="re-download even if the pdf exists")
    args = parser.parse_args()

    try:
        download(args.force)
    except (urllib.error.URLError, OSError) as exc:
        print(f"download failed: {exc}")
        return 2

    digest = sha256(PDF)
    print(f"sha256 {digest}")
    if EXPECTED_SHA256 and digest != EXPECTED_SHA256:
        print(f"hash mismatch: expected {EXPECTED_SHA256}")
        return 1
    if not EXPECTED_SHA256:
        print("no hash pinned yet; pin EXPECTED_SHA256 in this script once the file is verified")

    info = extract()
    manifest = {
        "source_url": URL,
        "sha256": digest,
        "bytes": PDF.stat().st_size,
        "fetched_on": dt.date.today().isoformat(),
        "licence": "Work of the United States government; public domain in the US under 17 U.S.C. 105",
        **info,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"pages extracted: {info['pages']} (empty: {info['empty_pages']}) -> {PAGES}")
    print("title page snippet:")
    print("  " + info["title_page_snippet"].replace("\n", "\n  "))
    return 0


if __name__ == "__main__":
    sys.exit(main())
