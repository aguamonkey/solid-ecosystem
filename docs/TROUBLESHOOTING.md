# Get unstuck without losing the evidence

Start with what you expected, what happened, and the setup you used. These checks are for a local learning instance. Preserve an unconfirmed key and original content before changing anything. Avoid deleting the data volume or saved mobile intent as a generic fix.

## Setup and connectivity

| Symptom | First check | Next action |
| --- | --- | --- |
| Docker says it cannot connect to its daemon | `docker info` | Start Docker Desktop/Engine, then retry `docker compose up --build -d --wait`. Installing the CLI alone does not start the engine. |
| Compose does not become healthy | `docker compose ps` and `docker compose logs --tail=100 api web` | Inspect the failing service and first useful error. After correcting the cause, rerun the start command. Keep the volume intact. |
| `make setup` rejects Python | `python3 --version` | Select Python 3.11+ explicitly, for example `make setup PYTHON=python3.12`. |
| Dependencies are missing or workspace imports fail | Confirm commands run at the repository root | Use `make setup` for Python and npm dependencies; use root `npm ci` for a JavaScript reinstall. Do not create separate lockfiles in application directories. |
| `make dev` reports an occupied port | Read the named port: API 8010 or web 5180 | Stop your own earlier development stack or choose the Docker route if its port is free. The launcher deliberately does not terminate unrelated processes. |
| Dashboard opens, API requests fail | Visit `/api/health` and `/api/ready` on the SAME origin as the dashboard | For Compose use `http://127.0.0.1:8080`; for native development use `http://127.0.0.1:5180`. Check both services and proxy logs. Health is a liveness response; readiness also attempts a storage read. |
| Mobile cannot reach the API | Check which machine the configured host identifies | iOS simulator: Mac loopback; Android emulator: `10.0.2.2`; physical phone: loopback points to the phone. Follow the [mobile addresses and LAN instructions](../apps/mobile/README.md). Metro connectivity and API connectivity are separate. |

For Compose, these read-only requests help distinguish a missing proxy/service from a storage-read failure:

```sh
curl -i http://127.0.0.1:8080/api/health
curl -i http://127.0.0.1:8080/api/ready
```

For native development, substitute port 5180. A healthy HTTP endpoint does not prove that a previous write failed or succeeded.

## Understand the submission result

| Result | Meaning | Recovery or investigation |
| --- | --- | --- |
| 201, `created` | A new reading was accepted | Inspect that identity in the ledger. |
| 200, `replayed` | The accepted intent was replayed | The original stored reading is returned. This is successful recovery. |
| 409 | The identity or key conflicts with an existing binding | Compare the original identity, key and content. For the same intent, restore the original values; for a new observation, use a fresh identity and key. Existing observations cannot be edited through resubmission. |
| 422 | The request violates input rules | Inspect the validation response. Check the header, identity, nonblank station and numeric finite Kelvin >= 0 against the [contract](../contracts/README.md). |
| Transport failure or 5xx | The write may be unconfirmed | Preserve the same key AND content; restore connectivity and use **Retry same submission**. Generating a new key does not resolve uncertainty. |
| Acknowledgement does not match | The client cannot confirm its intent from that response | Preserve the pending intent and investigate destination, response shape and original identity/content. A response alone is insufficient if it describes another observation. |

If a reading appears missing, look up its exact identity through `GET /api/readings/{identity}`. The ledger is paged; an item outside the loaded page is not necessarily absent. A 404 from one configured destination does not establish what happened at a different destination.

Web intent survives only while the tab remains open. Reloading to “fix” a failed send can discard it. Mobile persists one intent, and storage failures can prevent clearing or preparing work. Read the [mobile implementation limits](../apps/mobile/README.md#implemented) before forgetting saved intent; forgetting does not undo server writes.

Receipt processing is separate from recording. **Process one receipt** handles one pending local preview and may concern an older reading. No email is sent. Repeated ticks can process different events; they are not retries of a named submission.

## Share a useful reproduction

For an issue or support handoff, provide:

1. The commit (`git rev-parse --short HEAD`), OS, client and Docker/native setup.
2. Minimal reproduction steps, expected result and actual result.
3. HTTP method, path, status and response, using synthetic sample values. If investigating replay, keep the relationship between the synthetic original key and content clear.
4. The response `X-Request-ID` when available and the matching server log context. Storage-unconfirmed responses also include a `request_id`.
5. Whether the symptom survives a same-intent retry, a read of the exact identity, or an application restart. State which you actually tried.

Remove credentials, private data and unrelated logs before sharing. Never use real customer or employer data to demonstrate this project. An unresolved report with precise evidence is more useful than a confident diagnosis without a reproduction.
