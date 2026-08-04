---
id: TASK-1.1
title: Characterize current adapter behavior
status: To Do
assignee: []
created_date: '2026-08-04 11:40'
labels:
  - agent-first
  - setup
dependencies: []
references:
  - IMPLEMENTATION_PLAN.md
parent_task_id: TASK-1
priority: high
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Capture the selectors, command ordering, fallback behavior, directory handling, and special-file behavior of every current adapter before refactoring.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Regression tests cover every current adapter selector and fallback order.
- [ ] #2 The test inventory identifies each adapter’s Docker and setup-provider status.
<!-- AC:END -->
