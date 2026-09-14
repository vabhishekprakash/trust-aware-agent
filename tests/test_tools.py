"""Tests for the narrow calculator and the acronym lookup."""

from agent.tools import calc_lines, calculate, format_number, lookup_acronym, parse_number


def test_parse_number_handles_money_commas_suffixes_and_percent():
    assert parse_number("$500M") == 500e6
    assert parse_number("40,000") == 40000
    assert parse_number("1.5B") == 1.5e9
    assert parse_number("67%") == 67
    assert parse_number("-5") == -5
    assert parse_number("five") is None
    assert parse_number("500 million") is None


def test_calculate_does_one_operation_on_two_numbers():
    assert calculate("$500M - $100M") == 400e6
    assert calculate("37 - 5") == 32
    assert calculate("500 / 40000") == 0.0125
    assert calculate("7 - 5") == 2
    assert calculate("3 x 4") == 12
    assert calculate("1B / 100M") == 10
    assert calculate("1 / 0") is None
    assert calculate("import os") is None
    assert calculate("2 + 3 + 4") is None


def test_format_number_keeps_integers_whole_and_trims_decimals():
    assert format_number(400e6) == "400,000,000"
    assert format_number(0.0125) == "0.0125"
    assert format_number(32.0) == "32"


def test_calc_lines_finds_calculator_requests_in_a_draft():
    draft = "Let me compute that.\nCALC: $500M - $100M\n"
    assert calc_lines(draft) == ["$500M - $100M"]
    assert calc_lines("No arithmetic here.") == []


def test_lookup_acronym_uses_the_table_given():
    table = {"CDR": ["Critical Design Review"], "CE": ["Concurrent Engineering", "Chief Engineer"]}
    assert lookup_acronym("cdr", table) == ["Critical Design Review"]
    assert lookup_acronym("CE", table) == ["Concurrent Engineering", "Chief Engineer"]
    assert lookup_acronym("XYZ", table) == []
