"""
Methodology V2.1 (Phase 10.8B, Part 3) -- deterministic, Python-level
guard against fabricated quantitative evidence.

Phase 10.8A's discrimination audit and Phase 10.8B's full-cohort
correctness check (docs/validation/SPS_DISCRIMINATION_AUDIT.md,
SPS_METHODOLOGY_V2_1_CHANGELOG.md) found that 18 of 25 real companies in
the frozen Phase 10.8 validation cohort had at least one Financial
Health subscore citing a specific dollar/percentage/ratio figure that
does not appear anywhere in that company's own stored research brief --
e.g. Loom's Burn Efficiency rationale claimed "$2M ARR against $5M
funding, CAC of $500, 150 customers" when Loom's own research brief
states it raised $203.6M total funding and has 400,000 companies as
customers. The evidence-extraction prompt already told the model "do
not invent" figures (see EVIDENCE_REQUIREMENT_RULES in
evidence_extraction.py); that instruction alone was not sufficient, so
this module adds a second, Python-side check that does not depend on
the model choosing to comply.

This is intentionally a narrow, mechanical check: does every number-
shaped token quoted in a dimension's evidence also appear (after
normalizing whitespace/commas/case) somewhere in the source text the
model was actually given? It cannot verify that a number is *correct*
(only a domain expert or a second, independent source could), and it
cannot catch a fabricated CLAIM that contains no digits (e.g. an invented
qualitative claim like "the company has strong retention" with no
number attached) -- catching those remains the underlying prompt rule's
job. What this module catches, reliably: specific-sounding numbers
presented as observed fact that were never actually supplied to the
model at all. That was the dominant, most damaging pattern found in the
Phase 10.8 cohort.
"""

import re

_NUMERIC_PATTERN = re.compile(
    r"\$\s?\d[\d,\.]*\s?[MKBmkb]?\+?"   # $5M, $400K, $1.2M, $10M+
    r"|\d[\d,\.]*\s?%"                    # 30%, 12.5%
    r"|\d[\d,\.]*\s?:\s?\d[\d,\.]*"       # 5:1, 10:1
    r"|\d[\d,\.]*x\b"                     # 6x, 1.6x
)


def _normalize(token: str) -> str:
    return re.sub(r"[\s,]", "", token).lower().rstrip(".")


def extract_numeric_claims(text: str) -> set[str]:
    """All number-shaped substrings (currency, percentage, ratio,
    multiple) found in text, exactly as written."""
    return {match.strip() for match in _NUMERIC_PATTERN.findall(text or "")}


def find_unsupported_numeric_claims(
    evidence_items: list[str],
    source_text: str,
) -> list[str]:
    """
    The subset of numeric-looking tokens quoted anywhere in
    evidence_items that cannot be found (verbatim, after normalizing
    spacing/commas/case) anywhere in source_text. An empty list means
    every number cited in this dimension's evidence is traceable to the
    text the model actually saw.
    """
    source_norms = {_normalize(n) for n in extract_numeric_claims(source_text)}
    unsupported: list[str] = []
    for item in evidence_items:
        for n in extract_numeric_claims(item):
            if _normalize(n) not in source_norms:
                unsupported.append(n)
    return unsupported


def strip_unsupported_evidence(
    evidence_items: list[str],
    source_text: str,
) -> tuple[list[str], list[str]]:
    """
    Split evidence_items into (kept, dropped). An evidence bullet is
    dropped in its entirety, never edited in place, if ANY numeric claim
    inside it cannot be traced to source_text -- a bullet mixing one real
    number with one invented number is not partially trustworthy, since
    there is no way to know which half a downstream reader should
    believe.

    Bullets containing no numeric claims at all are always kept: this
    guard only targets quantitative fabrication (Phase 10.8's confirmed
    failure mode), never qualitative narrative, which is governed by the
    existing evidence-classification rules instead.
    """
    source_norms = {_normalize(n) for n in extract_numeric_claims(source_text)}
    kept: list[str] = []
    dropped: list[str] = []

    for item in evidence_items:
        claims = extract_numeric_claims(item)
        if claims and not all(_normalize(n) in source_norms for n in claims):
            dropped.append(item)
        else:
            kept.append(item)

    return kept, dropped


def apply_provenance_guard(
    dimensions: list,
    company_text: str,
) -> tuple[list, set[str]]:
    """
    Run the fabrication guard over one pillar's already-extracted
    EvidenceAnalysis objects (app/models/evidence_analysis.py).

    For every dimension not already Unavailable, both `evidence` and
    `signals` are checked. If stripping unsupported numeric claims still
    leaves at least one real, traceable evidence item, the dimension
    keeps its evidence_status but is downgraded to Low confidence (part
    of its original justification was invented, so the remaining
    justification is not the confidence level the model originally
    claimed). If nothing traceable survives, the dimension is forced to
    Unavailable -- a fabricated-only justification is not a real
    assessment, and Unavailable is the honest fallback the rest of the
    pipeline already knows how to handle (dropped from the pillar's
    weighted average, per app/ai/scoring.py::calculate_weighted_score).

    Returns (new_dimensions, altered_dimension_names) -- altered_dimension_names
    is for observability only (mirrors the existing corrected_names
    pattern in evidence_extraction.py / pillar_scoring.py), never used to
    change scoring behavior itself.
    """
    new_dimensions = []
    altered: set[str] = set()

    for dim in dimensions:
        if dim.evidence_status == "Unavailable" or (not dim.evidence and not dim.signals):
            new_dimensions.append(dim)
            continue

        kept_evidence, dropped_evidence = strip_unsupported_evidence(
            dim.evidence, company_text
        )
        kept_signals, dropped_signals = strip_unsupported_evidence(
            dim.signals, company_text
        )

        if not dropped_evidence and not dropped_signals:
            new_dimensions.append(dim)
            continue

        altered.add(dim.dimension)
        provenance_note = (
            "[Evidence provenance guard] Removed "
            f"{len(dropped_evidence) + len(dropped_signals)} claim(s) "
            "citing a specific number that does not appear anywhere in "
            "the supplied company information/research -- likely "
            "fabricated rather than observed."
        )

        if kept_evidence or kept_signals:
            new_dimensions.append(
                dim.model_copy(
                    update={
                        "evidence": kept_evidence,
                        "signals": kept_signals,
                        "confidence": "Low",
                        "rationale": f"{provenance_note} Original rationale: {dim.rationale}",
                    }
                )
            )
        else:
            new_dimensions.append(
                dim.model_copy(
                    update={
                        "evidence_status": "Unavailable",
                        "evidence": [],
                        "signals": [],
                        "confidence": "Low",
                        "missing_information": list(dim.missing_information or []) + [
                            "All previously cited evidence for this dimension quoted "
                            "specific figures not found in the supplied company "
                            "information/research and was removed by the evidence "
                            "provenance guard."
                        ],
                        "rationale": f"{provenance_note} Original rationale: {dim.rationale}",
                    }
                )
            )

    return new_dimensions, altered
