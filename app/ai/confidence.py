from models.evidence import Evidence


def calculate_confidence(evidence: list[Evidence | str]) -> str:
    if not evidence:
        return "Low"

    structured_evidence = [
        item for item in evidence
        if isinstance(item, Evidence)
    ]

    # Temporary backward compatibility:
    # old evidence strings count as medium-quality unverified evidence.
    string_evidence_count = sum(
        1 for item in evidence
        if isinstance(item, str)
    )

    verified = sum(
        1 for item in structured_evidence
        if item.verified
    )

    high = sum(
        1 for item in structured_evidence
        if item.confidence == "High"
    )

    medium = sum(
        1 for item in structured_evidence
        if item.confidence == "Medium"
    )

    score = (
        verified * 2 +
        high * 2 +
        medium +
        string_evidence_count
    )

    if score >= 12:
        return "High"

    if score >= 6:
        return "Medium"

    return "Low"