# Long-Term Design Plan

These items are intentionally deferred until the command sequencing and rerun
behavior are stable.

## 1. Clarify Directory Delegation Contract

Taidy should prefer passing directory inputs to tools that support directories,
so each tool can apply its own project config, ignore rules, and performance
optimizations. Taidy's own discovery pass should stay lightweight: identify
whether relevant files exist, choose tool groups, and support tools that require
explicit file lists. Document this contract clearly and add adapter metadata for
tools whose directory behavior is project-scoped or unsafe to batch.

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
