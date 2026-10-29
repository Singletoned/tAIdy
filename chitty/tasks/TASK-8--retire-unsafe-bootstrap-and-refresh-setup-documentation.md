---
title: Retire unsafe bootstrap and refresh setup documentation
status: backlog
labels:
  - agent-first
  - setup
priority: high
depends_on:
  - TASK-7
parent: TASK-1
created: 2026-08-04
---

## Description

Migrate bootstrap users to setup, remove downloaded-script execution from the supported path, and update concise CLI/README guidance.

### References

- PROJECT.md
- RELEASE_READINESS_PLAN.md

## Acceptance Criteria

- [ ] Bootstrap no longer executes downloaded remote scripts.
- [ ] Help and README explain normal-run fallback, setup targets, and incomplete-coverage summaries.
- [ ] Migration behavior and any breaking removal are documented.

## Plan

1. Replace the bootstrap user path with a compatibility message directing users to taidy setup.
2. Remove downloaded-script execution from the supported path; remove the command only in a documented breaking release.
3. Update CLI help and README for normal-run PATH/transient behavior, setup targets, incomplete coverage, and migration.
4. Verify documentation is consistent with the catalogue and configuration contract.

## Notes

Backlog.md ID: TASK-1.7

2026-10-29 review: moved to backlog. Direction is unresolved: `RELEASE_READINESS_PLAN.md` step 1 keeps `bootstrap` with pinned, verified downloads, while `PROJECT.md` and this chain replace it with `taidy setup` and INI config (config support was removed in `87a0ea5`). Decide the direction, then rewrite as smaller tickets.

## History

- 2026-08-04 → todo
- 2026-10-29 todo → backlog
