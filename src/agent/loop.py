"""The plan-act loop: retrieve, check for readings, draft, calculate when asked, decide, trace.

The agent's own actions are ANSWER, CLARIFY and ABSTAIN. CLARIFY and ABSTAIN
each have two paths, a prompt instruction the model may follow on its own
and a rule that code applies, and the trace records which path fired. The
readings step is the CLARIFY rule: the model lists the readings the passages
answer differently and code decides. ABSTAIN comes from the prompt alone: a
threshold on the best retrieval score was dropped after the first dev run,
where the score did not separate right answers from wrong ones (decisions.md).
The score stays in the trace as a signal. See docs/explanations/03-agent-loop.md.
"""

from __future__ import annotations

import re
import time
from typing import Optional

from agent.provider import Provider
from agent.retriever import Hit, Index
from agent.tools import calc_lines, calculate, format_number
from calibration.grader import classify_form, content_words, normalise, shared_words

TRACE_VERSION = "trace-v2"  # v2 adds the premise step and the REJECT action
DEFAULT_K = 8
ABSTAIN_TEXT = "The handbook does not say."

ANSWER_SYSTEM = (
    "You answer questions about the NASA Systems Engineering Handbook using only the passages you are given. "
    "If the passages do not contain the answer, reply exactly: The handbook does not say. "
    "If the question could mean two different things that the passages answer differently, ask which is meant "
    "instead of answering. If the question takes something for granted that the passages contradict, say so and "
    "give the correction. Answer in one or two sentences. If the answer needs arithmetic on numbers in the "
    "passages, reply with one line of the form CALC: <number> <+ or - or * or /> <number> and nothing else, "
    "for example CALC: 500 - 100; you will be given the result. Only do this when the question asks for a "
    "figure that has to be computed from two numbers in the passages."
)
READINGS_SYSTEM = (
    "You read a question and passages from the NASA Systems Engineering Handbook. Your only job is to say whether "
    "the question has more than one reading that the passages answer differently. Reply in exactly the format asked."
)
READINGS_FOOTER = (
    "If the passages answer this question one way, reply exactly: ONE READING. If the question can be read in two "
    "or more ways and the passages give a different answer for each, reply with one line per reading in the form "
    "READING: <what the question would mean, in a few words> | ANSWER: <the answer from the passages>. "
    "Describe each reading in words, not with a number. Do not list a reading the passages do not answer."
)
_READING = re.compile(
    r"READING\s*:\s*(.+?)\s*\|\s*ANSWER\s*:\s*(.+?)(?=\s*\|?\s*READING\s*:|\s*$)",
    re.IGNORECASE | re.DOTALL,
)
_BARE_LABEL = re.compile(r"^\W*\d*\W*$")

PREMISE_SYSTEM = (
    "You read a question and passages from the NASA Systems Engineering Handbook. Your only job is to say whether "
    "the question takes something for granted that the passages contradict. Reply in exactly the format asked."
)
PREMISE_FOOTER = (
    "If the question assumes nothing that the passages contradict, reply exactly: NO CONTRADICTION. Otherwise reply "
    "on one line: ASSUMPTION: <what the question takes for granted, in the question's own words> | PASSAGE: <the "
    "number of the passage that contradicts it> | CORRECTION: <what that passage says instead, in its words>."
)
_PREMISE = re.compile(
    r"ASSUMPTION\s*:\s*(.+?)\s*\|\s*PASSAGE\s*:\s*\[?\s*(\d+)\s*\]?\s*\|\s*CORRECTION\s*:\s*(.+)",
    re.IGNORECASE | re.DOTALL,
)
GATE_WORDS = 2
GATE_COVERAGE = 0.6


def parse_premise(text: str) -> Optional[dict]:
    """The assumption, passage number and correction the model named, or None for NO CONTRADICTION."""
    match = _PREMISE.search(text)
    if not match:
        return None
    return {"assumption": match.group(1).strip(), "passage": int(match.group(2)), "correction": match.group(3).strip().rstrip(".")}


def premise_grounded(parsed: dict, question: str, hits: list[Hit]) -> bool:
    """The gate, three checks in code.

    The assumption must be taken from the question: at least two content
    words, and most of its words, occur there. A model that restates the
    answer as the "assumption" fails this. The correction must be grounded
    in the cited passage by at least two words that are not in the question,
    and it must be about the assumption, sharing at least one word with it.
    """
    if not 1 <= parsed["passage"] <= len(hits):
        return False
    passage = hits[parsed["passage"] - 1].chunk["text"]
    assumption_words = len(content_words(parsed["assumption"]))
    from_question = shared_words(parsed["assumption"], question)
    if assumption_words == 0 or from_question < GATE_WORDS or from_question / assumption_words < GATE_COVERAGE:
        return False
    return (shared_words(parsed["correction"], passage, excluding=question) >= GATE_WORDS
            and shared_words(parsed["correction"], parsed["assumption"]) >= 1)


def passages_block(hits: list[Hit]) -> str:
    return "\n\n".join(
        f"[{i}] (page {h.chunk['page_start']}" + (f" to {h.chunk['page_end']}" if h.chunk["page_end"] != h.chunk["page_start"] else "") + f") {h.chunk['text']}"
        for i, h in enumerate(hits, start=1)
    )


def parse_readings(text: str) -> list[dict]:
    """Readings the model listed with their answers, one per line or run together with pipes.

    Empty for ONE READING or an unreadable reply.
    """
    readings = [{"reading": m.group(1).strip(), "answer": m.group(2).strip()} for m in _READING.finditer(text)]
    # A model that writes "READING: ... | ANSWER: ONE READING" has said there is one reading, not given one.
    return [r for r in readings if not r["answer"].upper().startswith("ONE READING")]


def distinct_answers(readings: list[dict]) -> int:
    return len({normalise(r["answer"]) for r in readings if normalise(r["answer"])})


def clarify_question(readings: list[dict]) -> str:
    """Ask which of two readings with different answers is meant.

    The model sometimes labels readings with bare numbers; then the answers
    themselves are the only words that tell the readings apart.
    """
    picked, seen = [], set()
    for r in readings:
        key = normalise(r["answer"])
        if key and key not in seen:
            seen.add(key)
            picked.append(r)
        if len(picked) == 2:
            break
    labels = [r["reading"] for r in picked]
    if any(_BARE_LABEL.match(label) for label in labels):
        labels = [r["answer"] for r in picked]
    return f"Do you mean {labels[0]}, or {labels[1]}?"


class Agent:
    def __init__(self, provider: Provider, index: Index, k: int = DEFAULT_K, seed: int = 42, max_tokens: int = 160):
        self.provider = provider
        self.index = index
        self.k = k
        self.seed = seed
        self.max_tokens = max_tokens

    def _ask(self, messages: list[dict], trace_calls: list, step: str) -> str:
        started = time.time()
        generation = self.provider.generate(messages, temperature=0.0, seed=self.seed, max_tokens=self.max_tokens)
        trace_calls.append({"step": step, "cached": generation.cached, "seconds": round(time.time() - started, 2)})
        return generation.text.strip()

    def run(self, question: str, item_id: Optional[str] = None) -> dict:
        started = time.time()
        calls: list = []
        trace = {
            "trace_version": TRACE_VERSION,
            "item_id": item_id,
            "question": question,
            "model": self.provider.model,
            "seed": self.seed,
            "k": self.k,
            "calls": calls,
        }

        # 1. retrieve
        retrieval_started = time.time()
        hits = self.index.search(question, k=self.k)
        trace["retrieval_seconds"] = round(time.time() - retrieval_started, 2)
        trace["retrieval"] = [{"id": h.chunk["id"], "page_start": h.chunk["page_start"], "page_end": h.chunk["page_end"], "score": round(h.score, 4)} for h in hits]
        passages = passages_block(hits)
        best = hits[0].score if hits else 0.0

        # 2. premise step: the REJECT rule, gated in code
        premise_raw = self._ask(
            [{"role": "system", "content": PREMISE_SYSTEM},
             {"role": "user", "content": f"Passages:\n{passages}\n\nQuestion: {question}\n\n{PREMISE_FOOTER}"}],
            calls, "premise")
        premise = parse_premise(premise_raw)
        grounded = premise is not None and premise_grounded(premise, question, hits)
        trace["premise"] = {"raw": premise_raw, "parsed": premise, "grounded": grounded, "fired": grounded}

        # 3. readings step: the CLARIFY rule
        readings_raw = self._ask(
            [{"role": "system", "content": READINGS_SYSTEM},
             {"role": "user", "content": f"Passages:\n{passages}\n\nQuestion: {question}\n\n{READINGS_FOOTER}"}],
            calls, "readings")
        readings = parse_readings(readings_raw)
        readings_fired = distinct_answers(readings) >= 2
        trace["readings"] = {"raw": readings_raw, "parsed": readings, "fired": readings_fired}

        # 3. draft, with one calculator round if asked
        messages = [{"role": "system", "content": ANSWER_SYSTEM},
                    {"role": "user", "content": f"Passages:\n{passages}\n\nQuestion: {question}"}]
        draft = self._ask(messages, calls, "draft")
        calc_records = []
        for expression in calc_lines(draft):
            result = calculate(expression)
            calc_records.append({"expression": expression, "result": None if result is None else format_number(result)})
        if calc_records:
            results = "; ".join(f"{c['expression']} = {c['result'] if c['result'] is not None else 'could not compute'}" for c in calc_records)
            messages = messages + [{"role": "assistant", "content": draft},
                                   {"role": "user", "content": f"Result: {results}. Now give the final answer in one or two sentences, without another CALC line."}]
            final_draft = self._ask(messages, calls, "draft_after_calc")
        else:
            final_draft = draft
        trace["draft"] = {"raw": draft, "calc": calc_records, "final": final_draft}

        # 4. decide
        form = classify_form(final_draft)
        abstain_prompt = form == "ABSTAIN"
        abstain_rule = False  # the score threshold was dropped; see the module docstring
        clarify_prompt = form == "CLARIFY"
        clarify_rule = readings_fired
        action, response = "ANSWER", final_draft
        if grounded:
            page = hits[premise["passage"] - 1].chunk["page_start"]
            action = "REJECT"
            response = f"The question assumes {premise['assumption']}. The handbook says {premise['correction']} (page {page})."
        elif clarify_prompt or clarify_rule:
            action = "CLARIFY"
            if clarify_rule and not clarify_prompt:
                response = clarify_question(readings)
        elif abstain_prompt or abstain_rule:
            action = "ABSTAIN"
            if abstain_rule and not abstain_prompt:
                response = ABSTAIN_TEXT
        trace.update({
            "form": form,
            "best_score": round(best, 4),
            "reject_by": "rule" if grounded else None,
            "clarify_by": _path(clarify_prompt, clarify_rule),
            "abstain_by": _path(abstain_prompt, abstain_rule),
            "action": action,
            "response": response,
            "seconds": round(time.time() - started, 2),
        })
        return trace


def _path(prompt: bool, rule: bool) -> Optional[str]:
    if prompt and rule:
        return "both"
    if prompt:
        return "prompt"
    if rule:
        return "rule"
    return None
