---
id: TASK-1.4
title: Define INI setup configuration contract
status: To Do
assignee: []
created_date: '2026-08-04 11:41'
labels:
  - agent-first
  - setup
dependencies:
  - TASK-1.3
references:
  - IMPLEMENTATION_PLAN.md
parent_task_id: TASK-1
priority: high
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Specify and implement the versioned INI schema, user/project paths, opt-in project configuration, precedence, validation, and mutually exclusive installation targets.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Configuration uses configparser and remains compatible with Python 3.8.
- [ ] #2 User configuration is default and project configuration is explicit and opt-in.
- [ ] #3 Malformed or ambiguous configuration produces actionable errors without fallback to another target.
- [ ] #4 Tests cover schema validation, precedence, path selection, and conflicting flags.
<!-- AC:END -->
