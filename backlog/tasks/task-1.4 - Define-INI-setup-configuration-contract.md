---
id: TASK-1.4
title: Define INI setup configuration contract
status: To Do
assignee: []
created_date: '2026-08-04 11:41'
updated_date: '2026-08-06 07:27'
labels:
  - agent-first
  - setup
dependencies:
  - TASK-1.3
references:
  - PROJECT.md
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

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Define a versioned INI schema using configparser for installation target, enabled transient runners, and narrowly scoped adapter overrides.
2. Before coding paths, decide and document the user-config path, explicit project-config filename/path, precedence, and migration behavior.
3. Reject malformed or ambiguous configuration with actionable errors; never silently choose another target.
4. Define mutually exclusive global, Taidy-managed-directory, and project-local target semantics.
5. Test schema parsing, validation, precedence, path selection, and conflicting flags.
<!-- SECTION:PLAN:END -->
