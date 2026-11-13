# Repository presentation and branches

## Suggested GitHub settings

Set these manually in the repository's About settings. The description and topics were not changed by the documentation polish.

**Description:** A cross-platform SOLID learning system: one example across web, API and mobile, with walkthroughs and tests.

**Topics (8):** `solid-principles`, `software-architecture`, `learning-by-doing`, `typescript`, `fastapi`, `react-native`, `expo`, `docker`.

## Branch review — 13 November 2026

Live GitHub refs were checked before the changes below:

- `develop` pointed to `c4309bd65e1fe3d33f914c6f117261013805a90a` and was the default branch.
- Created local and remote `main` at that exact `develop` commit, then set GitHub's default branch to `main` and verified it through the API.
- `feature/cross-platform-mobile` points to the same commit as `develop`. It is a stale-branch candidate with no unique commits at the time of review. No branch was deleted or rewritten.
- No other remote `feature/*` branches were returned by the live branch listing.

Documentation updates are published on both `main` and `develop`, with the working checkout on `develop`. The retained feature branch stays at its original commit; it has no unique commits relative to `develop`. This note records the synchronization, not a policy that the branches must always stay identical.

CI runs on pushes and pull requests without a branch-name filter, so adopting `main` requires no workflow changes. A hosted demo remains planned.
