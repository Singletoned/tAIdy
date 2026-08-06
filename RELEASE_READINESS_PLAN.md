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

### 1. Set the public support contract **[complete]**

The first public release is a reliable, curated tool rather than a broad best-effort beta.

- **Guaranteed locally:** Ruff (Python); ESLint and Prettier (JavaScript and TypeScript); Prettier (JSON, CSS, SCSS, HTML, and Markdown); gofmt; rustfmt; RuboCop; PHP CS Fixer; ShellCheck and shfmt; yamllint and Prettier (YAML); Taplo; and actionlint and Prettier (GitHub Actions workflows).
- **Guaranteed in Docker:** the same set except GitHub Actions workflows, which remain local-only until the production image installs and tests actionlint reliably on every supported platform.
- **Compatibility adapters:** Other existing adapters and fallback candidates remain best-effort and are not release guarantees until they are explicitly added to the manifest.
- **Missing adapters or tools:** report the affected input as `not_checked` and exit zero. Exit zero means every selected available tool completed successfully; it does not mean every input was checked.
- **Bootstrap:** retain its useful `uv` and Node.js provisioning role, but redesign its downloads around pinned, verified artifacts before the first public release.

**Acceptance criteria:** README, CLI help, JSON output, and exit codes use one unambiguous definition of “success.”

### 2. Establish one tool manifest **[complete: core policy]**

`ADAPTER_MANIFEST` in `taidy/cli.py` is the declarative source for every adapter selector's installation suggestions, Docker availability, and release tier. The runtime catalogue rejects command definitions outside the manifest, and unit tests verify that catalogue and suggestion behavior derives from it.

- CLI command selection remains adjacent to command construction, while the manifest validates its selector coverage.
- `suggest` derives its recommendations from the manifest.
- Each adapter is marked `curated` or `compatibility`, and `supported`, `conditional`, or `unavailable` in Docker.
- README documents the curated/compatibility distinction and identifies the manifest as the policy source.

Do not add language support outside the manifest. Production-image coverage that proves Docker installation for every documented Docker-supported adapter is implemented by step 3.

**Acceptance criteria:** CI fails if a documented Docker-supported tool is absent from the image or lacks an end-to-end test.

### 3. Repair behavior and test contracts **[complete]**

- Updated Docker expectations for the `not_checked` success contract.
- Production-image tests now build the real `Dockerfile`, invoke its entrypoint, and validate every Docker-supported manifest suggestion is executable.
- The production image preserves the Python tool target directory on `PATH`, fixing discovery of Ruff, Black, and yamllint.
- Docker tests cover no-tool, unsupported-file JSON, tool discovery, build failure, and dry-run outcomes.

**Acceptance criteria:** `make test-all` passes without permanently skipped production-image tests.

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
