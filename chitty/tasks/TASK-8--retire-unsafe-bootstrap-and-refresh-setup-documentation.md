---
title: Retire unsafe bootstrap and refresh setup documentation
status: todo
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

## History

- 2026-08-04 → todo
