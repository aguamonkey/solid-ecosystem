from threading import RLock

from .domain import (
    Observation,
    Page,
    ReceiptEvent,
    RecordKind,
    RecordResult,
    StoredReading,
    validate_key,
    validate_page,
)


class MemoryNotebook:
    def __init__(self) -> None:
        self._lock = RLock()
        self._readings: dict[str, StoredReading] = {}
        self._keys: dict[str, Observation] = {}
        self._pending: dict[str, ReceiptEvent] = {}
        self._acknowledged: dict[str, str] = {}

    def record(self, reading: Observation, key: str) -> RecordResult:
        validate_key(key)
        with self._lock:
            previous = self._keys.get(key)
            if previous is not None:
                if previous != reading:
                    return RecordResult(RecordKind.CONFLICT)
                return RecordResult(
                    RecordKind.REPLAYED, self._readings[reading.identity]
                )
            if reading.identity in self._readings:
                return RecordResult(RecordKind.CONFLICT)
            stored = StoredReading(len(self._readings) + 1, reading)
            event = ReceiptEvent(f"reading:{reading.identity}:v1", stored)
            self._readings[reading.identity] = stored
            self._keys[key] = reading
            self._pending[event.identity] = event
            return RecordResult(RecordKind.CREATED, stored)

    def get(self, identity: str) -> StoredReading | None:
        with self._lock:
            return self._readings.get(identity)

    def page(self, after: int, limit: int) -> Page:
        validate_page(after, limit)
        with self._lock:
            rows = tuple(
                row for row in self._readings.values() if row.sequence > after
            )[: limit + 1]
            return Page(
                rows[:limit], rows[limit - 1].sequence if len(rows) > limit else None
            )

    def peek_pending(self) -> ReceiptEvent | None:
        with self._lock:
            return next(iter(self._pending.values()), None)

    def acknowledge(self, identity: str, receipt: str) -> None:
        with self._lock:
            if identity in self._acknowledged:
                if self._acknowledged[identity] != receipt:
                    raise ValueError("Acknowledgement conflict")
                return
            if identity not in self._pending:
                raise ValueError("Unknown event")
            self._acknowledged[identity] = receipt
            del self._pending[identity]


class MemoryReceiptSink:
    def __init__(self) -> None:
        self._lock = RLock()
        self._receipts: dict[str, tuple[ReceiptEvent, str]] = {}

    def deliver(self, event: ReceiptEvent) -> str:
        with self._lock:
            old = self._receipts.get(event.identity)
            if old:
                if old[0] != event:
                    raise ValueError("Receipt identity/content conflict")
                return old[1]
            receipt = f"preview:{event.identity}"
            self._receipts[event.identity] = (event, receipt)
            return receipt
