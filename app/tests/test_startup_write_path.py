"""
Regression tests for the canonical Startup write path
(app/database/db.py::get_or_create_startup(), wired into save_analysis()).

Like test_startup_entity_migration.py, this file intentionally exercises
real SQL against the real configured DATABASE_URL -- there is no separate
test database in this project, and the thing under test IS real
concurrency-sensitive write behavior, which cannot be meaningfully
verified without a real Postgres connection. Every row this file creates
is under a distinctive "ZZTest Write Path" company-name prefix that
cannot collide with any real company, and is deleted in a finally block,
even on failure. No test here makes an LLM/Tavily call.

Run with:
    python -m app.tests.test_startup_write_path
"""

import threading

from sqlalchemy import text

from app.database.db import engine, get_or_create_startup, save_analysis

TEST_PREFIX = "ZZTest Write Path"


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _save_test_analysis(company_name, methodology: dict | None = None) -> int:
    """Minimal save_analysis() call -- every argument this function
    doesn't care about is a harmless placeholder; only company_name (via
    structured_analysis) and methodology matter to what's under test."""
    return save_analysis(
        company_text=f"Test company text for {company_name}",
        summary="s",
        risk_analysis="r",
        competitor_analysis="c",
        memo="m",
        structured_analysis={
            "company_name": company_name,
            "industry": "SaaS",
            "business_model": "Subscription",
        },
        investment_score={},
        founder_analysis={},
        market_analysis={},
        sources=[],
        traction_analysis={},
        market_score=None,
        team_score=None,
        product_score=None,
        competition_score=None,
        traction_score=None,
        financial_score=None,
        overall_score=None,
        recommendation=None,
        readiness_score=None,
        readiness_summary=None,
        methodology=methodology,
    )


def _cleanup(analysis_ids: list[int]) -> None:
    with engine.begin() as connection:
        if analysis_ids:
            connection.execute(
                text("DELETE FROM analyses WHERE id = ANY(:ids)"),
                {"ids": analysis_ids},
            )

        connection.execute(
            text("DELETE FROM startups WHERE normalized_name LIKE :pattern"),
            {"pattern": f"{TEST_PREFIX.lower()}%"},
        )


def test_new_company_creates_one_startup() -> None:
    ids = []

    try:
        ids.append(_save_test_analysis(f"{TEST_PREFIX} New"))

        with engine.begin() as connection:
            count = connection.execute(
                text("SELECT COUNT(*) FROM startups WHERE normalized_name = :n"),
                {"n": f"{TEST_PREFIX.lower()} new"},
            ).scalar()

        expect(count == 1, f"Expected exactly one startups row, got {count}")
    finally:
        _cleanup(ids)


def test_new_analysis_receives_startup_id() -> None:
    ids = []

    try:
        analysis_id = _save_test_analysis(f"{TEST_PREFIX} Linkage")
        ids.append(analysis_id)

        with engine.begin() as connection:
            startup_id = connection.execute(
                text("SELECT startup_id FROM analyses WHERE id = :id"),
                {"id": analysis_id},
            ).scalar()

        expect(
            startup_id is not None,
            "Expected the new analysis to receive a non-null startup_id",
        )
    finally:
        _cleanup(ids)


def test_second_analysis_reuses_same_startup() -> None:
    ids = []

    try:
        ids.append(_save_test_analysis(f"{TEST_PREFIX} Repeat"))
        ids.append(_save_test_analysis(f"{TEST_PREFIX} Repeat"))

        with engine.begin() as connection:
            startup_ids = connection.execute(
                text("SELECT DISTINCT startup_id FROM analyses WHERE id = ANY(:ids)"),
                {"ids": ids},
            ).scalars().all()

        expect(
            len(startup_ids) == 1,
            f"Expected both analyses to share one startup_id, got {startup_ids}",
        )
    finally:
        _cleanup(ids)


def test_case_variation_reuses_same_startup() -> None:
    ids = []

    try:
        ids.append(_save_test_analysis(f"{TEST_PREFIX} Case"))
        ids.append(_save_test_analysis(f"{TEST_PREFIX.upper()} CASE"))

        with engine.begin() as connection:
            startup_ids = connection.execute(
                text("SELECT DISTINCT startup_id FROM analyses WHERE id = ANY(:ids)"),
                {"ids": ids},
            ).scalars().all()

        expect(
            len(startup_ids) == 1,
            f"Expected a case variation to reuse the same startup_id, got {startup_ids}",
        )
    finally:
        _cleanup(ids)


def test_whitespace_variation_reuses_same_startup() -> None:
    ids = []

    try:
        ids.append(_save_test_analysis(f"{TEST_PREFIX} Whitespace"))
        ids.append(_save_test_analysis(f"   {TEST_PREFIX} Whitespace   "))

        with engine.begin() as connection:
            startup_ids = connection.execute(
                text("SELECT DISTINCT startup_id FROM analyses WHERE id = ANY(:ids)"),
                {"ids": ids},
            ).scalars().all()

        expect(
            len(startup_ids) == 1,
            f"Expected a whitespace variation to reuse the same startup_id, got {startup_ids}",
        )
    finally:
        _cleanup(ids)


def test_no_duplicate_startup_created_across_repeats() -> None:
    ids = []

    try:
        for _ in range(5):
            ids.append(_save_test_analysis(f"{TEST_PREFIX} NoDupe"))

        with engine.begin() as connection:
            count = connection.execute(
                text("SELECT COUNT(*) FROM startups WHERE normalized_name = :n"),
                {"n": f"{TEST_PREFIX.lower()} nodupe"},
            ).scalar()

        expect(count == 1, f"Expected exactly one startups row after 5 analyses, got {count}")
    finally:
        _cleanup(ids)


def test_canonical_name_not_overwritten_by_casing_variation() -> None:
    ids = []

    try:
        ids.append(_save_test_analysis(f"{TEST_PREFIX} Canonical"))
        ids.append(_save_test_analysis(f"{TEST_PREFIX.upper()} CANONICAL"))
        ids.append(_save_test_analysis(f"  {TEST_PREFIX.lower()} canonical  "))

        with engine.begin() as connection:
            canonical_name = connection.execute(
                text(
                    "SELECT canonical_name FROM startups WHERE normalized_name = :n"
                ),
                {"n": f"{TEST_PREFIX.lower()} canonical"},
            ).scalar()

        expect(
            canonical_name == f"{TEST_PREFIX} Canonical",
            f"Expected canonical_name to stay as the FIRST analysis's casing "
            f"({TEST_PREFIX} Canonical), got {canonical_name!r}",
        )
    finally:
        _cleanup(ids)


def test_null_or_empty_company_name_preserved_safe_behavior() -> None:
    ids = []

    try:
        ids.append(_save_test_analysis(None))
        ids.append(_save_test_analysis("   "))

        with engine.begin() as connection:
            startup_ids = connection.execute(
                text("SELECT startup_id FROM analyses WHERE id = ANY(:ids)"),
                {"ids": ids},
            ).scalars().all()

        expect(
            all(sid is None for sid in startup_ids),
            f"Expected null/empty company_name to leave startup_id NULL, got {startup_ids}",
        )
    finally:
        _cleanup(ids)


def test_methodology_json_unchanged_by_startup_linkage() -> None:
    ids = []
    fake_methodology = {
        "startup_intelligence_score": 55.5,
        "context": {"company_name": f"{TEST_PREFIX} Methodology"},
    }

    try:
        analysis_id = _save_test_analysis(
            f"{TEST_PREFIX} Methodology", methodology=fake_methodology
        )
        ids.append(analysis_id)

        with engine.begin() as connection:
            stored = connection.execute(
                text("SELECT methodology FROM analyses WHERE id = :id"),
                {"id": analysis_id},
            ).scalar()

        expect(
            stored == fake_methodology,
            f"Expected methodology JSONB unchanged by startup_id resolution, got {stored!r}",
        )
    finally:
        _cleanup(ids)


def test_repeated_calls_idempotent_at_identity_layer() -> None:
    """Calling get_or_create_startup() directly, repeatedly, for the same
    identity must always return the same id and never grow the startups
    table further."""
    company_name = f"{TEST_PREFIX} Idempotent"

    try:
        first_id = get_or_create_startup(company_name)
        second_id = get_or_create_startup(company_name.upper())
        third_id = get_or_create_startup(f"  {company_name.lower()}  ")

        with engine.begin() as connection:
            count = connection.execute(
                text("SELECT COUNT(*) FROM startups WHERE normalized_name = :n"),
                {"n": company_name.lower()},
            ).scalar()

        expect(
            first_id == second_id == third_id,
            f"Expected the same id every time, got {first_id}, {second_id}, {third_id}",
        )
        expect(count == 1, f"Expected exactly one startups row, got {count}")
    finally:
        _cleanup([])


def test_no_membership_created() -> None:
    ids = []

    try:
        with engine.begin() as connection:
            before = connection.execute(text("SELECT COUNT(*) FROM startup_memberships")).scalar()

        ids.append(_save_test_analysis(f"{TEST_PREFIX} NoMembership"))

        with engine.begin() as connection:
            after = connection.execute(text("SELECT COUNT(*) FROM startup_memberships")).scalar()

        expect(
            before == after,
            f"Expected startup_memberships row count unchanged by save_analysis(), "
            f"got {before} -> {after}",
        )
    finally:
        _cleanup(ids)


def test_no_saved_startup_created() -> None:
    ids = []

    try:
        with engine.begin() as connection:
            before = connection.execute(text("SELECT COUNT(*) FROM saved_startups")).scalar()

        ids.append(_save_test_analysis(f"{TEST_PREFIX} NoSaved"))

        with engine.begin() as connection:
            after = connection.execute(text("SELECT COUNT(*) FROM saved_startups")).scalar()

        expect(
            before == after,
            f"Expected saved_startups row count unchanged by save_analysis(), "
            f"got {before} -> {after}",
        )
    finally:
        _cleanup(ids)


def test_concurrent_new_company_resolves_to_one_startup() -> None:
    """Simulates the uniqueness race directly: two threads, each with
    their own DB connection, call get_or_create_startup() for the SAME
    brand-new identity at (as close to) the same instant. Proves the
    UNIQUE constraint + ON CONFLICT DO NOTHING path actually holds under
    real concurrent access, not just sequential calls."""
    company_name = f"{TEST_PREFIX} Concurrent"
    results: dict[str, int | None] = {}
    start_barrier = threading.Barrier(2)

    def worker(key: str) -> None:
        start_barrier.wait()  # maximize the chance both INSERTs overlap
        results[key] = get_or_create_startup(company_name)

    try:
        t1 = threading.Thread(target=worker, args=("a",))
        t2 = threading.Thread(target=worker, args=("b",))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        with engine.begin() as connection:
            count = connection.execute(
                text("SELECT COUNT(*) FROM startups WHERE normalized_name = :n"),
                {"n": company_name.lower()},
            ).scalar()

        expect(
            results["a"] is not None and results["a"] == results["b"],
            f"Expected both concurrent callers to resolve to the same id, got {results}",
        )
        expect(
            count == 1,
            f"Expected exactly one startups row despite the concurrent race, got {count}",
        )
    finally:
        _cleanup([])


TESTS = [
    test_new_company_creates_one_startup,
    test_new_analysis_receives_startup_id,
    test_second_analysis_reuses_same_startup,
    test_case_variation_reuses_same_startup,
    test_whitespace_variation_reuses_same_startup,
    test_no_duplicate_startup_created_across_repeats,
    test_canonical_name_not_overwritten_by_casing_variation,
    test_null_or_empty_company_name_preserved_safe_behavior,
    test_methodology_json_unchanged_by_startup_linkage,
    test_repeated_calls_idempotent_at_identity_layer,
    test_no_membership_created,
    test_no_saved_startup_created,
    test_concurrent_new_company_resolves_to_one_startup,
]


def main() -> None:
    print("\nCanonical Startup write path tests")
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
