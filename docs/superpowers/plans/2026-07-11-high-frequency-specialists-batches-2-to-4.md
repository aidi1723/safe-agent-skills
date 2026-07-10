# High-Frequency Specialists Batches 2 To 4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote the remaining eight identified high-frequency skills to independently verified specialists and publish a synchronized catalog, batch index, and maintenance baseline.

**Architecture:** Keep all public names, contracts, bundles, overlap ownership, and router behavior unchanged. For each skill, add one failing real-catalog depth test, one focused reference, decision/evidence/reference sections, a sorted policy override, content resealing, registry/schema validation, and an individual commit; synchronize batch history after each three-skill group and finalize documentation after all eight.

**Tech Stack:** Markdown, JSON, Python `unittest`, OneCode sanitizer CLI, SHA-256 auxiliary integrity, Git, GitHub Actions.

---

Worktree: `.worktrees/high-frequency-specialists-batches-2-to-4`.
Baseline: `96875bb`, 347 tests passing.

## Per-Skill Verification Contract

Every task below follows this complete sequence before the next skill starts:

1. Add the named test to `tests/test_skill_depth.py`:

   ```python
   def test_real_<case>_is_specialist_with_protected_reference(self):
       self.assert_real_specialist("<skill-name>")
   ```

2. Run only that test and observe `routing_card != specialist`.
3. Create the exact reference file named by the task.
4. Add `Decision Guidance`, `Evidence Minimum`, and `References` sections to
   the skill body; expand its safe workflow and failure boundary as specified.
5. Add the sorted specialist entry to `catalog/depth-policy.json`.
6. Run `reseal-content <skill-dir>` and `reindex --registry catalog`.
7. Run the single test, `quick_validate.py`, registry verification, schema
   check, `git diff --check`, and confirm no unrelated reports changed.
8. Commit only that skill, policy, catalog index, and depth test.

Use this validator command for every skill:

```bash
/tmp/safe-agent-skills-structural-venv/bin/python \
  "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" \
  <skill-dir>
```

### Task 1: Codebase Explore Map

**Files:**

- Create: `catalog/code/codebase-explore-map/references/repository-evidence-map.md`
- Modify: `catalog/code/codebase-explore-map/{SKILL.md,skill.json,SANITIZATION_REPORT.json}`
- Modify: `catalog/{depth-policy.json,index.json}`
- Modify: `tests/test_skill_depth.py`

- [ ] Add test case `codebase_explore` for `codebase-explore-map`; verify RED.
- [ ] Add a reference covering instruction precedence, manifests, entry points,
  runtime/data flow, ownership, generated/vendor exclusions, config, tests,
  release commands, targeted searches, unknowns, and stopping criteria.
- [ ] Add decision guidance for `orientation`, `change_mapping`,
  `incident_mapping`, and `architecture_review`; require evidence for relevant
  paths and prohibit filename-only architectural claims or broad inventory.
- [ ] Reseal, reindex, run the per-skill verification contract, and commit:
  `feat: deepen high-frequency codebase exploration skill`.

### Task 2: Execution Browser Check

**Files:**

- Create: `catalog/execution/execution-browser-check/references/browser-verification-evidence.md`
- Modify: `catalog/execution/execution-browser-check/{SKILL.md,skill.json,SANITIZATION_REPORT.json}`
- Modify: `catalog/{depth-policy.json,index.json}`
- Modify: `tests/test_skill_depth.py`

- [ ] Add test case `browser_check` for `execution-browser-check`; verify RED.
- [ ] Add a reference covering approved targets, server readiness, navigation,
  visible/DOM/URL assertions, screenshots, viewport matrix, forms, console and
  network failures, canvas/media checks, reproduction traces, and artifacts.
- [ ] Add decision guidance for `static_inspection`, `smoke_flow`,
  `responsive_visual`, and `stateful_flow`; require explicit approval before
  auth, payment, destructive submissions, uploads/downloads, account mutation,
  private sessions, or non-approved hosts.
- [ ] Reseal, reindex, verify, and commit:
  `feat: deepen high-frequency browser verification skill`.

### Task 3: Engineering CI Troubleshoot

**Files:**

- Create: `catalog/engineering/engineering-ci-troubleshoot/references/ci-diagnosis-evidence.md`
- Modify: `catalog/engineering/engineering-ci-troubleshoot/{SKILL.md,skill.json,SANITIZATION_REPORT.json}`
- Modify: `catalog/{depth-policy.json,index.json}`
- Modify: `tests/test_skill_depth.py`

- [ ] Add test case `ci_troubleshoot` for `engineering-ci-troubleshoot`; verify RED.
- [ ] Add a reference covering first actionable failure, job/matrix context,
  code/config/dependency/cache/environment/infrastructure/flake classification,
  bounded reproduction, minimal hypotheses, rerun evidence, and residual risk.
- [ ] Require evidence before fixes and prohibit remote reruns, secret changes,
  bypassed checks, release permission changes, and treating a passing retry as
  a flake fix.
- [ ] Reseal, reindex, verify, and commit:
  `feat: deepen high-frequency ci troubleshooting skill`.

### Task 4: Synchronize Batch 2

**Files:** Modify `batches/index.json`.

- [ ] Run `batch-check`; confirm exactly the three Batch 2 skills have stale
  catalog hashes.
- [ ] Run `batch-compact` with `--source-commit 89322c2`, then `batch-check`.
- [ ] Confirm 471 items, 167 historical compactions, 0 issues, and a diff that
  changes only three catalog hashes and `content_match` values.
- [ ] Commit: `chore: sync engineering specialist batch evidence`.

### Task 5: Office PDF Report

**Files:**

- Create: `catalog/office/office-pdf-report/references/pdf-evidence-rendering-guide.md`
- Modify: `catalog/office/office-pdf-report/{SKILL.md,skill.json,SANITIZATION_REPORT.json}`
- Modify: `catalog/{depth-policy.json,index.json}`
- Modify: `tests/test_skill_depth.py`

- [ ] Add test case `pdf_report` for `office-pdf-report`; verify RED.
- [ ] Add a reference covering file identity, metadata/text extraction, page
  rendering, OCR choice, tables, forms, signatures, page citations, encryption,
  damaged pages, extraction gaps, output verification, and original preservation.
- [ ] Add decision guidance for `text_extraction`, `content_review`,
  `layout_review`, and `artifact_generation`; forbid layout/signature claims
  from text alone and access outside approved files.
- [ ] Reseal, reindex, verify, and commit:
  `feat: deepen high-frequency pdf reporting skill`.

### Task 6: Office DOCX Brief

**Files:**

- Create: `catalog/office/office-docx-brief/references/docx-delivery-evidence.md`
- Modify: `catalog/office/office-docx-brief/{SKILL.md,skill.json,SANITIZATION_REPORT.json}`
- Modify: `catalog/{depth-policy.json,index.json}`
- Modify: `tests/test_skill_depth.py`

- [ ] Add test case `docx_brief` for `office-docx-brief`; verify RED.
- [ ] Add a reference covering purpose/audience, source facts, outline,
  styles/headings, tables/lists, headers/footers, pagination, references,
  comments/tracked content boundaries, export, rendering, and original files.
- [ ] Add decision guidance for `draft`, `edit`, `format`, and `review`; require
  rendered evidence for produced documents and explicit assumptions when
  requirements are incomplete.
- [ ] Reseal, reindex, verify, and commit:
  `feat: deepen high-frequency docx delivery skill`.

### Task 7: Data Table Analysis

**Files:**

- Create: `catalog/data/data-table-analysis/references/tabular-analysis-evidence.md`
- Modify: `catalog/data/data-table-analysis/{SKILL.md,skill.json,SANITIZATION_REPORT.json}`
- Modify: `catalog/{depth-policy.json,index.json}`
- Modify: `tests/test_skill_depth.py`

- [ ] Add test case `table_analysis` for `data-table-analysis`; verify RED.
- [ ] Add a reference covering schema/key definitions, counts, missingness,
  duplicates, types, joins, filters, units, denominators, outliers, aggregates,
  reproducible transformations, reconciliation, uncertainty, and privacy.
- [ ] Add decision guidance for `profile`, `clean`, `analyze`, and `reconcile`;
  separate cleaning from analysis, prohibit unsupported causality and external
  uploads, and preserve source data.
- [ ] Reseal, reindex, verify, and commit:
  `feat: deepen high-frequency table analysis skill`.

### Task 8: Synchronize Batch 3

- [ ] Repeat the Batch 2 synchronization contract for the three Batch 3 skills.
- [ ] Commit: `chore: sync document data specialist evidence`.

### Task 9: Content SEO Brief

**Files:**

- Create: `catalog/content/content-seo-brief/references/seo-content-evidence.md`
- Modify: `catalog/content/content-seo-brief/{SKILL.md,skill.json,SANITIZATION_REPORT.json}`
- Modify: `catalog/{depth-policy.json,index.json}`
- Modify: `tests/test_skill_depth.py`

- [ ] Add test case `seo_brief` for `content-seo-brief`; verify RED.
- [ ] Add a reference covering audience/market, page type, search intent,
  keyword/entity roles, information architecture, canonical intent, internal
  links, claims/sources, freshness, duplication, conversion, and handoff.
- [ ] Add decision guidance for `new_page`, `refresh`, `cluster`, and
  `product_listing`; prohibit ranking promises, stuffing, copied content,
  unsupported claims, and conflating content with technical SEO verification.
- [ ] Reseal, reindex, verify, and commit:
  `feat: deepen high-frequency seo briefing skill`.

### Task 10: Execution Publish Check

**Files:**

- Create: `catalog/execution/execution-publish-check/references/publication-readiness-evidence.md`
- Modify: `catalog/execution/execution-publish-check/{SKILL.md,skill.json,SANITIZATION_REPORT.json}`
- Modify: `catalog/{depth-policy.json,index.json}`
- Modify: `tests/test_skill_depth.py`

- [ ] Add test case `publish_check` for `execution-publish-check`; verify RED.
- [ ] Add a reference covering target, artifact identity/version/checksum,
  source revision, build/tests, provenance/license, generated files, config,
  migration, rollback, approval owner, blockers, and readiness status.
- [ ] Add decision guidance for `not_ready`, `ready_for_handoff`,
  `ready_for_approval`, and `approved_to_publish`; keep readiness separate from
  upload/push/release/deploy authority and required gates.
- [ ] Reseal, reindex, verify, and commit:
  `feat: deepen high-frequency publish readiness skill`.

### Task 11: Synchronize Batch 4

- [ ] Repeat the batch synchronization contract for the two Batch 4 skills.
- [ ] Confirm final 471 items, 167 historical compactions, 0 issues, and 16
  promoted records with `content_match: false`.
- [ ] Commit: `chore: sync publication specialist evidence`.

### Task 12: Final Documentation And Publication

**Files:** Modify `docs/skill-depth-policy.md`, `docs/maintenance-log.md`, and
`docs/structural-maintainability-closure-report-2026-07-11.md`.

- [ ] Record 157 routing cards, 15 specialists, 15 specialist references, 16
  evolved promoted records, 163 docs Markdown files, 355 tests if no additional
  tests are introduced, 43 router eval cases, and unchanged catalog trust.
- [ ] Run all depth/documentation tests, Schema v1 shape tests, depth/registry/
  schema/batch checks, `git diff --check`, and private-path scan.
- [ ] Run `scripts/verify.sh`; replace predicted counts with measured values.
- [ ] Commit: `docs: complete high-frequency specialist coverage`.
- [ ] Run full verification from committed feature HEAD.
- [ ] Fast-forward `main`, verify again, push without force, wait for all GitHub
  Actions Python jobs, and remove the clean worktree and merged branch.
