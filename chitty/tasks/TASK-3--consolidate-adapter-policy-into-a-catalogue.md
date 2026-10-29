---
title: Consolidate adapter policy into a catalogue
status: review
labels:
  - agent-first
  - setup
priority: high
depends_on:
  - TASK-2
parent: TASK-1
created: 2026-08-04
---

## Description

Replace duplicated adapter metadata with one typed catalogue that drives command selection, discovery, and suggestions while preserving current priorities.

### References

- PROJECT.md

## Acceptance Criteria

- [x] Existing command maps, discovery selectors, and suggestions derive from one catalogue.
- [x] No current adapter or priority changes without an explicit documented decision.
- [ ] Catalogue declares operation, selector, runner, directory behavior, Docker status, and setup-provider status.

## Plan

1. Introduce a typed adapter catalogue as the sole source of policy.
2. Each entry must declare selectors, format/lint operations, ordered PATH/uvx/bunx/native candidates, directory behavior, Docker availability, and supported/deferred/unsupported setup status.
3. Derive command selection, discovery selectors, and suggest recommendations from the catalogue.
4. Retain the current priority/order characterized in TASK-2; document and test every intentional change.

## Notes

TASK-2 characterization is complete; beginning catalogue extraction from the verified inventory.

Backlog.md ID: TASK-1.2

Catalogue landed in `ee13869` (`ADAPTER_MANIFEST`/`ADAPTER_CATALOGUE`) and `71f5dbd`; suggestions derive from it and `tests/unit/test_adapter_inventory.py` guards selectors and order. Criterion 3 is met apart from per-candidate runner metadata (PATH/uvx/bunx) and a real setup-provider status (`setup_status` is derived as `suggestion-only`); runner metadata moved to `TASK-4`, setup status waits on the bootstrap/setup decision.

## History

- 2026-08-04 → doing
- 2026-10-29 doing → review
