"""Tests for the staged grader that turns a draft answer into a correctness label."""

import pytest

from calibration.grader import (
    EXTRACT_MARK,
    GRADER_VERSION,
    ProviderJudge,
    abstain_tail,
    apply_human,
    build_extraction_messages,
    build_judge_messages,
    classify_form,
    exact_match,
    grade,
    grade_from_answers,
    ground_answers,
    mentions_specifics,
    normalise,
    parse_answers,
    parse_extraction,
    questions_for,
    quote_in,
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


def source_of(content: str) -> str:
    """The text a grounding call asks the judge to copy from."""
    return content.split("Text:\n", 1)[1].split(f"\n\n{EXTRACT_MARK}", 1)[0]


class StubJudge:
    """Scripted judge. Yes-or-no calls pop from `replies`; grounding calls copy the whole source unless `extract` says otherwise."""

    model = "stub-judge"

    def __init__(self, replies, extract=None):
        self.replies = list(replies)
        self.calls = []
        self.extract = extract

    def __call__(self, messages):
        self.calls.append(messages)
        content = messages[-1]["content"]
        if EXTRACT_MARK in content:
            if self.extract is not None:
                return self.extract(content)
            return f'"{source_of(content)}"'
        return self.replies.pop(0)

    def question_calls(self):
        return [c for c in self.calls if EXTRACT_MARK not in c[-1]["content"]]

    def grounding_calls(self):
        return [c for c in self.calls if EXTRACT_MARK in c[-1]["content"]]


def never_called(messages):
    raise AssertionError("judge must not be called")


def no_extraction(content):
    raise AssertionError("code should have grounded this YES without a copying call")


def reply(*answers):
    lines = ["REASON: stub."] + [f"Q{i}: {'YES' if a else 'NO'}" for i, a in enumerate(answers, start=1)]
    return "\n".join(lines)


def both(*answers, extract=None):
    return StubJudge([reply(*answers), reply(*answers)], extract=extract)


# Answer tuples per bucket: answerable (same, contradicts, omits, unsupported);
# ambiguous (flags, reading1, reading2, unsupported); unanswerable (answers,
# abstains, unsupported); false_premise (rejects, doubts, builds, unsupported).


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
    assert classify_form("The handbook defines the term but gives no statistics on how many projects exceed it.") == "ABSTAIN"


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


def test_mentions_specifics_finds_figures_dates_and_proper_nouns_mid_sentence():
    assert mentions_specifics(" for a CDR; it describes only the review's purpose.")
    assert mentions_specifics(" a figure. It would be about two million dollars.")
    assert mentions_specifics(" a figure, but roughly 2 million dollars.")
    assert mentions_specifics(" the date. It was issued in December.")
    assert not mentions_specifics(" the cost of a review.")
    assert not mentions_specifics(" the cost. It focuses on process. I checked.")
    assert mentions_specifics(" the cost. It focuses on NASA process.")


def test_mentions_specifics_ignores_terms_echoed_from_the_question():
    question = "What is the dollar cost cap on projects selected through an Announcement of Opportunity in an uncoupled program?"
    assert not mentions_specifics(" information about the dollar cost cap on projects selected through an Announcement of Opportunity.", question)
    assert mentions_specifics(" information about the cap, though the Science Mission Directorate sets one.", question)
    question = "At what life-cycle cost, above $250 million, is the commitment made with Congress?"
    assert not mentions_specifics(" the $250 million commitment with Congress.", question)
    assert mentions_specifics(" the $250 million commitment, which was $500 million before 2010.", question)
    question = "What minimum mass margin should a project hold at PDR?"
    assert mentions_specifics(" any details related to PDR (Pre-Development Review) for hardware projects.", question)


@pytest.fixture(autouse=True)
def small_corpus(monkeypatch):
    """A tiny acronym table and corpus so the code checks do not read the real handbook."""
    import calibration.grader as g

    monkeypatch.setattr(g, "ACRONYMS", {"PDR": ["Preliminary Design Review"], "CE": ["Concurrent Engineering", "Chief Engineer"], "KDP": ["Key Decision Point"]})
    monkeypatch.setattr(g, "CORPUS", " " + g.normalise(
        "The Agency Baseline Commitment is set at KDP C. Reviews are held at key decision points. The Program Manager approves the SEMP. "
        "NASA holds a Preliminary Design Review (PDR), a Critical Design Review (CDR) and a System Requirements Review (SRR) in each life cycle. "
        "Flight units and the Jet Propulsion Laboratory are not mentioned here."
    ) + " ")


def test_code_unsupported_catches_a_wrong_acronym_expansion():
    from calibration.grader import code_unsupported

    assert code_unsupported(UNANSWERABLE, "No details related to PDR (Pre-Development Review) are given.") == "PDR (Pre-Development Review)"
    assert code_unsupported(UNANSWERABLE, "No details related to PDR (Preliminary Design Review) are given.") is None
    assert code_unsupported(UNANSWERABLE, "The Chief Engineer (CE) signs it.") is None
    assert code_unsupported(UNANSWERABLE, "The Cost Estimator (CE) signs it.") == "CE (Cost Estimator)"
    # an acronym the handbook never uses is an outside claim, whatever its expansion
    assert code_unsupported(UNANSWERABLE, "The XYZ (Extra Yield Zone) is not in the table.") == "XYZ"


def test_code_unsupported_catches_a_false_claim_that_the_handbook_does_not_mention_a_term():
    from calibration.grader import code_unsupported

    draft = "The passage does not provide information about confidence levels, nor does it mention anything related to Agency Baseline Commitments or KDP C."
    hit = code_unsupported(UNANSWERABLE, draft)
    assert hit is not None and "Agency Baseline Commitments" in hit
    assert code_unsupported(UNANSWERABLE, "The handbook does not mention the Quantum Flux Capacitor.") is None
    assert code_unsupported(UNANSWERABLE, "The passage does not provide information about the Agency Baseline Commitment.") is None
    # an abstention about a detail is not an existence claim
    assert code_unsupported(UNANSWERABLE, "The handbook does not specify where lessons are captured after the Critical Design Review.") is None
    assert code_unsupported(UNANSWERABLE, "The handbook does not mention when the Program Manager signs.") is None


def test_wrong_expansion_makes_an_abstention_partial_even_if_the_judge_misses_it():
    item = {**UNANSWERABLE, "question": "What minimum mass margin should a project hold at PDR?"}
    draft = "The passage does not provide information about the mass margin or any details related to PDR (Pre-Development Review)."
    r = grade(item, draft, judge=both(False, True))
    assert (r["decided_by"], r["grade"], r["label"]) == ("judge", "PARTIAL", 0)
    assert r["judge_quotes"][0]["unsupported"] == "PDR (Pre-Development Review)"


def test_a_false_coverage_claim_blocks_the_rule_path_and_is_partial():
    item = {**UNANSWERABLE, "question": "What confidence level must the Agency Baseline Commitment be funded to at KDP C?"}
    draft = "The passage does not provide information about confidence levels, nor does it mention anything related to Agency Baseline Commitments or KDP C."
    r = grade(item, draft, judge=both(False, True))
    assert (r["decided_by"], r["grade"]) == ("judge", "PARTIAL")


def test_same_answer_must_add_something_beyond_the_question():
    item = {
        **ANSWERABLE,
        "question": "Which NASA requirements document says data management planning has to appear in the project plan?",
        "gold_answer": "NPR 7120.5",
        "gold_aliases": ["NPR7120.5", "7120.5", "NASA Procedural Requirements 7120.5"],
    }
    draft = "The NASA Systems Engineering Handbook (SEH) requires that data management planning appear in the project plan, " + "as the guidelines say. " * 8
    r = grade(item, draft, judge=both(True, False, False, extract=lambda c: '"The NASA Systems Engineering Handbook (SEH)"'))
    assert (r["grade"], r["judge_ungrounded"]) == ("WRONG", [["same"], ["same"]])


def test_mentions_specifics_matches_echoed_terms_word_by_word():
    question = "Who wrote the original 1995 edition of NASA SP-6105?"
    assert not mentions_specifics(" who wrote the original 1995 edition of NASA SP-6105.", question)
    assert mentions_specifics(" who wrote the original 1995 edition of NASA SP-6105; it was Griffin.", question)


def test_abstains_and_flags_are_grounded_by_the_code_patterns():
    draft = "The handbook does not specify a figure, but a CDR would typically run into the millions of dollars."
    r = grade(UNANSWERABLE, draft, judge=both(True, True, extract=lambda c: "NONE"))
    assert r["judge_quotes"][0]["abstains"] == "does not specify"
    assert r["judge_ungrounded"] == [["answers"], ["answers"]]
    assert r["grade"] == "CORRECT"
    judge = both(True, False, False, extract=no_extraction)
    r = grade(AMBIGUOUS, "Do you mean the review before Phase B or some other review?", judge=judge)
    assert r["decided_by"] == "judge" and r["grade"] == "CORRECT"
    assert r["judge_quotes"][0]["flags"].lower() == "do you mean"


def test_abstain_tail_is_the_text_after_the_refusal_phrase():
    assert abstain_tail("The handbook does not give a cost for a CDR.") == " a cost for a CDR."
    assert abstain_tail("No refusal here.") == "No refusal here."


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


# the judge's questions, the grounding check, and the mapping from answers to grades


def test_questions_are_anchored_on_the_reference_text_and_the_judge_is_not_asked_about_support():
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
    prompt = build_judge_messages(UNANSWERABLE, "x", "reference_first")[-1]["content"]
    assert "do not support" not in prompt


def test_ambiguous_item_needs_two_readings():
    with pytest.raises(ValueError):
        questions_for({**AMBIGUOUS, "readings": AMBIGUOUS["readings"][:1]})


@pytest.mark.parametrize(
    "answers, expected",
    [
        ({"same": True, "contradicts": False, "omits": False, "unsupported": False}, "CORRECT"),
        ({"same": True, "contradicts": False, "omits": False, "unsupported": True}, "PARTIAL"),
        ({"same": True, "contradicts": False, "omits": True, "unsupported": False}, "PARTIAL"),
        ({"same": True, "contradicts": True, "omits": False, "unsupported": False}, "PARTIAL"),
        ({"same": False, "contradicts": True, "omits": False, "unsupported": False}, "WRONG"),
        ({"same": False, "contradicts": False, "omits": True, "unsupported": False}, "PARTIAL"),
        ({"same": False, "contradicts": False, "omits": False, "unsupported": False}, "WRONG"),
        ({"same": False, "contradicts": False, "omits": False, "unsupported": True}, "WRONG"),
    ],
)
def test_answerable_mapping(answers, expected):
    assert grade_from_answers("answerable", answers) == expected


@pytest.mark.parametrize(
    "answers, expected",
    [
        ({"flags": True, "reading1": False, "reading2": False, "unsupported": False}, "CORRECT"),
        ({"flags": False, "reading1": True, "reading2": True, "unsupported": False}, "CORRECT"),
        ({"flags": False, "reading1": True, "reading2": True, "unsupported": True}, "PARTIAL"),
        ({"flags": False, "reading1": True, "reading2": False, "unsupported": False}, "PARTIAL"),
        ({"flags": False, "reading1": False, "reading2": False, "unsupported": False}, "WRONG"),
    ],
)
def test_ambiguous_mapping(answers, expected):
    assert grade_from_answers("ambiguous", answers) == expected


@pytest.mark.parametrize(
    "answers, expected",
    [
        ({"answers": False, "abstains": True, "unsupported": False}, "CORRECT"),
        ({"answers": False, "abstains": True, "unsupported": True}, "PARTIAL"),
        ({"answers": True, "abstains": True, "unsupported": False}, "PARTIAL"),
        ({"answers": True, "abstains": False, "unsupported": False}, "WRONG"),
        ({"answers": False, "abstains": False, "unsupported": False}, "WRONG"),
    ],
)
def test_unanswerable_mapping(answers, expected):
    assert grade_from_answers("unanswerable", answers) == expected


@pytest.mark.parametrize(
    "answers, expected",
    [
        ({"rejects": True, "doubts": False, "builds": False, "unsupported": False}, "CORRECT"),
        ({"rejects": True, "doubts": False, "builds": False, "unsupported": True}, "PARTIAL"),
        ({"rejects": True, "doubts": False, "builds": True, "unsupported": False}, "PARTIAL"),
        ({"rejects": False, "doubts": True, "builds": False, "unsupported": False}, "CORRECT"),
        ({"rejects": False, "doubts": True, "builds": True, "unsupported": False}, "PARTIAL"),
        ({"rejects": False, "doubts": False, "builds": True, "unsupported": False}, "WRONG"),
        ({"rejects": False, "doubts": False, "builds": False, "unsupported": False}, "WRONG"),
    ],
)
def test_false_premise_mapping(answers, expected):
    assert grade_from_answers("false_premise", answers) == expected


def test_false_premise_bare_abstention_is_partial_whether_by_rule_or_by_judge():
    neither = {"rejects": False, "doubts": False, "builds": False}
    assert grade_from_answers("false_premise", neither, form="ABSTAIN") == "PARTIAL"
    assert grade_from_answers("false_premise", neither, form="ANSWER") == "WRONG"
    # by rule, nothing specific after the refusal
    r = grade(FALSE_PREMISE, "I could not find any requirement for two decision points per phase.", judge=never_called)
    assert (r["decided_by"], r["grade"], r["label"]) == ("rules", "PARTIAL", 0)
    # by judge, a refusal that names something new after it and neither rejects nor builds
    draft = "The handbook does not say; the Decadal Survey might, but it is not in this passage."
    r = grade(FALSE_PREMISE, draft, judge=both(False, False, False))
    assert (r["decided_by"], r["grade"], r["label"]) == ("judge", "PARTIAL", 0)


def test_parse_answers_reads_answers_reason_and_any_copied_words():
    keys = ["a", "b"]
    assert parse_answers(keys, 'REASON: fine\nQ1: yes "some words"\nQ2) NO') == ({"a": True, "b": False}, "fine", {"a": "some words"})
    assert parse_answers(keys, "Sure. Q1 - YES, Q2: YES. Reason: ok") == ({"a": True, "b": True}, "ok", {})
    assert parse_answers(keys, "Q1: YES") is None
    assert parse_answers(keys, "GRADE: CORRECT\nREASON: x") is None


def test_parse_extraction_reads_quoted_words_none_and_bare_replies():
    assert parse_extraction('"the Program Manager"') == "the Program Manager"
    assert parse_extraction("The words are “the Program Manager”.") == "the Program Manager"
    assert parse_extraction("NONE") is None
    assert parse_extraction("None. The text has no such words.") is None
    assert parse_extraction("the manager of the program") == "the manager of the program"
    assert parse_extraction("") is None


def test_quote_in_matches_short_quotes_whole_and_long_quotes_by_coverage():
    text = "Someone senior, possibly the manager of the program, signs it off after the review board meets."
    assert quote_in(text, "the manager of the program")
    assert quote_in(text, "Manager of the Program!")
    assert not quote_in(text, "the Center Director")
    assert not quote_in(text, "")
    assert not quote_in(text, None)
    assert quote_in(text, "possibly the manager of the program signs it off after the board")
    assert not quote_in(text, "one two three four five six seven")
    assert not quote_in(text, "the review board meets every other week to argue about a great many unrelated things")


def test_ground_answers_turns_unverifiable_yes_into_no():
    answers = {"same": True, "contradicts": True, "omits": False, "unsupported": False}
    grounded, turned = ground_answers(ANSWERABLE, LONG_HEDGE, answers, {"same": "manager of the program"})
    assert grounded == {"same": True, "contradicts": False, "omits": False, "unsupported": False}
    assert turned == ["contradicts"]
    grounded, turned = ground_answers(ANSWERABLE, LONG_HEDGE, answers, {"same": "the Center Director", "contradicts": "review board"})
    assert grounded == {"same": False, "contradicts": True, "omits": False, "unsupported": False}
    assert turned == ["same"]


def test_omits_quote_must_come_from_the_reference_and_be_missing_from_the_candidate():
    answers = {"same": False, "contradicts": False, "omits": True, "unsupported": False}
    ok, turned = ground_answers(ANSWERABLE, LONG_HEDGE, answers, {"omits": "Program Manager"})
    assert ok["omits"] is True and turned == []
    present, turned = ground_answers(ANSWERABLE, "The Program Manager, I think.", answers, {"omits": "Program Manager"})
    assert present["omits"] is False and turned == ["omits"]
    foreign, turned = ground_answers(ANSWERABLE, LONG_HEDGE, answers, {"omits": "Center Director"})
    assert foreign["omits"] is False and turned == ["omits"]


def test_extraction_prompt_copies_from_the_candidate_except_for_omits():
    content = build_extraction_messages(ANSWERABLE, LONG_HEDGE, "same")[-1]["content"]
    assert source_of(content) == LONG_HEDGE
    assert "give the answer to the question" in content
    content = build_extraction_messages(ANSWERABLE, LONG_HEDGE, "omits")[-1]["content"]
    assert "Program Manager" in source_of(content)
    assert LONG_HEDGE in content
    content = build_extraction_messages(AMBIGUOUS, "x", "reading2")[-1]["content"]
    assert "the System Requirements Review" in content
    content = build_extraction_messages(UNANSWERABLE, "x", "unsupported")[-1]["content"]
    assert "do not support" in content
    with pytest.raises(ValueError):
        build_extraction_messages(ANSWERABLE, "x", "nonsense")


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


def test_unanswerable_plain_abstain_is_correct_and_clarify_is_wrong_without_judge():
    r = grade(UNANSWERABLE, "The handbook does not give the cost of a review.", judge=never_called)
    assert (r["grade"], r["label"], r["decided_by"]) == ("CORRECT", 1, "rules")
    r = grade(UNANSWERABLE, "The handbook does not say. It focuses on process.", judge=never_called)
    assert (r["grade"], r["decided_by"]) == ("CORRECT", "rules")
    r = grade(UNANSWERABLE, "The handbook defines the Agency Baseline Commitment but gives no statistics on how many projects exceed it.", judge=never_called)
    assert (r["grade"], r["decided_by"]) == ("CORRECT", "rules")
    r = grade(UNANSWERABLE, "Do you mean a CDR or a PDR?", judge=never_called)
    assert (r["grade"], r["decided_by"]) == ("WRONG", "rules")


def test_abstention_echoing_the_questions_own_names_is_correct_by_rule():
    item = {**UNANSWERABLE, "question": "What is the dollar cost cap on projects selected through an Announcement of Opportunity in an uncoupled program?"}
    draft = "The passage does not provide information about the dollar cost cap on projects selected through an Announcement of Opportunity in an uncoupled program."
    r = grade(item, draft, judge=never_called)
    assert (r["grade"], r["decided_by"]) == ("CORRECT", "rules")


def test_false_premise_plain_abstain_is_partial_without_judge():
    r = grade(FALSE_PREMISE, "I could not find any requirement for two decision points per phase.", judge=never_called)
    assert (r["grade"], r["label"], r["decided_by"]) == ("PARTIAL", 0, "rules")


def test_abstentions_that_go_on_to_name_specifics_go_to_the_judge():
    draft = "The handbook does not say which comes first. Of the two per phase, the entry KDP comes first."
    r = grade(FALSE_PREMISE, draft, judge=both(False, False, True))
    assert r["form"] == "ABSTAIN"
    assert (r["decided_by"], r["grade"]) == ("judge", "WRONG")
    draft = "The handbook does not state a figure, but a CDR would typically run into the millions of dollars."
    r = grade(UNANSWERABLE, draft, judge=both(True, True))
    assert (r["decided_by"], r["grade"], r["label"]) == ("judge", "PARTIAL", 0)
    draft = "The handbook does not give a cost for a CDR; it describes only the review's purpose."
    r = grade(UNANSWERABLE, draft, judge=both(False, True))
    assert (r["decided_by"], r["grade"]) == ("judge", "CORRECT")


def test_abstention_with_an_invented_expansion_is_partial():
    item = {**UNANSWERABLE, "question": "What minimum mass margin should a project hold at PDR?"}
    draft = "The passage does not provide information about the mass margin or any details related to PDR (Pre-Development Review)."
    r = grade(item, draft, judge=both(False, True))
    assert (r["decided_by"], r["grade"], r["label"]) == ("judge", "PARTIAL", 0)


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
    first, second = [c[-1]["content"] for c in judge.question_calls()]
    assert first.index("Reference answer") < first.index("Candidate answer")
    assert second.index("Candidate answer") < second.index("Reference answer")


def test_judge_sees_evidence_quote_and_the_questions():
    judge = both(True, False, False)
    grade(ANSWERABLE, LONG_HEDGE, judge=judge)
    prompt = judge.question_calls()[0][-1]["content"]
    assert "approved by the Program Manager" in prompt
    assert "Q1:" in prompt and "Q3:" in prompt and "Q4:" not in prompt
    assert EXTRACT_MARK not in prompt


def test_unanswerable_and_false_premise_prompts_carry_the_evidence():
    prompt = build_judge_messages(UNANSWERABLE, "some draft", "reference_first")[-1]["content"]
    assert "already known" in prompt and "Reviews are held at key decision points" in prompt
    prompt = build_judge_messages(FALSE_PREMISE, "some draft", "reference_first")[-1]["content"]
    assert "KDPs occur at the boundaries" in prompt
    assert "GRADE" not in prompt


def test_every_yes_is_grounded_by_a_copying_call():
    judge = both(True, False, False)
    r = grade(ANSWERABLE, LONG_HEDGE, judge=judge)
    assert r["grade"] == "CORRECT"
    assert len(judge.question_calls()) == 2
    assert len(judge.grounding_calls()) == 2
    assert LONG_HEDGE in judge.grounding_calls()[0][-1]["content"]
    assert r["judge_quotes"] == [{"same": LONG_HEDGE}] * 2
    assert r["judge_ungrounded"] == [[], []]


def test_reading_yes_is_grounded_by_code_when_the_draft_names_the_answer():
    judge = both(False, True, False, extract=no_extraction)
    r = grade(AMBIGUOUS, "It is the Critical Design Review, held before Phase C.", judge=judge)
    assert r["grade"] == "PARTIAL"
    assert r["judge_quotes"][0]["reading1"] == "the Critical Design Review"
    assert judge.grounding_calls() == []


def test_reading_yes_is_grounded_by_code_from_a_parenthesised_acronym():
    item = {**AMBIGUOUS, "readings": [
        {"reading": "before Phase C", "answer": "the Critical Design Review (CDR)", "page": "22"},
        {"reading": "before Phase B", "answer": "the System Requirements Review (SRR)", "page": "21"},
    ]}
    judge = both(False, True, True, extract=no_extraction)
    r = grade(item, "Both the CDR and the SRR come before implementation, depending on the phase.", judge=judge)
    assert r["grade"] == "CORRECT"
    assert r["judge_quotes"][0] == {"reading1": "CDR", "reading2": "SRR"}


def test_same_yes_is_grounded_by_code_when_the_draft_contains_an_alias():
    draft = "The PM signs it off, although " + "some people say " * 12 + "others do too."
    judge = both(True, False, False, extract=no_extraction)
    r = grade(ANSWERABLE, draft, judge=judge)
    assert r["grade"] == "CORRECT"
    assert r["judge_quotes"][0] == {"same": "PM"}


def test_a_yes_the_copying_call_cannot_back_becomes_no():
    r = grade(ANSWERABLE, LONG_HEDGE, judge=both(True, False, False, extract=lambda c: "NONE"))
    assert (r["grade"], r["label"]) == ("WRONG", 0)
    assert r["judge_answers"] == [{"same": False, "contradicts": False, "omits": False, "unsupported": False}] * 2
    assert r["judge_ungrounded"] == [["same"], ["same"]]
    assert r["judge_quotes"] == [{"same": None}] * 2


def test_copied_words_not_in_the_candidate_count_as_no():
    judge = both(False, True, True, extract=lambda c: '"the System Requirements Review"')
    r = grade(AMBIGUOUS, "The big design review, the one before you start building.", judge=judge)
    assert r["grade"] == "WRONG"
    assert r["judge_answers"][0] == {"flags": False, "reading1": False, "reading2": False, "unsupported": False}
    assert r["judge_ungrounded"] == [["reading1", "reading2"], ["reading1", "reading2"]]


def test_answer_bearing_yes_must_mention_the_answer_it_claims():
    r = grade(AMBIGUOUS, "The Critical Design Review (CDR).", judge=both(False, False, True))
    assert (r["grade"], r["judge_ungrounded"]) == ("WRONG", [["reading2"], ["reading2"]])
    r = grade(AMBIGUOUS, "The Critical Design Review (CDR).", judge=both(False, True, False))
    assert (r["grade"], r["judge_ungrounded"]) == ("PARTIAL", [[], []])
    r = grade(ANSWERABLE, LONG_HEDGE, judge=both(True, False, False, extract=lambda c: '"signs it off after the review board meets"'))
    assert (r["grade"], r["judge_ungrounded"]) == ("WRONG", [["same"], ["same"]])


def test_a_right_answer_padded_with_an_outside_name_is_partial():
    from calibration.grader import code_unsupported

    item = {**ANSWERABLE, "question": "What is AS9100?", "gold_answer": "a quality management system for the commercial aerospace industry", "gold_aliases": []}
    padded = "AS9100, developed by the Aerospace Industries Association (AIA), is a quality management system for the commercial aerospace industry."
    assert code_unsupported(item, padded) == "Aerospace Industries Association"
    # the exact stage would have accepted this; the outside name sends it to the judge, and the code check makes it PARTIAL
    r = grade(item, padded, judge=both(True, False, False))
    assert (r["decided_by"], r["grade"], r["label"]) == ("judge", "PARTIAL", 0)
    assert r["judge_quotes"][0]["unsupported"] == "Aerospace Industries Association"
    plain = "AS9100 is a quality management system for the commercial aerospace industry."
    assert code_unsupported(item, plain) is None
    assert grade(item, plain, judge=never_called)["decided_by"] == "exact"


def test_outside_terms_ignore_sentence_initial_capitals_known_names_and_negated_clauses():
    from calibration.grader import _outside_terms

    assert _outside_terms("Both the Program Manager and the SEMP matter.", "") == []
    assert _outside_terms("Ask the Program Manager. The SEMP is the plan.", "") == []
    assert _outside_terms("The Widget Review Board approves it.", "") == ["Widget Review Board"]
    assert _outside_terms("The Widget Review Board approves it.", "Who chairs the Widget Review Board?") == []
    assert _outside_terms("Only NASA and the JPL team see it.", "") == ["JPL"]
    assert _outside_terms("The handbook does not mention the Quantum Flux Capacitor.", "") == []


def test_unanswerable_answer_goes_to_judge_and_a_figure_is_wrong():
    r = grade(UNANSWERABLE, "A design review costs about two million dollars.", judge=both(True, False))
    assert (r["decided_by"], r["grade"], r["label"]) == ("judge", "WRONG", 0)


def test_false_premise_reject_correct_and_build_wrong():
    draft = "Actually the handbook places key decision points at phase boundaries, so there is no two per phase."
    assert grade(FALSE_PREMISE, draft, judge=both(True, False, False))["grade"] == "CORRECT"
    assert grade(FALSE_PREMISE, "The first of the two is the entry KDP.", judge=both(False, False, True))["grade"] == "WRONG"


def test_ambiguous_clarify_that_names_both_readings_is_correct():
    # v13: decided in code, the judge is not called
    r = grade(AMBIGUOUS, "Do you mean the review before Phase B or before Phase C?", judge=never_called)
    assert (r["decided_by"], r["grade"]) == ("rules", "CORRECT")
    # naming one reading still goes to the judge, whose questions carry both readings
    judge = both(True, False, False)
    r = grade(AMBIGUOUS, "Do you mean the review before Phase B or some other review?", judge=judge)
    assert (r["decided_by"], r["grade"]) == ("judge", "CORRECT")
    prompt = judge.question_calls()[0][-1]["content"]
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
    assert r["judge_answers"] == [{"same": True, "contradicts": False, "omits": False, "unsupported": False}] * 2
    assert r["judge_model"] == "stub-judge"


def test_partial_maps_to_label_zero_and_keeps_grade():
    r = grade(ANSWERABLE, LONG_HEDGE, judge=both(False, False, True))
    assert (r["grade"], r["label"]) == ("PARTIAL", 0)


def test_one_unreadable_reply_is_flagged_wrong_and_keeps_the_readable_grade():
    judge = StubJudge(["I think it is fine.", reply(True, False, False)])
    r = grade(ANSWERABLE, LONG_HEDGE, judge=judge)
    assert (r["grade"], r["label"], r["flag"]) == ("WRONG", 0, "judge_unparsed")
    assert r["judge_grades"] == [None, "CORRECT"]
    assert r["judge_answers"][0] is None
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
    assert set(r) >= {"judge_grades", "judge_answers", "judge_quotes", "judge_ungrounded", "judge_outputs", "flag", "judge_model", "decided_by", "label"}


READINGS_ITEM = {
    "id": "amb1",
    "bucket": "ambiguous",
    "question": "Who is the customer whose expectations a systems engineer has to capture at the start of the design processes?",
    "readings": [
        {"reading": "a systems engineer working at the top level of the Product Breakdown Structure", "answer": "the person or organization purchasing the product", "page": "46"},
        {"reading": "a systems engineer working several levels down in the Product Breakdown Structure", "answer": "the leader of the team that takes the element and integrates it into a larger assembly", "page": "46"},
    ],
    "evidence": [],
}


def test_clarify_alternatives_splits_a_composed_question():
    from calibration.grader import clarify_alternatives

    assert clarify_alternatives("Do you mean the project SEMP, or the program SEMP?") == ["the project SEMP", "the program SEMP"]
    assert clarify_alternatives("Both are held in Phase A. Do you mean the requirements review or the architecture review that follows it?") == [
        "the requirements review", "the architecture review that follows it"]
    assert clarify_alternatives("The Program Manager approves it.") == []


def test_a_clarify_that_names_both_readings_is_correct_by_rule():
    draft = "Do you mean Systems engineer at topmost level of project, or Systems engineer working three or four levels down in PBS?"
    r = grade(READINGS_ITEM, draft, judge=never_called)
    assert (r["decided_by"], r["grade"], r["label"]) == ("rules", "CORRECT", 1)


def test_a_clarify_that_names_one_reading_goes_to_the_judge():
    from calibration.grader import names_readings

    assert not names_readings("Do you mean the purchasing organization, or something else?", READINGS_ITEM["readings"])
    assert not names_readings("Do you mean the customer, or the customer's expectations?", READINGS_ITEM["readings"])
    assert not names_readings("Which customer do you mean?", READINGS_ITEM["readings"])


def test_a_clarify_on_an_answerable_item_is_still_wrong():
    r = grade(ANSWERABLE, "Do you mean the project manager, or the program manager?", judge=never_called)
    assert (r["decided_by"], r["grade"]) == ("rules", "WRONG")
