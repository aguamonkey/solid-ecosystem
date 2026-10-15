# Rust collector — planned

The [standalone Rust SOLID study project](https://github.com/aguamonkey/solid-principles-rust) will be developed separately after this ecosystem foundation.

This agent's eventual job: import bounded batches of readings, persist immutable submission intent and request keys locally, then deliver to Python after reconnection.
Python remains the authority for accepted observations. The agent must not label an uncertain HTTP result as a failed write or generate a new key on retry.

First milestone: a finite CLI import from a JSON fixture. Then durable pending work, retry classification, restart recovery and controlled concurrency.
No Rust executable, background worker or queue is implemented here yet.
