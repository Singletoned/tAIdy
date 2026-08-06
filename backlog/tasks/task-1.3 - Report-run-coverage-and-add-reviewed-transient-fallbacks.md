---
id: TASK-1.3
title: Report run coverage and add reviewed transient fallbacks
status: To Do
assignee: []
created_date: '2026-08-04 11:41'
updated_date: '2026-08-06 07:27'
labels:
  - agent-first
  - setup
dependencies:
  - TASK-1.2
references:
  - PROJECT.md
  - RELEASE_READINESS_PLAN.md
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

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Use catalogue results to aggregate processed, tool-finding, infrastructure-failure, unsupported, and recognized-but-unavailable file groups.
2. Render a compact final summary naming unavailable extensions/tools and one taidy setup recommendation.
3. Preserve zero exit for unavailable recognized files and non-zero exits for tool findings/infrastructure failures.
4. Add only reviewed, declared uvx/bunx candidates; PATH remains first.
5. Test aggregation, runner ordering, transient fallback, unavailable behavior, and mixed fixtures. Repair the affected Docker tests to assert result contracts rather than incidental Running: logs.
<!-- SECTION:PLAN:END -->
