# Build in small connected milestones

1. **Implemented: web → Python → durable observation.** Capture, ledger, exact replay/conflict handling, receipt preview, API contract, launcher and Compose checks.
2. **Current: cross-platform mobile client.** Expo / React Native for iOS and Android. Shared TypeScript HTTP package, capture and paging, one persisted pending submission with manual retry. Native installation and platform-specific testing remain explicit validation steps; bundling is not device execution.
3. **Standalone Rust SOLID workbook.** Return to the separate learning repository before implementing the collector.
4. **Rust connected collector.** File import, then durable queued intent, reconnect/retry and restart recovery.
5. **Cross-client demonstration.** The same observations visible in web/mobile; Rust batch import; controlled outages; compatibility checks across all implemented clients.
6. **Hosted demonstration.** Choose access policy/budget; configure HTTPS, persistent storage and backups; deploy API/web and document mobile/agent distribution.

The Swift SOLID repository remains the native Apple-platform study project. This ecosystem deliberately uses TypeScript for web and cross-platform mobile, Python for the backend and Rust for collection. Four components do not require four languages.
