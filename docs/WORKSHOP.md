# Teach a safe retry in 20 minutes

This is a facilitator plan and recording script, not evidence that a session has already been delivered. Installation happens beforehand. For individual study, use the [hands-on lesson](LEARNING_GUIDE.md).

Audience: developers familiar with basic HTTP/JSON. Outcome: participants can distinguish an unconfirmed submission from a rejected one, preserve retry intent, and identify a testable design boundary.

## Prepare

- Start a local stack using the root README. Confirm a fresh submission and API docs work before the audience joins.
- Prepare fresh identities for the recording and a spare take. Keep the original key/body visible for the replay experiment.
- Open the [architecture](ARCHITECTURE.md), [ports](../services/api/src/field_notebook/ports.py), [export policy](../services/api/src/field_notebook/exports.py) and [lost-acknowledgement test](../apps/web/tests/notebook.spec.ts).
- Rehearse API stop/start or browser request blocking using [the recording checklist](RECORDING.md). Keep the browser tab open. Have the existing [dashboard screenshot](images/dashboard.png) available if the environment fails; label it as a screenshot rather than presenting it as a live result.
- Offer the written [lesson](LEARNING_GUIDE.md) and [troubleshooting guide](TROUBLESHOOTING.md) so participation does not depend on hearing narration or reading small terminal text. Add corrected captions and a transcript when publishing a video.

## Run the session

| Time | Demonstrate or ask | Suggested explanation | Check for understanding |
| --- | --- | --- | --- |
| 0–2 min | “You tapped submit. The connection dropped. Was it saved?” | “A missing response leaves us uncertain. We need a way to try again without changing what we asked for.” | Ask for two possible server histories before revealing them. |
| 2–5 min | Submit one observation; find its ledger row. | “The UI displays Celsius. The API stores Kelvin. We can point to what each layer owns.” | Ask where a storage change belongs and where a display change belongs. |
| 5–9 min | Use lesson section 2: POST, exact replay, changed body. | “The observation identity names the record. The key binds an attempt to its original content.” | Have participants predict 201, 200 and 409 before each request. |
| 9–12 min | Cause an API outage, restore it, retry the saved browser intent. | “This shows recovery from an unavailable API. The browser test covers the separate case where storage succeeds and the response is lost.” | Ask why the same key AND content must be retained. |
| 12–16 min | Trace policy → ports → adapters; show shared contract tests. | “The interfaces describe the capabilities; the tests check the promises. SQLite and memory differ in restart durability.” | Ask why having the same method names alone is insufficient. |
| 16–19 min | Present the exporter exercise; invite a proposed solution. | “A renderer can be added through registration. The export policy needs a pager, not the whole database interface.” | Ask what changes and what stays untouched. Show the reference solution only after a prediction. |
| 19–20 min | Ask for a teach-back and name the limits. | “This demo has no background sync promise, hosted deployment or arbitrary external exactly-once guarantee.” | Ask each learner to name one guarantee and one explicit limit. |

For a two-minute portfolio recording, use the opening question, confirmed submission, outage/retry, and one code/test boundary. Link the full written lesson instead of rushing through all five principles. Use the [GIF checklist](RECORDING.md) for the shorter silent demonstration.

## Adapt to the audience

For someone new to backend work, stay with the two server histories and three HTTP outcomes before introducing SOLID terminology. For an experienced engineer, discuss the transaction boundary, receipt acknowledgement failure and why a singleton SQLite deployment is a deliberate limit. For a non-technical stakeholder, explain the user-facing uncertainty and recovery without opening the protocol definitions.

If a learner gets a different result, ask what they expected, what they observed, and which request/environment they used. Reproduce it before proposing a reset or architecture change. The [troubleshooting guide](TROUBLESHOOTING.md) gives a concrete route.

## Collect evidence and improve the lesson

No learner-completion rates, workshop attendance or adoption results are claimed here. Use this blank template AFTER a real session or an independent quick-start trial. Ask permission before quoting or identifying participants publicly.

```text
Date and commit:
Format: independent trial / live workshop / recorded lesson
Audience background and anonymised participant count:
Environment and setup time:
First observation completed without help? Evidence:
Replay and conflict correctly predicted? Evidence:
Lost-response explanation understood? Evidence:
Exporter exercise attempted/completed? Evidence:
Where help was needed:
Learner feedback:
Issue or documentation change made in response:
Follow-up outcome, if actually measured:
```

Record assistance as well as completion. A download or video view is not evidence that someone completed the lesson. Use recurring setup/support problems to prioritise documentation fixes, then rerun the relevant task with another learner. This connects teaching and developer feedback to concrete improvements in the experience.
