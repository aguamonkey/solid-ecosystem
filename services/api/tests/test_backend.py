import json
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from unittest.mock import Mock

from fastapi.testclient import TestClient

from field_notebook.domain import (
    Observation,
    Page,
    ReceiptEvent,
    RecordKind,
    StoredReading,
    StoreUnavailable,
)
from field_notebook.exports import (
    Artifact,
    Exporters,
    default_exports,
    export_page,
)
from field_notebook.http import create_app
from field_notebook.memory import MemoryNotebook, MemoryReceiptSink
from field_notebook.policy import (
    DeliveryKind,
    process_receipt,
    record_observation,
)
from field_notebook.sqlite_store import SqliteNotebook, SqliteReceiptSink


def observation(identity="one", kelvin=281):
    return Observation(identity, "North ridge", kelvin)


class StoreContract:
    def test_record_and_exact_replay_have_one_pending_event(self):
        first = self.store.record(observation(), "key")
        self.assertEqual(first.kind, RecordKind.CREATED)
        self.assertEqual(
            self.store.record(observation(), "key").kind, RecordKind.REPLAYED
        )
        self.assertEqual(len(self.store.page(0, 100).readings), 1)
        self.assertEqual(self.store.peek_pending().reading, first.reading)

    def test_reused_key_with_changed_content_conflicts(self):
        self.store.record(observation(), "key")
        self.assertEqual(
            self.store.record(observation(kelvin=282), "key").kind, RecordKind.CONFLICT
        )
        self.assertEqual(self.store.get("one").observation.kelvin, 281)

    def test_existing_identity_under_different_key_conflicts(self):
        self.store.record(observation(), "key")
        self.assertEqual(
            self.store.record(observation(), "new-key").kind, RecordKind.CONFLICT
        )

    def test_negative_zero_and_integer_replay_are_canonical(self):
        self.store.record(observation(kelvin=-0.0), "key")
        self.assertEqual(
            self.store.record(observation(kelvin=0), "key").kind, RecordKind.REPLAYED
        )

    def test_page_cursor_has_no_skips_or_duplicate_rows(self):
        for identity in ["a", "b", "c"]:
            self.store.record(observation(identity), identity)
        first = self.store.page(0, 2)
        second = self.store.page(first.next_cursor, 2)
        self.assertEqual(
            [row.observation.identity for row in first.readings], ["a", "b"]
        )
        self.assertEqual([row.observation.identity for row in second.readings], ["c"])
        self.assertIsNone(second.next_cursor)

    def test_cursor_domain_is_the_same_for_every_adapter(self):
        for after, limit in [
            (-1, 1),
            (True, 1),
            (2**63, 1),
            (0, 0),
            (0, 101),
            (0, True),
        ]:
            with self.assertRaises(ValueError):
                self.store.page(after, limit)
        self.assertEqual(self.store.page(2**63 - 1, 100).readings, ())

    def test_older_projection_is_unchanged_after_append(self):
        self.store.record(observation(), "key")
        before = self.store.page(0, 100)
        self.store.record(observation("two"), "two")
        self.assertEqual(len(before.readings), 1)
        with self.assertRaises(FrozenInstanceError):
            before.readings[0].observation.station = "Changed"

    def test_invalid_key_never_writes(self):
        for key in [" ", "a/b", "x" * 129]:
            with self.assertRaises(ValueError):
                self.store.record(observation(), key)
        self.assertEqual(self.store.page(0, 100).readings, ())
        self.assertIsNone(self.store.peek_pending())

    def test_missing_identity_returns_none(self):
        self.assertIsNone(self.store.get("missing"))

    def test_receipt_effect_is_idempotent_and_conflicts_on_changed_content(self):
        event = ReceiptEvent("event", StoredReading(1, observation()))
        receipt = self.sink.deliver(event)
        self.assertEqual(self.sink.deliver(event), receipt)
        with self.assertRaises(ValueError):
            self.sink.deliver(
                replace(event, reading=StoredReading(1, observation(kelvin=282)))
            )

    def test_processing_acknowledges_and_never_requeues_replayed_reading(self):
        self.store.record(observation(), "key")
        self.assertEqual(
            process_receipt(self.store, self.sink).kind, DeliveryKind.ACKNOWLEDGED
        )
        self.assertIsNone(self.store.peek_pending())
        self.store.record(observation(), "key")
        self.assertEqual(
            process_receipt(self.store, self.sink).kind, DeliveryKind.EMPTY
        )

    def test_acknowledgement_can_repeat_but_cannot_change_receipt(self):
        self.store.record(observation(), "key")
        event = self.store.peek_pending()
        self.store.acknowledge(event.identity, "receipt")
        self.store.acknowledge(event.identity, "receipt")
        with self.assertRaises(ValueError):
            self.store.acknowledge(event.identity, "different")
        with self.assertRaises(ValueError):
            self.store.acknowledge("missing", "receipt")


class MemoryContract(StoreContract, unittest.TestCase):
    def setUp(self):
        self.store = MemoryNotebook()
        self.sink = MemoryReceiptSink()


class SqliteContract(StoreContract, unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "notebook.sqlite3"
        self.store = SqliteNotebook(self.path)
        self.sink = SqliteReceiptSink(self.store)

    def test_data_idempotency_and_pending_event_survive_restart(self):
        self.store.record(observation(), "key")
        reopened = SqliteNotebook(self.path)
        self.assertEqual(reopened.get("one").observation, observation())
        self.assertEqual(
            reopened.record(observation(), "key").kind, RecordKind.REPLAYED
        )
        self.assertIsNotNone(reopened.peek_pending())

    def test_outbox_failure_rolls_back_reading_and_key(self):
        with self.store.connection(write=True) as connection:
            connection.execute(
                "CREATE TRIGGER reject_outbox BEFORE INSERT ON outbox "
                "BEGIN SELECT RAISE(ABORT,'test failure'); END"
            )
        with self.assertRaises(StoreUnavailable):
            self.store.record(observation(), "key")
        self.assertIsNone(self.store.get("one"))
        with self.store.connection(write=True) as connection:
            connection.execute("DROP TRIGGER reject_outbox")
        self.assertEqual(
            self.store.record(observation(), "key").kind, RecordKind.CREATED
        )

    def test_concurrent_same_key_creates_one_reading_and_event(self):
        with ThreadPoolExecutor(max_workers=6) as executor:
            results = list(
                executor.map(
                    lambda _: self.store.record(observation(), "key").kind, range(8)
                )
            )
        self.assertEqual(results.count(RecordKind.CREATED), 1)
        self.assertEqual(results.count(RecordKind.REPLAYED), 7)
        with self.store.connection() as connection:
            self.assertEqual(
                connection.execute("SELECT count(*) FROM outbox").fetchone()[0], 1
            )

    def test_ack_failure_then_restart_reuses_persisted_sink_effect(self):
        self.store.record(observation(), "key")
        queue = Mock()
        queue.peek_pending.side_effect = self.store.peek_pending
        queue.acknowledge.side_effect = OSError("Lost ack")
        self.assertEqual(
            process_receipt(queue, self.sink).kind, DeliveryKind.ACK_UNCONFIRMED
        )
        reopened = SqliteNotebook(self.path)
        self.assertEqual(
            process_receipt(reopened, SqliteReceiptSink(reopened)).kind,
            DeliveryKind.ACKNOWLEDGED,
        )
        with reopened.connection() as connection:
            self.assertEqual(
                connection.execute("SELECT count(*) FROM previews").fetchone()[0], 1
            )

    def test_concurrent_processing_reuses_one_persisted_preview(self):
        self.store.record(observation(), "key")
        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(
                executor.map(
                    lambda _: process_receipt(self.store, self.sink).kind, range(8)
                )
            )
        self.assertIn(DeliveryKind.ACKNOWLEDGED, results)
        self.assertTrue(
            all(
                kind in (DeliveryKind.ACKNOWLEDGED, DeliveryKind.EMPTY)
                for kind in results
            )
        )
        with self.store.connection() as connection:
            self.assertEqual(
                connection.execute("SELECT count(*) FROM previews").fetchone()[0], 1
            )

    def test_unknown_future_schema_is_rejected_without_downgrade(self):
        with self.store.connection(write=True) as connection:
            connection.execute("PRAGMA user_version=99")
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            SqliteNotebook(self.path)
        with sqlite3.connect(self.path) as connection:
            self.assertEqual(
                connection.execute("PRAGMA user_version").fetchone()[0], 99
            )


class PolicyBoundaryTests(unittest.TestCase):
    def test_invalid_request_key_does_not_call_writer(self):
        writer = Mock()
        with self.assertRaises(ValueError):
            record_observation(observation(), " ", writer)
        writer.record.assert_not_called()

    def test_empty_queue_does_not_call_sink(self):
        queue = Mock()
        queue.peek_pending.return_value = None
        sink = Mock()
        self.assertEqual(process_receipt(queue, sink).kind, DeliveryKind.EMPTY)
        sink.deliver.assert_not_called()
        queue.acknowledge.assert_not_called()

    def test_failed_queue_does_not_call_sink(self):
        queue = Mock()
        queue.peek_pending.side_effect = OSError("Offline")
        sink = Mock()
        self.assertEqual(
            process_receipt(queue, sink).kind, DeliveryKind.QUEUE_UNCONFIRMED
        )
        sink.deliver.assert_not_called()

    def test_sink_failure_does_not_acknowledge(self):
        store = MemoryNotebook()
        store.record(observation(), "key")
        sink = Mock()
        sink.deliver.side_effect = OSError("Offline")
        self.assertEqual(
            process_receipt(store, sink).kind, DeliveryKind.SINK_UNCONFIRMED
        )
        self.assertIsNotNone(store.peek_pending())

    def test_read_only_fixture_exports_without_write_methods(self):
        class Reader:
            def page(self, after, limit):
                return Page((StoredReading(1, observation()),), None)

        artifact, _ = export_page(Reader(), default_exports(), "json", 0, 25)
        self.assertEqual(json.loads(artifact.body)[0]["observation"]["identity"], "one")

    def test_new_exporter_uses_unchanged_export_policy(self):
        store = MemoryNotebook()
        store.record(observation(), "key")
        exporters = Exporters(
            (("test", lambda rows: Artifact(str(len(rows)), "text/plain")),)
        )
        self.assertEqual(export_page(store, exporters, "test", 0, 25)[0].body, "1")

    def test_duplicate_exporter_is_rejected(self):
        def renderer(rows):
            return Artifact("body", "text/plain")

        with self.assertRaises(ValueError):
            Exporters((("same", renderer), ("same", renderer)))


class ApiTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.store = SqliteNotebook(Path(directory.name) / "notebook.sqlite3")
        self.client = TestClient(
            create_app(
                self.store, self.store, self.store, SqliteReceiptSink(self.store)
            )
        )
        self.addCleanup(self.client.close)
        self.payload = {"identity": "one", "station": "North ridge", "kelvin": 281.0}

    def post(self, payload=None, key="key"):
        return self.client.post(
            "/readings",
            json=self.payload if payload is None else payload,
            headers={"Idempotency-Key": key},
        )

    def test_http_intake_replay_conflict_and_location(self):
        created = self.post()
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.headers["location"], "/readings/one")
        self.assertEqual(self.post().status_code, 200)
        self.assertEqual(self.post({**self.payload, "kelvin": 282}).status_code, 409)
        self.assertEqual(
            self.client.get("/readings/one").json()["observation"]["kelvin"], 281
        )

    def test_strict_invalid_inputs_never_write(self):
        for changes in [
            {"kelvin": True},
            {"kelvin": "281"},
            {"kelvin": -1},
            {"station": " "},
            {"identity": "a/b"},
            {"unexpected": 1},
        ]:
            with self.subTest(changes=changes):
                self.assertEqual(
                    self.post({**self.payload, **changes}).status_code, 422
                )
        self.assertEqual(self.client.get("/readings").json()["readings"], [])

    def test_missing_or_bad_idempotency_header_is_rejected(self):
        self.assertEqual(
            self.client.post("/readings", json=self.payload).status_code, 422
        )
        self.assertEqual(self.post(key=" ").status_code, 422)

    def test_missing_reading_returns_404(self):
        self.assertEqual(self.client.get("/readings/missing").status_code, 404)

    def test_http_cursor_validation_and_page_shape(self):
        self.post()
        self.post({**self.payload, "identity": "two"}, "two")
        first = self.client.get("/readings?limit=1").json()
        second = self.client.get(
            f"/readings?limit=1&after={first['next_cursor']}"
        ).json()
        self.assertEqual(second["readings"][0]["observation"]["identity"], "two")
        for query in ["limit=0", "limit=101", "after=-1", f"after={2**63}"]:
            self.assertEqual(self.client.get("/readings?" + query).status_code, 422)

    def test_export_selection_and_next_cursor(self):
        self.post()
        self.post({**self.payload, "identity": "two"}, "two")
        response = self.client.get("/export?format=json&limit=1")
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.headers["x-next-cursor"], "1")
        self.assertIn("North ridge", self.client.get("/export?format=text").text)
        self.assertEqual(self.client.get("/export?format=unknown").status_code, 422)

    def test_http_processing_is_separate_from_intake(self):
        self.post()
        self.assertIsNotNone(self.store.peek_pending())
        result = self.client.post("/outbox/process")
        self.assertEqual(result.json()["outcome"], "acknowledged")
        self.assertEqual(self.client.post("/outbox/process").json()["outcome"], "empty")

    def test_storage_unconfirmed_response_is_sanitised_and_correlated(self):
        writer = Mock()
        writer.record.side_effect = StoreUnavailable("Private database path")
        client = TestClient(
            create_app(self.store, writer, self.store, MemoryReceiptSink())
        )
        with self.assertLogs("field_notebook", level="ERROR"):
            response = client.post(
                "/readings", json=self.payload, headers={"Idempotency-Key": "key"}
            )
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("Private database path", response.text)
        self.assertEqual(
            response.json()["request_id"], response.headers["x-request-id"]
        )
        client.close()

    def test_lost_commit_ack_can_be_reconciled_by_same_http_request(self):
        writer = Mock()

        def record_then_lose_ack(reading, key):
            self.store.record(reading, key)
            raise StoreUnavailable("Commit acknowledged too late")

        writer.record.side_effect = record_then_lose_ack
        client = TestClient(
            create_app(self.store, writer, self.store, MemoryReceiptSink())
        )
        with self.assertLogs("field_notebook", level="ERROR"):
            first = client.post(
                "/readings", json=self.payload, headers={"Idempotency-Key": "key"}
            )
        self.assertEqual(first.status_code, 503)
        self.assertEqual(self.post().status_code, 200)
        self.assertEqual(len(self.store.page(0, 100).readings), 1)
        client.close()

    def test_openapi_documents_interactive_workflow(self):
        schema = self.client.get("/openapi.json").json()
        self.assertIn("/outbox/process", schema["paths"])
        self.assertEqual(self.client.get("/docs").status_code, 200)
        self.assertEqual(self.client.get("/health").status_code, 200)
        self.assertEqual(self.client.get("/ready").status_code, 200)


class MemoryApiTests(ApiTests):
    def setUp(self):
        self.store = MemoryNotebook()
        self.client = TestClient(
            create_app(self.store, self.store, self.store, MemoryReceiptSink())
        )
        self.addCleanup(self.client.close)
        self.payload = {"identity": "one", "station": "North ridge", "kelvin": 281.0}


if __name__ == "__main__":
    unittest.main()
