# Verification of the cross-platform milestone

- Clean root `npm ci` from the committed workspace lockfile.
- Python: lint, formatting, strict mypy, OpenAPI drift check and 57 backend tests pass.
- Shared TypeScript package: seven tests pass, including recreated policy state, failed persistence, failed acknowledgement cleanup and overlapping-send prevention.
- Web: strict production build and eight Playwright tests pass against the real isolated Python API. Lost server acknowledgements are retried with identical content/key.
- Mobile: strict TypeScript and formatting checks pass; Expo SDK compatibility check passes; Expo Doctor passes all 21 checks.
- Android and iOS production JavaScript/Hermes exports both succeed. These are bundles, not signed application binaries.
- iOS 27 simulator: Expo Go installed and loaded the actual Field Notebook screen. The first-run Expo developer-menu overlay is present. Native form submission, local-draft recovery after termination and accessibility flows have not been exercised end to end.
- Android: bundle verified; emulator/device execution remains to do.

The full native outage/restart workflow is in `WALKTHROUGH.md`. Do not claim that package-level fake-storage tests prove AsyncStorage/device behaviour.

## Local simulator troubleshooting

On this Mac, `expo start --localhost` bound Metro to IPv6 while advertising a `127.0.0.1` bundle URL. For this verification, Metro was restarted with `REACT_NATIVE_PACKAGER_HOSTNAME=127.0.0.1 npx expo start --lan --port 8082`, then opened through `xcrun simctl openurl <device-id> exp://127.0.0.1:8082`. That loaded the iOS bundle. The default documented `make mobile` uses Expo's LAN mode.

The usual `--ios` CLI window-activation step also hit a local macOS AppleScript error. Opening the installed simulator app through `simctl` avoided that optional window-activation step. No platform code was changed to hide these environment issues.

Dependency advisories remain as documented in `DEPENDENCIES.md`. Docker verification runs in GitHub Actions because Docker is not installed on this Mac.
