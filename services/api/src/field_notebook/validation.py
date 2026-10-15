"""Field notebook: validation, formatting and storage change independently."""

from dataclasses import dataclass
from math import isfinite


def _valid_kelvin(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return isfinite(value) and value >= 0
    except OverflowError:
        return False


@dataclass(frozen=True)
class Reading:
    station: str
    kelvin: float

    def __post_init__(self) -> None:
        if not isinstance(self.station, str) or not self.station.strip():
            raise ValueError("A station is required")
        if not _valid_kelvin(self.kelvin):
            raise ValueError("Temperature must be finite, nonnegative kelvin")
