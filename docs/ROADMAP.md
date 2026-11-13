# Build in small connected milestones

1. **Implemented: web → Python → durable observation.** Capture, ledger, exact replay/conflict handling, receipt preview, API contract, launcher and Compose checks.
2. **Current: cross-platform mobile client.** Expo / React Native for iOS and Android. Shared TypeScript HTTP package, capture and paging, one persisted pending submission with manual retry. Native installation and platform-specific testing remain explicit validation steps; bundling is not device execution.
3. **Current: developer education materials.** A hands-on lesson, exporter exercise/reference solution, workshop script and troubleshooting guide are written. Independent learner trials, recorded delivery and measured learning outcomes remain to do. Use [the workshop evidence template](WORKSHOP.md#collect-evidence-and-improve-the-lesson); publish only observed results.
4. **Next: demonstrate and validate the existing slice.** Record submit → ledger → retry with narration, captions and a transcript. Run native submission/restart/retry on iOS and Android, record actual environments/results, and improve setup from independent learner feedback before widening the system.
5. **Hosted demonstration.** Choose access policy/budget; configure HTTPS, persistent storage and backups; deploy API/web and document mobile distribution. Verify the learning journey against the hosted environment.
6. **Later: Rust learning and connected collector.** Keep the standalone Rust workbook independent. Add file import, then durable queued intent, reconnect/retry and restart recovery only when these support a clear additional lesson.
7. **Later: broader cross-client demonstration.** Extend the same-observation journey to Rust batch import and compatibility checks across all implemented clients.

The Swift SOLID repository remains the native Apple-platform study project. This ecosystem deliberately uses TypeScript for web and cross-platform mobile, Python for the backend and Rust for collection. Four components do not require four languages.
