# Release Readiness Plan

## Purpose

Prepare Taidy for external users by making its support contract, release gates, Docker image, and documentation agree. This plan deliberately puts product decisions before implementation work that would otherwise be speculative.

## Current assessment

- Unit tests, integration tests, and mypy pass.
- Docker tests fail (three failures) and skip the production-image tests.
- The Docker workflow does not reliably test the image produced by its build.
- The CLI, Dockerfile, suggestions, and documentation have separate tool lists and have drifted.
- `bootstrap` downloads and executes remote installer scripts without artifact verification.

## Ordered implementation plan

### 1. Set the public support contract **[input required before implementation]**

Ask for a decision on the following when this step begins:

1. Is the first public release a **best-effort beta** or a **reliable, curated tool**?
2. Which languages and tools are supported in the first release, separately for local and Docker use?
3. When a file is recognized but no suitable tool is available, should Taidy exit non-zero or exit zero with an explicit `not checked` result?
4. Should `taidy bootstrap` remain a supported feature, be redesigned around pinned/verified artifacts, or be removed?

**Acceptance criteria:** README, CLI help, JSON output, and exit codes use one unambiguous definition of “success.”

### 2. Establish one tool manifest

Create a single declarative manifest for tool adapters and use it to generate or validate:

- CLI command selection and fallback order;
- `suggest` recommendations;
- Docker-installed tools;
- supported-language documentation; and
- the test matrix.

Do not add language support outside the manifest. Mark each adapter as local-only, Docker-supported, or experimental.

**Acceptance criteria:** CI fails if a documented Docker-supported tool is absent from the image or lacks an end-to-end test.

### 3. Repair behavior and test contracts

- Resolve the three failing Docker tests by first choosing the contract from step 1, then changing implementation and tests together.
- Replace assertions that only check for `Running:` with assertions for the selected command, file outcome, and exit code.
- Add production-image tests that build the real `Dockerfile`, invoke the entrypoint correctly, and validate every Docker-supported manifest entry.
- Cover no-tool, unsupported-file, tool-finding, infrastructure-failure, JSON, and dry-run outcomes.

**Acceptance criteria:** `just test-all` passes without permanently skipped production-image tests.

### 4. Make CI and releases trustworthy

- Add a normal pull-request CI workflow for formatting/linting, type checking, unit tests, integration tests, package build/install, and targeted Docker tests.
- Make release publication depend on the same checks.
- Build a locally tagged image or test by immutable digest; never validate a pre-existing `:latest` tag.
- Remove `|| true` from functional Docker checks.
- Validate that the Git tag, package version, and `taidy --version` agree. Prefer a single version source rather than editing source files during publishing.

**Acceptance criteria:** a release cannot publish a package or image that has not passed the full required test suite.

### 5. Harden installation and supply chain

- Remove or redesign `bootstrap` according to the decision in step 1.
- Pin Docker base-image digests and all downloaded/installable tool versions.
- Verify downloaded artifacts with checksums or signatures before execution.
- Avoid mutable `latest`, `stable`, and unversioned package installs in release images.
- Publish image tags/digests and supported-platform information.

**Acceptance criteria:** the released package and image can be rebuilt reproducibly from declared versions, without executing unverified remote scripts.

### 6. Refresh public documentation and onboarding

- Replace broad claims such as “all file types” and “all tools” with the manifest-derived support matrix.
- Document Docker-supported versus local-only adapters.
- Explain mutations, fallback behavior, exit codes, security scanning scope, and what a zero exit code guarantees.
- Add a concise compatibility policy and issue-report template.

**Acceptance criteria:** a new user can select the right installation path and predict which files will be checked or changed.

## Cleanup completed during this review

- Ignored `.envrc` so local direnv configuration is not accidentally committed.
- Removed the unused `go121` Docker test environment.
- Removed the unconsumed generated Docker-usage workflow artifact.
- Corrected Docker documentation to stop claiming the image includes every adapter and corrected its Justfile entry.
- Corrected stale maintainer guidance about removed `.taidy.json` configuration.
- Removed the obsolete SQL-support claim and clarified the legacy Docker-test entry in the changelog.

## Local generated files to clear

Run `just clean` when convenient to remove ignored stale build artifacts (`dist/`, `*.egg-info/`, and Python bytecode). Do not remove the user-owned `.envrc`.
