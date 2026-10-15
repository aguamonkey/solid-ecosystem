# Field Notebook mobile · iOS + Android

An Expo / React Native TypeScript client for the same Python API as the web dashboard. Swift remains in its standalone SOLID workbook.

## Run

From the repository root, `make setup PYTHON=python3.12` installs the Python environment and all npm workspaces. Then:

```sh
make dev
# In another terminal:
make mobile
```

Use the Expo terminal's `i` / `a` actions for an iOS simulator / Android emulator, or use the matching Expo Go version on a phone. Local simulator/emulator tools must be installed separately; `make mobile` does not install Xcode or Android Studio.

The default API URL is `http://127.0.0.1:5180/api` for the iOS simulator and `http://10.0.2.2:5180/api` for the Android emulator. These address the development stack through the web proxy. With Docker, use port 8080 instead. You can edit the URL in the app before preparing a submission, or set `EXPO_PUBLIC_API_URL` before starting Expo. This URL is public build configuration, never a secret.

## Physical devices

Loopback on a phone means the phone itself. Prefer a hosted HTTPS API when available.
For a trusted local network demo, run `npm run dev --workspace field-notebook-web -- --host 0.0.0.0` with the API running on 8010; set the app's API URL to `http://YOUR_MAC_LAN_IP:5180/api`. Both devices need network access to that Mac. This exposes the unauthenticated development proxy on the LAN; stop it afterwards. The normal `make dev` binds loopback.

## Implemented

- Browse confirmed observations, refresh, and follow the next-page cursor.
- Submit an observation using the shared HTTP adapter and runtime response validation.
- Save one pending intent with AsyncStorage BEFORE sending: destination, request key and original values.
- Restore that intent after app restart; retry it manually without generating a new key.
- Clear it only after a matching acknowledgement. If clearing fails, exact replay can recover.
- Explicitly forget local intent after a warning; forgetting cannot undo a server write.

This is one saved pending submission, not an offline batch queue or background sync engine. Loaded ledger pages are not cached across app termination. Corrupt/unreadable saved work blocks new submissions instead of silently deleting it. AsyncStorage is unencrypted; this demo stores observations and request intent, not credentials.

## Study the boundaries

`App.tsx` renders and coordinates user actions. `src/storage.ts` implements the storage port. `packages/notebook-client` owns shared HTTP and acknowledgement rules; its `PendingSubmission` policy owns save/send/clear order without importing React Native or AsyncStorage.

```sh
npm run check:mobile
npm run test:client
npm run export:check --workspace @field-notebook/mobile
```

Exports verify bundling for iOS and Android; they do not prove installation, signing or device behaviour. See root validation notes for what was actually exercised.
