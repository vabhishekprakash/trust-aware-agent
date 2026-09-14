"""Tests for the agent loop with a scripted provider and a fake index: no model, no embeddings."""

import pytest

from agent.loop import ABSTAIN_TEXT, TRACE_VERSION, Agent, clarify_question, distinct_answers, parse_readings
from agent.retriever import Hit


class FakeGeneration:
    def __init__(self, text):
        self.text = text
        self.cached = False


class ScriptedProvider:
    model = "scripted"

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def generate(self, messages, **kwargs):
        self.calls.append(messages)
        return FakeGeneration(self.replies.pop(0))


class FakeIndex:
    def __init__(self, hits):
        self.hits = hits

    def search(self, query, k=5):
        return self.hits[:k]


CHUNKS = [
    {"id": "c00010", "text": "The SEMP is approved by the Program Manager.", "page_start": "20", "page_end": "20", "word_count": 8},
    {"id": "c00011", "text": "Type C projects cost up to $500M and Type D up to $100M.", "page_start": "38", "page_end": "38", "word_count": 12},
]
HITS = [Hit(CHUNKS[0], 0.81), Hit(CHUNKS[1], 0.64)]


def make_agent(replies, threshold=None, hits=HITS):
    return Agent(ScriptedProvider(replies), FakeIndex(hits), k=2, abstain_threshold=threshold)


def test_parse_readings_and_distinct_answers():
    text = "READING: the project SEMP | ANSWER: the SRR\nREADING: the program SEMP | ANSWER: the MDR/SDR"
    readings = parse_readings(text)
    assert [r["answer"] for r in readings] == ["the SRR", "the MDR/SDR"]
    assert distinct_answers(readings) == 2
    assert parse_readings("ONE READING") == []
    same = parse_readings("READING: a | ANSWER: the SRR\nREADING: b | ANSWER: The SRR.")
    assert distinct_answers(same) == 1


def test_parse_readings_run_together_on_one_line():
    text = "READING: 1 | ANSWER: the leader of the team | READING: 2 | ANSWER: the purchaser | READING: 3 | ANSWER: the purchaser"
    readings = parse_readings(text)
    assert [r["reading"] for r in readings] == ["1", "2", "3"]
    assert [r["answer"] for r in readings] == ["the leader of the team", "the purchaser", "the purchaser"]
    assert distinct_answers(readings) == 2


def test_an_answer_of_one_reading_is_not_a_reading():
    text = "READING: more than one system | ANSWER: MORE THAN ONE | READING: Reading 1: building more than one | ANSWER: ONE READING"
    readings = parse_readings(text)
    assert [r["answer"] for r in readings] == ["MORE THAN ONE"]
    assert distinct_answers(readings) == 1


def test_clarify_question_falls_back_to_answers_for_bare_labels():
    readings = [{"reading": "[1]", "answer": "the CDR"}, {"reading": "2", "answer": "the CDR"}, {"reading": "3", "answer": "the PRR"}]
    assert clarify_question(readings) == "Do you mean the CDR, or the PRR?"
    readings = [{"reading": "an end item", "answer": "the CDR"}, {"reading": "a production run", "answer": "the PRR"}]
    assert clarify_question(readings) == "Do you mean an end item, or a production run?"


def test_run_together_readings_fire_the_rule():
    replies = ["READING: 1 | ANSWER: the team leader | READING: 2 | ANSWER: the purchaser", "The purchaser."]
    trace = make_agent(replies).run("Who is the customer?")
    assert (trace["action"], trace["clarify_by"]) == ("CLARIFY", "rule")
    assert trace["response"] == "Do you mean the team leader, or the purchaser?"


def test_plain_answer_leaves_a_full_trace():
    agent = make_agent(["ONE READING", "The Program Manager approves the SEMP."])
    trace = agent.run("Who approves the SEMP?", item_id="q1")
    assert trace["trace_version"] == TRACE_VERSION
    assert trace["action"] == "ANSWER"
    assert trace["response"] == "The Program Manager approves the SEMP."
    assert [r["id"] for r in trace["retrieval"]] == ["c00010", "c00011"]
    assert trace["retrieval"][0]["score"] == 0.81
    assert trace["readings"] == {"raw": "ONE READING", "parsed": [], "fired": False}
    assert trace["draft"]["calc"] == []
    assert trace["clarify_by"] is None and trace["abstain_by"] is None
    assert [c["step"] for c in trace["calls"]] == ["readings", "draft"]
    assert trace["k"] == 2 and trace["item_id"] == "q1" and trace["best_score"] == 0.81


def test_passages_and_question_reach_both_prompts():
    provider = ScriptedProvider(["ONE READING", "The Program Manager."])
    Agent(provider, FakeIndex(HITS), k=2).run("Who approves the SEMP?")
    for messages in provider.calls:
        content = messages[-1]["content"]
        assert "The SEMP is approved by the Program Manager." in content
        assert "Who approves the SEMP?" in content
        assert "[1] (page 20)" in content


def test_readings_step_makes_the_rule_clarify_and_composes_the_question():
    replies = ["READING: the project SEMP | ANSWER: the SRR\nREADING: the program SEMP | ANSWER: the MDR/SDR", "The SRR."]
    trace = make_agent(replies).run("At which review is the SEMP baselined?")
    assert trace["action"] == "CLARIFY"
    assert trace["clarify_by"] == "rule"
    assert trace["response"] == "Do you mean the project SEMP, or the program SEMP?"
    assert trace["draft"]["final"] == "The SRR."
    assert trace["readings"]["fired"] is True


def test_readings_with_the_same_answer_do_not_fire():
    replies = ["READING: a | ANSWER: the SRR\nREADING: b | ANSWER: the SRR", "The SRR."]
    trace = make_agent(replies).run("At which review is the SEMP baselined?")
    assert trace["action"] == "ANSWER" and trace["clarify_by"] is None


def test_prompt_clarify_keeps_the_models_own_question():
    trace = make_agent(["ONE READING", "Do you mean the project SEMP or the program SEMP?"]).run("Which SEMP?")
    assert trace["action"] == "CLARIFY"
    assert trace["clarify_by"] == "prompt"
    assert trace["response"] == "Do you mean the project SEMP or the program SEMP?"


def test_both_clarify_paths_are_recorded_and_the_models_question_is_kept():
    replies = ["READING: a | ANSWER: x\nREADING: b | ANSWER: y", "Do you mean a or b?"]
    trace = make_agent(replies).run("q")
    assert (trace["action"], trace["clarify_by"], trace["response"]) == ("CLARIFY", "both", "Do you mean a or b?")


def test_abstain_by_prompt_and_by_rule():
    trace = make_agent(["ONE READING", "The handbook does not say."]).run("How much does a CDR cost?")
    assert (trace["action"], trace["abstain_by"], trace["response"]) == ("ABSTAIN", "prompt", "The handbook does not say.")
    trace = make_agent(["ONE READING", "About two million dollars."], threshold=0.9).run("How much does a CDR cost?")
    assert (trace["action"], trace["abstain_by"], trace["response"]) == ("ABSTAIN", "rule", ABSTAIN_TEXT)
    assert trace["draft"]["final"] == "About two million dollars."
    trace = make_agent(["ONE READING", "The handbook does not say."], threshold=0.9).run("How much does a CDR cost?")
    assert trace["abstain_by"] == "both"
    trace = make_agent(["ONE READING", "The Program Manager."], threshold=0.5).run("Who approves the SEMP?")
    assert trace["action"] == "ANSWER" and trace["abstain_by"] is None


def test_clarify_wins_over_abstain_when_both_apply():
    replies = ["READING: a | ANSWER: x\nREADING: b | ANSWER: y", "The handbook does not say."]
    trace = make_agent(replies, threshold=0.9).run("q")
    assert trace["action"] == "CLARIFY"
    assert trace["abstain_by"] == "both"


def test_calculator_round_trip_is_traced():
    replies = ["ONE READING", "CALC: $500M - $100M", "The gap is $400M."]
    provider = ScriptedProvider(replies)
    trace = Agent(provider, FakeIndex(HITS), k=2).run("By how much do the Type C and Type D bounds differ?")
    assert trace["draft"]["calc"] == [{"expression": "$500M - $100M", "result": "400,000,000"}]
    assert trace["draft"]["final"] == "The gap is $400M."
    assert trace["action"] == "ANSWER"
    assert [c["step"] for c in trace["calls"]] == ["readings", "draft", "draft_after_calc"]
    assert "Result: $500M - $100M = 400,000,000" in provider.calls[-1][-1]["content"]


def test_uncomputable_calculator_line_is_reported_back():
    replies = ["ONE READING", "CALC: five minus three", "The handbook does not say."]
    trace = make_agent(replies).run("q")
    assert trace["draft"]["calc"] == [{"expression": "five minus three", "result": None}]
    assert trace["action"] == "ABSTAIN"
