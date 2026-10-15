# Dependency verification

The mobile client starts from the official Expo blank TypeScript template (SDK 57), with SDK-compatible modules installed using `expo install`. Run version checks from `apps/mobile` with `npx expo install --check` and `npx expo-doctor`.

The root lockfile makes the checked dependency tree reproducible. Native exports do not replace simulator/device tests or signed release builds.

At initial setup, `npm audit` reports 22 advisory entries through Expo/React Native's transitive dependency tree, including `braces`, `node-forge` and `uuid`. A normal `npm audit fix` does not resolve them; npm proposes major downgrades of Expo/React Native with `--force`. Those downgrades were not applied because they conflict with the current supported template. These advisories remain unresolved; no claim of an audit-clean mobile toolchain is made.

Review upstream patches before release/distribution. Do not add untested transitive overrides or disable audit reporting to conceal them. The existing web-only dependency tree previously audited clean; the expanded mobile toolchain changes that result.
