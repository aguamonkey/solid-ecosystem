# Shared TypeScript client

Both web and mobile import `@field-notebook/client`; neither imports code from the other's app directory.
This workspace contains domain DTOs, capability interfaces, runtime HTTP decoding, acknowledgement matching and input validation.

`@field-notebook/client/pending` adds a single-intent persistence policy through an `IntentStore` port. The mobile app supplies AsyncStorage. The web app retains its original tab-local submission workflow; sharing a transport does not imply sharing every client behaviour.

Tests compile this package and exercise retry identity, failed persistence, restart, failed clearing, malformed responses and conflicts. Temporary output lives in ignored `.test-build`.
The shared contract is about observable behaviour, not a requirement for iOS and Android to have identical UI or storage.
