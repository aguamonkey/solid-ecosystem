# Field Notebook dashboard

TypeScript + Vite, with no UI framework needed for this first slice. `src/api.ts` owns HTTP and runtime response decoding; `src/main.ts` captures intent and renders DOM nodes. User-provided station/identity text is inserted through `textContent`.

Use the root `make dev` to run both web and API. `/api` always goes through a same-origin proxy; no permissive CORS configuration is required.

Unconfirmed submissions keep their original key/content while this tab is open. This is not durable offline sync. Refresh retains previously loaded records on failure; successful Refresh resets to the first page. Load next page follows the server cursor.

`npm run build` checks strict TypeScript and builds static assets. `npm test` uses Playwright and a separate real Python test server/database. See the root README for environment setup.
