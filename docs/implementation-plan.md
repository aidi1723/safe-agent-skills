# Skill Sanitizer Implementation Plan

> **For agentic workers:** Execute task-by-task. Use test-driven development
> for code changes and verify each task before moving forward.

**Goal:** Build a standalone local skill sanitizer that can classify, scan,
report, and later sanitize community skills under OneCode policy.

**Architecture:** The first implementation is a local Python CLI inside the
`onecode-skill-sanitizer` folder. It reads a skill source directory, calculates
source hashes, classifies the skill into the shared taxonomy, runs deterministic
risk rules, and emits a JSON sanitization report. It does not execute imported
skill scripts.

**Tech Stack:** Python 3.11 standard library, `unittest`, JSON reports,
Markdown docs.

---

## Files

- Modify: `docs/skill-taxonomy.md` to use user-facing top-level categories.
- Modify: `docs/architecture.md` to include taxonomy classification.
- Modify: `docs/mvp-roadmap.md` to make taxonomy part of MVP 1.
- Modify: `schemas/skill-manifest.schema.json` to add `taxonomy`.
- Modify: `examples/sanitization-report.example.json` to show taxonomy.
- Create: `pyproject.toml` for the standalone sanitizer package.
- Create: `src/onecode_skill_sanitizer/__init__.py`.
- Create: `src/onecode_skill_sanitizer/taxonomy.py`.
- Create: `src/onecode_skill_sanitizer/scanner.py`.
- Create: `src/onecode_skill_sanitizer/cli.py`.
- Create: `tests/test_scan_cli.py`.
- Create: `tests/test_workflow_cli.py`.
- Create: `tests/test_registry_cli.py`.
- Create: `schemas/registry-index.schema.json`.
- Create: `schemas/verify-report.schema.json`.
- Create: `examples/registry-index.example.json`.
- Create: `examples/verify-report.example.json`.

## Task 1: Documentation And Taxonomy

- [x] Replace the old taxonomy with top-level directories: `design`, `code`,
  `engineering`, `security`, `office`, `execution`, `research`, `data`,
  `business`, `content`, `commerce`, `media`, `compliance`, `ai`, `vertical`.
- [x] Add taxonomy to the architecture flow.
- [x] Add taxonomy to the manifest schema and example report.

## Task 2: Local Scan CLI

- [x] Write a failing test that creates a sample unsafe skill and expects a
  JSON scan report with taxonomy, source hash, findings, risk level, and
  `review_required` status.
- [x] Run the focused test and confirm it fails because the package does not
  exist yet.
- [x] Implement the minimal package and `scan` command.
- [x] Run the focused test and confirm it passes.

## Task 3: Scanner Coverage

- [x] Add tests for `curl | bash`, broad filesystem access, policy bypass, and
  secret-like strings.
- [x] Implement deterministic scanner rules for those patterns.
- [x] Verify the scanner returns stable finding IDs and severity levels.

## Task 4: Taxonomy Selection

- [x] Add tests for category detection from explicit manifest fields, folder
  names, and text signals.
- [x] Implement manifest-first classification and fallback keyword scoring.
- [x] Verify unknown classifications become `review_required`.

## Task 5: Report And Registry Prep

- [x] Add tests for writing report JSON with `--out`.
- [x] Implement stable JSON output and output directory creation.
- [x] Add fields needed by future registry work: `files`, `hashes`,
  `required_verifiers`, and `recommendation`.

## Task 6: Final Verification

- [x] Run `python3 -m unittest discover -s onecode-skill-sanitizer/tests -v`
  with `PYTHONPATH=onecode-skill-sanitizer/src`.
- [x] Run JSON formatting checks for schema and example report.
- [x] Scan for unresolved placeholders in `onecode-skill-sanitizer`.
- [x] Record the verified command outputs in the final handoff.

## Task 7: Local Sanitize, Audit, And Approve Workflow

- [x] Write failing tests for `sanitize`, `audit`, and `approve`.
- [x] Implement `sanitize <source> --out <registry-dir>` without executing
  imported skill scripts.
- [x] Generate sanitized `SKILL.md`, `skill.json`, and
  `SANITIZATION_REPORT.json`.
- [x] Implement `audit <skill-dir>` so only `trusted` skills pass.
- [x] Add tamper detection by verifying `SKILL.md` against
  `hashes.sanitized_sha256`.
- [x] Implement `approve <skill-dir>` to mark a reviewed skill as `trusted`
  and record approval evidence.

## Task 8: Provenance Records

- [x] Require every scanned and sanitized skill to record source URL, author,
  license, reference, collector, local path, and capture time.
- [x] Read provenance from source `skill.json` when available.
- [x] Allow CLI overrides with `--source-url`, `--author`, `--license`,
  `--reference`, and `--collected-by`.
- [x] Write `unknown` for missing provenance values instead of omitting fields.
- [x] Add tests for scan and sanitize provenance records.

## Task 9: Batch Registry And Selection

- [x] Write failing tests for batch `import`, `list`, `inspect`, and `select`.
- [x] Implement `import <incoming> --registry <registry>` to sanitize child
  folders into `registry/<category>/<name>/`.
- [x] Generate `registry/index.json` from actual skill manifests.
- [x] Implement `list --registry`.
- [x] Implement `inspect <name> --registry`.
- [x] Implement `select <task> --registry`, defaulting to `trusted` skills
  only.
- [x] Add `--include-review-required` for review-mode selection.

## Task 10: Registry Verification And Review State

- [x] Write failing tests for registry verification, tamper detection,
  unknown provenance detection, index refresh, reject, disable, and reindex.
- [x] Implement `verify --registry` with `ok` / `failed` result.
- [x] Detect sanitized hash mismatch and missing sanitized skill files.
- [x] Count unknown provenance records.
- [x] Refresh `index.json` after `approve`, `reject`, and `disable`.
- [x] Implement `reindex --registry`.
- [x] Add registry index and verify report schemas and examples.
