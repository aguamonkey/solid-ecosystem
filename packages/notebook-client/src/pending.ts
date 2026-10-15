import type { NotebookWriter, Submission } from "./index";

export interface SavedIntent {
  version: 1;
  endpoint: string;
  submission: Submission;
}
export interface IntentStore {
  load(): Promise<SavedIntent | null>;
  save(intent: SavedIntent): Promise<void>;
  clear(): Promise<void>;
}

// Saving intent precedes the network call. Clearing follows a matching acknowledgement.
// A failed save never sends; a failed clear leaves the original intent retryable.
export class PendingSubmission {
  private active = false;
  constructor(private readonly store: IntentStore) {}

  restore(): Promise<SavedIntent | null> {
    return this.store.load();
  }

  async prepare(intent: SavedIntent): Promise<void> {
    if (this.active)
      throw new Error("A submission operation is already in progress.");
    this.active = true;
    try {
      if (await this.store.load())
        throw new Error("Resolve the saved submission first.");
      await this.store.save(intent);
    } finally {
      this.active = false;
    }
  }

  async send(writer: NotebookWriter): Promise<"created" | "replayed"> {
    if (this.active)
      throw new Error("A submission operation is already in progress.");
    this.active = true;
    try {
      const intent = await this.store.load();
      if (!intent) throw new Error("No saved submission to send.");
      const outcome = await writer.record(intent.submission);
      await this.store.clear();
      return outcome;
    } finally {
      this.active = false;
    }
  }
}
