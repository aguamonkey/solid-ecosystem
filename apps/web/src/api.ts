export interface Observation {
  identity: string;
  station: string;
  kelvin: number;
}
export interface Reading {
  sequence: number;
  observation: Observation;
}
export interface Page {
  readings: Reading[];
  next_cursor: number | null;
}
export interface Submission {
  observation: Observation;
  key: string;
}

function object(value: unknown): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error("The API returned an unexpected response.");
  }
  return value as Record<string, unknown>;
}
function reading(value: unknown): Reading {
  const row = object(value);
  const observation = object(row.observation);
  if (
    !Number.isSafeInteger(row.sequence) ||
    (row.sequence as number) < 1 ||
    typeof observation.identity !== "string" ||
    typeof observation.station !== "string" ||
    typeof observation.kelvin !== "number" ||
    !Number.isFinite(observation.kelvin) ||
    observation.kelvin < 0
  ) {
    throw new Error("The API returned an invalid observation.");
  }
  return {
    sequence: row.sequence as number,
    observation: observation as unknown as Observation,
  };
}

// The UI depends on capabilities; the HTTP adapter owns transport and decoding.
export interface NotebookReader {
  page(after: number): Promise<Page>;
}
export interface NotebookWriter {
  record(submission: Submission): Promise<"created" | "replayed">;
}
export interface ReceiptProcessor {
  process(): Promise<string>;
}

export class HttpNotebook
  implements NotebookReader, NotebookWriter, ReceiptProcessor
{
  constructor(private readonly base = "/api") {}

  private async request(path: string, init?: RequestInit): Promise<unknown> {
    const response = await fetch(this.base + path, {
      ...init,
      signal: AbortSignal.timeout(10000),
    });
    if (!response.ok) {
      if (response.status === 409)
        throw new Error(
          "This identity or request key is already in use. Resolve the conflict before starting another submission.",
        );
      if (response.status === 422)
        throw new Error(
          "The API rejected these values. Check the observation before starting another submission.",
        );
      throw new Error(
        `API returned ${response.status}. The result may be unconfirmed; retry the same submission.`,
      );
    }
    return response.json();
  }

  async page(after: number): Promise<Page> {
    const body = object(
      await this.request(`/readings?after=${after}&limit=25`),
    );
    if (
      !Array.isArray(body.readings) ||
      !(
        body.next_cursor === null ||
        (Number.isSafeInteger(body.next_cursor) &&
          (body.next_cursor as number) > after)
      )
    ) {
      throw new Error("The API returned an invalid page.");
    }
    return {
      readings: body.readings.map(reading),
      next_cursor: body.next_cursor as number | null,
    };
  }

  async record(submission: Submission): Promise<"created" | "replayed"> {
    const body = object(
      await this.request("/readings", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": submission.key,
        },
        body: JSON.stringify(submission.observation),
      }),
    );
    const confirmed = reading(body.reading);
    const sent = submission.observation;
    if (
      (body.outcome !== "created" && body.outcome !== "replayed") ||
      confirmed.observation.identity !== sent.identity ||
      confirmed.observation.station !== sent.station ||
      confirmed.observation.kelvin !== sent.kelvin
    ) {
      throw new Error(
        "The acknowledgement did not match this submission. Retry the same request.",
      );
    }
    return body.outcome;
  }

  async process(): Promise<string> {
    const body = object(
      await this.request("/outbox/process", { method: "POST" }),
    );
    if (body.outcome === "empty") return "No pending receipts.";
    if (body.outcome === "acknowledged")
      return `Receipt acknowledged for ${String(body.event_id)}.`;
    throw new Error(
      "Receipt processing is unconfirmed. Another tick checks the next pending event.",
    );
  }
}
