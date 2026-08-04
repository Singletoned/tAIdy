# Implementation Plan

## Project Context

Taidy is an agent-first meta-formatter/linter for mixed-language repositories. Its default run formats and lints by orchestrating existing tools. Output should be concise and readable by default, with structured output only on request.

The short-term objective is to preserve the broad adapter coverage already used in production while making tool selection, missing-tool reporting, and setup behavior predictable enough for reliable agent use.

## Confirmed Decisions

- Do not reduce current working language/tool support.
- Normal runs use PATH tools first, then explicitly supported transient runners such as `uvx` and `bunx`; they never install tools or write configuration.
- Recognized files that cannot be processed are reported in a clear final summary with `taidy setup` guidance. This best-effort condition exits zero; tool findings and infrastructure failures remain non-zero.
- `taidy setup` explicitly provisions tools. On first use it asks where to install them and persists that choice.
- Setup supports global, Taidy-managed-directory, and project-local targets. It never guesses a target.
- User configuration is the default; project configuration is explicit and opt-in.
- Configuration uses INI via Python 3.8's standard-library `configparser`.
- Docker remains an alternative path with its documented tool set preinstalled.

## Current State

- `taidy/cli.py` contains most application logic and duplicates tool knowledge found in suggestions, Docker, tests, and docs.
- Unit tests, integration tests, and mypy pass. Three Docker tests currently fail, and production-image tests are skipped.
- The existing `bootstrap` command downloads and executes remote scripts; it does not meet the explicit setup model.
- `PROJECT.md` records the durable scope and configuration policy. `RELEASE_READINESS_PLAN.md` covers later public-release work.

## Phase 1: Adapter Catalogue and Honest Run Outcomes

### Goal

Create one internal source of truth for existing adapters, preserve their behavior, and make it clear which files were processed, failed, or could not be checked.

### Dependencies

- Characterize current adapter behavior before refactoring.
- Do not remove adapters merely because their setup provider or Docker support is deferred.

### Tasks

1. Inventory every linter/formatter adapter from the current maps: selectors, special filenames, operation, fallback order, directory behavior, and Docker availability.
2. Introduce a typed adapter catalogue as the source of truth. Each adapter declares:
   - file selectors and supported operations;
   - ordered PATH, `uvx`, `bunx`, or native-only candidates;
   - directory/project-scope behavior;
   - Docker availability; and
   - setup status (`supported`, `deferred`, or `unsupported`).
3. Derive command selection, discovery, and `suggest` data from the catalogue while retaining existing priority order.
4. Record per-file-group outcomes: processed, tool finding, infrastructure failure, unsupported, and recognized-but-unavailable.
5. Add a compact final summary naming unavailable extensions/tools and suggesting `taidy setup` once. Preserve zero exit for unavailable recognized files; preserve non-zero exits for real execution failures.
6. Add reviewed transient `uvx`/`bunx` candidates only where package and invocation are known. PATH remains preferred.
7. Keep `bootstrap` temporarily for compatibility, but mark it deprecated in help/docs. Do not remove it until `setup` replaces its supported use case in Phase 2.

### Testing and Validation

- Add characterization tests for every existing adapter selector and fallback order.
- Unit-test catalogue resolution, PATH precedence, transient fallback, unavailable outcomes, and exit aggregation.
- Add integration fixtures for mixed extensions and special filenames.
- Repair the failing Docker assertions to verify the agreed outcome contract rather than incidental log strings.
- Require `just test`, `just typecheck`, and the affected Docker tests to pass.

### Exit Criteria

- No current adapter or priority changes without an explicit decision and regression test.
- The catalogue drives execution and missing-tool reporting.
- Default output lets an agent distinguish checked, finding, failure, and not-checked results without verbose logs.

## Phase 2: Explicit Setup and Persisted Installation Policy

### Goal

Replace implicit remote bootstrap behavior with `taidy setup`, which records an explicit installation policy before provisioning reviewed tool providers.

### Dependencies

- Phase 1 catalogue supplies project analysis, package identities, and provider status.
- Decide and document configuration paths, project-config filename, and precedence before implementation.

### Tasks

1. Define a versioned INI schema for installation target, enabled transient runners, and narrowly scoped adapter overrides.
2. Define user-config path, explicit project-config path, precedence, validation, and migration behavior. Reject malformed/ambiguous configuration rather than silently choosing another target.
3. Implement `taidy setup` in two stages:
   - analyze the current project and display required tools plus proposed target;
   - obtain interactive confirmation, or require explicit target flags non-interactively, then persist config and provision supported tools.
4. Add mutually exclusive target flags for global, Taidy-managed-directory, and project-local installation.
5. Implement reviewed providers first for Python and JS/TS/web-document tools using declared `uv`/`uvx` and Bun/Bunx package data. Report native/deferred adapters; do not invent installers.
6. Replace the old bootstrap path with a compatibility message pointing to `taidy setup`, then remove it only in a documented breaking release.
7. Update help and README for first-run behavior, setup targets, transient runners, and incomplete coverage.

### Testing and Validation

- Unit-test INI parsing, schema validation, config precedence, path selection, and conflicting flags.
- Use temporary HOME/config/project directories to verify normal runs write nothing and setup writes only the chosen configuration.
- Mock providers and assert exact commands; prohibit shell-piped installers and unapproved global changes.
- Manually verify first normal run, interactive setup, non-interactive setup for each target, malformed config, and an opt-in project override.

### Exit Criteria

- Normal format/lint runs do not install tools or alter config.
- Setup never guesses an installation target; non-interactive setup with no saved policy requires an explicit target.
- User-default and opt-in project configuration are documented and test-covered.
- The user-facing bootstrap path no longer executes downloaded scripts.

## Architecture Decisions

- Keep a small CLI surface: default run, `lint`, `format`, `setup`, `suggest`, and Docker execution.
- Keep adapter policy/data, command execution, installation providers, and output rendering separate.
- Let underlying tools own formatter/linter rules; Taidy configures orchestration and installation policy only.
- Keep readable text primary. Add structured serialization behind an explicit flag after the outcome model is stable.

## Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Refactoring loses working production support | Characterize all adapters first; make preservation a Phase 1 exit criterion. |
| Runner behavior differs across platforms | Declare runners per adapter and test generated commands; keep PATH first. |
| Setup changes a machine unexpectedly | Require saved or explicit target; use isolated HOME tests; never set up during normal runs. |
| Concise output hides diagnostics | Preserve failing-tool diagnostics and retain an explicit verbose mode. |
| INI becomes insufficient | Version the schema and constrain its scope to policy, not formatter rules. |

## Later Phases

- Add reviewed setup providers for native ecosystems without relaxing explicit-target rules.
- Generate Docker installation and support validation from the catalogue; pin and verify artifacts.
- Repair Docker CI, test the image actually built, and make full tests release gates.
- Publish a manifest-derived support matrix and improve token-efficient output filtering based on real agent runs.

## Open Questions

- Exact user/project config paths, project-config filename, and precedence details.
- Package version, registry, and verification policy for each setup provider.
- The Taidy-managed tool-directory location per operating system.
- Whether a later strict mode should return non-zero for unavailable recognized files.
- The release in which `bootstrap` is removed.

## Definition of Done

The first two phases are done when Taidy preserves its adapter coverage through one catalogue, reports incomplete coverage clearly without side effects, and provides an INI-backed `taidy setup` that records an explicit target and provisions only reviewed providers. All changed behavior has unit/integration coverage, and the affected Docker tests pass.
