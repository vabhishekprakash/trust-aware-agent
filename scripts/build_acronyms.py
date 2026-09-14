"""Build the handbook's acronym table from Appendix A of the extracted text.

Usage:
    python scripts/build_acronyms.py

Reads data/corpus/pages.jsonl, finds the Appendix A pages, and writes
data/corpus/acronyms.json as {acronym: [expansion, ...]}. An entry such as
"Concurrent Engineering or Chief Engineer" becomes two expansions. The grader
uses the table to catch a draft that expands an acronym the wrong way.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "data" / "corpus" / "pages.jsonl"
OUT = ROOT / "data" / "corpus" / "acronyms.json"
ACRONYM_LINE = re.compile(r"^[A-Z][A-Za-z0-9&/-]{1,9}$")
SKIP = {"NASA SYSTEMS ENGINEERING HANDBOOK", "Appendix A: Acronyms"}


def main() -> int:
    pages = [json.loads(l) for l in PAGES.read_text(encoding="utf-8").splitlines() if l.strip()]
    appendix = [p for p in pages if "Appendix A: Acronyms" in p["text"]]
    table: dict[str, list[str]] = {}
    current = None
    for page in appendix:
        for raw in page["text"].split("\n"):
            line = " ".join(raw.replace("\xad", "").split())
            if not line or line in SKIP or line.isdigit():
                continue
            if ACRONYM_LINE.match(line) and not (current and line.islower()):
                current = line
                table.setdefault(current, [])
                continue
            if current is None:
                continue
            if table[current]:
                table[current][-1] = (table[current][-1] + " " + line).strip()
            else:
                table[current].append(line)
    for acronym, expansions in table.items():
        joined = " ".join(expansions)
        table[acronym] = [part.strip() for part in re.split(r"\s+or\s+", joined) if part.strip()]
    table = {k: v for k, v in table.items() if v}
    OUT.write_text(json.dumps(table, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(table)} acronyms from {len(appendix)} pages -> {OUT}")
    for sample in ("ABC", "CDR", "CE", "KDP", "PDR", "SEMP", "TRL"):
        print(f"  {sample}: {table.get(sample)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
