"""Synthetic company representation (Phase 10.8F, Part 10).

A SyntheticCompany is a bag of typed evidence + a declared stage.
Company IDs are always neutral (SYNTH_*), never a real company name --
enforced by a validator here, not merely a convention (Part 40's
real-company-leakage check is backed by this).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.calibration.sps_v3.types import EvidenceBase, NegativeSignalObservation, Stage

_FORBIDDEN_NAME_FRAGMENTS = (
    "stripe", "spacex", "databricks", "rippling", "plaid", "relaw", "dome",
    "notion", "figma", "deel", "toast", "faire", "klaviyo", "chime",
    "abnormal", "bumble", "peloton", "clubhouse", "wework", "loom",
    "better.com", "bolt", "gopuff", "away", "rivet", "openroll",
    "fixpoint", "lunabill", "sourcebot", "bear ai", "bravi", "denki",
    "canva",
    # Pre-existing canonical-database leakage (Phase 10.8H's leakage
    # register), added here for code-level enforcement completeness.
    "ramp business", "vanta", "brex", "airtable", "retool", "livecheck", "linear",
)


def _assert_neutral_id(company_id: str) -> None:
    """Phase 10.8F Part 40: SYNTH_-prefixed ids (adversarial/stress
    fixtures) must never reference a real company at all. Phase 10.8I
    introduces a second, deliberately different id family --
    CAL_<number>_<NAME>-prefixed ids for REAL calibration companies
    (Phase 10.8H/I), which are explicitly allowed to name a real company
    (that is the entire point of calibration) but must never match a
    company already in docs/validation/SPS_V3_CALIBRATION_LEAKAGE_REGISTER.md
    -- checked against the same fragment list, in the opposite polarity:
    forbidden for SYNTH_, but for CAL_ ids the check instead guards
    against accidentally reusing an ALREADY-LEAKED real company name,
    which the leakage register itself enumerates. Any other prefix is
    rejected outright -- there is no third, unvalidated path."""
    lowered = company_id.lower()
    if re.match(r"^synth_", lowered):
        for fragment in _FORBIDDEN_NAME_FRAGMENTS:
            if fragment in lowered:
                raise ValueError(
                    f"Synthetic company id {company_id!r} appears to reference a real company "
                    f"({fragment!r}) -- forbidden per Phase 10.8F Part 40."
                )
        return
    if re.match(r"^cal_\d+_", lowered):
        for fragment in _FORBIDDEN_NAME_FRAGMENTS:
            if fragment in lowered:
                raise ValueError(
                    f"Calibration company id {company_id!r} matches an ALREADY-LEAKED real "
                    f"company ({fragment!r}) per docs/validation/SPS_V3_CALIBRATION_LEAKAGE_REGISTER.md "
                    f"-- forbidden for calibration reuse per Phase 10.8H Part 18."
                )
        return
    raise ValueError(
        f"Company ids must start with SYNTH_ (synthetic adversarial fixtures) or "
        f"CAL_<number>_ (real Phase 10.8H/I calibration companies), got: {company_id!r}"
    )


@dataclass(frozen=True)
class SyntheticCompany:
    company_id: str
    stage: Stage
    evidence: tuple[EvidenceBase, ...] = field(default_factory=tuple)
    negative_signals: tuple[NegativeSignalObservation, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _assert_neutral_id(self.company_id)

    def with_extra_evidence(self, *new_evidence: EvidenceBase) -> "SyntheticCompany":
        return SyntheticCompany(
            company_id=self.company_id,
            stage=self.stage,
            evidence=self.evidence + tuple(new_evidence),
            negative_signals=self.negative_signals,
        )

    def with_extra_negative_signals(self, *new_signals: NegativeSignalObservation) -> "SyntheticCompany":
        return SyntheticCompany(
            company_id=self.company_id,
            stage=self.stage,
            evidence=self.evidence,
            negative_signals=self.negative_signals + tuple(new_signals),
        )

    def with_stage(self, stage: Stage) -> "SyntheticCompany":
        return SyntheticCompany(
            company_id=self.company_id,
            stage=stage,
            evidence=self.evidence,
            negative_signals=self.negative_signals,
        )

    def evidence_of_type(self, cls) -> tuple:
        return tuple(e for e in self.evidence if isinstance(e, cls))
