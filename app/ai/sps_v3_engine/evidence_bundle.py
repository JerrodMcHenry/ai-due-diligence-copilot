"""
Production evidence bundle (Phase 10.9, Part 6).

The deterministic evaluators in evaluators.py are duck-typed: every
`eval_*` function only ever reads `company.evidence` and
`company.negative_signals` (and `apply_staleness_filter` in freshness.py
reads the same two fields plus `.stage`). This class carries exactly that
shape into production, with zero of the calibration harness's own
constraints -- no SYNTH_/CAL_ id-prefix validation, no real-company-name
leakage checks -- because a production analysis is a real startup by
definition; those checks exist in
app.calibration.sps_v3.company.SyntheticCompany solely to keep synthetic
test fixtures from ever silently naming a real company, and firing the
same rule against a real production startup's own name would be nonsense.

Deliberately NOT a subclass of, or otherwise coupled to,
SyntheticCompany -- the calibration harness (Phase 10.8F-10.8J,
frozen this phase) is left completely untouched. This is a parallel,
production-only type with the same duck-typed interface.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.ai.sps_v3_engine.types import EvidenceBase, NegativeSignalObservation, Stage


@dataclass(frozen=True)
class EvidenceBundle:
    company_id: str
    stage: Stage
    evidence: tuple[EvidenceBase, ...] = field(default_factory=tuple)
    negative_signals: tuple[NegativeSignalObservation, ...] = field(default_factory=tuple)

    def with_extra_evidence(self, *new_evidence: EvidenceBase) -> "EvidenceBundle":
        return EvidenceBundle(
            company_id=self.company_id,
            stage=self.stage,
            evidence=self.evidence + tuple(new_evidence),
            negative_signals=self.negative_signals,
        )

    def with_extra_negative_signals(self, *new_signals: NegativeSignalObservation) -> "EvidenceBundle":
        return EvidenceBundle(
            company_id=self.company_id,
            stage=self.stage,
            evidence=self.evidence,
            negative_signals=self.negative_signals + tuple(new_signals),
        )

    def with_stage(self, stage: Stage) -> "EvidenceBundle":
        return EvidenceBundle(
            company_id=self.company_id,
            stage=stage,
            evidence=self.evidence,
            negative_signals=self.negative_signals,
        )

    def evidence_of_type(self, cls) -> tuple:
        return tuple(e for e in self.evidence if isinstance(e, cls))
