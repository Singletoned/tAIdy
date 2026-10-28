---
title: Implement explicit taidy setup workflow
status: todo
labels:
  - agent-first
  - setup
priority: high
depends_on:
  - TASK-5
parent: TASK-1
created: 2026-08-04
---

## Description

Implement setup analysis, interactive confirmation, explicit non-interactive target flags, and persisted target selection without changing normal-run side effects.

### References

- PROJECT.md

## Acceptance Criteria

- [ ] Setup analyzes the project and presents proposed tools and installation target before provisioning.
- [ ] First interactive setup asks for a target; non-interactive setup with no saved policy requires an explicit target.
- [ ] Global, Taidy-managed-directory, and project-local targets are mutually exclusive.
- [ ] Normal format/lint commands never create config or install tools.

## Plan

1. Use the catalogue to analyze the current project and show proposed tools plus target before provisioning.
2. In interactive first use, request confirmation and persist the choice. In non-interactive use with no saved policy, require an explicit target flag.
3. Implement mutually exclusive target flags and persist only the selected user or opt-in project configuration.
4. Use isolated temporary HOME/config/project integration tests to prove normal format/lint runs write nothing and setup writes only selected config.
5. Manually verify first normal run, interactive setup, each non-interactive target, malformed config, and project override.

## Notes

Backlog.md ID: TASK-1.5

## History

- 2026-08-04 → todo
