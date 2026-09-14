"""Tests for the second-judge comparison helpers."""

from calibration import grader
from calibration.judge_compare import (agreement, binary, bootstrap_share, categorise_reply, lenient_parse_answers, lenient_parser,
                                       lenient_text, overlap, paired_difference)

KEYS = ["same", "contradicts", "omits"]


def test_strict_format_parses_and_is_categorised_parsed():
    reply = "REASON: fine.\nQ1: YES\nQ2: NO\nQ3: NO"
    assert categorise_reply(KEYS, reply, truncated=False) == "parsed"


def test_markdown_and_numbering_are_format_failures_the_lenient_reading_recovers():
    reply = "**REASON:** The candidate matches.\n**Q1:** YES\n2. No\nQuestion 3: no, nothing is left out."
    assert grader.parse_answers(KEYS, reply) is None
    parsed = lenient_parse_answers(KEYS, reply)
    assert parsed is not None and parsed[0] == {"same": True, "contradicts": False, "omits": False}
    assert categorise_reply(KEYS, reply, truncated=False) == "format"


def test_answer_on_the_line_after_the_question():
    reply = "Q1: Does the candidate give the same answer?\nYes.\nQ2: Does it contradict?\nNo\nQ3: Does it omit?\nNo"
    assert lenient_parse_answers(KEYS, reply)[0] == {"same": True, "contradicts": False, "omits": False}
    assert "Q1: YES" in lenient_text(reply)


def test_truncated_and_task_failures():
    cut = "REASON: The candidate discusses the review process at great length and"
    assert categorise_reply(KEYS, cut, truncated=True) == "truncated"
    assert categorise_reply(KEYS, "I cannot evaluate this candidate.", truncated=False) == "task"
    assert categorise_reply(KEYS, "Q1: YES\nQ2: NO", truncated=False) == "task"  # one question never answered


def test_lenient_parser_swaps_and_restores():
    original = grader.parse_answers
    with lenient_parser():
        assert grader.parse_answers is not original
        assert grader.parse_answers(KEYS, "1. yes\n2. no\n3. no") is not None
    assert grader.parse_answers is original


def test_agreement_intervals_and_overlap():
    assert binary("CORRECT") == 1 and binary("PARTIAL") == 0 and binary(None) is None
    pairs = [("CORRECT", "CORRECT"), ("PARTIAL", "WRONG"), ("CORRECT", "WRONG"), (None, "WRONG")]
    assert agreement(pairs) == (2, 3)
    assert agreement(pairs, three_way=True) == (1, 3)
    point, lo, hi = bootstrap_share([1, 1, 1, 0])
    assert point == 0.75 and lo <= point <= hi
    diff, dlo, dhi = paired_difference([1, 1, 1, 1], [1, 1, 0, 0])
    assert diff == 0.5 and dlo <= diff <= dhi
    o = overlap({1, 2, 3}, {3, 4})
    assert o["both"] == [3] and o["first_only"] == [1, 2] and o["second_only"] == [4]


def test_classify_copy_catches_an_echo_of_the_instruction_phrase_without_a_colon():
    from calibration.grader import build_extraction_messages
    from calibration.judge_compare import classify_copy, split_extraction_message

    item = {"bucket": "ambiguous", "question": "When is the TMA done?", "readings": [
        {"reading": "initial", "answer": "at program/project outset", "page": "1"},
        {"reading": "final", "answer": "just prior to the PDR", "page": "1"}]}
    draft = "It is performed at program/project outset and just prior to the Preliminary Design Review (PDR)."
    message = build_extraction_messages(item, draft, "reading2")[-1]["content"]
    source, instruction = split_extraction_message(message)
    assert source == draft
    assert classify_copy(' "just prior to the PDR"', source, instruction) == "echoed"
    assert classify_copy('"just prior to the Preliminary Design Review (PDR)"', source, instruction) == "copied"
    assert classify_copy("NONE", source, instruction) == "none"
    assert classify_copy('"at the critical design review"', source, instruction) == "not found"


def test_classify_copy_a_none_that_quotes_the_phrase_is_not_an_echo():
    from calibration.grader import build_extraction_messages, parse_extraction
    from calibration.judge_compare import classify_copy, split_extraction_message

    item = {"bucket": "ambiguous", "question": "Which review comes last?", "readings": [
        {"reading": "first", "answer": "the Operational Readiness Review (ORR)", "page": "1"},
        {"reading": "second", "answer": "the FRR", "page": "1"}]}
    draft = "The last review is the Flight Readiness Review."
    source, instruction = split_extraction_message(build_extraction_messages(item, draft, "reading1")[-1]["content"])
    reply = 'NONE (The given text does not contain the phrase "Operational Readiness Review (ORR)".)'
    assert parse_extraction(reply) == "Operational Readiness Review (ORR)"  # the grader reads the quote as the copy
    assert classify_copy(reply, source, instruction) == "none quoting a phrase"


def test_classify_copy_a_leaves_out_copy_of_the_draft_is_not_an_echo():
    from calibration.grader import build_extraction_messages
    from calibration.judge_compare import classify_copy, copy_target, split_extraction_message

    item = {"bucket": "answerable", "question": "What is the SRR?", "gold_answer": "the System Requirements Review",
            "evidence": [{"quote": "The System Requirements Review examines the requirements.", "page": "1"}]}
    draft = "It is a design review."
    message = build_extraction_messages(item, draft, "omits")[-1]["content"]
    source, instruction = split_extraction_message(message)
    assert copy_target(instruction) is None
    assert classify_copy(f'"{draft}"', source, instruction) == "not found"
    contradict = split_extraction_message(build_extraction_messages(item, draft, "contradicts")[-1]["content"])[1]
    assert copy_target(contradict) is None  # quotes the answer to go against, not a phrase to find
    same = split_extraction_message(build_extraction_messages(item, draft, "same")[-1]["content"])[1]
    assert copy_target(same) is None  # quotes the question, not a phrase to find


def test_classify_copy_an_echo_of_the_correction_phrase():
    from calibration.grader import build_extraction_messages
    from calibration.judge_compare import classify_copy, copy_target, split_extraction_message

    fix = "The handbook says the SEMP is a subordinate document to the project plan."
    item = {"bucket": "false_premise", "question": "Why is the project plan subordinate to the SEMP?", "premise_fix": fix}
    draft = "The project plan is a subordinate document to the SEMP."
    source, instruction = split_extraction_message(build_extraction_messages(item, draft, "rejects")[-1]["content"])
    assert copy_target(instruction) == fix
    assert classify_copy(f'"{fix}"', source, instruction) == "echoed"


def test_order_rule_effect_counts_cost_and_saved():
    from calibration.judge_compare import order_rule_effect

    records = [{"flag": "position_disagreement", "judge_grades": ["PARTIAL", "CORRECT"]},
               {"flag": "position_disagreement", "judge_grades": ["WRONG", "CORRECT"]},
               {"flag": "position_disagreement", "judge_grades": ["PARTIAL", "WRONG"]},
               {"flag": None, "judge_grades": ["CORRECT", "CORRECT"]}]
    assert order_rule_effect(records, ["CORRECT", "WRONG", "CORRECT", "WRONG"]) == {"cost": 1, "saved": 1, "no effect": 1}
