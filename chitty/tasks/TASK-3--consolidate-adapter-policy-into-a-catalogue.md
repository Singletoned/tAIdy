---
title: Consolidate adapter policy into a catalogue
status: doing
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

- [ ] Existing command maps, discovery selectors, and suggestions derive from one catalogue.
- [ ] No current adapter or priority changes without an explicit documented decision.
- [ ] Catalogue declares operation, selector, runner, directory behavior, Docker status, and setup-provider status.

## Plan

1. Introduce a typed adapter catalogue as the sole source of policy.
2. Each entry must declare selectors, format/lint operations, ordered PATH/uvx/bunx/native candidates, directory behavior, Docker availability, and supported/deferred/unsupported setup status.
3. Derive command selection, discovery selectors, and suggest recommendations from the catalogue.
4. Retain the current priority/order characterized in TASK-2; document and test every intentional change.

## Notes

TASK-2 characterization is complete; beginning catalogue extraction from the verified inventory.

Backlog.md ID: TASK-1.2

## History

- 2026-08-04 → doing
