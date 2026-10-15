# Your first connected journey

1. Start the system using the root README. Open the dashboard.
2. Enter identity `ridge-001`, station `North ridge`, Kelvin `281.25`. Record it. The ledger shows 8.10 °C; the API still stores 281.25 K.
3. Open the API workbench. GET `/readings/ridge-001` confirms that same record.
4. In the workbench, POST the same reading twice with the SAME `Idempotency-Key` (use a fresh identity, e.g. `workbench-001`). The first response is 201; the second is 200. Change Kelvin under that key: 409. Existing history stays unchanged.
5. On the dashboard, process one receipt. This acknowledges one pending preview, not necessarily the last reading you entered. Repeat until empty.
6. Stop and restart the system. Refresh: observations remain. Compose uses a named volume; native development uses ignored `data/notebook.sqlite3`. `docker compose down` preserves the volume; `down -v` deletes it.
7. To explore uncertainty, stop the API, submit a NEW reading in the open dashboard, then restart the API. Click **Retry same submission**. The page retains key/content while open. Closing/reloading the tab loses that draft; durable client outboxes are a later milestone.

## Follow the code

`apps/web/src/main.ts` captures intent → `apps/web/src/api.ts` sends/decodes HTTP → `services/api/src/field_notebook/http.py` maps HTTP → `policy.py` orchestrates → `sqlite_store.py` commits.

Explain what each layer owns before reading every line. Then find the matching boundary test in `services/api/tests/test_backend.py`.

Interview prompt: **The database committed, but the client timed out. What should happen next, and what information must survive to make it safe?**
Answer using a stable key, the original content, durable server bindings, and an explicit unconfirmed state. Do not promise exactly-once delivery across arbitrary external systems.
