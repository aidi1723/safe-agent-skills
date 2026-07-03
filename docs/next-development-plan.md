# Next Development Plan

Date: 2026-06-12

## Purpose

This plan starts after the audit hardening closure. It tracks capability
upgrades that are larger than the completed remediation work.

The next phase should preserve the current project boundary:

- skills provide method guidance only
- host runtime controls permissions
- source and report records must remain deterministic and verifiable
- new claims require tests and documentation updates

## Phase 1: Scanner Engine Upgrade

Goal: move from mostly regular-expression scanning to a small deterministic
analysis engine for command-like instructions.

Recommended work:

- add a shell command tokenizer using standard library primitives where
  possible
- extract command sequences from Markdown, fenced code blocks, and prose
- track simple data flow for downloaded file paths
- detect variable-assigned dangerous commands, for example:
  `cmd=curl ...` followed by `$cmd | bash`
- detect command substitution and process substitution in higher-risk contexts
- build a dedicated scanner bypass fixture suite

Acceptance criteria:

- scanner regression tests cover at least 20 bypass cases
- every new scanner claim has a failing test first
- false-positive examples are documented for each broad rule family
- `bash scripts/verify.sh` remains the release gate

## Phase 2: Real Source Import Pipeline

Goal: distinguish reference-only guidance from real upstream source imports
with auditable capture records.

Recommended work:

- add `source-import` command or equivalent bounded workflow
- record upstream URL, commit/tag/release, capture timestamp, license snapshot,
  and upstream content hash
- separate upstream hash from local sanitized hash
- require `source.usage = source_import` only for this path
- keep `github_reference` and `web_reference` metadata-only unless capture
  evidence exists

Acceptance criteria:

- source-import fixture proves upstream content hash is reproducible
- schema-check rejects `source_import` without upstream capture metadata
  (completed for the schema gate on 2026-07-03)
- imported content is never executed during intake
- docs clearly separate import, reference, and local authoring paths

Status note: the schema gate is complete. A networked `source-import` command
or direct Git/archive capture workflow remains future work and should keep the
same no-execution intake boundary.

## Phase 3: Router Quality Metrics

Goal: make deterministic routing quality measurable rather than only
behaviorally tested.

Recommended work:

- expand `evals/router-quality.json` with positive and negative cases
- add Chinese, English, typo, and mixed-domain route cases
- emit per-case false positive, false negative, and missing capability records
- add a router quality summary command
- document current deterministic router limits

Acceptance criteria:

- router evaluation has at least 30 cases
- no unrelated scenario bundle is selected for low-signal maintenance tasks
- required safety invariants are surfaced as covered or missing
- router quality report is included in release verification output or docs

## Phase 4: Documentation Consolidation

Goal: reduce duplicated public claims and make future updates harder to drift.

Recommended work:

- split docs into public overview, operator guide, maintainer guide, and
  internal design archive
- centralize current catalog counts in one generated or easy-to-refresh place
- keep update statements chronological but avoid duplicating baseline claims
- add a short "Claims Boundary" page linked from README

Acceptance criteria:

- README has one current baseline section
- catalog counts in README, catalog status, and open-source statement agree
- old phase documents remain historical and clearly dated
- `rg` checks or schema checks catch stale count patterns where practical

## Phase 5: Optional Host Integration Contracts

Goal: make it easier for Codex, Claude Code, Cursor, and other hosts to consume
task packs without interpreting skills as permission grants.

Recommended work:

- define a compact host integration contract for task packs
- add examples for approved shell, browser, network, and filesystem policies
- document how hosts should ignore or downgrade skills requiring missing
  runtime capabilities
- keep connector execution out of skill definitions

Acceptance criteria:

- host contract includes allowed action boundaries and failure behavior
- task-pack examples show permissions as host-owned
- integration docs pass schema and markdown checks
- no skill grants runtime permissions by itself

## Recommended Next Step

Start with Phase 1, scanner engine upgrade.

The first implementation slice should be small:

1. Add scanner bypass fixtures for variable assignment and command
   substitution.
2. Add a tokenized command extraction helper.
3. Keep regex rules as fallback.
4. Verify with focused tests and full `bash scripts/verify.sh`.

Do not start Phase 2 until Phase 1 has a stable fixture suite.
