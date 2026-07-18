from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreRange:
    minimum: float
    maximum: float


EXPECTED_SCORES: dict[str, dict[str, ScoreRange]] = {
    "stripe_series_a": {
        "overall": ScoreRange(82.0, 88.0),
        "market": ScoreRange(8.0, 9.5),
        "team": ScoreRange(8.0, 9.5),
        "product": ScoreRange(8.0, 9.5),
        "execution": ScoreRange(7.5, 9.0),
        "traction": ScoreRange(7.5, 9.0),
        "financial_health": ScoreRange(7.0, 9.0),
    },
}