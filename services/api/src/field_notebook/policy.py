from dataclasses import dataclass
from enum import Enum

from .domain import Observation, RecordResult, validate_key
from .ports import ReadingWriter, ReceiptQueue, ReceiptSink


class DeliveryKind(Enum):
    EMPTY = "empty"
    QUEUE_UNCONFIRMED = "queue-unconfirmed"
    SINK_UNCONFIRMED = "sink-unconfirmed"
    ACK_UNCONFIRMED = "ack-unconfirmed"
    ACKNOWLEDGED = "acknowledged"


@dataclass(frozen=True)
class Delivery:
    kind: DeliveryKind
    event_id: str | None = None
    receipt: str | None = None


def record_observation(
    reading: Observation, key: str, writer: ReadingWriter
) -> RecordResult:
    validate_key(key)
    return writer.record(reading, key)


def process_receipt(queue: ReceiptQueue, sink: ReceiptSink) -> Delivery:
    try:
        event = queue.peek_pending()
    except Exception:
        return Delivery(DeliveryKind.QUEUE_UNCONFIRMED)
    if event is None:
        return Delivery(DeliveryKind.EMPTY)
    try:
        receipt = sink.deliver(event)
        if not isinstance(receipt, str) or not receipt.strip():
            raise ValueError("Sink must return a receipt")
    except Exception:
        return Delivery(DeliveryKind.SINK_UNCONFIRMED, event.identity)
    try:
        queue.acknowledge(event.identity, receipt)
    except Exception:
        return Delivery(DeliveryKind.ACK_UNCONFIRMED, event.identity, receipt)
    return Delivery(DeliveryKind.ACKNOWLEDGED, event.identity, receipt)
