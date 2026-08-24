"""
Guard tests proving PASS A blinding cannot be violated by blind_loader.py.

These are the tests referenced by the PASS A task's requirement: "Add a
guard/test proving forbidden fields cannot reach the scoring context." No
LLM calls, no benchmark files modified.

Run with:
    python -m app.calibration.v2.test_blind_loader
"""

from app.calibration.v2.blind_loader import (
    FORBIDDEN_FIELDS,
    PERMITTED_FIELDS,
    HoldoutAccessError,
    calibration_filenames,
    holdout_filenames,
    load_all_calibration_companies,
    load_calibration_company,
)


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_exactly_fifteen_calibration_companies() -> None:
    files = calibration_filenames()
    expect(
        len(files) == 15,
        f"expected 15 calibration-set files in manifest.json, found {len(files)}: {files}",
    )


def test_exactly_five_holdout_companies() -> None:
    files = holdout_filenames()
    expected = {"doordash.json", "fab_com.json", "homejoy.json", "rdio.json", "zenefits.json"}
    expect(
        set(files) == expected,
        f"expected holdout set {expected}, found {set(files)}",
    )


def test_forbidden_fields_never_present_in_any_blind_record() -> None:
    companies = load_all_calibration_companies()
    expect(len(companies) == 15, f"expected 15 loaded records, got {len(companies)}")
    for filename, record in companies.items():
        for forbidden in FORBIDDEN_FIELDS:
            expect(
                forbidden not in record,
                f"BLINDING VIOLATION: {forbidden!r} present in blind record for {filename}",
            )


def test_only_permitted_fields_present() -> None:
    companies = load_all_calibration_companies()
    for filename, record in companies.items():
        extra = set(record.keys()) - PERMITTED_FIELDS
        expect(
            not extra,
            f"unexpected field(s) {extra} present in blind record for {filename} "
            "-- PERMITTED_FIELDS is an allowlist and should have excluded these",
        )


def test_permitted_fields_actually_present() -> None:
    companies = load_all_calibration_companies()
    for filename, record in companies.items():
        for required in ("historical_evidence", "sources", "snapshot_date", "snapshot_stage"):
            expect(required in record, f"{filename} missing expected field {required!r}")


def test_holdout_companies_rejected_by_filename() -> None:
    for h in holdout_filenames():
        try:
            load_calibration_company(h)
        except HoldoutAccessError:
            continue
        raise AssertionError(f"{h} should have raised HoldoutAccessError but did not")


def test_holdout_never_appears_in_load_all() -> None:
    companies = load_all_calibration_companies()
    for h in holdout_filenames():
        expect(h not in companies, f"HOLDOUT QUARANTINE VIOLATION: {h} present in load_all result")


TESTS = [
    test_exactly_fifteen_calibration_companies,
    test_exactly_five_holdout_companies,
    test_forbidden_fields_never_present_in_any_blind_record,
    test_only_permitted_fields_present,
    test_permitted_fields_actually_present,
    test_holdout_companies_rejected_by_filename,
    test_holdout_never_appears_in_load_all,
]


def main() -> None:
    print("\nPASS A blind-loader guard tests")
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
