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
to a grade. Where the question is about a specific piece of text (the answer
for each reading, the premise correction) that text is quoted in the
question; for the answerable bucket the gold answer is not quoted, because
quoting it made the judge match strings instead of meaning. Earlier versions
asked the judge for a grade directly. With llama3.1 8B that was unstable: it
graded the question instead of the candidate on the unanswerable and
false-premise buckets, and adding three words to the prompt flipped a correct
clarifying question from CORRECT to PARTIAL in both orders. An abstract
question ("does it reject the assumption?") was also answered against the
judge's own written reason; the same question quoting the correction was not.
"""

from __future__ import annotations

import copy
import re
from typing import Callable, Optional

GRADER_VERSION = "grader-v3"
GRADES = ("CORRECT", "PARTIAL", "WRONG")
FORMS = ("ANSWER", "ABSTAIN", "CLARIFY")
BUCKETS = ("answerable", "ambiguous", "unanswerable", "false_premise")
EXACT_MAX_WORDS = 30
_STRICTNESS = {"CORRECT": 0, "PARTIAL": 1, "WRONG": 2}

Judge = Callable[[list[dict]], str]

# "a" is stripped only at the start: in this handbook the letter A is a label
# (Phase A, KDP A, Appendix A) and stripping it would turn "Phase A" into "phase".
_ARTICLES = re.compile(r"\b(the|an)\b|^a\b")
_PUNCT = re.compile(r"[^\w\s]")
_THOUSANDS = re.compile(r"(?<=\d),(?=\d{3}\b)")
_QUOTES = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"'})
_SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+")

_ABSTAIN = re.compile(
    r"""
    \b(does\s+not|doesn't|do\s+not|don't|did\s+not|didn't)\s+
        (say|state|specify|mention|contain|provide|address|cover|give)\b
  | \bnot\s+(found|stated|specified|mentioned|covered|contained|provided|available|addressed|given)\b
  | \b(cannot|can't|could\s+not|couldn't|unable\s+to|not\s+able\s+to)\s+(find|locate|determine)\b
  | \bno\s+(information|mention|reference|details?)\b
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

_ANSWER_LINE = re.compile(r"\bQ(\d)\s*[:.)-]\s*(YES|NO)\b", re.IGNORECASE)
_REASON = re.compile(r"reason\s*:\s*(.+)", re.IGNORECASE | re.DOTALL)

SYSTEM_PROMPT = (
    "You read a candidate answer to a question about the NASA Systems Engineering Handbook "
    "and answer yes-or-no questions about what the candidate says. Use only the material you "
    "are given. Do not use outside knowledge. Judge meaning, not wording. "
    "Reply in exactly the format requested."
)


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


def questions_for(item: dict) -> list[tuple[str, str]]:
    """The yes-or-no questions the judge answers for this item, as (key, text)."""
    bucket = item["bucket"]
    if bucket == "answerable":
        # The gold answer is deliberately not quoted here: quoting it made the
        # judge match strings, and paraphrases came back as "not the same".
        return [
            ("same", "Does the candidate give the same answer as the reference answer or one of the acceptable forms, "
                     "allowing for any difference in wording?"),
            ("contradicts", "Does the candidate state a different answer, or something that contradicts the reference answer?"),
            ("omits", "Does the candidate leave out a part of the reference answer that carries meaning, "
                      "such as an item in a list, a number, or a condition?"),
        ]
    if bucket == "ambiguous":
        readings = item.get("readings") or []
        if len(readings) < 2:
            raise ValueError("an ambiguous item needs at least two readings")
        names = " or ".join(f'"{r["reading"]}"' for r in readings)
        questions = [("flags", f"Does the candidate ask which reading is meant, for example whether the user means {names}?")]
        for i, r in enumerate(readings, start=1):
            questions.append((f"reading{i}", f'Does the candidate give "{r["answer"]}" as the answer for reading {i}?'))
        return questions
    if bucket == "unanswerable":
        return [
            ("answers", "Does the candidate give a specific answer, figure, name, or date to the question?"),
            ("abstains", "Does the candidate say that the handbook does not contain the answer, or that it could not find one?"),
        ]
    if bucket == "false_premise":
        fix = item.get("premise_fix", "")
        return [
            ("rejects", f'Does the candidate say that the assumption in the question is wrong, or state the correction: "{fix}"?'),
            ("doubts", "Does the candidate express doubt about the assumption without correcting it?"),
            ("builds", "Does the candidate answer the question as if the assumption were true?"),
        ]
    raise ValueError(f"unknown bucket {bucket!r}")


def grade_from_answers(bucket: str, answers: dict) -> str:
    a = answers
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
        return "The handbook does not answer this question. That is already known; do not judge it."
    if bucket == "false_premise":
        return (
            "The question rests on an assumption that the handbook contradicts. That is already known; do not judge it.\n"
            f"What the handbook actually says: {item.get('premise_fix', '')}"
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


def _reason_of(text: str) -> str:
    match = _REASON.search(text)
    return match.group(1).strip().splitlines()[0].strip() if match else ""


def parse_answers(keys: list[str], text: str) -> Optional[tuple[dict, str]]:
    """Return ({key: bool}, reason), or None when any question went unanswered."""
    found = {}
    for number, answer in _ANSWER_LINE.findall(text):
        index = int(number) - 1
        if 0 <= index < len(keys) and keys[index] not in found:
            found[keys[index]] = answer.upper() == "YES"
    if len(found) != len(keys):
        return None
    return found, _reason_of(text)


def _label(grade: str) -> int:
    return 1 if grade == "CORRECT" else 0


def _decide(record: dict, decided_by: str, grade: str, reason: str) -> dict:
    record.update(decided_by=decided_by, grade=grade, label=_label(grade), reason=reason)
    return record


def _run_judge(record: dict, item: dict, draft: str, judge: Judge) -> dict:
    bucket = item["bucket"]
    keys = [key for key, _ in questions_for(item)]
    outputs, parsed = [], []
    for order in ("reference_first", "candidate_first"):
        reply = judge(build_judge_messages(item, draft, order))
        outputs.append(reply)
        parsed.append(parse_answers(keys, reply))
    record["judge_outputs"] = outputs
    record["judge_answers"] = [p[0] if p else None for p in parsed]
    record["judge_grades"] = [grade_from_answers(bucket, p[0]) if p else None for p in parsed]
    graded = [(g, p[1]) for g, p in zip(record["judge_grades"], parsed) if p]

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

    # For the last two buckets the rules accept an abstention only when it is
    # the whole draft (one sentence). A longer draft may abstain and then
    # speculate or build on the premise anyway, so the judge reads it.
    plain_abstain = form == "ABSTAIN" and len(sentences(draft)) == 1

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
