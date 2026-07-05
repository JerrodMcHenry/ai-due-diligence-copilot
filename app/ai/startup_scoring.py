from models.startup import SIEMethodologyAnalysis


PILLAR_WEIGHTS = {
    "market": 0.20,
    "team": 0.20,
    "product": 0.20,
    "execution": 0.15,
    "traction": 0.15,
    "financial_health": 0.10,
}


def calculate_startup_intelligence_score(
    analysis: SIEMethodologyAnalysis,
) -> float:
    total = 0.0

    for pillar_name, weight in PILLAR_WEIGHTS.items():
        pillar = getattr(analysis, pillar_name)

        if pillar and pillar.score is not None:
            total += pillar.score * weight

    return round(total, 1)