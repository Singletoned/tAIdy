---
title: Provision reviewed Python and Bun tool providers
status: backlog
labels:
  - agent-first
  - setup
priority: high
depends_on:
  - TASK-6
parent: TASK-1
created: 2026-08-04
---

## Description

Use declared package/provider data to provision reviewed Python and JS/TS/web-document adapters after explicit setup approval. Report native or deferred adapters without guessing installers.

### References

- PROJECT.md

## Acceptance Criteria

- [ ] Providers use declared package identities and exact tested commands.
- [ ] Provider tests prove no shell-piped installer and no global installation without explicit target approval.
- [ ] Deferred/native adapters are reported clearly and are not installed speculatively.

## Plan

1. Implement only reviewed Python and JS/TS/web-document setup providers from declared catalogue package data.
2. Invoke uv/uvx and Bun/Bunx using exact tested commands after explicit target approval.
3. Report native/deferred adapters instead of guessing installers.
4. Mock provider invocations and assert no shell-piped installer and no unapproved global install.

## Notes

Backlog.md ID: TASK-1.6

2026-10-29 review: moved to backlog. Direction is unresolved: `RELEASE_READINESS_PLAN.md` step 1 keeps `bootstrap` with pinned, verified downloads, while `PROJECT.md` and this chain replace it with `taidy setup` and INI config (config support was removed in `87a0ea5`). Decide the direction, then rewrite as smaller tickets.

## History

- 2026-08-04 → todo
- 2026-10-29 todo → backlog
