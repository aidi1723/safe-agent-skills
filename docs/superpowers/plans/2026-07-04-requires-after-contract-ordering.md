# Requires After Contract Ordering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `contract.requires_after` ordering metadata to schema validation, contract graphs, diagnostics, tests, and release records.

**Architecture:** Extend the existing contract graph rather than adding a second scheduler. `requires_after` becomes an explicit graph edge, and diagnostics reports missing predecessor references separately from missing artifact preconditions.

**Tech Stack:** Python standard library, `unittest`, existing `onecode_skill_sanitizer` CLI and router modules.

---

### Task 1: Router Ordering Tests

**Files:**
- Modify: `tests/test_router.py`

- [ ] Add a failing test proving `build_contract_graph()` creates a
  `contract_requires_after` edge and topology layer from predecessor to
  dependent skill.
- [ ] Add a failing test proving `build_contract_diagnostics()` reports missing
  `requires_after` predecessors as ordering issues.
- [ ] Run the focused tests and confirm they fail before implementation.

### Task 2: Schema Tests

**Files:**
- Modify: `tests/test_registry_cli.py`

- [ ] Extend the valid optional contract test with `requires_after`.
- [ ] Extend invalid contract-value coverage so self-referential or malformed
  `requires_after` values fail schema validation.
- [ ] Run focused schema tests and confirm the new failure before
  implementation.

### Task 3: Implementation

**Files:**
- Modify: `src/onecode_skill_sanitizer/router.py`
- Modify: `src/onecode_skill_sanitizer/cli.py`

- [ ] Add `requires_after` to allowed contract fields.
- [ ] Validate `requires_after` with the same string-array rules used by skill
  conflict lists, including self-reference rejection.
- [ ] Add graph edges for selected `requires_after` predecessors.
- [ ] Add diagnostics for missing ordering predecessors.
- [ ] Render ordering diagnostics in Markdown and agent instructions.

### Task 4: Documentation And Release Notes

**Files:**
- Create: `docs/updates/2026-07-04-requires-after-contract-ordering.md`
- Modify: `docs/maintenance-log.md`
- Modify: `docs/scheduler-hardening-roadmap.md`
- Modify: `/private/tmp/safe-agent-release-notes-20260703.md`

- [ ] Record the update, verification commands, and method-only boundary.
- [ ] Move explicit `requires_after` from roadmap remaining work to completed
  diagnostic/order metadata.
- [ ] Update GitHub release notes before publishing.

### Task 5: Verification And Publish

- [ ] Run `bash scripts/verify.sh`.
- [ ] Run `git diff --check`.
- [ ] Run `router-eval`.
- [ ] Run `schema-check`.
- [ ] Run `maintain-check`.
- [ ] Run `verify`.
- [ ] Commit, push, update GitHub Release, then read back the Release body.
