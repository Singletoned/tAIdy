---
id: TASK-1
title: Agent-first setup foundation
status: To Do
assignee: []
created_date: '2026-08-04 11:40'
updated_date: '2026-08-06 07:27'
labels:
  - initiative
  - agent-first
dependencies: []
references:
  - PROJECT.md
  - RELEASE_READINESS_PLAN.md
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Deliver the first two phases of IMPLEMENTATION_PLAN.md: preserve existing adapter coverage through one catalogue, make normal-run outcomes explicit, and replace implicit bootstrap behavior with explicit setup.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Existing working adapters remain supported unless an explicit task documents a change.
- [ ] #2 Normal runs never install tools or write configuration.
- [ ] #3 Setup persists an explicit installation target before provisioning reviewed tools.
- [ ] #4 All changed behavior has unit/integration coverage and affected Docker tests pass.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Delivery policy
- Preserve current working language/tool coverage; do not remove an adapter because its Docker or setup provider is deferred.
- Normal runs use PATH first, then only adapter-declared uvx/bunx fallbacks. They never install tools or write config.
- Recognized but unavailable files produce an incomplete-coverage summary and exit zero; findings and infrastructure failures remain non-zero.
- Setup is explicit. It asks for or receives a target, persists it, and supports global, Taidy-managed, and project-local installation. User config is default; project config is opt-in.
- Use Python 3.8-compatible INI configuration through configparser.

## Architecture
Keep adapter policy/data, command execution, installation providers, and output rendering separate. Underlying tools own formatting rules; Taidy configures orchestration and installation policy. Keep human-readable output primary and defer structured serialization until the outcome model is stable.

## Known constraints and risks
CLI tool knowledge is currently duplicated across execution, suggestions, Docker, tests, and docs. Unit/integration/type checks pass, but three Docker tests fail and production-image tests are skipped. Bootstrap currently executes remote downloaded scripts and must be replaced by the explicit setup path. Characterization tests and PATH-first runner ordering prevent adapter regressions; isolated HOME tests prevent unexpected machine changes.

## Later work
After these subtasks: expand reviewed native setup providers, derive/pin Docker support from the catalogue, make built-image tests/release gates trustworthy, publish the support matrix, then improve token-efficient output filtering.
<!-- SECTION:PLAN:END -->
