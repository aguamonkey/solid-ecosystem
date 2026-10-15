import AsyncStorage from "@react-native-async-storage/async-storage";
import { validateObservation, type Submission } from "@field-notebook/client";
import type { IntentStore, SavedIntent } from "@field-notebook/client/pending";

const key = "field-notebook.pending.v1";

function decode(raw: string): SavedIntent {
  const value: unknown = JSON.parse(raw);
  if (!value || typeof value !== "object")
    throw new Error("Saved intent is damaged.");
  const intent = value as Partial<SavedIntent>;
  if (
    intent.version !== 1 ||
    typeof intent.endpoint !== "string" ||
    !/^https?:\/\//.test(intent.endpoint) ||
    !intent.submission ||
    typeof intent.submission.key !== "string" ||
    !/^[A-Za-z0-9_-]{1,128}$/.test(intent.submission.key)
  ) {
    throw new Error(
      "Saved intent is invalid. It has been preserved for recovery.",
    );
  }
  const submission = intent.submission as Submission;
  if (
    !submission.observation ||
    typeof submission.observation.identity !== "string" ||
    typeof submission.observation.station !== "string" ||
    typeof submission.observation.kelvin !== "number"
  ) {
    throw new Error(
      "Saved observation is damaged. It has been preserved for recovery.",
    );
  }
  validateObservation(submission.observation);
  return intent as SavedIntent;
}

export const intentStore: IntentStore = {
  async load() {
    const raw = await AsyncStorage.getItem(key);
    return raw === null ? null : decode(raw);
  },
  async save(intent) {
    await AsyncStorage.setItem(key, JSON.stringify(intent));
  },
  async clear() {
    await AsyncStorage.removeItem(key);
  },
};
