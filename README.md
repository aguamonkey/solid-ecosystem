# Field Notebook · SOLID Ecosystem

A cross-platform SOLID learning system: one example across web, API and mobile, with walkthroughs and tests.

Follow one observation from capture to durable storage, then explore what happens when the response never reaches the client. The lessons connect each design principle to a concrete change, failure or test.

**Status:** Implemented: web dashboard, FastAPI API with SQLite, React Native/Expo app, Docker setup and GitHub Actions CI. Planned: Rust collector and hosted demo. Native device testing is partial: an iOS simulator launch and iOS/Android bundles were checked; full native submission/restart/retry workflows and Android device execution remain unverified. See [verification scope](docs/VERIFICATION.md).

**Video walkthrough:** TODO — record the [5–7 minute script](docs/VIDEO_SCRIPT.md) with narration. The [GIF recording checklist](docs/RECORDING.md) covers submit → ledger → retry; the GIF is not recorded yet.

## Quick start

From this repository's root, choose one:

```sh
# Docker Engine/Desktop with Compose v2
docker compose up --build -d --wait
# Dashboard: http://127.0.0.1:8080 · API docs: http://127.0.0.1:8080/api/docs
```

```sh
# Python 3.11+, Node 22.13+ (22 LTS) or 24.3+ (24 LTS), npm and make
make setup && make dev
# Dashboard: http://127.0.0.1:5180 · API docs: http://127.0.0.1:5180/api/docs
```

If macOS selects an older Python, use `make setup PYTHON=python3.12 && make dev`. See the run sections below for persistence, shutdown and mobile setup.

## Choose your route

| Your goal | Start here | What you'll leave with |
| --- | --- | --- |
| Try the application | [First connected journey](docs/WALKTHROUGH.md) | A recorded observation, a replay and a recovered submission |
| Learn the design | [Hands-on lesson](docs/LEARNING_GUIDE.md) | Predictions, observable results and a small exporter exercise with a reference solution |
| Teach the system | [Workshop guide](docs/WORKSHOP.md) | A timed demonstration, discussion prompts and checks for understanding |
| Integrate or diagnose | [API contract](contracts/README.md) and [troubleshooting](docs/TROUBLESHOOTING.md) | Request rules, symptom-based checks and useful diagnostic evidence |
| Review the engineering | [Architecture](docs/ARCHITECTURE.md) and [verification](docs/VERIFICATION.md) | Code boundaries, trade-offs and the limits of the testing evidence |

The hands-on lesson assumes basic HTTP/JSON knowledge and some Python or TypeScript. You do not need prior SOLID knowledge. Timings are estimates and exclude installation.

## What you'll learn

- **Single responsibility (SRP):** follow [HTTP mapping](services/api/src/field_notebook/http.py), [domain validation](services/api/src/field_notebook/domain.py), [policy](services/api/src/field_notebook/policy.py) and [SQLite storage](services/api/src/field_notebook/sqlite_store.py) as separate responsibilities.
- **Open/closed (OCP):** add a renderer to the captured registry in [exports.py](services/api/src/field_notebook/exports.py) without changing `export_page`; see `test_new_exporter_uses_unchanged_export_policy` in the [backend tests](services/api/tests/test_backend.py).
- **Liskov substitution (LSP):** compare [memory](services/api/src/field_notebook/memory.py) and [SQLite](services/api/src/field_notebook/sqlite_store.py) adapters against the same `StoreContract` in the [backend tests](services/api/tests/test_backend.py).
- **Interface segregation (ISP):** inspect the focused `ReadingWriter`, `ReadingLookup`, `ReadingPager`, `ReceiptQueue` and `ReceiptSink` protocols in [ports.py](services/api/src/field_notebook/ports.py); export policy needs only a pager.
- **Dependency inversion (DIP):** [policy.py](services/api/src/field_notebook/policy.py) accepts protocols, while [the executable](services/api/src/field_notebook/__main__.py) wires concrete adapters. On mobile, [pending-submission policy](packages/notebook-client/src/pending.ts) accepts a persistence port; the platform supplies storage.

Start with the [guided walkthrough](docs/WALKTHROUGH.md), then use the [architecture and evidence map](docs/ARCHITECTURE.md) to explain the boundaries.

**Language workbooks:** [Swift](https://github.com/aguamonkey/SOLID-Principles-with-Swift) · [TypeScript](https://github.com/aguamonkey/solid-principles-typescript) · [Python](https://github.com/aguamonkey/solid-principles-python) · [Rust](https://github.com/aguamonkey/solid-principles-rust).

## At a glance

| Component | Technology | Status |
| --- | --- | --- |
| [Dashboard](apps/web) | TypeScript | Working capture, ledger and receipt controls |
| [API](services/api) | Python / FastAPI / SQLite | Working durable storage and retry contracts |
| [Mobile app](apps/mobile) | React Native / Expo / TypeScript | Capture, ledger and saved pending intent for iOS + Android |
| [Collector](agents/collector) | Rust | Planned; no executable yet |

![Field Notebook dashboard](docs/images/dashboard.png)

The web/API slice is working. The mobile client is implemented with iOS/Android bundling checks; an initial iOS simulator launch was checked, while full device workflows are tracked separately. Rust and public hosting remain later milestones.

## Run with Docker

Requires Docker Engine/Desktop with Compose v2. Start from this repository's root:

```sh
docker compose up --build -d --wait
```

Open **http://127.0.0.1:8080**. API workbench: **http://127.0.0.1:8080/api/docs**.

Stop with `docker compose down`. Records survive in the named `notebook-data` volume. `docker compose down -v` permanently deletes that data.

## Run without Docker

Requires Python 3.11+, Node 22.13+ (22 LTS) or 24.3+ (24 LTS) and npm. On macOS, the system Python may be too old; select an installed current Python explicitly.

```sh
make setup PYTHON=python3.12
make dev
```

Open **http://127.0.0.1:5180**. The API runs on 8010; `/api` is proxied by Vite. Ctrl+C stops both owned processes. Data stays in ignored `data/notebook.sqlite3`. The launcher refuses occupied ports instead of stopping unrelated servers.

Optional demo observations (explicit; never loaded automatically):

```sh
python3 scripts/seed.py
# For Docker, add: --base http://127.0.0.1:8080
```

## Mobile companion

After `make setup`, run `make dev`, then `make mobile` in a second terminal. See the [mobile guide](apps/mobile/README.md) for simulator, Android emulator and physical-device API addresses.
The app saves one pending submission before sending, then restores it after restart for manual retry.

JavaScript dependencies use one root `package-lock.json` with npm workspaces. Run `npm ci` from the repository root; do not install a separate dependency tree inside each application.

## Learn the system

- [Guided walkthrough](docs/WALKTHROUGH.md): submit, inspect, retry, conflict, process, restart.
- [Hands-on lesson](docs/LEARNING_GUIDE.md): predict outcomes, trace boundaries and extend an exporter.
- [Workshop guide](docs/WORKSHOP.md): teach the lesson and gather feedback on where learners get stuck.
- [Troubleshooting](docs/TROUBLESHOOTING.md): diagnose setup, requests and mobile connectivity.
- [Architecture and SOLID map](docs/ARCHITECTURE.md): responsibilities, evidence and trade-offs.
- [API contract](contracts/README.md): shared meanings across languages.
- [Roadmap](docs/ROADMAP.md): mobile, Rust and eventual deployment.

[Verification scope](docs/VERIFICATION.md) distinguishes bundles, tests and native execution.

Dependency compatibility and unresolved upstream advisories are recorded in [dependency notes](docs/DEPENDENCIES.md).

[Repository presentation notes](docs/REPOSITORY.md) include suggested GitHub metadata and the branch review.

## Check your changes

```sh
make check
cd apps/web
npx playwright install chromium
npm test
```

The API suite tests memory/SQLite contracts, transactions, concurrent retries, restart recovery and HTTP responses. Browser tests exercise the real Python API through the web proxy, plus deliberate lost acknowledgements and unavailable reads. Their temporary database is isolated from development data.
Shared client tests cover saved intent and uncertain retries. `make check` also typechecks mobile; CI exports both native bundles.
CI also builds and smoke-checks the Compose stack. OpenAPI generation is checked for drift.

[GitHub Actions](.github/workflows/ci.yml) runs on every push and pull request and supports manual runs. This is continuous integration; automatic deployment to a hosted environment is not configured. The [video script](docs/VIDEO_SCRIPT.md) explains how to present the checks and an optional code change.

## Related study repositories

[Swift](https://github.com/aguamonkey/SOLID-Principles-with-Swift) · [TypeScript](https://github.com/aguamonkey/solid-principles-typescript) · [Python](https://github.com/aguamonkey/solid-principles-python) · [Rust](https://github.com/aguamonkey/solid-principles-rust)

Those repositories teach the principles independently. This repository owns the connected application and runs without their checkouts. Python backend adapted from the MIT-licensed Python workbook; see [architecture](docs/ARCHITECTURE.md) for provenance.
