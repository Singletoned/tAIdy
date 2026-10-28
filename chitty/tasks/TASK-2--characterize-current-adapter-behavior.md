---
title: Characterize current adapter behavior
status: done
labels:
  - agent-first
  - setup
priority: high
parent: TASK-1
created: 2026-08-04
---

## Description

Capture the selectors, command ordering, fallback behavior, directory handling, and special-file behavior of every current adapter before refactoring.

### References

- PROJECT.md

## Acceptance Criteria

- [x] Regression tests cover every current adapter selector and fallback order.
- [x] The test inventory identifies each adapter’s Docker and setup-provider status.

## Plan

1. Inventory every linter and formatter in the existing maps before refactoring.
2. Record extensions, special filenames, operation, ordered commands/fallbacks, directory/project scope, Docker availability, and setup-provider status.
3. Add characterization tests for selectors and fallback ordering. Capture mixed-extension and special-filename fixtures where needed.
4. Hand the inventory to TASK-3 as the preservation baseline.

## Notes

Added tests/unit/test_adapter_inventory.py as the pre-catalogue preservation snapshot. It records every selector, candidate order, current Docker status, and current setup-suggestion status. Validation passed: ruff check tests/unit/test_adapter_inventory.py; python -m unittest tests.unit.test_adapter_inventory; just test. just format remains blocked by intentionally invalid shell fixtures in tests/sample_files (existing behavior).

Backlog.md ID: TASK-1.1

## Summary

Characterized all current adapters in a regression-test inventory, including selector dispatch, fallback order, Docker availability, and setup-suggestion status. Verified with Ruff, the focused unit test, and just test.

## History

- 2026-08-04 → done
