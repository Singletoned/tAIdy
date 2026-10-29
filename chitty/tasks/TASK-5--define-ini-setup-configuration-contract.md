---
title: Define INI setup configuration contract
status: backlog
labels:
  - agent-first
  - setup
priority: high
depends_on:
  - TASK-4
parent: TASK-1
created: 2026-08-04
---

## Description

Specify and implement the versioned INI schema, user/project paths, opt-in project configuration, precedence, validation, and mutually exclusive installation targets.

### References

- PROJECT.md

## Acceptance Criteria

- [ ] Configuration uses configparser and remains compatible with Python 3.8.
- [ ] User configuration is default and project configuration is explicit and opt-in.
- [ ] Malformed or ambiguous configuration produces actionable errors without fallback to another target.
- [ ] Tests cover schema validation, precedence, path selection, and conflicting flags.

## Plan

1. Define a versioned INI schema using configparser for installation target, enabled transient runners, and narrowly scoped adapter overrides.
2. Before coding paths, decide and document the user-config path, explicit project-config filename/path, precedence, and migration behavior.
3. Reject malformed or ambiguous configuration with actionable errors; never silently choose another target.
4. Define mutually exclusive global, Taidy-managed-directory, and project-local target semantics.
5. Test schema parsing, validation, precedence, path selection, and conflicting flags.

## Notes

Backlog.md ID: TASK-1.4

2026-10-29 review: moved to backlog. Direction is unresolved: `RELEASE_READINESS_PLAN.md` step 1 keeps `bootstrap` with pinned, verified downloads, while `PROJECT.md` and this chain replace it with `taidy setup` and INI config (config support was removed in `87a0ea5`). Decide the direction, then rewrite as smaller tickets.

## History

- 2026-08-04 → todo
- 2026-10-29 todo → backlog
