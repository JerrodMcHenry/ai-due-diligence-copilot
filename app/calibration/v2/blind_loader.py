"""
PASS A blind-scoring loader for SIE Methodology v2 calibration.

Loads calibration-set benchmark records (app/benchmarks/companies/*.json) and
exposes ONLY the fields permitted during blind scoring:

    company_name, snapshot_date, snapshot_stage, industry, business_model,
    historical_evidence, normalized_facts, sources

It never exposes expected_quality_tier, future_outcome, or benchmark_notes
(which itself sometimes narrates future outcomes in its why_included /
evidence_repair_log text) -- those fields are stripped before the record is
returned to any caller, not merely hidden by convention.

It refuses to load any record the manifest marks as "holdout" -- the five
holdout companies (Fab.com, Rdio, Homejoy, DoorDash, Zenefits) are quarantined
and this loader is the enforcement point for that quarantine during
calibration work.

This module does not modify app/benchmarks/companies/*.json in any way -- it
only reads them and returns a filtered in-memory copy. It is calibration-only
tooling; it is not part of, and does not touch, the production scoring
pipeline (app/ai/*, app/workflows/*) or the production analyses table.

Run the guard tests with:
    python -m app.calibration.v2.test_blind_loader
"""

import json
from pathlib import Path
from typing import Any

BENCHMARK_DIR = Path(__file__).resolve().parents[3] / "app" / "benchmarks"
COMPANIES_DIR = BENCHMARK_DIR / "companies"
MANIFEST_PATH = BENCHMARK_DIR / "manifest.json"

# Fields that must NEVER appear in a blind-scoring record.
FORBIDDEN_FIELDS = {"expected_quality_tier", "future_outcome", "benchmark_notes"}

# The complete allowlist for PASS A. Anything not in this set is dropped,
# even if it isn't explicitly forbidden -- an allowlist is safer than a
# denylist for this purpose, since a new field added to the benchmark schema
# later defaults to excluded rather than defaulting to leaked.
PERMITTED_FIELDS = {
    "company_name",
    "snapshot_date",
    "snapshot_stage",
    "industry",
    "business_model",
    "historical_evidence",
    "normalized_facts",
    "sources",
}


class HoldoutAccessError(Exception):
    """Raised when calibration tooling attempts to load a holdout record."""


class ForbiddenFieldError(Exception):
    """Raised if a forbidden field is ever found on a record about to be
    returned to a caller -- this should be unreachable given PERMITTED_FIELDS
    is an allowlist, but is checked explicitly as a defense-in-depth guard."""


def _load_manifest() -> dict[str, Any]:
    with open(MANIFEST_PATH) as f:
        return json.load(f)


def _manifest_entry(filename: str, manifest: dict[str, Any]) -> dict[str, Any]:
    entry = next((c for c in manifest["companies"] if c["file"] == filename), None)
    if entry is None:
        raise ValueError(f"Unknown benchmark file: {filename!r} (not in manifest.json)")
    return entry


def load_calibration_company(filename: str) -> dict[str, Any]:
    """
    Load a single calibration-set company record, stripped to only the
    fields permitted during PASS A blind scoring.

    Raises HoldoutAccessError if `filename` refers to a holdout-set record --
    this is a hard stop, not a warning, since holdout companies must remain
    completely quarantined during calibration work.
    """
    manifest = _load_manifest()
    entry = _manifest_entry(filename, manifest)

    if entry["set"] != "calibration":
        raise HoldoutAccessError(
            f"{filename} is a HOLDOUT record (set={entry['set']!r}, "
            f"company={entry.get('company_name')!r}). Holdout records are "
            "quarantined and must never be loaded by calibration tooling, "
            "blind scoring included."
        )

    with open(COMPANIES_DIR / filename) as f:
        raw = json.load(f)

    blind = {k: v for k, v in raw.items() if k in PERMITTED_FIELDS}

    for forbidden in FORBIDDEN_FIELDS:
        if forbidden in blind:
            # Should be unreachable given PERMITTED_FIELDS is an allowlist
            # that never includes a forbidden field -- kept as an explicit,
            # fail-loud defense-in-depth check rather than trusting the
            # allowlist silently.
            raise ForbiddenFieldError(
                f"{forbidden!r} leaked into blind record for {filename}"
            )

    return blind


def load_all_calibration_companies() -> dict[str, dict[str, Any]]:
    """Load every calibration-set company's blind record, keyed by filename."""
    manifest = _load_manifest()
    out: dict[str, dict[str, Any]] = {}
    for entry in manifest["companies"]:
        if entry["set"] == "calibration":
            out[entry["file"]] = load_calibration_company(entry["file"])
    return out


def calibration_filenames() -> list[str]:
    manifest = _load_manifest()
    return sorted(
        entry["file"] for entry in manifest["companies"] if entry["set"] == "calibration"
    )


def holdout_filenames() -> list[str]:
    manifest = _load_manifest()
    return sorted(
        entry["file"] for entry in manifest["companies"] if entry["set"] == "holdout"
    )
