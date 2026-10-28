---
title: Report run coverage and add reviewed transient fallbacks
status: todo
labels:
  - agent-first
  - setup
priority: high
depends_on:
  - TASK-3
parent: TASK-1
created: 2026-08-04
---

## Description

Use the catalogue to distinguish processed, finding, failed, unsupported, and unavailable file groups; add reviewed PATH-first uvx/bunx fallback candidates.

### References

- PROJECT.md
- RELEASE_READINESS_PLAN.md

## Acceptance Criteria

- [ ] Default output has a compact final summary of unavailable recognized file groups and one taidy setup hint.
- [ ] Unavailable recognized files exit zero; tool findings and infrastructure failures retain non-zero exits.
- [ ] PATH remains preferred over declared transient runners.
- [ ] Affected Docker tests verify outcomes rather than incidental log text.

## Plan

1. Use catalogue results to aggregate processed, tool-finding, infrastructure-failure, unsupported, and recognized-but-unavailable file groups.
2. Render a compact final summary naming unavailable extensions/tools and one taidy setup recommendation.
3. Preserve zero exit for unavailable recognized files and non-zero exits for tool findings/infrastructure failures.
4. Add only reviewed, declared uvx/bunx candidates; PATH remains first.
5. Test aggregation, runner ordering, transient fallback, unavailable behavior, and mixed fixtures. Repair the affected Docker tests to assert result contracts rather than incidental Running: logs.

## Notes

Backlog.md ID: TASK-1.3

## History

- 2026-08-04 → todo
