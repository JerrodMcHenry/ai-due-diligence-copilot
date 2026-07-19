from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreRange:
    minimum: float
    maximum: float
    allow_unavailable: bool = False

    def __post_init__(self) -> None:
        if self.minimum > self.maximum:
            raise ValueError(
                "ScoreRange minimum cannot be greater than maximum."
            )


EXPECTED_SCORES: dict[str, dict[str, ScoreRange]] = {
    "stripe_series_a": {
        "overall": ScoreRange(82.0, 88.0),
        "market": ScoreRange(7.5, 9.0),
        "team": ScoreRange(8.0, 9.5),
        "product": ScoreRange(8.0, 9.5),
        "execution": ScoreRange(7.5, 9.0),
        "traction": ScoreRange(
            7.5,
            9.0,
            allow_unavailable=True,
        ),
        "financial_health": ScoreRange(
            7.0,
            9.0,
            allow_unavailable=True,
        ),
    },
}