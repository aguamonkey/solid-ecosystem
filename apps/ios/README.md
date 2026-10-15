# Swift client — planned

The existing Swift study apps remain in [their own repository](https://github.com/aguamonkey/SOLID-Principles-with-Swift).
This directory will contain a new Field Notebook iOS application, not a conversion of every teaching example.

First milestone: browse API observations and submit one observation with a stable request key.
Then: persist submission intent locally, model pending/confirmed/conflict states, recover after app termination, and test retries using URLProtocol fixtures.

Use the shared [API contract](../../contracts/README.md). Run through Xcode separately; Docker does not run an iOS simulator.
This milestone contains no Swift application or Xcode project yet.
