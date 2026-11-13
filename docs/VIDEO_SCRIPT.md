# Recording script: what happens when submit gets no response?

Aim for 5–7 minutes. Audience: developers who understand basic HTTP but are new to reliable retries. The goal is to explain one problem, demonstrate the recovery and connect it to a code boundary and test. You do not need to cover all five SOLID principles in one recording.

This is a script to rehearse and adapt, not a claim that the video has been recorded. The [20-minute workshop](WORKSHOP.md) covers a longer session. Use the [capture checklist](RECORDING.md) for outage commands and GIF conversion.

## Before pressing record

1. Start the stack and rehearse the full journey. Use fresh observation identities for each take. Keep the browser tab open throughout the outage/retry sequence.
2. Open the dashboard, [pending policy](../packages/notebook-client/src/pending.ts), [ports](../services/api/src/field_notebook/ports.py), [export policy](../services/api/src/field_notebook/exports.py), [browser test](../apps/web/tests/notebook.spec.ts) and [CI workflow](../.github/workflows/ci.yml). Show only the files you actually use in your version.
3. Install test dependencies and Playwright Chromium before filming. Run the focused browser test once before recording. It uses separate servers and isolated data, not the development database.
4. Open an actual GitHub Actions run for the commit you plan to discuss. Check its conclusion; if it is pending or failing, say so. Do not present a previous green run as verification of a new untested change.
5. Increase editor and terminal text size, hide notifications, and frame only relevant windows. Plan corrected captions and a transcript for the published video.

## 0:00–0:35 — Start with the question

**Show:** the dashboard, with the capture form and ledger visible.

**Say:**

> You submit an observation and the connection drops. Was it saved? There are two possibilities: the request never arrived, or the server saved it and the reply never reached you. From a timeout alone, the app cannot tell which happened. I'll show how this example preserves the original submission so we can retry it safely, then point to the code and test that support that behaviour.

**Understand:** a timeout describes what the client observed. It does not establish the server's final state.

## 0:35–1:15 — Establish the normal result

**Show:** submit a fresh identity, station `North ridge`, Kelvin `281.25`; locate the confirmed row and **8.10 °C** in the ledger.

**Say:**

> This is one example across a TypeScript dashboard, a Python API and an Expo mobile client. The API stores the measurement in Kelvin; the dashboard displays Celsius. Each layer has a specific responsibility. First, here's the normal confirmed result.

**Understand:** the observation identity names an immutable record. The request key binds a submission to its original content. They are separate values, even when an example gives them similar names.

## 1:15–2:20 — Demonstrate recovery

**Show:** start a new submission with a fresh identity. Follow [capture steps 4–6](RECORDING.md#capture-checklist): make the API unavailable, submit, restore connectivity, then click **Retry same submission**. Retain the browser tab. Trim service startup waits.

**Say:**

> Here the API is unavailable, so the client keeps the submission unconfirmed. It retains the request key and the original values. When connectivity returns, retry sends that same intent. If it had already been accepted, the server would return the original reading. If it had never arrived, the server could accept it now.
>
> This live demonstration covers an unavailable API. In a moment I'll show the test for the more subtle case where the database commit succeeds but its reply is lost.

**Understand:** changing the content is a new intent, not a safe retry. This system also protects observation identities: reusing one under a new key conflicts. Do not describe it as a system where every new key automatically creates a duplicate.

## 2:20–3:15 — Show the boundary, not a file tour

**Show:** the `ReadingWriter` protocol in [ports.py](../services/api/src/field_notebook/ports.py), then `record_observation` in [policy.py](../services/api/src/field_notebook/policy.py). Briefly point to the adapter wiring in [the executable](../services/api/src/field_notebook/__main__.py).

**Say:**

> The recording policy asks for a writer through this protocol. It doesn't choose SQLite itself. The executable supplies that adapter. That's the dependency-inversion boundary here: the policy expresses the capability it needs, and adapter selection happens outside it. The transaction and durable retry bindings live in the SQLite implementation. The interface alone doesn't guarantee correctness; we need behaviour tests as well.

**Understand:** dependency inversion makes the policy independent of a particular adapter. It does not itself create idempotency or persistence. Those guarantees come from the adapter implementation and the contract it must satisfy.

## 3:15–4:30 — Show evidence for the difficult case

**Show:** the test named `lost acknowledgement retries identical intent without creating another row` in [notebook.spec.ts](../apps/web/tests/notebook.spec.ts). Highlight `route.fetch()` followed by `route.abort()`, the key/body comparisons, and the final row-count assertion.

**Say:**

> This test sends the request through the real API and lets it commit, then deliberately drops the reply. It checks that the retry uses identical content and the same key, and that only one matching observation exists. That is stronger evidence than simply turning the network off before a request is sent.

With the dependencies installed, run from the repository root:

```sh
npm --prefix apps/web test -- --grep 'lost acknowledgement'
```

**Say after observing the result:** describe the actual outcome. If it fails, inspect the failure rather than claiming the scenario passed. A prepared recording of a completed run is fine if labelled with its commit and environment.

**Understand:** the test checks this system's storage/retry contract. It does not establish exactly-once effects across arbitrary external services.

## 4:30–5:15 — Put CI in context

**Show:** the [workflow](../.github/workflows/ci.yml), then the actual Actions run and matching commit. Point to the two jobs rather than scrolling through installation logs.

**Say:**

> Every push and pull request triggers these checks. One job checks the API, types, shared client, web browser journeys and mobile bundles. The other builds the Docker stack and checks it can retain observations after an API restart. This is continuous integration. There isn't a hosted deployment step yet, so I wouldn't describe it as automatic deployment. Mobile bundle checks also don't replace native device testing.

**Understand:** a green run covers the checks that ran on that commit. It does not establish that every possible workflow or device was tested.

## 5:15–6:00 — Give the viewer something to do

**Show:** the [hands-on lesson](LEARNING_GUIDE.md), particularly the exporter exercise and its reference solution.

**Say:**

> If you want to try this yourself, the repository includes a lesson where you predict created, replayed and conflicting requests, then add an exporter without changing the export policy. Before opening the solution, ask yourself which capability that exporter needs. The troubleshooting guide covers setup and unexpected results.
>
> The key idea is that unconfirmed doesn't mean unsaved. Preserving the original intent lets the client recover without guessing what happened on the server.

## Optional follow-up: make a change and show CI

For a separate 5–10 minute coding lesson, extend the exporter example. That gives the change a teaching purpose: OCP through renderer registration, plus ISP through a pager-only dependency. Keep the first video focused on retries.

1. Work on a new local feature branch. Explain the desired output and acceptance criteria before typing.
2. Add a focused test beside `test_new_exporter_uses_unchanged_export_policy` in [test_backend.py](../services/api/tests/test_backend.py). For example, specify a new renderer's output and media type. Run the test before implementing the renderer and explain the observed failure.
3. Implement and register the renderer in the test's `Exporters` instance; leave `export_page` unchanged. Explain that this is an isolated extension example, not a new format deployed through the default HTTP API.
4. Run the focused test, then `make check`. Push that branch and open a pull request when ready. CI triggers automatically; show the diff and resulting run after it finishes. Cut the wait, retaining the commit identity and honest result.
5. Explain what the assertions establish and what they leave out. A test that only checks that the registry contains a name is weaker than checking useful rendered output.

There is no need to merge a demonstration change or add deployment infrastructure for the recording. If you later wire a new format into the running API, treat that as a real feature with appropriate HTTP checks and documentation.
