import logging
from collections.abc import Awaitable, Callable
from dataclasses import asdict
from typing import Annotated
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, ConfigDict, Field

from .domain import Observation, RecordKind, StoreUnavailable
from .exports import Exporters, default_exports, export_page
from .policy import process_receipt, record_observation
from .ports import ReadingReader, ReadingWriter, ReceiptQueue, ReceiptSink

logger = logging.getLogger("field_notebook")


class ReadingInput(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        allow_inf_nan=False,
        json_schema_extra={
            "examples": [
                {"identity": "ridge-001", "station": "North ridge", "kelvin": 281.25}
            ]
        },
    )
    identity: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    station: str = Field(min_length=1, max_length=120)
    kelvin: float = Field(ge=0)


class ReadingOutput(BaseModel):
    sequence: int
    observation: ReadingInput


class AcceptedOutput(BaseModel):
    outcome: str
    reading: ReadingOutput


class PageOutput(BaseModel):
    readings: list[ReadingOutput]
    next_cursor: int | None


class DeliveryOutput(BaseModel):
    outcome: str
    event_id: str | None
    receipt: str | None


After = Annotated[int, Query(ge=0, le=9223372036854775807)]
Limit = Annotated[int, Query(ge=1, le=100)]
Key = Annotated[
    str,
    Header(
        alias="Idempotency-Key",
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9_-]+$",
    ),
]


def create_app(
    reader: ReadingReader,
    writer: ReadingWriter,
    queue: ReceiptQueue,
    sink: ReceiptSink,
    exporters: Exporters | None = None,
    root_path: str = "",
) -> FastAPI:
    formats = exporters if exporters is not None else default_exports()
    app = FastAPI(
        title="Field Notebook",
        root_path=root_path,
        version="1.0.0",
        description=(
            "Study SOLID through durable observations and retry-safe intake. "
            "Try requests below. Records are append-only; identities cannot "
            "overwrite history. Receipt processing creates local previews."
        ),
    )

    @app.middleware("http")
    async def request_context(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = uuid4().hex
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request method=%s path=%s status=%s request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            request_id,
        )
        return response

    @app.exception_handler(StoreUnavailable)
    async def storage_unconfirmed(request: Request, error: Exception) -> JSONResponse:
        logger.error(
            "storage_unconfirmed request_id=%s",
            getattr(request.state, "request_id", "unknown"),
            exc_info=error,
        )
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Storage unconfirmed; retry with the same key and content.",
                "request_id": getattr(request.state, "request_id", "unknown"),
            },
        )

    @app.get("/", include_in_schema=False)
    def index() -> RedirectResponse:
        return RedirectResponse("/docs")

    @app.get("/health", tags=["Operations"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready", tags=["Operations"])
    def ready() -> dict[str, str]:
        reader.page(0, 1)
        return {"status": "ready"}

    @app.post(
        "/readings",
        response_model=AcceptedOutput,
        status_code=201,
        tags=["Readings"],
        responses={
            200: {"description": "Exact idempotent replay"},
            409: {"description": "Identity or key conflict"},
            503: {"description": "Storage acknowledgement unconfirmed"},
        },
    )
    def record(
        body: ReadingInput, response: Response, idempotency_key: Key
    ) -> AcceptedOutput:
        try:
            observation = Observation(body.identity, body.station, body.kelvin)
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        result = record_observation(observation, idempotency_key, writer)
        if result.kind is RecordKind.CONFLICT:
            raise HTTPException(
                409, "Key or reading identity is already bound to different intent."
            )
        if result.reading is None:
            raise RuntimeError("Writer violated the acknowledgement contract")
        response.status_code = 201 if result.kind is RecordKind.CREATED else 200
        response.headers["Location"] = f"/readings/{observation.identity}"
        return AcceptedOutput(
            outcome=result.kind.value, reading=ReadingOutput(**asdict(result.reading))
        )

    @app.get("/readings", response_model=PageOutput, tags=["Readings"])
    def list_readings(after: After = 0, limit: Limit = 25) -> PageOutput:
        page = reader.page(after, limit)
        return PageOutput(
            readings=[ReadingOutput(**asdict(row)) for row in page.readings],
            next_cursor=page.next_cursor,
        )

    @app.get("/readings/{identity}", response_model=ReadingOutput, tags=["Readings"])
    def get_reading(identity: str) -> ReadingOutput:
        row = reader.get(identity)
        if row is None:
            raise HTTPException(404, "Reading not found")
        return ReadingOutput(**asdict(row))

    @app.get("/export", tags=["Exports"])
    def export(format: str = "json", after: After = 0, limit: Limit = 25) -> Response:
        if format not in formats.formats():
            raise HTTPException(422, {"supported_formats": formats.formats()})
        artifact, cursor = export_page(reader, formats, format, after, limit)
        headers = {} if cursor is None else {"X-Next-Cursor": str(cursor)}
        return Response(artifact.body, media_type=artifact.media_type, headers=headers)

    @app.post(
        "/outbox/process",
        response_model=DeliveryOutput,
        tags=["Receipts"],
        description=(
            "Process one pending event using an idempotent local preview sink. "
            "Retries reuse its receipt; no email is sent."
        ),
    )
    def process(response: Response) -> DeliveryOutput:
        result = process_receipt(queue, sink)
        if result.kind.value.endswith("unconfirmed"):
            response.status_code = 503
        return DeliveryOutput(
            outcome=result.kind.value, event_id=result.event_id, receipt=result.receipt
        )

    return app
