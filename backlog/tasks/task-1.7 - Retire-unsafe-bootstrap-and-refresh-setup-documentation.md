---
id: TASK-1.7
title: Retire unsafe bootstrap and refresh setup documentation
status: To Do
assignee: []
created_date: "2026-08-04 11:41"
updated_date: "2026-08-06 07:27"
labels:
  - agent-first
  - setup
dependencies:
  - TASK-1.6
references:
  - PROJECT.md
  - RELEASE_READINESS_PLAN.md
parent_task_id: TASK-1
priority: high
ordinal: 8000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Migrate bootstrap users to setup, remove downloaded-script execution from the supported path, and update concise CLI/README guidance.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Bootstrap no longer executes downloaded remote scripts.
- [ ] #2 Help and README explain normal-run fallback, setup targets, and incomplete-coverage summaries.
- [ ] #3 Migration behavior and any breaking removal are documented.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->

1. Replace the bootstrap user path with a compatibility message directing users to taidy setup.
2. Remove downloaded-script execution from the supported path; remove the command only in a documented breaking release.
3. Update CLI help and README for normal-run PATH/transient behavior, setup targets, incomplete coverage, and migration.
4. Verify documentation is consistent with the catalogue and configuration contract.
<!-- SECTION:PLAN:END -->
