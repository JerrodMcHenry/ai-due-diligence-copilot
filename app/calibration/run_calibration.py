import json
from pathlib import Path
from typing import Any

from app.calibration.expected_scores import (
    EXPECTED_SCORES,
    ScoreRange,
)
from app.workflows.due_diligence_workflow import run_due_diligence


CALIBRATION_DIR = Path(__file__).resolve().parent
DATA_DIR = CALIBRATION_DIR / "data"
REPORTS_DIR = CALIBRATION_DIR / "reports"


def serialize_value(value: Any) -> Any:
    """Convert Pydantic models and nested objects into JSON-safe values."""

    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")

    if isinstance(value, dict):
        return {
            key: serialize_value(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [serialize_value(item) for item in value]

    return value


def extract_actual_scores(
    results: dict[str, Any],
) -> dict[str, float | None]:
    """Extract top-level calibration scores from workflow results."""

    sie_analysis = results["sie_analysis"]
    scorecard = sie_analysis.startup_scorecard

    return {
        "overall": scorecard.overall_score,
        "market": scorecard.market.score,
        "team": scorecard.team.score,
        "product": scorecard.product.score,
        "execution": scorecard.execution.score,
        "traction": scorecard.traction.score,
        "financial_health": scorecard.financial_health.score,
    }


def score_matches_expectation(
    actual_score: float | None,
    expected_range: ScoreRange,
) -> bool:
    """
    Return True when a score satisfies its calibration expectation.

    A missing score passes only when the benchmark explicitly allows
    unavailable evidence for that metric.
    """

    if actual_score is None:
        return expected_range.allow_unavailable

    return (
        expected_range.minimum
        <= actual_score
        <= expected_range.maximum
    )


def format_actual_score(actual_score: float | None) -> str:
    """Format an actual score for terminal output."""

    if actual_score is None:
        return "None"

    return f"{actual_score:.1f}"


def format_expected_range(expected_range: ScoreRange) -> str:
    """Format the expected score range and availability rule."""

    range_display = (
        f"{expected_range.minimum:.1f}"
        f"–{expected_range.maximum:.1f}"
    )

    if expected_range.allow_unavailable:
        return f"{range_display} or None"

    return range_display


def save_report(
    case_name: str,
    results: dict[str, Any],
) -> Path:
    """Save the complete workflow output as a JSON calibration report."""

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    report_path = REPORTS_DIR / f"{case_name}.json"
    serialized_results = serialize_value(results)

    with report_path.open("w", encoding="utf-8") as report_file:
        json.dump(
            serialized_results,
            report_file,
            indent=2,
            ensure_ascii=False,
        )

    return report_path


def run_case(case_name: str) -> bool:
    """Run and evaluate one calibration benchmark."""

    input_path = DATA_DIR / f"{case_name}.txt"
    company_text = input_path.read_text(encoding="utf-8")

    print(f"\nRunning calibration: {case_name}")
    print("-" * 72)

    results = run_due_diligence(company_text)

    report_path = save_report(case_name, results)
    actual_scores = extract_actual_scores(results)
    expected_scores = EXPECTED_SCORES[case_name]

    case_passed = True

    for metric_name, expected_range in expected_scores.items():
        actual_score = actual_scores.get(metric_name)

        passed = score_matches_expectation(
            actual_score=actual_score,
            expected_range=expected_range,
        )

        status = "PASS" if passed else "FAIL"
        actual_display = format_actual_score(actual_score)
        expected_display = format_expected_range(expected_range)

        print(
            f"{metric_name:<20}"
            f"{actual_display:<10}"
            f"{expected_display:<22}"
            f"{status}"
        )

        if not passed:
            case_passed = False

    print(f"\nReport saved: {report_path}")
    print(f"Case result: {'PASS' if case_passed else 'FAIL'}")

    return case_passed


def validate_calibration_cases() -> list[str]:
    """Validate benchmark files and expected-score configuration."""

    errors: list[str] = []

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    benchmark_files = {
        path.stem
        for path in DATA_DIR.glob("*.txt")
        if path.is_file()
    }

    if not benchmark_files:
        errors.append(f"No benchmark files found in {DATA_DIR}")

    for case_name in EXPECTED_SCORES:
        if case_name not in benchmark_files:
            errors.append(
                f"Missing benchmark file: {case_name}.txt"
            )

    for case_name in benchmark_files:
        if case_name not in EXPECTED_SCORES:
            errors.append(
                f"No expected scores configured for: {case_name}"
            )

    return errors


def main() -> None:
    """Run the complete calibration suite."""

    errors = validate_calibration_cases()

    if errors:
        print("\nCalibration configuration failed:\n")

        for error in errors:
            print(f"- {error}")

        raise SystemExit(1)

    passed_cases = 0
    total_cases = len(EXPECTED_SCORES)

    for case_name in EXPECTED_SCORES:
        if run_case(case_name):
            passed_cases += 1

    print("\n" + "=" * 72)
    print("CALIBRATION SUMMARY")
    print("=" * 72)
    print(f"Passed: {passed_cases}/{total_cases}")
    print(f"Failed: {total_cases - passed_cases}/{total_cases}")

    if passed_cases != total_cases:
        raise SystemExit(1)


if __name__ == "__main__":
    main()