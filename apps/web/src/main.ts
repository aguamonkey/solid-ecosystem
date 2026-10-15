import "./style.css";
import {
  HttpNotebook,
  type NotebookReader,
  type NotebookWriter,
  type ReceiptProcessor,
  type Reading,
  type Submission,
} from "./api";

document.querySelector<HTMLDivElement>("#app")!.innerHTML = `
  <header class="masthead"><a class="brand" href="/">FN<span>Field Notebook</span></a><span class="edition">SOLID ECOSYSTEM / FIELD STATION 01</span><a href="/api/docs" target="_blank" rel="noreferrer">API workbench ↗</a></header>
  <main>
    <section class="intro"><div><p class="eyebrow">A record of the world, one observation at a time.</p><h1>Small observations.<br><em>Connected thinking.</em></h1><p class="lede">Capture a temperature. Follow its journey from a browser to a durable record. Explore the engineering behind every acknowledgement.</p></div><aside class="field-mark" aria-label="Field Notebook expedition emblem"><span>FIELD NOTES</span><div class="contours"><b>01</b></div><span>COLLECT / CONNECT / UNDERSTAND</span></aside></section>
    <div class="workspace">
      <section class="capture panel" aria-labelledby="capture-heading"><p class="eyebrow">01 / CAPTURE</p><h2 id="capture-heading">Make an observation.</h2><p>Give each observation its own identity. Confirmed records stay unchanged.</p>
        <form id="capture"><fieldset id="fields"><label for="identity">Observation identity</label><input id="identity" name="identity" pattern="[A-Za-z0-9_-]{1,64}" maxlength="64" placeholder="ridge-001" required><label for="station">Station name</label><input id="station" name="station" maxlength="120" placeholder="North ridge" required><label for="kelvin">Temperature <span>Kelvin</span></label><input id="kelvin" name="kelvin" type="number" min="0" step="any" placeholder="281.25" required><p class="hint">281.25 K is 8.10 °C. The API stores Kelvin.</p></fieldset><button id="submit" type="submit">Record observation <span>↗</span></button></form>
        <p id="submission-status" class="status" role="status" aria-live="polite">Ready when you are.</p><button id="new-submission" class="quiet" hidden>Start a new submission</button><p class="hint">An unconfirmed retry keeps the same identity, values and request key. Keep this tab open; offline persistence comes in a later milestone.</p>
      </section>
      <section class="ledger panel" aria-labelledby="ledger-heading"><div class="section-head"><div><p class="eyebrow">02 / OBSERVE</p><h2 id="ledger-heading">The field ledger.</h2></div><button id="refresh" class="quiet">Refresh ↻</button></div><div class="ledger-info"><span id="count">No records loaded</span><a href="/api/export?format=json&limit=100" target="_blank" rel="noreferrer">Export first 100 ↗</a></div><p id="read-status" class="status" role="status" aria-live="polite">Connecting to the notebook…</p><div id="records" class="records"></div><button id="more" class="quiet" hidden>Load next page</button><div class="receipt"><div><h3>Close the loop.</h3><p>Process one pending receipt preview. No email is sent.</p></div><button id="process" class="quiet">Process one receipt →</button></div><p id="receipt-status" class="status" role="status" aria-live="polite"></p></section>
    </div>
    <section class="journey" aria-label="Ecosystem component status"><p class="eyebrow">ONE SYSTEM / FOUR PERSPECTIVES</p><div><article><span class="component">01 / SWIFT</span><h3>In the field.</h3><p>Native capture and offline sync.</p><small>Planned · not connected yet</small></article><article><span class="component">02 / TYPESCRIPT</span><h3>At the desk.</h3><p>The dashboard you are using.</p><small>Implemented · web client</small></article><article><span class="component">03 / PYTHON</span><h3>In the notebook.</h3><p>Durable records and receipt intent.</p><small>Implemented · API service</small></article><article><span class="component">04 / RUST</span><h3>Between connections.</h3><p>Queued collection and safe retries.</p><small>Planned · collector agent</small></article></div></section>
  </main><footer><span>FIELD NOTEBOOK / A SOLID LEARNING ECOSYSTEM</span><a href="https://github.com/aguamonkey/solid-ecosystem">Read the source ↗</a></footer>
`;

function element<T extends HTMLElement>(id: string): T {
  return document.getElementById(id) as T;
}
function message(id: string, text: string, failed = false): void {
  const target = element(id);
  target.textContent = text;
  target.classList.toggle("failed", failed);
}
function describe(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "The connection failed. Please try again.";
}

function mount(
  reader: NotebookReader,
  writer: NotebookWriter,
  receipts: ReceiptProcessor,
): void {
  let rows: Reading[] = [];
  let cursor: number | null = null;
  let pending: Submission | null = null;
  const submit = element<HTMLButtonElement>("submit");
  const newSubmission = element<HTMLButtonElement>("new-submission");

  function renderRows(): void {
    const container = element("records");
    container.replaceChildren();
    for (const row of rows) {
      const article = document.createElement("article");
      article.className = "record";
      const number = document.createElement("span");
      number.className = "sequence";
      number.textContent = String(row.sequence).padStart(2, "0");
      const details = document.createElement("div");
      const title = document.createElement("h3");
      title.textContent = row.observation.station;
      const identity = document.createElement("p");
      identity.textContent = row.observation.identity;
      details.append(title, identity);
      const temperature = document.createElement("div");
      temperature.className = "temperature";
      const kelvin = document.createElement("strong");
      kelvin.textContent = `${row.observation.kelvin.toFixed(2)} K`;
      const celsius = document.createElement("span");
      celsius.textContent = `${(row.observation.kelvin - 273.15).toFixed(2)} °C`;
      temperature.append(kelvin, celsius);
      article.append(number, details, temperature);
      container.append(article);
    }
    element("count").textContent =
      `${rows.length} observation${rows.length === 1 ? "" : "s"} loaded · oldest first`;
    element("more").hidden = cursor === null;
  }

  async function load(append = false): Promise<void> {
    const refresh = element<HTMLButtonElement>("refresh");
    const more = element<HTMLButtonElement>("more");
    refresh.disabled = more.disabled = true;
    try {
      const page = await reader.page(append ? (cursor ?? 0) : 0);
      rows = append ? [...rows, ...page.readings] : page.readings;
      cursor = page.next_cursor;
      renderRows();
      message(
        "read-status",
        rows.length
          ? "Confirmed observations from the API."
          : "Your ledger is empty. Record your first observation.",
      );
    } catch (error) {
      message(
        "read-status",
        `Could not refresh. ${describe(error)} Previously loaded records remain visible.`,
        true,
      );
    } finally {
      refresh.disabled = more.disabled = false;
    }
  }

  element<HTMLFormElement>("capture").addEventListener(
    "submit",
    async (event) => {
      event.preventDefault();
      if (!pending) {
        const station = element<HTMLInputElement>("station").value;
        if (!station.trim()) {
          message(
            "submission-status",
            "Enter a station name with visible characters.",
            true,
          );
          return;
        }
        pending = {
          key: crypto.randomUUID(),
          observation: {
            identity: element<HTMLInputElement>("identity").value,
            station,
            kelvin: Number(element<HTMLInputElement>("kelvin").value),
          },
        };
      }
      element<HTMLFieldSetElement>("fields").disabled = true;
      submit.disabled = true;
      newSubmission.hidden = true;
      message("submission-status", "Awaiting acknowledgement…");
      try {
        const outcome = await writer.record(pending);
        message(
          "submission-status",
          outcome === "created"
            ? "Observation confirmed and stored."
            : "Earlier submission confirmed. No duplicate was created.",
        );
        submit.textContent = "Confirmed ✓";
        await load();
      } catch (error) {
        message(
          "submission-status",
          `${describe(error)} No new request key has been generated.`,
          true,
        );
        submit.disabled = false;
        submit.textContent = "Retry same submission ↗";
      } finally {
        newSubmission.hidden = false;
      }
    },
  );
  newSubmission.addEventListener("click", () => {
    pending = null;
    element<HTMLFieldSetElement>("fields").disabled = false;
    submit.disabled = false;
    submit.textContent = "Record observation ↗";
    newSubmission.hidden = true;
    message(
      "submission-status",
      "Ready for a new submission. Starting again does not cancel any earlier write.",
    );
  });
  element("refresh").addEventListener("click", () => void load());
  element("more").addEventListener("click", () => void load(true));
  element<HTMLButtonElement>("process").addEventListener("click", async () => {
    const button = element<HTMLButtonElement>("process");
    button.disabled = true;
    try {
      message("receipt-status", await receipts.process());
    } catch (error) {
      message("receipt-status", describe(error), true);
    } finally {
      button.disabled = false;
    }
  });
  void load();
}

const notebook = new HttpNotebook();
mount(notebook, notebook, notebook);
