# Long-Term Design Plan

These items are intentionally deferred until the command sequencing and rerun
behavior are stable.

## 1. Make Discovery the Single Source of Truth

Taidy currently discovers files with its own ignore rules, but may later pass a
whole directory to external tools. Decide whether Taidy owns discovery entirely
or whether adapters can explicitly delegate directory handling when their native
ignore behavior matches Taidy's contract.

## 2. Replace Stringly Tool Metadata with Adapter Semantics

The current tool registry only models availability, command construction, and
directory support. Add explicit adapter metadata for whether a command mutates
files, accepts file arguments, operates at project scope, can be batched, needs a
specific working directory, or should run before/after another command.

## 3. Separate Tool Findings from Infrastructure Failures

Tool findings are normal linter output. Infrastructure errors, such as failed
subprocess execution, invalid config, or Docker preparation failures, should be
reported distinctly and with enough diagnostic detail for engineers to fix root
causes.

## 4. Introduce a Shared Tool Manifest

The CLI command maps, installation suggestions, Docker image, and documentation
all encode overlapping tool knowledge. Move that information toward one manifest
that can drive command registration, docs, Docker installation, and suggestions.
