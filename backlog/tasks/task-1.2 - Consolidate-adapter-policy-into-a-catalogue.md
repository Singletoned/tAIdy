---
id: TASK-1.2
title: Consolidate adapter policy into a catalogue
status: To Do
assignee: []
created_date: '2026-08-04 11:41'
labels:
  - agent-first
  - setup
dependencies:
  - TASK-1.1
references:
  - IMPLEMENTATION_PLAN.md
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
