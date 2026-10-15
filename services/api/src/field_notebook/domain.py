import re
from dataclasses import dataclass
from enum import Enum

from .validation import Reading


@dataclass(frozen=True)
class Observation:
    identity: str
    station: str
    kelvin: float

    def __post_init__(self) -> None:
        if (
            not isinstance(self.identity, str)
            or re.fullmatch(r"[A-Za-z0-9_-]{1,64}", self.identity) is None
        ):
            raise ValueError(
                "Identity must contain 1–64 letters, digits, underscores or hyphens"
            )
        Reading(self.station, self.kelvin)
        # Canonical numeric intent makes 0, 0.0 and -0.0 the same replay.
        object.__setattr__(self, "kelvin", float(self.kelvin) if self.kelvin else 0.0)
        if len(self.station) > 120:
            raise ValueError("Station must contain at most 120 characters")


@dataclass(frozen=True)
class StoredReading:
    sequence: int
    observation: Observation


@dataclass(frozen=True)
class Page:
    readings: tuple[StoredReading, ...]
    next_cursor: int | None


class RecordKind(Enum):
    CREATED = "created"
    REPLAYED = "replayed"
    CONFLICT = "conflict"


@dataclass(frozen=True)
class RecordResult:
    kind: RecordKind
    reading: StoredReading | None = None


@dataclass(frozen=True)
class ReceiptEvent:
    identity: str
    reading: StoredReading


class StoreUnavailable(Exception):
    """A storage acknowledgement is unavailable; effects may be unconfirmed."""


def validate_key(key: str) -> None:
    if not isinstance(key, str) or re.fullmatch(r"[A-Za-z0-9_-]{1,128}", key) is None:
        raise ValueError("Idempotency key must contain 1–128 identifier characters")


def validate_page(after: int, limit: int) -> None:
    if (
        type(after) is not int
        or not 0 <= after <= 9223372036854775807
        or type(limit) is not int
        or not 1 <= limit <= 100
    ):
        raise ValueError("Use a nonnegative cursor and a limit from 1 to 100")
