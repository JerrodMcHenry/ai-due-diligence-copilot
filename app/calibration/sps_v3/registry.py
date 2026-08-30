"""
Provisional constant registry (Phase 10.8F, Part 3).

Every numeric threshold the V3 rulebook marks CALIBRATION REQUIRED
lives here, centrally, with metadata -- never scattered as a magic
number inside an evaluator. This is what lets Part 33's sensitivity
analysis vary "every arbitrary constant" from one place, and what lets
the final report enumerate every provisional assumption exhaustively
rather than by grepping code for stray numbers.

Values here are PROVISIONAL_FOR_TESTING or CALIBRATION_REQUIRED, never
RULEBOOK_DEFINED unless the rulebook itself specified an exact number
(it did not, for any score band or threshold -- see SPS_V3_RULEBOOK.md
Part 19's explicit refusal to assert final values). Nothing in this
registry should be read as an approved production constant.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


class ParameterStatus(str, Enum):
    RULEBOOK_DEFINED = "RULEBOOK_DEFINED"
    PROVISIONAL_FOR_TESTING = "PROVISIONAL_FOR_TESTING"
    CALIBRATION_REQUIRED = "CALIBRATION_REQUIRED"


@dataclass(frozen=True)
class ProvisionalParameter:
    name: str
    value: Decimal
    status: ParameterStatus
    reason: str
    source: str
    sensitivity_range: tuple[Decimal, Decimal]


class ParameterRegistry:
    def __init__(self) -> None:
        self._params: dict[str, ProvisionalParameter] = {}

    def register(self, param: ProvisionalParameter) -> None:
        if param.name in self._params:
            raise ValueError(f"Parameter {param.name} already registered -- registry entries are append-only per name.")
        self._params[param.name] = param

    def get(self, name: str) -> ProvisionalParameter:
        return self._params[name]

    def value(self, name: str) -> Decimal:
        return self._params[name].value

    def all(self) -> dict[str, ProvisionalParameter]:
        return dict(self._params)

    def with_override(self, name: str, value: Decimal) -> "ParameterRegistry":
        """Returns a NEW registry with one parameter's value overridden --
        used by Part 32-34's sensitivity/boundary tests. Never mutates
        the base registry, so the default registry stays a stable
        baseline across the whole test run."""
        new_registry = ParameterRegistry()
        for existing_name, param in self._params.items():
            if existing_name == name:
                new_registry.register(
                    ProvisionalParameter(
                        name=param.name,
                        value=value,
                        status=param.status,
                        reason=param.reason + " [OVERRIDDEN for sensitivity test]",
                        source=param.source,
                        sensitivity_range=param.sensitivity_range,
                    )
                )
            else:
                new_registry.register(param)
        return new_registry


def build_default_registry() -> ParameterRegistry:
    """The single baseline registry every evaluator/aggregator reads
    from by default. Every entry here is provisional-for-testing --
    chosen only to exercise the architecture, per Rulebook Part 5's
    explicit instruction, never presented as methodology-approved."""

    registry = ParameterRegistry()

    def P(name: str, value: str, reason: str, source: str, lo: str, hi: str) -> None:
        registry.register(
            ProvisionalParameter(
                name=name,
                value=Decimal(value),
                status=ParameterStatus.CALIBRATION_REQUIRED,
                reason=reason,
                source=source,
                sensitivity_range=(Decimal(lo), Decimal(hi)),
            )
        )

    # --- Category B classification -> score band midpoints ---
    # Rulebook Part 19: bands must be non-overlapping and monotonic;
    # exact values are explicitly not asserted by the rulebook. These
    # four provisional midpoints are used by the generic
    # classification-to-score mapper (evaluators.py) for every
    # Category B dimension using the standard 4-label ladder.
    P("band.no_signal", "0", "NO_SIGNAL never scores -- placeholder only, unused numerically.", "10.8F provisional", "0", "0")
    P("band.single_signal", "5.5", "Provisional midpoint for a single-populated-field classification (Rulebook 'credible but ordinary').", "10.8F provisional", "5.0", "6.0")
    P("band.multiple_signals", "7.5", "Provisional midpoint for a multi-field classification ('strong, specifically evidenced').", "10.8F provisional", "7.0", "8.0")
    P("band.comprehensive", "9.5", "Provisional midpoint for the strongest classification ('exceptional').", "10.8F provisional", "9.0", "10.0")
    P("band.negative_signal", "2.0", "Provisional midpoint for a contradicted/negative classification.", "10.8F provisional", "0.0", "4.0")

    # --- Publishability gates (Phase 10.8J simplification, Part 10-11 --
    # ONE rule at the SPS level, ONE rule at the pillar level. Three
    # parameters retired here (never silently -- see the note below and
    # docs/methodology/SPS_V3_SIMPLIFICATION_10_8J.md for the full
    # reasoning): `gate.min_dimensions_per_pillar` (a raw dimension-count
    # floor, redundant with weighted pillar coverage and sometimes in
    # tension with it), `gate.min_publishable_pillars` and
    # `gate.min_critical_pillars_present` (both folded into the single
    # overall-coverage test, which -- being a PILLAR_WEIGHTS-weighted sum
    # -- already reflects too-few-pillars or wrong-pillars-represented
    # without a separate dedicated check for either). Examined and
    # retained unchanged in Phase 10.8I; not recalibrated here --
    # 10.8I's 9-20% real-company coverage figures reflect THAT phase's
    # deliberately shallow 1-2-query verification research, not
    # production-depth research (V2.1's existing multi-query pipeline is
    # already deeper than what 10.8I's calibration pass used), so they
    # are not, on their own, evidence this floor is miscalibrated.
    P("gate.overall_coverage_floor_pct", "35", "Overall coverage % floor for SPS publishability -- the SOLE SPS-level publishability rule as of Phase 10.8J.", "Rulebook Part 22 (marked CALIBRATION REQUIRED); examined, retained unchanged in 10.8I and 10.8J", "20", "50")
    P("gate.min_pillar_coverage_pct", "40", "Minimum pillar-level coverage % to publish that pillar -- the SOLE pillar-level publishability rule as of Phase 10.8J.", "Rulebook Part 22", "25", "55")

    # --- Traction: Current Scale stage-relative bands (illustrative,
    # one metric_type x one stage pair per Rulebook Part 13; full
    # matrix explicitly not built here, CALIBRATION REQUIRED throughout) ---
    P("traction.current_scale.seed.arr_ordinary_ceiling", "100000", "Below this ARR at Seed = ordinary-low band.", "Rulebook Part 13/15 (CALIBRATION REQUIRED)", "50000", "250000")
    P("traction.current_scale.seed.arr_strong_ceiling", "1000000", "Below this ARR at Seed = strong band; above = exceptional-for-stage.", "Rulebook Part 13/15", "500000", "2000000")
    P("traction.current_scale.series_a.arr_ordinary_ceiling", "1000000", "Below this ARR at Series A = ordinary-low band.", "Rulebook Part 13/15", "500000", "2000000")
    P("traction.current_scale.series_a.arr_strong_ceiling", "5000000", "Below this ARR at Series A = strong band.", "Rulebook Part 13/15", "3000000", "10000000")
    P("traction.current_scale.growth.arr_ordinary_ceiling", "10000000", "Below this ARR at Growth = ordinary-low band.", "Rulebook Part 13/15", "5000000", "20000000")
    P("traction.current_scale.growth.arr_strong_ceiling", "50000000", "Below this ARR at Growth = strong band.", "Rulebook Part 13/15", "25000000", "100000000")

    # --- Traction: Growth Trajectory ---
    P("traction.growth_trajectory.strong_yoy_pct", "100", "YoY growth % at/above which Growth Trajectory is STRONG.", "Rulebook Part 13", "50", "200")
    P("traction.growth_trajectory.exceptional_yoy_pct", "300", "YoY growth % at/above which Growth Trajectory is EXCEPTIONAL.", "Rulebook Part 13", "150", "500")
    P("traction.growth_trajectory.decline_negative_threshold_pct", "0", "YoY growth below this (i.e. any decline) triggers the negative-evidence band.", "Rulebook Part 13/17", "0", "0")

    # --- Financial Health: Capital Efficiency ---
    P("finhealth.capital_efficiency.strong_burn_to_revenue_ratio", "1.0", "burn/revenue ratio at/below which Capital Efficiency is STRONG.", "Rulebook Part 14", "0.5", "1.5")
    P("finhealth.capital_efficiency.exceptional_burn_to_revenue_ratio", "0.3", "burn/revenue ratio at/below which Capital Efficiency is EXCEPTIONAL.", "Rulebook Part 14", "0.1", "0.6")
    P("finhealth.capital_efficiency.severe_constraint_months_runway", "3", "Disclosed runway below this many months triggers severe_cash_constraint negative evidence.", "Rulebook Part 17", "1", "6")

    # --- Freshness/staleness thresholds (Phase 10.8G, Rulebook amendment
    # Part 11-12) -- NEW parameters, not a recalibration of any existing
    # one. "Borderline" begins at 75% of stale_after_months (fixed ratio,
    # not itself a separate provisional parameter, to keep the schema small).
    P("freshness.structural_fact.stale_after_months", "600", "Founder history/funding events -- effectively never stale within any realistic analysis horizon.", "10.8G Part 11 (new)", "240", "1200")
    P("freshness.historical_fact.stale_after_months", "36", "Market size/growth estimates, competitive landscape, product capability claims -- stale slowly.", "10.8G Part 11 (new)", "18", "60")
    P("freshness.recent_performance.stale_after_months", "18", "Customer count, retention, commercial contracts -- moderate staleness.", "10.8G Part 11 (new)", "9", "24")
    P("freshness.current_state.stale_after_months", "12", "Revenue, cash, burn, runway statements -- stales quickly.", "10.8G Part 11 (new)", "6", "18")

    # --- Confidence weighting (Rulebook Part 21 -- deterministic
    # weakest-link + provenance-grade mapping) ---
    P("confidence.min_grade_for_high", "0", "Ordinal threshold marker only -- see confidence.py for the actual (non-numeric) grade comparison logic; kept here for registry completeness/traceability.", "Rulebook Part 21", "0", "0")

    return registry


DEFAULT_REGISTRY = build_default_registry()
