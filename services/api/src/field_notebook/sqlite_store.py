import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from .domain import (
    Observation,
    Page,
    ReceiptEvent,
    RecordKind,
    RecordResult,
    StoredReading,
    StoreUnavailable,
    validate_key,
    validate_page,
)


def fingerprint(reading: Observation) -> str:
    return json.dumps(
        [reading.identity, reading.station, float(reading.kelvin)],
        ensure_ascii=True,
        separators=(",", ":"),
    )


def _stored(row: sqlite3.Row) -> StoredReading:
    return StoredReading(
        int(row["sequence"]),
        Observation(str(row["identity"]), str(row["station"]), float(row["kelvin"])),
    )


class SqliteNotebook:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection(write=True) as connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise ValueError("Unsupported database schema version")
            if version == 0:
                for statement in (
                    """CREATE TABLE readings (
                        sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                        identity TEXT NOT NULL UNIQUE,
                        station TEXT NOT NULL,
                        kelvin REAL NOT NULL CHECK(kelvin>=0)
                    )""",
                    """CREATE TABLE requests (
                        key TEXT PRIMARY KEY,
                        fingerprint TEXT NOT NULL,
                        reading_id TEXT NOT NULL REFERENCES readings(identity)
                    )""",
                    """CREATE TABLE outbox (
                        sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                        identity TEXT NOT NULL UNIQUE,
                        reading_id TEXT NOT NULL UNIQUE REFERENCES readings(identity),
                        receipt TEXT
                    )""",
                    """CREATE TABLE previews (
                        identity TEXT PRIMARY KEY,
                        fingerprint TEXT NOT NULL,
                        receipt TEXT NOT NULL
                    )""",
                ):
                    connection.execute(statement)
                connection.execute("PRAGMA user_version=1")

    @contextmanager
    def connection(self, write: bool = False) -> Iterator[sqlite3.Connection]:
        connection: sqlite3.Connection | None = None
        try:
            connection = sqlite3.connect(self.path, timeout=5, isolation_level=None)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys=ON")
            if write:
                connection.execute("BEGIN IMMEDIATE")
            yield connection
            if write:
                connection.execute("COMMIT")
        except BaseException as error:
            if connection is not None and connection.in_transaction:
                connection.execute("ROLLBACK")
            if isinstance(error, sqlite3.Error):
                raise StoreUnavailable("Storage acknowledgement unavailable") from error
            raise
        finally:
            if connection is not None:
                connection.close()

    def record(self, reading: Observation, key: str) -> RecordResult:
        validate_key(key)
        with self.connection(write=True) as connection:
            previous = connection.execute(
                "SELECT fingerprint FROM requests WHERE key=?", (key,)
            ).fetchone()
            if previous is not None:
                if previous[0] != fingerprint(reading):
                    return RecordResult(RecordKind.CONFLICT)
                row = connection.execute(
                    "SELECT * FROM readings WHERE identity=?", (reading.identity,)
                ).fetchone()
                return RecordResult(RecordKind.REPLAYED, _stored(row))
            if connection.execute(
                "SELECT 1 FROM readings WHERE identity=?", (reading.identity,)
            ).fetchone():
                return RecordResult(RecordKind.CONFLICT)
            connection.execute(
                "INSERT INTO readings(identity,station,kelvin) VALUES (?,?,?)",
                (reading.identity, reading.station, reading.kelvin),
            )
            connection.execute(
                "INSERT INTO requests VALUES (?,?,?)",
                (key, fingerprint(reading), reading.identity),
            )
            connection.execute(
                "INSERT INTO outbox(identity,reading_id) VALUES (?,?)",
                (f"reading:{reading.identity}:v1", reading.identity),
            )
            row = connection.execute(
                "SELECT * FROM readings WHERE identity=?", (reading.identity,)
            ).fetchone()
            return RecordResult(RecordKind.CREATED, _stored(row))

    def get(self, identity: str) -> StoredReading | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM readings WHERE identity=?", (identity,)
            ).fetchone()
            return None if row is None else _stored(row)

    def page(self, after: int, limit: int) -> Page:
        validate_page(after, limit)
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM readings WHERE sequence>? ORDER BY sequence LIMIT ?",
                (after, limit + 1),
            ).fetchall()
            return Page(
                tuple(_stored(row) for row in rows[:limit]),
                int(rows[limit - 1]["sequence"]) if len(rows) > limit else None,
            )

    def peek_pending(self) -> ReceiptEvent | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT r.*,o.identity AS event_id FROM outbox o "
                "JOIN readings r "
                "ON r.identity=o.reading_id WHERE o.receipt IS NULL "
                "ORDER BY "
                "o.sequence LIMIT 1"
            ).fetchone()
            return (
                None
                if row is None
                else ReceiptEvent(str(row["event_id"]), _stored(row))
            )

    def acknowledge(self, identity: str, receipt: str) -> None:
        with self.connection(write=True) as connection:
            row = connection.execute(
                "SELECT receipt FROM outbox WHERE identity=?", (identity,)
            ).fetchone()
            if row is None:
                raise ValueError("Unknown event")
            if row[0] is not None and row[0] != receipt:
                raise ValueError("Acknowledgement conflict")
            connection.execute(
                "UPDATE outbox SET receipt=? WHERE identity=?", (receipt, identity)
            )


class SqliteReceiptSink:
    def __init__(self, store: SqliteNotebook) -> None:
        self._store = store

    def deliver(self, event: ReceiptEvent) -> str:
        content = json.dumps(
            [event.reading.sequence, fingerprint(event.reading.observation)]
        )
        with self._store.connection(write=True) as connection:
            previous = connection.execute(
                "SELECT fingerprint,receipt FROM previews WHERE identity=?",
                (event.identity,),
            ).fetchone()
            if previous:
                if previous[0] != content:
                    raise ValueError("Receipt identity/content conflict")
                return str(previous[1])
            receipt = f"preview:{event.identity}"
            connection.execute(
                "INSERT INTO previews VALUES (?,?,?)",
                (event.identity, content, receipt),
            )
            return receipt
