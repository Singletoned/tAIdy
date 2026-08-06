---
id: TASK-1.1
title: Characterize current adapter behavior
status: Done
assignee: []
created_date: "2026-08-04 11:40"
updated_date: "2026-08-06 08:12"
labels:
  - agent-first
  - setup
dependencies: []
references:
  - PROJECT.md
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

- [x] #1 Regression tests cover every current adapter selector and fallback order.
- [x] #2 The test inventory identifies each adapter’s Docker and setup-provider status.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->

1. Inventory every linter and formatter in the existing maps before refactoring.
2. Record extensions, special filenames, operation, ordered commands/fallbacks, directory/project scope, Docker availability, and setup-provider status.
3. Add characterization tests for selectors and fallback ordering. Capture mixed-extension and special-filename fixtures where needed.
4. Hand the inventory to TASK-1.2 as the preservation baseline.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Added tests/unit/test_adapter_inventory.py as the pre-catalogue preservation snapshot. It records every selector, candidate order, current Docker status, and current setup-suggestion status. Validation passed: ruff check tests/unit/test_adapter_inventory.py; python -m unittest tests.unit.test_adapter_inventory; just test. just format remains blocked by intentionally invalid shell fixtures in tests/sample_files (existing behavior).

<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->

Characterized all current adapters in a regression-test inventory, including selector dispatch, fallback order, Docker availability, and setup-suggestion status. Verified with Ruff, the focused unit test, and just test.

<!-- SECTION:FINAL_SUMMARY:END -->
