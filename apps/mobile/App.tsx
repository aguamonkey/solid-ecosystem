import { useEffect, useState } from "react";
import {
  Alert,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";
import { StatusBar } from "expo-status-bar";
import * as Crypto from "expo-crypto";
import {
  HttpNotebook,
  validateObservation,
  type Reading,
} from "@field-notebook/client";
import {
  PendingSubmission,
  type SavedIntent,
} from "@field-notebook/client/pending";
import { intentStore } from "./src/storage";

const desk = new PendingSubmission(intentStore);
const defaultEndpoint =
  process.env.EXPO_PUBLIC_API_URL ??
  (Platform.OS === "android"
    ? "http://10.0.2.2:5180/api"
    : "http://127.0.0.1:5180/api");
const describe = (error: unknown) =>
  error instanceof Error ? error.message : "Connection unavailable.";

function endpoint(value: string): string {
  const url = new URL(value.trim());
  if (
    !["http:", "https:"].includes(url.protocol) ||
    url.username ||
    url.password ||
    url.search ||
    url.hash
  ) {
    throw new Error(
      "Use an HTTP(S) API base URL without credentials, query or fragment.",
    );
  }
  return url.toString().replace(/\/$/, "");
}

function Notebook() {
  const [base, setBase] = useState(defaultEndpoint);
  const [identity, setIdentity] = useState("");
  const [station, setStation] = useState("");
  const [temperature, setTemperature] = useState("");
  const [saved, setSaved] = useState<SavedIntent | null>(null);
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(false);
  const [rows, setRows] = useState<Reading[]>([]);
  const [cursor, setCursor] = useState<number | null>(null);
  const [ledgerBase, setLedgerBase] = useState<string | null>(null);
  const [notice, setNotice] = useState("Restoring saved work…");
  const [readNotice, setReadNotice] = useState(
    "Refresh to read confirmed observations.",
  );

  useEffect(() => {
    let active = true;
    void desk
      .restore()
      .then((intent) => {
        if (!active) return;
        setSaved(intent);
        if (intent) {
          setBase(intent.endpoint);
          setIdentity(intent.submission.observation.identity);
          setStation(intent.submission.observation.station);
          setTemperature(String(intent.submission.observation.kelvin));
        }
        setNotice(
          intent
            ? "Saved submission restored. Retry its original request."
            : "Ready for your next observation.",
        );
        setReady(true);
      })
      .catch((error: unknown) => {
        if (active)
          setNotice(`Could not restore saved work. ${describe(error)}`);
      });
    return () => {
      active = false;
    };
  }, []);

  async function refresh(append = false) {
    setLoading(true);
    try {
      const target = endpoint(base);
      const page = await new HttpNotebook(target).page(
        append ? (cursor ?? 0) : 0,
      );
      setRows((previous) =>
        append && ledgerBase === target
          ? [...previous, ...page.readings]
          : page.readings,
      );
      setCursor(page.next_cursor);
      setLedgerBase(target);
      setReadNotice(
        page.readings.length
          ? "Confirmed observations · oldest first."
          : "No observations on this page.",
      );
    } catch (error) {
      setReadNotice(
        `Refresh unavailable. ${describe(error)} Previously loaded records remain visible.`,
      );
    } finally {
      setLoading(false);
    }
  }

  async function submit() {
    setBusy(true);
    try {
      let intent = saved;
      if (!intent) {
        if (!temperature.trim())
          throw new Error("Enter a temperature in Kelvin.");
        const observation = { identity, station, kelvin: Number(temperature) };
        validateObservation(observation);
        intent = {
          version: 1,
          endpoint: endpoint(base),
          submission: { key: Crypto.randomUUID(), observation },
        };
        await desk.prepare(intent);
        setSaved(intent);
      }
      setNotice("Intent saved on this device. Awaiting acknowledgement…");
      const outcome = await desk.send(new HttpNotebook(intent.endpoint));
      setSaved(null);
      setIdentity("");
      setStation("");
      setTemperature("");
      setNotice(
        outcome === "created"
          ? "Observation confirmed and stored."
          : "Earlier submission confirmed. No duplicate created.",
      );
      await refresh();
    } catch (error) {
      // Reload storage even when a storage operation itself failed. Never enable
      // a new request on an assumption that the previous intent disappeared.
      try {
        setSaved(await desk.restore());
      } catch {
        setReady(false);
      }
      setNotice(
        `${describe(error)} Any saved submission keeps its original key and content.`,
      );
    } finally {
      setBusy(false);
    }
  }

  function discard() {
    Alert.alert(
      "Forget saved submission?",
      "This does not cancel a write that may already have reached the API. Check the ledger before reusing its identity.",
      [
        { text: "Keep submission", style: "cancel" },
        {
          text: "Forget on this device",
          style: "destructive",
          onPress: () => {
            setBusy(true);
            void intentStore
              .clear()
              .then(() => {
                setSaved(null);
                setNotice(
                  "Local intent forgotten. Earlier server writes are unchanged.",
                );
              })
              .catch((error: unknown) => setNotice(describe(error)))
              .finally(() => setBusy(false));
          },
        },
      ],
    );
  }

  const locked = !ready || busy || saved !== null;
  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar style="dark" />
      <ScrollView
        contentContainerStyle={styles.page}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.masthead}>
          <Text style={styles.brand}>FN / FIELD NOTEBOOK</Text>
          <Text style={styles.edition}>MOBILE 01</Text>
        </View>
        <Text style={styles.eyebrow}>COLLECT / CONNECT / UNDERSTAND</Text>
        <Text style={styles.title}>Out in the field.</Text>
        <Text style={styles.intro}>
          Keep the observation. Recover the connection.
        </Text>
        <View style={styles.panel}>
          <Text style={styles.section}>CONNECTION</Text>
          <Text style={styles.label}>API base URL</Text>
          <TextInput
            accessibilityLabel="API base URL"
            style={styles.input}
            value={base}
            editable={!locked && !loading}
            onChangeText={(value) => {
              setBase(value);
              setRows([]);
              setCursor(null);
              setLedgerBase(null);
              setReadNotice("Connection changed. Refresh this ledger.");
            }}
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="url"
          />
          <Text style={styles.hint}>
            A physical phone needs your computer’s LAN address or a hosted HTTPS
            API.
          </Text>
        </View>
        <View style={styles.panel}>
          <Text style={styles.section}>01 / CAPTURE</Text>
          <Text style={styles.heading}>Make an observation.</Text>
          <Text style={styles.label}>Observation identity</Text>
          <TextInput
            accessibilityLabel="Observation identity"
            style={styles.input}
            value={identity}
            editable={!locked}
            onChangeText={setIdentity}
            autoCapitalize="none"
            autoCorrect={false}
            maxLength={64}
            placeholder="ridge-001"
          />
          <Text style={styles.label}>Station name</Text>
          <TextInput
            accessibilityLabel="Station name"
            style={styles.input}
            value={station}
            editable={!locked}
            onChangeText={setStation}
            placeholder="North ridge"
          />
          <Text style={styles.label}>Temperature / Kelvin</Text>
          <TextInput
            accessibilityLabel="Temperature Kelvin"
            style={styles.input}
            value={temperature}
            editable={!locked}
            onChangeText={setTemperature}
            keyboardType="decimal-pad"
            placeholder="281.25"
          />
          <Pressable
            accessibilityRole="button"
            disabled={!ready || busy || loading}
            onPress={() => void submit()}
            style={[
              styles.button,
              (!ready || busy || loading) && styles.disabled,
            ]}
          >
            <Text style={styles.buttonText}>
              {busy
                ? "Working…"
                : saved
                  ? "Retry saved submission ↗"
                  : "Record observation ↗"}
            </Text>
          </Pressable>
          <Text accessibilityLiveRegion="polite" style={styles.notice}>
            {notice}
          </Text>
          {saved && (
            <>
              <Text style={styles.hint}>
                One pending submission is saved on this device, including its
                destination. Retry manually when connected. No background sync
                runs.
              </Text>
              <Pressable
                accessibilityRole="button"
                disabled={busy}
                onPress={discard}
              >
                <Text style={styles.link}>Forget saved submission…</Text>
              </Pressable>
            </>
          )}
        </View>
        <View style={styles.panel}>
          <Text style={styles.section}>02 / OBSERVE</Text>
          <Text style={styles.heading}>The field ledger.</Text>
          <Pressable
            accessibilityRole="button"
            disabled={loading || busy}
            onPress={() => void refresh()}
            style={styles.secondary}
          >
            <Text>{loading ? "Refreshing…" : "Refresh observations ↻"}</Text>
          </Pressable>
          <Text accessibilityLiveRegion="polite" style={styles.notice}>
            {readNotice}
          </Text>
          {rows.map((row) => (
            <View key={row.observation.identity} style={styles.record}>
              <View style={styles.details}>
                <Text style={styles.station}>{row.observation.station}</Text>
                <Text style={styles.hint}>{row.observation.identity}</Text>
              </View>
              <View>
                <Text style={styles.kelvin}>
                  {row.observation.kelvin.toFixed(2)} K
                </Text>
                <Text style={styles.celsius}>
                  {(row.observation.kelvin - 273.15).toFixed(2)} °C
                </Text>
              </View>
            </View>
          ))}
          {cursor !== null && (
            <Pressable
              accessibilityRole="button"
              disabled={
                loading || busy || ledgerBase !== base.replace(/\/$/, "")
              }
              onPress={() => void refresh(true)}
              style={styles.secondary}
            >
              <Text>Load next page →</Text>
            </Pressable>
          )}
        </View>
        <Text style={styles.footer}>
          A SOLID LEARNING ECOSYSTEM / iOS + ANDROID
        </Text>
      </ScrollView>
    </SafeAreaView>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <Notebook />
    </SafeAreaProvider>
  );
}
const serif = Platform.OS === "ios" ? "Georgia" : "serif";
const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#f2eee4" },
  page: {
    padding: 22,
    paddingBottom: 50,
    maxWidth: 700,
    width: "100%",
    alignSelf: "center",
  },
  masthead: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingBottom: 22,
    borderBottomWidth: 1,
    borderColor: "#d1d0bf",
    marginBottom: 30,
  },
  brand: { fontWeight: "700", fontSize: 13, color: "#26362c" },
  edition: { fontSize: 10, color: "#62695d" },
  eyebrow: {
    color: "#9d4027",
    fontSize: 10,
    letterSpacing: 1.6,
    marginBottom: 12,
  },
  title: { fontFamily: serif, fontSize: 40, color: "#26362c" },
  intro: {
    fontSize: 15,
    lineHeight: 23,
    color: "#62695d",
    marginTop: 12,
    marginBottom: 26,
  },
  panel: {
    backgroundColor: "#faf8f1",
    padding: 22,
    borderWidth: 1,
    borderColor: "#d1d0bf",
    marginBottom: 20,
  },
  section: {
    fontSize: 10,
    letterSpacing: 1.6,
    color: "#9d4027",
    marginBottom: 14,
  },
  heading: {
    fontFamily: serif,
    fontSize: 28,
    color: "#26362c",
    marginBottom: 10,
  },
  label: {
    fontWeight: "600",
    fontSize: 12,
    color: "#26362c",
    marginTop: 14,
    marginBottom: 8,
  },
  input: {
    backgroundColor: "#fffefa",
    padding: 13,
    borderWidth: 1,
    borderColor: "#c6c8b8",
    color: "#26362c",
    fontSize: 14,
  },
  hint: { fontSize: 11, lineHeight: 17, color: "#62695d", marginTop: 9 },
  button: { backgroundColor: "#26362c", padding: 15, marginTop: 24 },
  buttonText: {
    color: "#fffefa",
    textAlign: "center",
    fontSize: 13,
    fontWeight: "600",
  },
  disabled: { opacity: 0.5 },
  notice: { fontSize: 12, lineHeight: 19, color: "#62695d", marginTop: 16 },
  link: {
    fontSize: 12,
    color: "#9d4027",
    textDecorationLine: "underline",
    paddingVertical: 16,
  },
  secondary: {
    padding: 13,
    borderWidth: 1,
    borderColor: "#d1d0bf",
    marginTop: 14,
  },
  record: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: 12,
    paddingVertical: 18,
    borderBottomWidth: 1,
    borderColor: "#d1d0bf",
  },
  details: { flex: 1 },
  station: { fontSize: 15, fontWeight: "600", color: "#26362c" },
  kelvin: { fontFamily: serif, fontSize: 23, color: "#26362c" },
  celsius: { fontSize: 11, textAlign: "right", color: "#62695d", marginTop: 5 },
  footer: {
    fontSize: 10,
    letterSpacing: 1.3,
    lineHeight: 18,
    color: "#62695d",
    marginTop: 8,
  },
});
