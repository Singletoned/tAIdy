---
id: TASK-1.5
title: Implement explicit taidy setup workflow
status: To Do
assignee: []
created_date: '2026-08-04 11:41'
labels:
  - agent-first
  - setup
dependencies:
  - TASK-1.4
references:
  - IMPLEMENTATION_PLAN.md
parent_task_id: TASK-1
priority: high
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement setup analysis, interactive confirmation, explicit non-interactive target flags, and persisted target selection without changing normal-run side effects.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Setup analyzes the project and presents proposed tools and installation target before provisioning.
- [ ] #2 First interactive setup asks for a target; non-interactive setup with no saved policy requires an explicit target.
- [ ] #3 Global, Taidy-managed-directory, and project-local targets are mutually exclusive.
- [ ] #4 Normal format/lint commands never create config or install tools.
<!-- AC:END -->
