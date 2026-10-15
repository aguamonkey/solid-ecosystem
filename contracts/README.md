# Shared contract

`openapi.json` is generated from the Python service. It is checked in CI; it is not a second handwritten source of truth.
With the API environment installed, run `services/api/.venv/bin/python scripts/contract.py --check`.
After deliberate API changes, regenerate without `--check`, review the diff and update affected clients in the same pull request.

The browser uses `/api` through Vite locally and Nginx in Compose. The service itself exposes `/readings`, etc.; the proxy strips `/api`.
Native clients will use the public `/api` base URL. A simulator on this Mac can use `http://127.0.0.1:5180/api`; a physical device cannot use the Mac's loopback address.

## Submission rules

- POST `/api/readings` with `Idempotency-Key`, and `{identity, station, kelvin}` JSON.
- Identity: 1–64 ASCII letters/digits/underscore/hyphen. Key: same character set, 1–128 characters.
- Station: nonblank, at most 120 characters. Kelvin: finite number >= 0, never a boolean/string.
- 201: created; 200: exact replay; 409: conflicting identity/key; 422: invalid input.
- Timeouts, transport failure and 5xx can leave the write unconfirmed. Retry the same key AND content. Changing the key can turn a recoverable retry into a conflict.
- Requests with different keys cannot reuse an existing observation identity. Observations are immutable.
- GET `/api/readings` returns ordered pages (25 default, 100 maximum). Follow `next_cursor`; null means no next page at that moment. This is a live append-only listing, not a frozen snapshot.
- POST `/api/outbox/process` is one worker tick. A second tick may process a different event; it is not replay of a named HTTP operation. Receipts are local previews, not email.

The web client decodes responses at runtime. Shared data formats do not require sharing language-specific domain classes.
