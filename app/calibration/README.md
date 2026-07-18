# SIE Calibration Suite

The calibration suite evaluates whether changes to the SIE methodology,
prompts, evidence rules, or scoring pipeline produce reasonable and
consistent results across benchmark startups.

## Structure

- `data/` contains benchmark company inputs.
- `expected_scores.py` defines acceptable score ranges.
- `run_calibration.py` runs each benchmark and compares actual scores
  against expected ranges.
- `reports/` stores the complete JSON output from each run.

## Naming convention

Benchmark files should include the company and historical stage:

- `stripe_series_a.txt`
- `snowflake_series_b.txt`
- `wework_2019.txt`
- `theranos_2015.txt`

The filename must match the corresponding key in `EXPECTED_SCORES`.

## Calibration rules

1. Expected values should be ranges, not exact scores.
2. Do not change the methodology because of one unexpected result.
3. Look for repeated scoring patterns across several benchmark companies.
4. Preserve complete reports for comparison and debugging.
5. Calibration should not modify the production scoring formula.

## Running calibration

From the project root:

```bash
python -m app.calibration.run_calibration
```

---

## 4. Create the initial `run_calibration.py`

This first version validates the calibration configuration before we connect it to the analysis pipeline:

```python
from pathlib import Path

from app.calibration.expected_scores import EXPECTED_SCORES


CALIBRATION_DIR = Path(__file__).resolve().parent
DATA_DIR = CALIBRATION_DIR / "data"
REPORTS_DIR = CALIBRATION_DIR / "reports"


def validate_calibration_cases() -> list[str]:
    errors: list[str] = []

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    benchmark_files = {
        path.stem: path
        for path in DATA_DIR.glob("*.txt")
        if path.is_file()
    }

    if not benchmark_files:
        errors.append(
            f"No benchmark files were found in {DATA_DIR}."
        )

    for case_name in EXPECTED_SCORES:
        if case_name not in benchmark_files:
            errors.append(
                f"Missing benchmark file: {case_name}.txt"
            )

    for case_name in benchmark_files:
        if case_name not in EXPECTED_SCORES:
            errors.append(
                f"No expected score ranges configured for: {case_name}"
            )

    for case_name, score_ranges in EXPECTED_SCORES.items():
        for metric_name, expected_range in score_ranges.items():
            if expected_range.minimum > expected_range.maximum:
                errors.append(
                    f"{case_name}.{metric_name}: minimum cannot exceed maximum."
                )

    return errors


def main() -> None:
    errors = validate_calibration_cases()

    if errors:
        print("\nCalibration configuration failed:\n")

        for error in errors:
            print(f"- {error}")

        raise SystemExit(1)

    print("\nCalibration configuration passed.")
    print(f"Cases configured: {len(EXPECTED_SCORES)}")
    print(f"Data directory: {DATA_DIR}")
    print(f"Reports directory: {REPORTS_DIR}")


if __name__ == "__main__":
    main()
```
