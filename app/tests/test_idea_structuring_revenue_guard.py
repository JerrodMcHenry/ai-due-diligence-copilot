"""
Build V3 -- Structured Venture Model, Part 24/26 (extraction quality).

Regression coverage for a real, LIVE-reproduced defect: structure_idea()'s
own safety filter verifies that a "user_provided" field's source_quote is
REAL TEXT from the founder's description, but -- before this fix -- never
verified that the quote actually STATED the claimed number. A live run of
the exact Part 23-C scenario ("We charge $199 per location per month. We
have three paying gyms.") returned monthly_revenue=597 (199 x 3) tagged
"user_provided", backed by a real-but-non-numerically-supporting quote --
SIE silently computed a founder's revenue for them, which Part 7 ("No
Hallucinated Business Data") and the validation group's own prompt rules
explicitly forbid.

These tests exercise `_extract_numbers`/`_revenue_value_is_verifiable`
directly -- the two pure, deterministic functions the fix actually lives
in -- rather than the real OpenAI-backed structure_idea() call, matching
this repo's existing convention of not hitting a live LLM from an
automated test (see test_idea_lab.py, which never calls structure_idea()
either). The live-LLM reproduction/fix confirmation itself was performed
manually against the real API (see Build V3's final report) and is not
re-run here since a non-deterministic external call has no place in a
regression suite.

Run with: python -m app.tests.test_idea_structuring_revenue_guard
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.ai.idea_structuring import _extract_numbers, _revenue_value_is_verifiable  # noqa: E402


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_extract_numbers_reads_plain_dollar_and_suffixed_figures() -> None:
    numbers = _extract_numbers("We charge $199 per month and closed $850K ARR last quarter, up from 72 customers.")
    expect(199 in numbers, f"Expected 199 in {numbers}")
    expect(850_000 in numbers, f"Expected 850000 (from $850K) in {numbers}")
    expect(72 in numbers, f"Expected 72 in {numbers}")


def test_extract_numbers_handles_commas_and_m_suffix() -> None:
    numbers = _extract_numbers("We raised $1,200,000 and are targeting $2.5M ARR.")
    expect(1_200_000 in numbers, f"Expected 1200000 in {numbers}")
    expect(2_500_000 in numbers, f"Expected 2500000 (from $2.5M) in {numbers}")


def test_extract_numbers_does_not_read_spelled_out_numbers() -> None:
    # "three" is not a numeral -- this is deliberate: the guard only
    # verifies figures the founder wrote as digits, never words.
    numbers = _extract_numbers("We have three paying gyms.")
    expect(numbers == [], f"Expected no numeric figures from a spelled-out count, got {numbers}")


def test_revenue_guard_accepts_none() -> None:
    expect(_revenue_value_is_verifiable(None, "anything") is True, "None (nothing claimed) must always pass")


def test_revenue_guard_accepts_a_directly_stated_figure() -> None:
    description = "We collect $12,500 in revenue every month from our subscribers."
    expect(_revenue_value_is_verifiable(12_500, description) is True, "A directly stated monthly figure must pass")


def test_revenue_guard_accepts_arr_divided_by_twelve() -> None:
    # The one derivation the prompt explicitly sanctions (unit
    # conversion of a stated fact, not an invented computation).
    description = "We have $850K ARR today."
    expect(
        _revenue_value_is_verifiable(70_833, description) is True,
        "ARR / 12 (a real, stated annual figure divided by 12) must pass",
    )


def test_revenue_guard_rejects_price_times_customer_count_fabrication() -> None:
    # The exact live-reproduced defect: 199 (stated) x 3 (stated,
    # spelled out) = 597 is not a number the founder ever wrote, and is
    # not the sanctioned ARR/12 conversion either.
    description = "We charge $199 per location per month. We have three paying gyms."
    expect(
        _revenue_value_is_verifiable(597, description) is False,
        "price x customer_count must NOT be accepted as a verified monthly_revenue figure",
    )


def test_revenue_guard_rejects_an_unrelated_invented_number() -> None:
    description = "We help local restaurants predict inventory needs."
    expect(
        _revenue_value_is_verifiable(15_000, description) is False,
        "A number with no textual support anywhere in the description must be rejected",
    )


def test_revenue_guard_allows_small_rounding_tolerance() -> None:
    # 850000 / 12 = 70833.33... -- the LLM's own integer rounding (70833)
    # must still pass, not fail on floating-point precision.
    description = "We have $850K ARR today."
    expect(_revenue_value_is_verifiable(70_833, description) is True, "Rounded ARR/12 must still verify")


TESTS = [
    test_extract_numbers_reads_plain_dollar_and_suffixed_figures,
    test_extract_numbers_handles_commas_and_m_suffix,
    test_extract_numbers_does_not_read_spelled_out_numbers,
    test_revenue_guard_accepts_none,
    test_revenue_guard_accepts_a_directly_stated_figure,
    test_revenue_guard_accepts_arr_divided_by_twelve,
    test_revenue_guard_rejects_price_times_customer_count_fabrication,
    test_revenue_guard_rejects_an_unrelated_invented_number,
    test_revenue_guard_allows_small_rounding_tolerance,
]


def main() -> None:
    print("\nBuild V3 -- idea_structuring revenue-guard regression suite")
    print("-" * 72)

    failures: list[str] = []
    for test in TESTS:
        name = test.__name__
        try:
            test()
        except AssertionError as error:
            print(f"FAIL  {name}\n      {error}")
            failures.append(name)
        else:
            print(f"PASS  {name}")

    print("-" * 72)
    print(f"{len(TESTS) - len(failures)}/{len(TESTS)} passed")

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
