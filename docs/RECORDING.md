# TODO: record submit → ledger → retry

The GIF has not been recorded. This checkout has no installed npm workspace dependencies or API virtualenv, and the installed Docker CLI cannot reach its daemon, so an interactive capture was not made during the documentation polish. The existing [dashboard screenshot](images/dashboard.png) remains in the README.

## Capture checklist

1. Run `docker compose up --build -d --wait` from the repository root. Open `http://127.0.0.1:8080` in a desktop browser at approximately 1280 × 900. Use a local learning instance and fresh observation identities; do not erase an existing data volume.
2. Start a window/region recording with QuickTime Player or another screen recorder. Frame the capture form and ledger, keeping unrelated windows and personal information out of view.
3. Enter identity `gif-submit-001` (choose a fresh suffix on later takes), station `North ridge`, Kelvin `281.25`. Click **Record observation**. Pause on the confirmed submission status.
4. Show the matching ledger row and **8.10 °C**. Pause for about two seconds, then click **Start a new submission** and enter a fresh identity `gif-retry-001`, station `North ridge`, Kelvin `282`.
5. In a separate terminal, run `docker compose stop api`. Keep the browser tab open and click **Record observation**. Show the unconfirmed status and **Retry same submission** control. Do not reload: web intent survives only in the open tab.
6. Run `docker compose start api`, then `docker compose up -d --wait` to wait for readiness. Back in the browser, click **Retry same submission**. Show confirmation and the new ledger row. This demonstrates recovery from an unavailable API; it does not simulate a lost acknowledgement after commit. That separate case is covered in `apps/web/tests/notebook.spec.ts`.
7. Stop recording and save a trimmed 15–25 second clip to `docs/walkthrough.mov`. Cut terminal switching and readiness waits, while retaining the failure and retry states. With ffmpeg installed, convert it from the repository root:

   ```sh
   ffmpeg -i docs/walkthrough.mov -filter_complex '[0:v]fps=10,scale=960:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse' -loop 0 docs/walkthrough.gif
   ```

8. Review the GIF: submit → confirmed ledger → unconfirmed submission → retry → confirmed ledger. Check that labels remain readable and no private content appears. Aim for under 5 MB; shorten pauses or reduce dimensions if needed.
9. Replace the README's GIF TODO with `![Submit an observation, inspect the ledger, then retry after an API outage](docs/walkthrough.gif)`. Keep the separate video placeholder until a narrated video exists. Commit the GIF, not the raw recording.
10. Run `docker compose down` when finished. The named data volume is retained.

Without Docker, use `make setup && make dev` and `http://127.0.0.1:5180`. For the outage, use browser developer tools to block requests matching `*/api/readings`, submit, then disable that request-blocking rule and retry. Keep the development servers running and the tab open throughout, so a Vite restart cannot reload the page and discard the intent.
