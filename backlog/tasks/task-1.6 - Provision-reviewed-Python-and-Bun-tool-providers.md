---
id: TASK-1.6
title: Provision reviewed Python and Bun tool providers
status: To Do
assignee: []
created_date: '2026-08-04 11:41'
updated_date: '2026-08-06 07:27'
labels:
  - agent-first
  - setup
dependencies:
  - TASK-1.5
references:
  - PROJECT.md
parent_task_id: TASK-1
priority: high
ordinal: 7000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Use declared package/provider data to provision reviewed Python and JS/TS/web-document adapters after explicit setup approval. Report native or deferred adapters without guessing installers.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Providers use declared package identities and exact tested commands.
- [ ] #2 Provider tests prove no shell-piped installer and no global installation without explicit target approval.
- [ ] #3 Deferred/native adapters are reported clearly and are not installed speculatively.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Implement only reviewed Python and JS/TS/web-document setup providers from declared catalogue package data.
2. Invoke uv/uvx and Bun/Bunx using exact tested commands after explicit target approval.
3. Report native/deferred adapters instead of guessing installers.
4. Mock provider invocations and assert no shell-piped installer and no unapproved global install.
<!-- SECTION:PLAN:END -->
