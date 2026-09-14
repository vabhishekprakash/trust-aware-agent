"""Tests for the staged grader that turns a draft answer into a correctness label."""

import pytest

from calibration.grader import (
    GRADER_VERSION,
    ProviderJudge,
    apply_human,
    build_judge_messages,
    classify_form,
    exact_match,
    grade,
    grade_from_answers,
    normalise,
    parse_answers,
    questions_for,
)

ANSWERABLE = {
    "id": "q1",
    "bucket": "answerable",
    "question": "Who approves the SEMP?",
    "gold_answer": "the Program Manager",
    "gold_aliases": ["program manager", "PM"],
    "expected": "answer",
    "evidence": [{"page": "20", "quote": "The SEMP is approved by the Program Manager."}],
}
UNANSWERABLE = {
    "id": "q2",
    "bucket": "unanswerable",
    "question": "How much does a design review cost?",
    "gold_answer": None,
    "gold_aliases": [],
    "expected": "abstain",
    "evidence": [{"page": "30", "quote": "Reviews are held at key decision points."}],
}
FALSE_PREMISE = {
    "id": "q3",
    "bucket": "false_premise",
    "question": "Since the handbook requires two key decision points per phase, which comes first?",
    "gold_answer": None,
    "gold_aliases": [],
    "premise_fix": "The handbook defines key decision points at phase boundaries, not two per phase.",
    "expected": "abstain",
    "evidence": [{"page": "25", "quote": "KDPs occur at the boundaries between phases."}],
}
AMBIGUOUS = {
    "id": "q4",
    "bucket": "ambiguous",
    "question": "Which review comes before implementation?",
    "gold_answer": None,
    "gold_aliases": [],
    "readings": [
        {"reading": "before Phase C", "answer": "the Critical Design Review", "page": "22"},
        {"reading": "before Phase B", "answer": "the System Requirements Review", "page": "21"},
    ],
    "expected": "clarify",
    "evidence": [{"page": "22", "quote": "CDR precedes Phase C."}, {"page": "21", "quote": "SRR precedes Phase B."}],
}

LONG_HEDGE = "Someone senior, possibly the manager of the program, signs it off after the review board meets."


class StubJudge:
    model = "stub-judge"

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def __call__(self, messages):
        self.calls.append(messages)
        return self.replies.pop(0)


def never_called(messages):
    raise AssertionError("judge must not be called")


def reply(*answers):
    lines = ["REASON: stub."] + [f"Q{i}: {'YES' if a else 'NO'}" for i, a in enumerate(answers, start=1)]
    return "\n".join(lines)


def both(*answers):
    return StubJudge([reply(*answers), reply(*answers)])


# stage 1 and 2: normalise and classify the form


def test_normalise_strips_case_punctuation_articles_and_number_commas():
    assert normalise("The Program Manager.") == "program manager"
    assert normalise("1,000 items") == "1000 items"
    assert normalise("  An   answer,  ") == "answer"
    assert normalise("A Program Manager") == "program manager"


def test_normalise_keeps_the_letter_a_used_as_a_label():
    assert normalise("Phase A") == "phase a"
    assert normalise("Appendix A and KDP A") == "appendix a and kdp a"
    assert not exact_match("It happens in Phase B.", "Phase A", [])
    assert exact_match("It happens in Phase A.", "Phase A", [])


def test_curly_apostrophes_do_not_defeat_the_abstain_patterns():
    assert classify_form("The handbook doesn’t say when the SRR is held.") == "ABSTAIN"


def test_an_answer_followed_by_a_short_question_is_not_a_clarification():
    assert classify_form("Phase A. Anything else?") == "ANSWER"
    assert classify_form("Do you mean Phase A?") == "CLARIFY"


def test_classify_form_detects_abstain():
    assert classify_form("The handbook does not specify the cost of a review.") == "ABSTAIN"
    assert classify_form("I could not find this in the handbook.") == "ABSTAIN"


def test_classify_form_detects_clarify():
    assert classify_form("Do you mean the review in Phase A or the one in Phase B?") == "CLARIFY"
    assert classify_form("Which phase?") == "CLARIFY"


def test_classify_form_defaults_to_answer():
    assert classify_form("The Program Manager approves the SEMP.") == "ANSWER"
    assert classify_form("It is long enough that a trailing question mark alone does not make it a clarification " * 2 + "?") == "ANSWER"


def test_clarifying_question_wins_over_an_abstain_phrase_inside_it():
    assert classify_form("The handbook does not say which one you mean: do you mean the SRR or the SDR?") == "CLARIFY"


def test_abstain_wins_over_a_bare_short_question():
    assert classify_form("The handbook does not say. Shall I look elsewhere?") == "ABSTAIN"


def test_classify_form_hint_overrides_patterns():
    assert classify_form("Which phase?", hint="ANSWER") == "ANSWER"
    with pytest.raises(ValueError):
        classify_form("x", hint="MAYBE")


# stage 3: the exact check


def test_exact_match_accepts_equality_and_short_containment():
    assert exact_match("the program manager", "the Program Manager", [])
    assert exact_match("It is approved by the PM.", "the Program Manager", ["PM"])


def test_exact_match_refuses_negations_choices_and_long_drafts():
    assert not exact_match("It is 12, not 17.", "17", ["seventeen"])
    assert not exact_match("It isn’t 17.", "17", ["seventeen"])
    assert not exact_match("Either 17 or 12 processes.", "17", ["seventeen"])
    assert not exact_match("PM " + "filler " * 29, "the Program Manager", ["PM"])
    assert exact_match("About 10 times.", "10", ["ten"])
    assert exact_match("About 10 times: Type A starts above $1 billion and Type D tops out at $100 million.", "10", ["ten"])


def test_exact_match_ignores_empty_gold_and_empty_aliases():
    assert not exact_match("anything", None, ["x"])
    assert not exact_match("anything", "", [""])
    assert exact_match("the PM", "the Program Manager", ["", "PM"])


# the judge's questions and the mapping from answers to grades


def test_questions_are_anchored_on_the_reference_text():
    keys = [k for k, _ in questions_for(ANSWERABLE)]
    assert keys == ["same", "contradicts", "omits"]
    assert all("reference answer" in text for _, text in questions_for(ANSWERABLE))
    assert not any("the Program Manager" in text for _, text in questions_for(ANSWERABLE))
    amb = questions_for(AMBIGUOUS)
    assert [k for k, _ in amb] == ["flags", "reading1", "reading2"]
    assert "before Phase C" in amb[0][1] and "before Phase B" in amb[0][1]
    assert "the Critical Design Review" in amb[1][1]
    assert "the System Requirements Review" in amb[2][1]
    fp = questions_for(FALSE_PREMISE)
    assert [k for k, _ in fp] == ["rejects", "doubts", "builds"]
    assert FALSE_PREMISE["premise_fix"] in fp[0][1]
    assert [k for k, _ in questions_for(UNANSWERABLE)] == ["answers", "abstains"]


def test_ambiguous_item_needs_two_readings():
    with pytest.raises(ValueError):
        questions_for({**AMBIGUOUS, "readings": AMBIGUOUS["readings"][:1]})


@pytest.mark.parametrize(
    "answers, expected",
    [
        ({"same": True, "contradicts": False, "omits": False}, "CORRECT"),
        ({"same": True, "contradicts": False, "omits": True}, "PARTIAL"),
        ({"same": True, "contradicts": True, "omits": False}, "PARTIAL"),
        ({"same": False, "contradicts": True, "omits": False}, "WRONG"),
        ({"same": False, "contradicts": False, "omits": True}, "PARTIAL"),
        ({"same": False, "contradicts": False, "omits": False}, "WRONG"),
    ],
)
def test_answerable_mapping(answers, expected):
    assert grade_from_answers("answerable", answers) == expected


@pytest.mark.parametrize(
    "answers, expected",
    [
        ({"flags": True, "reading1": False, "reading2": False}, "CORRECT"),
        ({"flags": False, "reading1": True, "reading2": True}, "CORRECT"),
        ({"flags": False, "reading1": True, "reading2": False}, "PARTIAL"),
        ({"flags": False, "reading1": False, "reading2": False}, "WRONG"),
    ],
)
def test_ambiguous_mapping(answers, expected):
    assert grade_from_answers("ambiguous", answers) == expected


@pytest.mark.parametrize(
    "answers, expected",
    [
        ({"answers": False, "abstains": True}, "CORRECT"),
        ({"answers": True, "abstains": True}, "PARTIAL"),
        ({"answers": True, "abstains": False}, "WRONG"),
        ({"answers": False, "abstains": False}, "WRONG"),
    ],
)
def test_unanswerable_mapping(answers, expected):
    assert grade_from_answers("unanswerable", answers) == expected


@pytest.mark.parametrize(
    "answers, expected",
    [
        ({"rejects": True, "doubts": False, "builds": False}, "CORRECT"),
        ({"rejects": True, "doubts": False, "builds": True}, "PARTIAL"),
        ({"rejects": False, "doubts": True, "builds": False}, "CORRECT"),
        ({"rejects": False, "doubts": True, "builds": True}, "PARTIAL"),
        ({"rejects": False, "doubts": False, "builds": True}, "WRONG"),
        ({"rejects": False, "doubts": False, "builds": False}, "WRONG"),
    ],
)
def test_false_premise_mapping(answers, expected):
    assert grade_from_answers("false_premise", answers) == expected


def test_parse_answers_accepts_format_variants_and_rejects_missing_lines():
    keys = ["a", "b"]
    assert parse_answers(keys, "REASON: fine\nQ1: yes\nQ2) NO") == ({"a": True, "b": False}, "fine")
    assert parse_answers(keys, "Sure. Q1 - YES, Q2: YES. Reason: ok") == ({"a": True, "b": True}, "ok")
    assert parse_answers(keys, "Q1: YES") is None
    assert parse_answers(keys, "GRADE: CORRECT\nREASON: x") is None


# rule-decided cases: the judge is never called


def test_exact_alias_match_is_correct_without_judge():
    r = grade(ANSWERABLE, "It is approved by the PM.", judge=never_called)
    assert (r["grade"], r["label"], r["decided_by"]) == ("CORRECT", 1, "exact")


def test_answerable_abstain_is_wrong_without_judge():
    r = grade(ANSWERABLE, "The handbook does not say who approves the SEMP.", judge=never_called)
    assert (r["grade"], r["label"], r["decided_by"]) == ("WRONG", 0, "rules")


def test_answerable_abstain_that_still_names_the_answer_goes_to_judge():
    judge = both(True, False, False)
    r = grade(ANSWERABLE, "The handbook does not specify a date, but the SEMP is approved by the Program Manager.", judge=judge)
    assert r["form"] == "ABSTAIN"
    assert r["decided_by"] == "judge"
    assert r["grade"] == "CORRECT"


def test_answerable_clarify_is_wrong_without_judge():
    r = grade(ANSWERABLE, "Do you mean the SEMP for a program or a project?", judge=never_called)
    assert (r["grade"], r["decided_by"]) == ("WRONG", "rules")


def test_unanswerable_abstain_is_correct_and_clarify_is_wrong_without_judge():
    r = grade(UNANSWERABLE, "The handbook does not give the cost of a review.", judge=never_called)
    assert (r["grade"], r["label"], r["decided_by"]) == ("CORRECT", 1, "rules")
    r = grade(UNANSWERABLE, "Do you mean a CDR or a PDR?", judge=never_called)
    assert (r["grade"], r["decided_by"]) == ("WRONG", "rules")


def test_false_premise_abstain_is_correct_without_judge():
    r = grade(FALSE_PREMISE, "I could not find any requirement for two decision points per phase.", judge=never_called)
    assert (r["grade"], r["label"]) == ("CORRECT", 1)


def test_multi_sentence_abstentions_go_to_the_judge():
    draft = "The handbook does not say which comes first. Of the two per phase, the entry KDP comes first."
    r = grade(FALSE_PREMISE, draft, judge=both(False, False, True))
    assert r["form"] == "ABSTAIN"
    assert (r["decided_by"], r["grade"]) == ("judge", "WRONG")
    draft = "The handbook does not give a figure. It would be about two million dollars."
    r = grade(UNANSWERABLE, draft, judge=both(True, True))
    assert (r["decided_by"], r["grade"], r["label"]) == ("judge", "PARTIAL", 0)
    draft = "The handbook does not give a cost for a CDR; it describes only the review's purpose, timing, and criteria."
    r = grade(UNANSWERABLE, draft, judge=never_called)
    assert (r["decided_by"], r["grade"]) == ("rules", "CORRECT")


def test_ambiguous_abstain_is_wrong_without_judge():
    r = grade(AMBIGUOUS, "The handbook does not cover this.", judge=never_called)
    assert (r["grade"], r["decided_by"]) == ("WRONG", "rules")


def test_unknown_bucket_is_rejected():
    with pytest.raises(ValueError):
        grade({**ANSWERABLE, "bucket": "other"}, "x", judge=never_called)


# judge-decided cases


def test_long_draft_containing_gold_goes_to_judge_in_both_orders():
    draft = "The Program Manager approves it, although " + "some people say " * 12 + "the Center Director does."
    judge = both(True, True, False)
    r = grade(ANSWERABLE, draft, judge=judge)
    assert r["decided_by"] == "judge"
    assert r["grade"] == "PARTIAL"
    assert len(judge.calls) == 2
    first, second = judge.calls[0][-1]["content"], judge.calls[1][-1]["content"]
    assert first.index("Reference answer") < first.index("Candidate answer")
    assert second.index("Candidate answer") < second.index("Reference answer")


def test_judge_sees_evidence_quote_and_the_questions():
    judge = both(True, False, False)
    grade(ANSWERABLE, LONG_HEDGE, judge=judge)
    prompt = judge.calls[0][-1]["content"]
    assert "approved by the Program Manager" in prompt
    assert "Q1:" in prompt and "Q3:" in prompt and "Q4:" not in prompt


def test_unanswerable_answer_goes_to_judge_and_a_figure_is_wrong():
    r = grade(UNANSWERABLE, "A design review costs about two million dollars.", judge=both(True, False))
    assert (r["decided_by"], r["grade"], r["label"]) == ("judge", "WRONG", 0)


def test_unanswerable_prompt_says_the_answer_is_already_known():
    prompt = build_judge_messages(UNANSWERABLE, "some draft", "reference_first")[-1]["content"]
    assert "already known" in prompt
    assert "GRADE" not in prompt


def test_false_premise_reject_correct_and_build_wrong():
    draft = "Actually the handbook places key decision points at phase boundaries, so there is no two per phase."
    assert grade(FALSE_PREMISE, draft, judge=both(True, False, False))["grade"] == "CORRECT"
    assert grade(FALSE_PREMISE, "The first of the two is the entry KDP.", judge=both(False, False, True))["grade"] == "WRONG"


def test_ambiguous_clarify_that_names_both_readings_is_correct():
    judge = both(True, False, False)
    r = grade(AMBIGUOUS, "Do you mean the review before Phase B or before Phase C?", judge=judge)
    assert r["grade"] == "CORRECT"
    prompt = judge.calls[0][-1]["content"]
    assert "before Phase C" in prompt and "before Phase B" in prompt


def test_disagreeing_orders_take_stricter_grade_and_flag():
    judge = StubJudge([reply(True, False, False), reply(True, False, True)])
    r = grade(ANSWERABLE, LONG_HEDGE, judge=judge)
    assert r["judge_grades"] == ["CORRECT", "PARTIAL"]
    assert (r["grade"], r["label"], r["flag"]) == ("PARTIAL", 0, "position_disagreement")


def test_agreeing_orders_produce_no_flag_and_keep_answers():
    r = grade(ANSWERABLE, LONG_HEDGE, judge=both(True, False, False))
    assert (r["grade"], r["label"], r["flag"]) == ("CORRECT", 1, None)
    assert r["judge_grades"] == ["CORRECT", "CORRECT"]
    assert r["judge_answers"] == [{"same": True, "contradicts": False, "omits": False}] * 2
    assert r["judge_model"] == "stub-judge"


def test_partial_maps_to_label_zero_and_keeps_grade():
    r = grade(ANSWERABLE, LONG_HEDGE, judge=both(False, False, True))
    assert (r["grade"], r["label"]) == ("PARTIAL", 0)


def test_one_unreadable_reply_is_flagged_wrong_and_keeps_the_readable_grade():
    judge = StubJudge(["I think it is fine.", reply(True, False, False)])
    r = grade(ANSWERABLE, LONG_HEDGE, judge=judge)
    assert (r["grade"], r["label"], r["flag"]) == ("WRONG", 0, "judge_unparsed")
    assert r["judge_grades"] == [None, "CORRECT"]
    assert r["judge_outputs"][0] == "I think it is fine."


def test_two_unreadable_replies_are_flagged_wrong():
    r = grade(UNANSWERABLE, "About two million dollars.", judge=StubJudge(["no", "GRADE: CORRECT"]))
    assert (r["grade"], r["label"], r["flag"]) == ("WRONG", 0, "judge_unparsed")


# human override, the provider adapter, and the record shape


def test_human_override_wins_and_keeps_machine_grade():
    r = grade(UNANSWERABLE, "It costs about two million dollars.", judge=both(True, False))
    r2 = apply_human(r, "CORRECT", "owner: the figure is in a table the item writer missed")
    assert (r2["grade"], r2["label"], r2["decided_by"], r2["machine_grade"]) == ("CORRECT", 1, "human", "WRONG")
    assert r["decided_by"] == "judge", "apply_human must not mutate the original record"


def test_apply_human_rejects_unknown_grade():
    r = grade(ANSWERABLE, "the program manager", judge=never_called)
    with pytest.raises(ValueError):
        apply_human(r, "MAYBE", "typo")


def test_provider_judge_calls_the_provider_deterministically():
    class FakeGeneration:
        text = reply(True, False, False)

    class FakeProvider:
        model = "fake-model"

        def __init__(self):
            self.calls = []

        def generate(self, messages, **kwargs):
            self.calls.append((messages, kwargs))
            return FakeGeneration()

    provider = FakeProvider()
    judge = ProviderJudge(provider, seed=7)
    assert judge.model == "fake-model"
    assert judge([{"role": "user", "content": "x"}]) == FakeGeneration.text
    _, kwargs = provider.calls[0]
    assert kwargs["temperature"] == 0.0 and kwargs["seed"] == 7 and kwargs["max_tokens"] == 200


def test_record_carries_identity_version_form_and_reason():
    r = grade(ANSWERABLE, "the program manager", judge=never_called)
    assert (r["item_id"], r["bucket"], r["form"]) == ("q1", "answerable", "ANSWER")
    assert r["grader_version"] == GRADER_VERSION
    assert r["reason"]
    assert set(r) >= {"judge_grades", "judge_answers", "judge_outputs", "flag", "judge_model", "decided_by", "label"}
