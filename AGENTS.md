# Repository Agent Guidelines

## Project

- Taidy is a Python 3.8+ CLI meta-formatter/linter. It uses only the standard library at runtime.
- Keep the agent-first contract intact: default execution formats then lints; tools retain their documented priority/fallback order.
- Adapter policy lives in `taidy/cli.py`. Preserve selector coverage and candidate priority with `tests/unit/test_adapter_inventory.py` when changing it.

## Formatting

- Run `make format` regularly and before committing changes. It runs Taidy across the whole repository; Taidy is the sole formatting authority, so do not follow it with individual formatters such as Ruff.
- Treat any `make format` failure as an issue to fix; do not bypass it or hide failures.

## Development

- Use the repository `Makefile` and its `mate`-listed targets for development workflows.
- Run `make test` for fast validation, `make test-docker` when Docker coverage is relevant, and `make typecheck` after Python changes.
- Tests use `unittest`: unit tests are in `tests/unit/`, integration tests in `tests/integration/`, and Docker tests in `tests/docker_tests/`.
- Add adapter changes with selector/fallback characterization coverage and applicable Docker coverage.

## Chitty

Tasks live in `chitty/`. Use the `chitty` CLI (or MCP tools); do not hand-edit
task files. `chitty --help` is the full command reference.

- Put paths, globs, commands, IDs and code in backticks in titles, descriptions,
  criteria and notes.
- Work on one task per session. Start with `chitty inbox --pull`, then `chitty show <ID>`.
- Backlog tasks need refinement; promote them to `todo` before taking them on.
- Use a task's optional `parent` field to group flat task IDs under one goal.
- Before writing code, write your approach with `chitty edit <ID> --plan` and
  set `-s doing`. Wait for approval if the human asked for it.
- Tick acceptance criteria as you meet them: `chitty edit <ID> --check N`
  (numbers are shown by `chitty show`).
- Record anything surprising with `--note`. When work is ready, set `-s review`.
  Never review a ticket you worked on: review promptly, rather than at
  merge-request time. Pass it with `-s done --note "Reviewed: ..."`; fail it
  with `-s doing --note "reason"`. Create new tickets for out-of-scope findings.
- Set `-s done` when every criterion is ticked and the work is verified; write
  `--summary` with the handoff, verification, and follow-ups. Run `chitty fix`
  to apply safe repairs; it fails loudly when a problem remains.
- Before preparing a merge request, run `chitty archive` with no ID to process
  completed tasks in one batch. The default moves them to `archive/`; with
  `archive = "delete"`, Git history retains the record instead.
- End commits for task work with `Task: <ID>` lines using the ticket's own ID
  (for example, `Task: TASK-12`) so `git log --grep <ID>` finds a ticket's
  code. This is a convention; no hook enforces it.
- When work cannot proceed, set `-s blocked --note "reason"` and move on; do
  not pick up blocked work. If a person must act outside the repo, add a
  `-c human` task and depend on it.
- Found unrelated work? `chitty add` it (`-c human` if it needs a person).
  Suggest work for another project without touching its checkout using
  `chitty suggest PROJECT "title" -d "why"`.
  Don't do it in this session.
