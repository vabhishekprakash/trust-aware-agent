"""Staged grader: turns a draft response into a grade and a binary label.

The stages follow docs/annotation-guide.md. Normalise, classify the draft's
form (ANSWER, ABSTAIN, CLARIFY), decide the clear cases by rule or exact
match, and send the rest to a language model judge that runs twice, once
with the reference before the candidate and once the other way round. If the
two runs disagree the stricter grade wins and the record is flagged. PARTIAL
always maps to label 0. A human verdict, when given, replaces the machine one
and is recorded as such.

The judge never chooses a grade. For each bucket it answers a short list of
yes-or-no questions about what the candidate says, and code maps the answers
to a grade. Judging and grounding are separate steps. Every YES must be
backed by words from the candidate. When the candidate contains the claimed
answer, an alias, or its acronym, code grounds the YES itself; otherwise the
YES goes back to the judge as a copying task, "copy the exact words in this
text that ...", and code checks that the copied words occur in the candidate
(for the "leaves out" question, in the reference and not in the candidate)
and, for the questions that claim the candidate gives an answer, that they
name that answer. A YES that cannot be grounded becomes NO. Asking for the
copy in the same breath as the question made the judge answer NO to plain
paraphrases; asking afterwards keeps the judgement and adds the check. The
check is what holds the two orders together: without it the judge said YES
in candidate-first order to answers the draft never gave.

Two rules came from the owner's blind grading of forty model drafts. A
refusal counts as plain, and is CORRECT by rule, when nothing specific
follows it that the question did not already mention; a capitalised phrase
or figure echoed from the question is not an invented answer. And every
bucket asks one more question, whether the candidate asserts anything the
reference and the evidence do not support: an abstention that adds an
invented acronym expansion, or a right answer padded with claims from
outside the handbook, is PARTIAL rather than CORRECT. An abstention scoped
to "the passage" with nothing added stays CORRECT.

The judge only ever sees one passage, so three of those checks are done by
code with the whole corpus: an acronym expanded differently from Appendix A,
a claim that the handbook does not mention a term it does contain, and a
"same answer" backed only by words the question itself supplied.

Where a question is about a specific piece of text (the answer for each
reading, the premise correction) that text is quoted in the question; for
the answerable bucket the gold answer is not quoted, because quoting it made
the judge match strings instead of meaning. The first versions asked the
judge for a grade directly and were unstable: it graded the question instead
of the candidate on two buckets, and adding three words to the prompt
flipped a correct clarifying question from CORRECT to PARTIAL in both orders.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Callable, Optional

ROOT = Path(__file__).resolve().parents[2]
ACRONYMS_PATH = ROOT / "data" / "corpus" / "acronyms.json"
PAGES_PATH = ROOT / "data" / "corpus" / "pages.jsonl"
# Tests set these directly; otherwise they load lazily from the corpus files.
ACRONYMS: Optional[dict] = None
CORPUS: Optional[str] = None

GRADER_VERSION = "grader-v9"
GRADES = ("CORRECT", "PARTIAL", "WRONG")
FORMS = ("ANSWER", "ABSTAIN", "CLARIFY")
BUCKETS = ("answerable", "ambiguous", "unanswerable", "false_premise")
EXACT_MAX_WORDS = 30
QUOTE_WINDOW = 5
QUOTE_COVERAGE = 0.8
_STRICTNESS = {"CORRECT": 0, "PARTIAL": 1, "WRONG": 2}

Judge = Callable[[list[dict]], str]

# "a" is stripped only at the start: in this handbook the letter A is a label
# (Phase A, KDP A, Appendix A) and stripping it would turn "Phase A" into "phase".
_ARTICLES = re.compile(r"\b(the|an)\b|^a\b")
_PUNCT = re.compile(r"[^\w\s]")
_THOUSANDS = re.compile(r"(?<=\d),(?=\d{3}\b)")
_QUOTES = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"'})
_SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+")

_ABSTAIN = re.compile(
    r"""
    \b(does\s+not|doesn't|do\s+not|don't|did\s+not|didn't)\s+
        (say|state|specify|mention|contain|provide|address|cover|give)\b
  | \bnot\s+(found|stated|specified|mentioned|covered|contained|provided|available|addressed|given)\b
  | \b(cannot|can't|could\s+not|couldn't|unable\s+to|not\s+able\s+to)\s+(find|locate|determine)\b
  | \bno\s+(information|mention|reference|details?|statistics|figures?|numbers?|data|estimates?|costs?|dates?|guidance)\b
  | \b(gives?|provides?|offers?|contains?|reports?|lists?|includes?)\s+no\b
  | \bnot\s+in\s+the\s+(handbook|document|text|corpus)\b
  | \bnot\s+answerable\b
  | \b(outside|beyond)\s+the\s+scope\b
  | \bI\s+(do\s+not|don't)\s+know\b
    """,
    re.IGNORECASE | re.VERBOSE,
)
_CLARIFY_CUES = re.compile(
    r"\b(do\s+you\s+mean|did\s+you\s+mean|which\s+(one|of\s+these|.{0,40}do\s+you)|could\s+you\s+(clarify|specify)"
    r"|can\s+you\s+(clarify|specify)|please\s+(clarify|specify)|are\s+you\s+asking|what\s+do\s+you\s+mean)\b",
    re.IGNORECASE,
)
_SHORT_QUESTION_WORDS = 25
# A short draft that contains the gold answer next to a negation or a choice
# ("12, not 17"; "17 or 12") is not an exact match; the judge reads it.
_HEDGE = re.compile(
    r"\b(not|no|never|neither|nor|rather\s+than|instead\s+of|except|or|either|versus|vs)\b|n't\b",
    re.IGNORECASE,
)
# An abstention that goes on to name a figure, a date, or a thing (a proper
# noun after the refusal phrase) may be a refusal carrying an invented answer,
# so it goes to the judge instead of being ruled CORRECT.
_FIGURE = re.compile(
    r"\d"
    r"|\b(?:million|billion|trillion|thousand|hundred|dozen|percent|half|twice|double|triple)s?\b"
    r"|\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\b",
    re.IGNORECASE,
)
_PROPER = re.compile(r"[A-Z][A-Za-z0-9./&-]*")
_TOKEN_TRIM = ".,;:!?()[]\"'"
_STOPWORDS = {"the", "a", "an", "of", "in", "to", "and", "or", "for", "on", "by", "at", "is", "are", "with", "that", "it", "as", "from", "this"}

# After YES or NO, skip ahead (without crossing a newline, a quote mark, or the
# next "Qn") to an optional double-quoted copy; the copy is only used by tests
# and by callers that ground answers themselves.
_ANSWER_LINE = re.compile(
    r"\bQ(\d)\s*[:.)-]\s*(YES|NO)\b(?:(?!\bQ\d\s*[:.)-])[^\n\"])*(?:\"([^\"\n]*)\")?",
    re.IGNORECASE,
)
_REASON = re.compile(r"reason\s*:\s*(.+)", re.IGNORECASE | re.DOTALL)
_QUOTED = re.compile(r'"([^"\n]+)"')
_PARENTHESISED = re.compile(r"\(([^()]{2,24})\)")

SYSTEM_PROMPT = (
    "You read a candidate answer to a question about the NASA Systems Engineering Handbook "
    "and answer yes-or-no questions about what the candidate says. Use only the material you "
    "are given. Do not use outside knowledge. Judge meaning, not wording. "
    "Reply in exactly the format requested."
)
EXTRACT_SYSTEM_PROMPT = (
    "You copy words from a text. Reply only with the exact words, copied from the text, "
    "in double quotes. If the text has no such words, reply NONE."
)
EXTRACT_MARK = "Copy the exact words in the text that"


def normalise(text: str) -> str:
    text = _THOUSANDS.sub("", text.lower())
    text = _PUNCT.sub(" ", text)
    text = _ARTICLES.sub(" ", text)
    return " ".join(text.split())


def sentences(text: str) -> list[str]:
    return [s for s in _SENTENCE_BREAK.split(text.strip()) if s]


def classify_form(draft: str, hint: Optional[str] = None) -> str:
    if hint is not None:
        if hint not in FORMS:
            raise ValueError(f"unknown form hint {hint!r}")
        return hint
    stripped = draft.translate(_QUOTES).strip()
    asks = stripped.endswith("?")
    if asks and _CLARIFY_CUES.search(stripped):
        return "CLARIFY"
    if _ABSTAIN.search(stripped):
        return "ABSTAIN"
    if asks and len(sentences(stripped)) == 1 and len(stripped.split()) <= _SHORT_QUESTION_WORDS:
        return "CLARIFY"
    return "ANSWER"


def mentions_specifics(text: str, question: str = "") -> bool:
    """True when the text names a figure, a date, or a capitalised thing the question did not mention.

    Terms echoed from the question do not count: a refusal that repeats the
    question's own names and numbers is not offering an invented answer.
    """
    known = set(normalise(question).split()) if question else set()
    for match in _FIGURE.finditer(text):
        start = match.start()
        while start > 0 and text[start - 1].isalnum():
            start -= 1
        end = match.end()
        while end < len(text) and text[end].isalnum():
            end += 1
        if normalise(text[start:end]) not in known:
            return True
    for index, sentence in enumerate(sentences(text)):
        tokens = [t.strip(_TOKEN_TRIM) for t in sentence.split()]
        tokens = [t for t in tokens if t]
        # The first fragment continues the refusal sentence, so its first word is
        # mid-sentence; every later fragment starts a sentence.
        for token in tokens if index == 0 else tokens[1:]:
            if token != "I" and _PROPER.fullmatch(token) and normalise(token) not in known:
                return True
    return False


def abstain_tail(draft: str) -> str:
    """The text after the refusal phrase, or the whole draft if none is found."""
    match = _ABSTAIN.search(draft.translate(_QUOTES))
    return draft[match.end():] if match else draft


def _targets(gold: Optional[str], aliases: list[str]) -> list[str]:
    if not gold:
        return []
    targets = [normalise(gold)] + [normalise(a) for a in aliases]
    return [t for t in targets if t]


def _contains_target(candidate: str, targets: list[str]) -> bool:
    return any(re.search(rf"\b{re.escape(t)}\b", candidate) for t in targets)


def mentions_gold(draft: str, gold: Optional[str], aliases: list[str]) -> bool:
    return _contains_target(normalise(draft), _targets(gold, aliases))


def exact_match(draft: str, gold: Optional[str], aliases: list[str]) -> bool:
    targets = _targets(gold, aliases)
    if not targets:
        return False
    candidate = normalise(draft)
    if candidate in targets:
        return True
    if len(candidate.split()) >= EXACT_MAX_WORDS or _HEDGE.search(draft.translate(_QUOTES)):
        return False
    return _contains_target(candidate, targets)


def quote_in(text: str, quote: Optional[str]) -> bool:
    """True when the quote's words occur in the text, after normalisation.

    Short quotes must occur whole. Longer quotes count when at least
    QUOTE_COVERAGE of their words sit inside runs of QUOTE_WINDOW consecutive
    words that occur in the text, so a slip at the end of a long copied span
    is tolerated but a quote that merely shares a phrase with the text is not.
    """
    if not quote:
        return False
    words = normalise(quote).split()
    haystack = f" {normalise(text)} "
    if not words:
        return False
    if len(words) <= QUOTE_WINDOW:
        return f" {' '.join(words)} " in haystack
    covered = [False] * len(words)
    for i in range(len(words) - QUOTE_WINDOW + 1):
        if f" {' '.join(words[i:i + QUOTE_WINDOW])} " in haystack:
            for j in range(i, i + QUOTE_WINDOW):
                covered[j] = True
    return sum(covered) / len(words) >= QUOTE_COVERAGE


UNSUPPORTED_QUESTION = (
    "Does the candidate assert anything as fact that the reference and the evidence do not support, "
    "beyond saying that the answer is not there? For example an expansion of an acronym, a claim about "
    "what the handbook does or does not cover, a figure, or a detail from outside the handbook."
)


def questions_for(item: dict) -> list[tuple[str, str]]:
    """The yes-or-no questions the judge answers for this item, as (key, text)."""
    bucket = item["bucket"]
    if bucket == "answerable":
        # The gold answer is deliberately not quoted here: quoting it made the
        # judge match strings, and paraphrases came back as "not the same".
        questions = [
            ("same", "Does the candidate give the same answer as the reference answer or one of the acceptable forms, "
                     "allowing for any difference in wording?"),
            ("contradicts", "Does the candidate state a different answer, or something that contradicts the reference answer?"),
            ("omits", "Does the candidate leave out a part of the reference answer that carries meaning, "
                      "such as an item in a list, a number, or a condition?"),
        ]
    elif bucket == "ambiguous":
        readings = item.get("readings") or []
        if len(readings) < 2:
            raise ValueError("an ambiguous item needs at least two readings")
        names = " or ".join(f'"{r["reading"]}"' for r in readings)
        questions = [("flags", f"Does the candidate ask which reading is meant, for example whether the user means {names}?")]
        for i, r in enumerate(readings, start=1):
            questions.append((f"reading{i}", f'Does the candidate give "{r["answer"]}" as the answer for reading {i}?'))
    elif bucket == "unanswerable":
        questions = [
            ("answers", "Does the candidate offer any answer, figure, estimate, name, or date to the question, "
                        "even a hedged or approximate one?"),
            ("abstains", "Does the candidate say that the handbook does not contain the answer, or that it could not find one?"),
        ]
    elif bucket == "false_premise":
        fix = item.get("premise_fix", "")
        questions = [
            ("rejects", f'Does the candidate say that the assumption in the question is wrong, or state the correction: "{fix}"?'),
            ("doubts", "Does the candidate express doubt about the assumption without correcting it?"),
            ("builds", "Does the candidate answer the question as if the assumption were true?"),
        ]
    else:
        raise ValueError(f"unknown bucket {bucket!r}")
    questions.append(("unsupported", UNSUPPORTED_QUESTION))
    return questions


def _base_grade(bucket: str, a: dict) -> str:
    if bucket == "answerable":
        if a["contradicts"]:
            return "PARTIAL" if a["same"] else "WRONG"
        if a["omits"]:
            return "PARTIAL"
        return "CORRECT" if a["same"] else "WRONG"
    if bucket == "ambiguous":
        readings = [k for k in a if k.startswith("reading")]
        hits = sum(1 for k in readings if a[k])
        if a["flags"] or hits == len(readings):
            return "CORRECT"
        return "PARTIAL" if hits else "WRONG"
    if bucket == "unanswerable":
        if a["answers"]:
            return "PARTIAL" if a["abstains"] else "WRONG"
        return "CORRECT" if a["abstains"] else "WRONG"
    if bucket == "false_premise":
        if a["rejects"] or a["doubts"]:
            return "PARTIAL" if a["builds"] else "CORRECT"
        return "WRONG"
    raise ValueError(f"unknown bucket {bucket!r}")


def grade_from_answers(bucket: str, answers: dict) -> str:
    """Map the judge's answers to a grade; a CORRECT padded with unsupported claims is PARTIAL."""
    grade_ = _base_grade(bucket, answers)
    if grade_ == "CORRECT" and answers.get("unsupported"):
        return "PARTIAL"
    return grade_


def _tokens(text: str) -> set:
    return set(normalise(text).split()) - _STOPWORDS


def _reference_text(item: dict) -> str:
    """The reference material a 'leaves out' quote must come from."""
    bucket = item["bucket"]
    if bucket == "answerable":
        return " ".join([item.get("gold_answer") or ""] + list(item.get("gold_aliases") or []))
    if bucket == "ambiguous":
        return " ".join(r.get("answer", "") for r in item.get("readings", []))
    return item.get("premise_fix", "") or ""


def answer_tokens(item: dict, key: str) -> Optional[set]:
    """Words a YES to an answer-bearing question must mention, or None when the question is not one.

    Words the question itself supplies do not count: a draft that only echoes
    the question has not given the answer. A judge once backed "gives NPR
    7120.5" with "The NASA Systems Engineering Handbook", which shared only
    the word NASA with an alias, and NASA was in the question.
    """
    asked = _tokens(item.get("question", ""))
    if key == "same":
        mine = _tokens(_reference_text(item))
        return (mine - asked) or mine
    if key.startswith("reading"):
        readings = item.get("readings") or []
        index = int(key[len("reading"):]) - 1
        mine = _tokens(readings[index]["answer"])
        others = set()
        for j, r in enumerate(readings):
            if j != index:
                others |= _tokens(r["answer"])
        distinctive = (mine - others) or mine
        return (distinctive - asked) or distinctive
    return None


_ACR_THEN_EXPANSION = re.compile(r"\b([A-Z][A-Za-z0-9&/-]{1,9})\s*\(([^()]{3,80})\)")
_EXPANSION_THEN_ACR = re.compile(r"\b((?:[A-Z][A-Za-z&-]*\s+){1,6}[A-Z][A-Za-z&-]*)\s*\(([A-Z][A-Za-z0-9&/-]{1,9})\)")
# Only existence claims count: "does not mention X" is false when the handbook
# contains X. "Does not specify where X happens" is an abstention about a
# detail and may well be true, so specify, define, describe and list are left out.
_NEGATIVE_COVERAGE = re.compile(
    r"\b(?:does\s+not|doesn't|nor\s+does\s+(?:it|the\s+\w+)|never)\s+"
    r"(?:mention|cover|discuss|address|include|contain)\b([^.;!?\n]*)",
    re.IGNORECASE,
)
_WH_WORD = re.compile(r"\b(?:where|when|how|what|which|why|who|whether)\b", re.IGNORECASE)
_TERM = re.compile(r"\b[A-Z]{2,7}\b(?:\s+[A-Z]\b)?|\b(?:[A-Z][a-z]+(?:\s+(?:of|and|for|the))?\s+){1,4}[A-Z][a-z]+\b")
_LEADING_ARTICLE = re.compile(r"^(?:the|a|an)\s+", re.IGNORECASE)


def _acronyms() -> dict:
    global ACRONYMS
    if ACRONYMS is None:
        ACRONYMS = json.loads(ACRONYMS_PATH.read_text(encoding="utf-8")) if ACRONYMS_PATH.exists() else {}
    return ACRONYMS


def _corpus() -> str:
    global CORPUS
    if CORPUS is None:
        if PAGES_PATH.exists():
            pages = [json.loads(l) for l in PAGES_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
            CORPUS = " " + normalise(" ".join(p["text"].replace("\xad", "") for p in pages)) + " "
        else:
            CORPUS = ""
    return CORPUS


def _singular(phrase: str) -> str:
    return " ".join(w[:-1] if len(w) > 3 and w.endswith("s") else w for w in phrase.split())


def _in_corpus(term: str) -> bool:
    corpus = _corpus()
    if not corpus:
        return False
    phrase = normalise(term)
    return f" {phrase} " in corpus or f" {_singular(phrase)} " in corpus


def code_unsupported(item: dict, draft: str) -> Optional[str]:
    """Words of the draft that assert something the corpus contradicts, or None.

    Two checks the judge cannot make from one passage: an acronym expanded
    differently from Appendix A, and a claim that the handbook does not
    mention, cover or define a term that the handbook does contain.
    """
    text = draft.translate(_QUOTES)
    table = _acronyms()
    pairs = [(a, e) for a, e in _ACR_THEN_EXPANSION.findall(text)] + [(a, e) for e, a in _EXPANSION_THEN_ACR.findall(text)]
    for acronym, expansion in pairs:
        known = table.get(acronym)
        if not known:
            continue
        expansion = _LEADING_ARTICLE.sub("", expansion.strip())
        given = normalise(expansion)
        if not any(given == normalise(k) or given in normalise(k) or normalise(k) in given for k in known):
            return f"{acronym} ({expansion})"
    for match in _NEGATIVE_COVERAGE.finditer(text):
        span, rest = match.group(0), match.group(1)
        if _WH_WORD.search(rest):
            continue
        for term in _TERM.findall(rest):
            if term.strip() and _in_corpus(term):
                return " ".join(span.split())[:200]
    return None


def _evidence_block(item: dict) -> str:
    lines = []
    for ev in item.get("evidence", []):
        lines.append(f'Evidence from the handbook (page {ev.get("page", "?")}): "{ev.get("quote", "")}"')
    return "\n".join(lines)


def _reference_block(item: dict) -> str:
    bucket = item["bucket"]
    if bucket == "answerable":
        aliases = "; ".join(item.get("gold_aliases") or []) or "none"
        return f"Reference answer: {item['gold_answer']}\nAcceptable forms: {aliases}\n{_evidence_block(item)}"
    if bucket == "ambiguous":
        readings = "\n".join(
            f"Reading {i}: {r['reading']}. Answer for reading {i}: {r['answer']} (page {r.get('page', '?')})"
            for i, r in enumerate(item.get("readings", []), start=1)
        )
        return f"The question can be read in more than one way, and the handbook answers each differently.\n{readings}\n{_evidence_block(item)}"
    if bucket == "unanswerable":
        return (
            "The handbook does not answer this question. That is already known; do not judge it. "
            "The closest passage is given so that you can tell what the handbook does say.\n"
            f"{_evidence_block(item)}"
        )
    if bucket == "false_premise":
        return (
            "The question rests on an assumption that the handbook contradicts. That is already known; do not judge it.\n"
            f"What the handbook actually says: {item.get('premise_fix', '')}\n{_evidence_block(item)}"
        )
    raise ValueError(f"unknown bucket {bucket!r}")


def build_judge_messages(item: dict, draft: str, order: str) -> list[dict]:
    question = f"Question: {item['question']}"
    reference = _reference_block(item)
    candidate = f"Candidate answer: {draft}"
    questions = questions_for(item)
    asked = "\n".join(["Answer these questions about the candidate answer:"] + [f"Q{i}: {text}" for i, (_, text) in enumerate(questions, start=1)])
    footer = (
        "Reply with one line 'REASON: <one sentence about the candidate>' followed by one line per question, "
        f"Q1 to Q{len(questions)}, each in the form 'Q1: YES' or 'Q1: NO'."
    )
    if order == "reference_first":
        blocks = [question, reference, candidate, asked, footer]
    elif order == "candidate_first":
        blocks = [question, candidate, reference, asked, footer]
    else:
        raise ValueError(f"unknown order {order!r}")
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "\n\n".join(blocks)},
    ]


def _claim(item: dict, draft: str, key: str) -> str:
    """What the copied words must do, for the grounding call, per question key."""
    if key == "same":
        return f'give the answer to the question "{item["question"]}"'
    if key == "contradicts":
        return f'state a different answer or contradict this answer: "{item.get("gold_answer", "")}"'
    if key == "omits":
        return f'are missing from this answer: "{draft}"'
    if key == "flags":
        return "ask which reading of the question is meant"
    if key.startswith("reading"):
        index = int(key[len("reading"):]) - 1
        return f'give "{item["readings"][index]["answer"]}" as the answer, in any wording'
    if key == "answers":
        return "offer an answer, figure, estimate, name, or date to the question"
    if key == "abstains":
        return "say that the handbook does not contain the answer, or that it could not be found"
    if key == "rejects":
        return f'say that the question\'s assumption is wrong, or state this correction: "{item.get("premise_fix", "")}"'
    if key == "doubts":
        return "express doubt about the question's assumption"
    if key == "builds":
        return "answer the question as if its assumption were true"
    if key == "unsupported":
        return "assert something as fact that the reference and the evidence do not support"
    raise ValueError(f"unknown question key {key!r}")


def build_extraction_messages(item: dict, draft: str, key: str) -> list[dict]:
    """The grounding call: copy from the candidate (or, for 'leaves out', from the reference)."""
    source = _reference_text(item) if key == "omits" else draft
    return [
        {"role": "system", "content": EXTRACT_SYSTEM_PROMPT},
        {"role": "user", "content": f"Text:\n{source}\n\n{EXTRACT_MARK} {_claim(item, draft, key)}. If there are none, reply NONE."},
    ]


def code_quote(item: dict, draft: str, key: str) -> Optional[str]:
    """Words the draft itself supplies for an answer-bearing YES, or None when the judge must copy.

    For "same" the candidates are the gold answer and its aliases; for a
    reading, its answer and any parenthesised acronym in it. The first one
    found in the draft settles the YES without a copying call.
    """
    if key == "same":
        candidates = [item.get("gold_answer") or ""] + list(item.get("gold_aliases") or [])
    elif key.startswith("reading"):
        answer = item["readings"][int(key[len("reading"):]) - 1]["answer"]
        candidates = [answer] + _PARENTHESISED.findall(answer)
    else:
        return None
    for text in candidates:
        text = text.strip()
        if text and quote_in(draft, text):
            return text
    return None


def parse_extraction(text: str) -> Optional[str]:
    """The copied words from a grounding reply, or None for NONE or an unusable reply."""
    text = text.translate(_QUOTES).strip()
    match = _QUOTED.search(text)
    if match:
        return match.group(1).strip()
    if not text or text.upper().startswith("NONE"):
        return None
    first = text.splitlines()[0].strip().strip("'")
    return first if 0 < len(first.split()) <= 60 else None


def _reason_of(text: str) -> str:
    match = _REASON.search(text)
    return match.group(1).strip().splitlines()[0].strip() if match else ""


def parse_answers(keys: list[str], text: str) -> Optional[tuple[dict, str, dict]]:
    """Return ({key: bool}, reason, {key: copied words}), or None when a question went unanswered."""
    text = text.translate(_QUOTES)
    found, quotes = {}, {}
    for number, answer, quote in _ANSWER_LINE.findall(text):
        index = int(number) - 1
        if 0 <= index < len(keys) and keys[index] not in found:
            found[keys[index]] = answer.upper() == "YES"
            if quote:
                quotes[keys[index]] = quote.strip()
    if len(found) != len(keys):
        return None
    return found, _reason_of(text), quotes


def ground_answers(item: dict, draft: str, answers: dict, quotes: dict) -> tuple[dict, list[str]]:
    """Turn every YES whose copied words cannot be verified into NO; return the keys that were turned.

    The copied words must occur in the candidate (for "leaves out", in the
    reference and not in the candidate). For the questions that claim the
    candidate gives an answer ("same" and each reading) the copied words must
    also mention that answer: a judge once backed "gives the SRR" with a copy
    of the candidate's "Critical Design Review", which was in the draft but
    was not the answer claimed.
    """
    grounded, ungrounded = dict(answers), []
    for key, value in answers.items():
        if not value:
            continue
        quote = quotes.get(key)
        if key == "omits":
            ok = quote_in(_reference_text(item), quote) and not quote_in(draft, quote)
        else:
            ok = quote_in(draft, quote)
            must_mention = answer_tokens(item, key)
            if ok and must_mention and not (_tokens(quote) & must_mention):
                ok = False
        if not ok:
            grounded[key] = False
            ungrounded.append(key)
    return grounded, ungrounded


def _label(grade: str) -> int:
    return 1 if grade == "CORRECT" else 0


def _decide(record: dict, decided_by: str, grade: str, reason: str) -> dict:
    record.update(decided_by=decided_by, grade=grade, label=_label(grade), reason=reason)
    return record


def _run_judge(record: dict, item: dict, draft: str, judge: Judge) -> dict:
    bucket = item["bucket"]
    keys = [key for key, _ in questions_for(item)]
    outputs, graded = [], []
    for order in ("reference_first", "candidate_first"):
        reply = judge(build_judge_messages(item, draft, order))
        outputs.append(reply)
        parsed = parse_answers(keys, reply)
        if parsed is None:
            record["judge_answers"].append(None)
            record["judge_quotes"].append(None)
            record["judge_ungrounded"].append(None)
            record["judge_grades"].append(None)
            continue
        answers, reason, _ = parsed
        quotes = {}
        for key, value in answers.items():
            if value:
                known = code_quote(item, draft, key)
                quotes[key] = known if known is not None else parse_extraction(judge(build_extraction_messages(item, draft, key)))
        answers, ungrounded = ground_answers(item, draft, answers, quotes)
        contradicted = code_unsupported(item, draft)
        if contradicted:
            answers["unsupported"] = True
            quotes["unsupported"] = contradicted
        grade_ = grade_from_answers(bucket, answers)
        record["judge_answers"].append(answers)
        record["judge_quotes"].append(quotes)
        record["judge_ungrounded"].append(ungrounded)
        record["judge_grades"].append(grade_)
        graded.append((grade_, reason))
    record["judge_outputs"] = outputs

    if len(graded) < 2:
        record["flag"] = "judge_unparsed"
        return _decide(record, "judge", "WRONG", "a judge reply could not be parsed; label 0 until a person reads it")

    worst = max(graded, key=lambda g: _STRICTNESS[g[0]])
    if graded[0][0] != graded[1][0]:
        record["flag"] = "position_disagreement"
        reason = f"judge grades differed by order ({graded[0][0]} vs {graded[1][0]}); stricter kept: {worst[1]}"
        return _decide(record, "judge", worst[0], reason)
    return _decide(record, "judge", worst[0], worst[1])


def grade(item: dict, draft: str, judge: Judge, form_hint: Optional[str] = None) -> dict:
    bucket = item["bucket"]
    if bucket not in BUCKETS:
        raise ValueError(f"unknown bucket {bucket!r}")
    form = classify_form(draft, form_hint)
    record = {
        "item_id": item.get("id"),
        "bucket": bucket,
        "draft": draft,
        "form": form,
        "grader_version": GRADER_VERSION,
        "decided_by": None,
        "grade": None,
        "label": None,
        "judge_model": getattr(judge, "model", None),
        "judge_grades": [],
        "judge_answers": [],
        "judge_quotes": [],
        "judge_ungrounded": [],
        "judge_outputs": [],
        "flag": None,
        "reason": "",
    }

    if bucket == "answerable":
        if form == "ABSTAIN":
            if mentions_gold(draft, item.get("gold_answer"), item.get("gold_aliases") or []):
                return _run_judge(record, item, draft, judge)
            return _decide(record, "rules", "WRONG", "the handbook holds the answer and the draft did not give it")
        if form == "CLARIFY":
            return _decide(record, "rules", "WRONG", "the question is not ambiguous, so a clarifying question is a miss")
        if exact_match(draft, item.get("gold_answer"), item.get("gold_aliases") or []):
            return _decide(record, "exact", "CORRECT", "matches the reference answer or an accepted alias")
        return _run_judge(record, item, draft, judge)

    if bucket == "ambiguous":
        if form == "ABSTAIN":
            return _decide(record, "rules", "WRONG", "the handbook answers both readings; abstaining is a miss")
        return _run_judge(record, item, draft, judge)

    # For the last two buckets the rules accept an abstention only when nothing
    # specific follows the refusal phrase that the question did not already
    # mention. A refusal that goes on to name a new figure, date, or thing may
    # carry an invented answer, so the judge reads it.
    plain_abstain = (
        form == "ABSTAIN"
        and not mentions_specifics(abstain_tail(draft), item.get("question", ""))
        and code_unsupported(item, draft) is None
    )

    if bucket == "unanswerable":
        if plain_abstain:
            return _decide(record, "rules", "CORRECT", "the handbook has no answer and the draft says so")
        if form == "CLARIFY":
            return _decide(record, "rules", "WRONG", "no reading of the question is answerable, so clarifying dodges it")
        return _run_judge(record, item, draft, judge)

    # false_premise
    if plain_abstain:
        return _decide(record, "rules", "CORRECT", "the draft did not build on the false premise")
    return _run_judge(record, item, draft, judge)


def apply_human(record: dict, human_grade: str, note: str) -> dict:
    if human_grade not in GRADES:
        raise ValueError(f"unknown grade {human_grade!r}")
    updated = copy.deepcopy(record)
    updated["machine_grade"] = record["grade"]
    updated["grade"] = human_grade
    updated["label"] = _label(human_grade)
    updated["decided_by"] = "human"
    updated["reason"] = note
    return updated


class ProviderJudge:
    """Adapter that lets a provider act as the judge callable."""

    def __init__(self, provider, seed: int = 42, max_tokens: int = 200):
        self.provider = provider
        self.model = provider.model
        self.seed = seed
        self.max_tokens = max_tokens

    def __call__(self, messages: list[dict]) -> str:
        return self.provider.generate(messages, temperature=0.0, seed=self.seed, max_tokens=self.max_tokens).text
