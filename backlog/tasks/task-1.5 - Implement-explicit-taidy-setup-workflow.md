---
id: TASK-1.5
title: Implement explicit taidy setup workflow
status: To Do
assignee: []
created_date: '2026-08-04 11:41'
updated_date: '2026-08-06 07:27'
labels:
  - agent-first
  - setup
dependencies:
  - TASK-1.4
references:
  - PROJECT.md
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

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Use the catalogue to analyze the current project and show proposed tools plus target before provisioning.
2. In interactive first use, request confirmation and persist the choice. In non-interactive use with no saved policy, require an explicit target flag.
3. Implement mutually exclusive target flags and persist only the selected user or opt-in project configuration.
4. Use isolated temporary HOME/config/project integration tests to prove normal format/lint runs write nothing and setup writes only selected config.
5. Manually verify first normal run, interactive setup, each non-interactive target, malformed config, and project override.
<!-- SECTION:PLAN:END -->
