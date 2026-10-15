import { test } from "node:test";
import assert from "node:assert/strict";
import { HttpNotebook } from "../.test-build/index.js";
import { PendingSubmission } from "../.test-build/pending.js";

const intent = {
  version: 1,
  endpoint: "https://example.test/api",
  submission: {
    key: "stable-key",
    observation: { identity: "one", station: "Ridge", kelvin: 281 },
  },
};
function storage() {
  let saved = null;
  return {
    load: async () => saved,
    save: async (value) => {
      saved = structuredClone(value);
    },
    clear: async () => {
      saved = null;
    },
  };
}
test("prepare saves before any network call and refuses overwriting unresolved intent", async () => {
  const store = storage();
  const desk = new PendingSubmission(store);
  await desk.prepare(intent);
  assert.deepEqual(await desk.restore(), intent);
  await assert.rejects(
    () => desk.prepare({ ...intent, endpoint: "https://other.test" }),
    /Resolve/,
  );
});
test("restart and failed send preserve the original endpoint, key and content", async () => {
  const store = storage();
  await new PendingSubmission(store).prepare(intent);
  const restarted = new PendingSubmission(store);
  let received;
  await assert.rejects(() =>
    restarted.send({
      record: async (value) => {
        received = value;
        throw new Error("offline");
      },
    }),
  );
  assert.deepEqual(received, intent.submission);
  assert.deepEqual(await restarted.restore(), intent);
  assert.equal(
    await restarted.send({
      record: async (value) => {
        assert.deepEqual(value, received);
        return "replayed";
      },
    }),
    "replayed",
  );
  assert.equal(await restarted.restore(), null);
});
test("failed initial persistence prevents preparation and sends nothing", async () => {
  const desk = new PendingSubmission({
    ...storage(),
    save: async () => {
      throw new Error("disk");
    },
  });
  await assert.rejects(() => desk.prepare(intent), /disk/);
});
test("failed clear after acknowledgement retains intent for exact replay", async () => {
  const store = storage();
  const desk = new PendingSubmission({
    ...store,
    clear: async () => {
      throw new Error("disk");
    },
  });
  await desk.prepare(intent);
  await assert.rejects(
    () => desk.send({ record: async () => "created" }),
    /disk/,
  );
  assert.deepEqual(await desk.restore(), intent);
});
test("HTTP adapter sends exact key/content and only accepts matching acknowledgement", async () => {
  let captured;
  const client = new HttpNotebook(
    "https://example.test/api",
    async (url, init) => {
      captured = { url, init };
      return Response.json(
        {
          outcome: "created",
          reading: { sequence: 1, observation: intent.submission.observation },
        },
        { status: 201 },
      );
    },
  );
  assert.equal(await client.record(intent.submission), "created");
  assert.equal(captured.url, "https://example.test/api/readings");
  assert.equal(captured.init.headers["Idempotency-Key"], "stable-key");
  assert.deepEqual(
    JSON.parse(captured.init.body),
    intent.submission.observation,
  );
  const wrong = new HttpNotebook("/api", async () =>
    Response.json({
      outcome: "created",
      reading: {
        sequence: 1,
        observation: { ...intent.submission.observation, identity: "other" },
      },
    }),
  );
  await assert.rejects(() => wrong.record(intent.submission), /did not match/);
});
test("unknown outcomes, malformed pages and conflicts are not reported as success", async () => {
  const unknown = new HttpNotebook("/api", async () =>
    Response.json({
      outcome: "maybe",
      reading: { sequence: 1, observation: intent.submission.observation },
    }),
  );
  await assert.rejects(
    () => unknown.record(intent.submission),
    /did not match/,
  );
  const malformed = new HttpNotebook("/api", async () =>
    Response.json({ readings: [], next_cursor: -1 }),
  );
  await assert.rejects(() => malformed.page(0), /invalid page/);
  const conflict = new HttpNotebook(
    "/api",
    async () => new Response("{}", { status: 409 }),
  );
  await assert.rejects(
    () => conflict.record(intent.submission),
    /already in use/,
  );
});

test("overlapping sends cannot clear a later intent or perform parallel deliveries", async () => {
  const store = storage();
  const desk = new PendingSubmission(store);
  await desk.prepare(intent);
  let release;
  const waiting = new Promise((resolve) => {
    release = resolve;
  });
  const sending = desk.send({
    record: async () => {
      await waiting;
      return "created";
    },
  });
  await assert.rejects(
    () => desk.send({ record: async () => "created" }),
    /in progress/,
  );
  await assert.rejects(() => desk.prepare(intent), /in progress/);
  release();
  await sending;
  assert.equal(await desk.restore(), null);
});
