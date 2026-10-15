# Field Notebook · SOLID Ecosystem

**One observation. Four perspectives on reliable software.**

A connected learning and portfolio project: record observations, keep durable history, recover from uncertain acknowledgements, and study why the boundaries exist.

| Component | Technology | Status |
| --- | --- | --- |
| [Dashboard](apps/web) | TypeScript | Working capture, ledger and receipt controls |
| [API](services/api) | Python / FastAPI / SQLite | Working durable storage and retry contracts |
| [iOS app](apps/ios) | Swift | Planned; no Xcode app yet |
| [Collector](agents/collector) | Rust | Planned; no executable yet |

![Field Notebook dashboard](docs/images/dashboard.png)

This is the first integrated slice, not yet the finished four-client ecosystem or a hosted service.

## Run with Docker

Requires Docker Engine/Desktop with Compose v2. Start from this repository's root:

```sh
docker compose up --build -d --wait
```

Open **http://127.0.0.1:8080**. API workbench: **http://127.0.0.1:8080/api/docs**.

Stop with `docker compose down`. Records survive in the named `notebook-data` volume. `docker compose down -v` permanently deletes that data.

## Run without Docker

Requires Python 3.11+, Node 22.12+ and npm. On macOS, the system Python may be too old; select an installed current Python explicitly.

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

## Learn the system

- [Guided walkthrough](docs/WALKTHROUGH.md): submit, inspect, retry, conflict, process, restart.
- [Architecture and SOLID map](docs/ARCHITECTURE.md): responsibilities, evidence and trade-offs.
- [API contract](contracts/README.md): shared meanings across languages.
- [Roadmap](docs/ROADMAP.md): Swift, Rust and eventual deployment.

## Check your changes

```sh
make check
cd apps/web
npx playwright install chromium
npm test
```

The API suite tests memory/SQLite contracts, transactions, concurrent retries, restart recovery and HTTP responses. Browser tests exercise the real Python API through the web proxy, plus deliberate lost acknowledgements and unavailable reads. Their temporary database is isolated from development data.
CI also builds and smoke-checks the Compose stack. OpenAPI generation is checked for drift.

## Related study repositories

[Swift](https://github.com/aguamonkey/SOLID-Principles-with-Swift) · [TypeScript](https://github.com/aguamonkey/solid-principles-typescript) · [Python](https://github.com/aguamonkey/solid-principles-python) · [Rust](https://github.com/aguamonkey/solid-principles-rust)

Those repositories teach the principles independently. This repository owns the connected application and runs without their checkouts. Python backend adapted from the MIT-licensed Python workbook; see [architecture](docs/ARCHITECTURE.md) for provenance.
