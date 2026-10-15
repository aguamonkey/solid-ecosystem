from typing import Protocol

from .domain import Observation, Page, ReceiptEvent, RecordResult, StoredReading


class ReadingWriter(Protocol):
    # The idempotency binding, reading and pending event commit together.
    def record(self, reading: Observation, key: str) -> RecordResult: ...


class ReadingLookup(Protocol):
    def get(self, identity: str) -> StoredReading | None: ...


class ReadingPager(Protocol):
    def page(self, after: int, limit: int) -> Page: ...


class ReadingReader(ReadingLookup, ReadingPager, Protocol):
    """HTTP read routes need both; exporters request only the pager."""


class ReceiptQueue(Protocol):
    def peek_pending(self) -> ReceiptEvent | None: ...
    def acknowledge(self, identity: str, receipt: str) -> None: ...


class ReceiptSink(Protocol):
    # Same event identity/content must return the same receipt without another effect.
    def deliver(self, event: ReceiptEvent) -> str: ...
