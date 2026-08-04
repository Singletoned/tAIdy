---
id: TASK-1.3
title: Report run coverage and add reviewed transient fallbacks
status: To Do
assignee: []
created_date: '2026-08-04 11:41'
labels:
  - agent-first
  - setup
dependencies:
  - TASK-1.2
references:
  - IMPLEMENTATION_PLAN.md
parent_task_id: TASK-1
priority: high
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Use the catalogue to distinguish processed, finding, failed, unsupported, and unavailable file groups; add reviewed PATH-first uvx/bunx fallback candidates.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Default output has a compact final summary of unavailable recognized file groups and one taidy setup hint.
- [ ] #2 Unavailable recognized files exit zero; tool findings and infrastructure failures retain non-zero exits.
- [ ] #3 PATH remains preferred over declared transient runners.
- [ ] #4 Affected Docker tests verify outcomes rather than incidental log text.
<!-- AC:END -->
