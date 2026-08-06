---
id: TASK-1.2
title: Consolidate adapter policy into a catalogue
status: In Progress
assignee: []
created_date: '2026-08-04 11:41'
updated_date: '2026-08-06 08:12'
labels:
  - agent-first
  - setup
dependencies:
  - TASK-1.1
references:
  - PROJECT.md
parent_task_id: TASK-1
priority: high
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Replace duplicated adapter metadata with one typed catalogue that drives command selection, discovery, and suggestions while preserving current priorities.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Existing command maps, discovery selectors, and suggestions derive from one catalogue.
- [ ] #2 No current adapter or priority changes without an explicit documented decision.
- [ ] #3 Catalogue declares operation, selector, runner, directory behavior, Docker status, and setup-provider status.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Introduce a typed adapter catalogue as the sole source of policy.
2. Each entry must declare selectors, format/lint operations, ordered PATH/uvx/bunx/native candidates, directory behavior, Docker availability, and supported/deferred/unsupported setup status.
3. Derive command selection, discovery selectors, and suggest recommendations from the catalogue.
4. Retain the current priority/order characterized in TASK-1.1; document and test every intentional change.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
TASK-1.1 characterization is complete; beginning catalogue extraction from the verified inventory.
<!-- SECTION:NOTES:END -->
