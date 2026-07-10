# High-Frequency Core Specialists Batch 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote `code-review-risk`, `code-test-regression`, and `research-source-check` to independently verified specialists with protected on-demand references.

**Architecture:** Preserve all existing skill names, contracts, bundles, overlap ownership, and router behavior. Implement one skill at a time through a real-catalog failing test, one focused reference, specialist policy classification, content resealing, registry checks, and a dedicated commit; synchronize shared batch and documentation evidence only after all three pass.

**Tech Stack:** Markdown skill instructions, JSON depth/catalog/batch indexes, Python `unittest`, OneCode sanitizer CLI, SHA-256 auxiliary integrity, Git.

---

Run commands from:

```bash
cd .worktrees/high-frequency-specialists-batch-1
export PATH=/tmp/safe-agent-skills-structural-venv/bin:$PATH
```

Baseline commit: `990842d`. Baseline verification: 344 tests passing.

### Task 1: Deepen Code Review Risk

**Files:**

- Create: `catalog/code/code-review-risk/references/review-evidence-checklist.md`
- Modify: `catalog/code/code-review-risk/SKILL.md`
- Modify: `catalog/code/code-review-risk/skill.json`
- Modify: `catalog/code/code-review-risk/SANITIZATION_REPORT.json`
- Modify: `catalog/depth-policy.json`
- Modify: `catalog/index.json`
- Modify: `tests/test_skill_depth.py`

- [ ] **Step 1: Write the failing specialist test**

Add a reusable assertion to `SkillDepthTest`:

```python
def assert_real_specialist(self, name: str):
    report = audit_catalog_depth(ROOT / "catalog", ROOT / "catalog/depth-policy.json")
    skill_report = next(item for item in report["skills"] if item["name"] == name)
    skill_dir = next((ROOT / "catalog").glob(f"*/{name}"))
    manifest = json.loads((skill_dir / "skill.json").read_text(encoding="utf-8"))
    self.assertEqual(skill_report["depth_class"], "specialist")
    self.assertEqual(skill_report["reference_count"], 1)
    self.assertIn("Decision Guidance", skill_report["sections"])
    self.assertIn("Evidence Minimum", skill_report["sections"])
    self.assertIn("References", skill_report["sections"])
    self.assertEqual(skill_report["warnings"], [])
    self.assertEqual(
        manifest["hashes"]["auxiliary_sha256"],
        auxiliary_content_sha256(skill_dir),
    )
```

Add:

```python
def test_real_code_review_is_specialist_with_protected_reference(self):
    self.assert_real_specialist("code-review-risk")
```

- [ ] **Step 2: Verify RED**

```bash
PYTHONPATH=src python -m unittest \
  tests.test_skill_depth.SkillDepthTest.test_real_code_review_is_specialist_with_protected_reference -v
```

Expected: FAIL because `code-review-risk` is a routing card without a
reference.

- [ ] **Step 3: Add the review evidence reference**

Create `review-evidence-checklist.md` with:

```markdown
# Code Review Evidence Checklist

Use this checklist for a high-confidence review of a change set. Review the
requested behavior and changed boundary, not the repository in the abstract.

## Intent And Reachability

- Record the intended behavior, affected users, entry points, changed files,
  and observable success criteria.
- Trace whether each suspected path is reachable with realistic inputs and
  configuration. Do not report purely hypothetical behavior as a defect.
- Separate facts visible in the diff from assumptions that require execution,
  external state, or product clarification.

## Correctness And State

- Check input validation, output contracts, error paths, cleanup, retries,
  partial failure, ordering, concurrency, idempotency, caching, and persistence.
- Follow data across module, process, API, schema, and storage boundaries.
- Review compatibility, migrations, feature flags, defaults, and rollback when
  the change affects shared or persisted behavior.

## Finding Standard

Each finding must state severity, file and line, triggering conditions,
concrete impact, supporting evidence, and the smallest correction target.
Classify severity from impact, likelihood, reachability, blast radius, and
recoverability. Keep optional cleanup separate from defects.

## Test And Residual Risk

Map risky behavior to existing or missing tests. Name unverified assumptions,
unavailable runtime evidence, generated files not reviewed, and downstream
consumers that may still require validation.
```

- [ ] **Step 4: Deepen the skill body**

Keep the existing required sections and add:

- `## Decision Guidance`: classify findings as `critical`, `high`, `medium`,
  `low`, or `advisory`; require reachability and concrete impact; separate
  correctness from optional maintainability advice.
- `## Evidence Minimum`: intended behavior, diff/base, affected contracts,
  triggering path, impact, file/line evidence, test coverage, residual risk.
- `## References`: load the checklist for multi-file, shared-contract,
  concurrency, persistence, security, migration, or release-sensitive reviews.

Expand the safe workflow to trace data and state boundaries, compatibility,
error handling, and test gaps. Keep output findings-first. Do not authorize
running code, changing files, contacting services, or accepting the change.

- [ ] **Step 5: Classify, reseal, and reindex**

Add the sorted policy entry:

```json
"code-review-risk": "specialist"
```

Run:

```bash
PYTHONPATH=src python -m onecode_skill_sanitizer reseal-content \
  catalog/code/code-review-risk
PYTHONPATH=src python -m onecode_skill_sanitizer reindex --registry catalog
```

- [ ] **Step 6: Verify GREEN and commit**

```bash
PYTHONPATH=src python -m unittest \
  tests.test_skill_depth.SkillDepthTest.test_real_code_review_is_specialist_with_protected_reference -v
/tmp/safe-agent-skills-structural-venv/bin/python \
  "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" \
  catalog/code/code-review-risk
PYTHONPATH=src python -m onecode_skill_sanitizer verify --registry catalog
PYTHONPATH=src python -m onecode_skill_sanitizer schema-check --registry catalog
git diff --check
git add catalog/code/code-review-risk catalog/depth-policy.json \
  catalog/index.json tests/test_skill_depth.py
git commit -m "feat: deepen high-frequency code review skill"
```

Expected: test and validators pass; registry remains 172 skills, 166 trusted,
0 tampered; no unrelated report changes.

### Task 2: Deepen Code Test Regression

**Files:**

- Create: `catalog/code/code-test-regression/references/regression-evidence-guide.md`
- Modify: `catalog/code/code-test-regression/SKILL.md`
- Modify: `catalog/code/code-test-regression/skill.json`
- Modify: `catalog/code/code-test-regression/SANITIZATION_REPORT.json`
- Modify: `catalog/depth-policy.json`
- Modify: `catalog/index.json`
- Modify: `tests/test_skill_depth.py`

- [ ] **Step 1: Write and run the failing test**

Add:

```python
def test_real_regression_testing_is_specialist_with_protected_reference(self):
    self.assert_real_specialist("code-test-regression")
```

Run the single test. Expected: FAIL because the skill remains a routing card.

- [ ] **Step 2: Add the regression evidence reference**

Create `regression-evidence-guide.md` with:

```markdown
# Regression Test Evidence Guide

Use this guide to prove a behavior change and protect it from recurrence. Bind
the test to an externally meaningful contract rather than incidental internals.

## Choose The Test Boundary

- Use a unit test for isolated deterministic logic and an integration or
  contract test when the defect crosses modules, schemas, storage, processes,
  or service boundaries.
- Use end-to-end coverage only when the user-visible workflow or integration
  wiring is the behavior at risk.
- Prefer the lowest boundary that reproduces the failure without replacing
  real behavior with mocks.

## Red And Green Evidence

Record the failing assertion against the old behavior and the passing result
after the change. A test written after implementation must be proven by
temporarily reverting the fix or otherwise reproducing the original failure.
Distinguish assertion failure from setup, import, timeout, or environment error.

## Reliability

Minimize fixtures, time, randomness, shared state, network dependence, and
implementation-coupled mocks. Review snapshots line by line and update them
only when the entire output change is intended. Treat retries as evidence of
flakiness, not as proof of correctness.

## Verification Scope

Run the targeted test, then the nearest shared test group, and expand to the
full suite when the change touches shared contracts or broad workflows. Record
commands, counts, skipped tests, unavailable dependencies, flakes, and residual
risk.
```

- [ ] **Step 3: Deepen, classify, and reseal**

Add decision guidance for unit/integration/contract/e2e selection, true RED vs
test errors, behavioral vs implementation assertions, and targeted vs broad
verification. Add evidence minimums for old failure, new pass, test identity,
fixture dependencies, command output, skipped/flaky coverage, and residual
risk. Link the reference for shared boundaries, snapshots, timing, mocks,
flaky tests, and broad blast radius.

Add:

```json
"code-test-regression": "specialist"
```

Run `reseal-content` for this skill and `reindex --registry catalog`.

- [ ] **Step 4: Verify GREEN and commit**

Run the single new test, `quick_validate.py`, registry verification, schema
check, and `git diff --check`, then commit:

```bash
git add catalog/code/code-test-regression catalog/depth-policy.json \
  catalog/index.json tests/test_skill_depth.py
git commit -m "feat: deepen high-frequency regression testing skill"
```

### Task 3: Deepen Research Source Check

**Files:**

- Create: `catalog/research/research-source-check/references/source-evidence-assessment.md`
- Modify: `catalog/research/research-source-check/SKILL.md`
- Modify: `catalog/research/research-source-check/skill.json`
- Modify: `catalog/research/research-source-check/SANITIZATION_REPORT.json`
- Modify: `catalog/depth-policy.json`
- Modify: `catalog/index.json`
- Modify: `tests/test_skill_depth.py`

- [ ] **Step 1: Write and run the failing test**

Add:

```python
def test_real_source_check_is_specialist_with_protected_reference(self):
    self.assert_real_specialist("research-source-check")
```

Run the single test. Expected: FAIL because the skill remains a routing card.

- [ ] **Step 2: Add the source evidence reference**

Create `source-evidence-assessment.md` with:

```markdown
# Source Evidence Assessment

Use this guide to verify claims at the level required by their impact and
volatility. A citation is useful only when it directly supports the attached
claim and the reader can identify the source.

## Source Strength

Prefer primary records, official documentation, standards, statutes, filings,
datasets, and original research. Use strong secondary synthesis when primary
material is unavailable or requires interpretation. Treat search snippets,
aggregators, unsourced summaries, and copied citations as discovery leads, not
verification evidence.

Assess authority, directness, scope, date, version, methodology, independence,
conflicts of interest, and whether the cited passage supports the complete
claim rather than a nearby idea.

## Claim Status

Mark each material claim `verified`, `qualified`, `disputed`, `stale`, or
`unverified`. Separate source facts, calculations, inference, forecasts, and
opinion. For dynamic facts, record the as-of date and the event or update that
would require rechecking.

## Conflicts And Gaps

When sources disagree, compare definitions, dates, populations, methods,
versions, jurisdictions, and incentives. Do not silently average incompatible
figures. State the disagreement and explain which evidence is more applicable.

## Citation Record

Record title, publisher or author, publication or update date, stable URL or
identifier, access date when relevant, and the exact claim supported. Note
paywalls, inaccessible archives, missing versions, and evidence that could not
be independently checked.
```

- [ ] **Step 3: Deepen, classify, and reseal**

Add decision guidance for source tiers and claim states, evidence minimums for
claim/source mapping and freshness, and a reference link for dynamic,
disputed, high-impact, regulated, multi-source, or inaccessible evidence.
Explicitly prohibit fabricated citations, snippet-only verification, silent
conflict resolution, and bypassing access controls.

Add:

```json
"research-source-check": "specialist"
```

Run `reseal-content` and `reindex`.

- [ ] **Step 4: Verify GREEN and commit**

Run the single new test, `quick_validate.py`, registry verification, schema
check, and `git diff --check`, then commit:

```bash
git add catalog/research/research-source-check catalog/depth-policy.json \
  catalog/index.json tests/test_skill_depth.py
git commit -m "feat: deepen high-frequency source verification skill"
```

### Task 4: Synchronize Batch History

**Files:**

- Modify: `batches/index.json`

- [ ] **Step 1: Verify the three expected stale catalog hashes**

Run `batch-check`. Expected: exit 2 with exactly three
`batch-index-catalog-hash-mismatch` issues corresponding to the three evolved
skills.

- [ ] **Step 2: Rebuild and validate**

```bash
PYTHONPATH=src python -m onecode_skill_sanitizer batch-compact \
  --batches batches --catalog catalog --index batches/index.json \
  --source-commit 89322c2
PYTHONPATH=src python -m onecode_skill_sanitizer batch-check \
  --batches batches --catalog catalog --index batches/index.json
git diff -- batches/index.json
```

Expected: 471 items, 167 historical compactions, 0 issues. Only the three
skills' current catalog hashes and `content_match` values change; their
historical source hashes, commits, and promotion records remain unchanged.

- [ ] **Step 3: Commit**

```bash
git add batches/index.json
git commit -m "chore: sync specialist batch-one evidence"
```

### Task 5: Update Maintained Evidence And Publish

**Files:**

- Modify: `docs/skill-depth-policy.md`
- Modify: `docs/maintenance-log.md`
- Modify: `docs/structural-maintainability-closure-report-2026-07-11.md`

- [ ] **Step 1: Record measured outcomes**

Update maintained documents to record:

- 165 routing cards and 7 specialists;
- 7 specialist reference assets;
- 8 promoted records whose historical body differs from current catalog;
- 161 Markdown files under `docs/` after the approved spec and this plan;
- 347 tests if the three planned tests are the only additions;
- unchanged 43 router evaluation cases;
- 172 catalog skills, 166 trusted, 0 tampered, 0 unknown provenance;
- the first high-frequency batch and its three skills.

- [ ] **Step 2: Run focused compatibility checks**

```bash
PYTHONPATH=src python -m unittest tests.test_skill_depth tests.test_documentation -v
PYTHONPATH=src python -m unittest \
  tests.test_router_cli.RouterCliTest.test_smart_schema_v1_preserves_current_contract \
  tests.test_router_cli.RouterCliTest.test_task_pack_mesh_schema_v1_preserves_current_contract_shape -v
PYTHONPATH=src python -m onecode_skill_sanitizer depth-check \
  --catalog catalog --policy catalog/depth-policy.json
git diff --check
```

- [ ] **Step 3: Run full verification and correct metrics**

```bash
PATH=/tmp/safe-agent-skills-structural-venv/bin:$PATH bash scripts/verify.sh
```

Expected: exit 0. Replace predicted documentation/test/router totals with fresh
measured values if they differ, then rerun affected checks.

- [ ] **Step 4: Commit maintained evidence**

```bash
git add docs/skill-depth-policy.md docs/maintenance-log.md \
  docs/structural-maintainability-closure-report-2026-07-11.md
git commit -m "docs: record specialist batch one"
```

- [ ] **Step 5: Verify committed HEAD, integrate, and publish**

Run the full suite from committed feature HEAD. Use
`superpowers:finishing-a-development-branch` to fast-forward `main`, rerun the
suite on `main`, push without force, wait for all GitHub Actions Python matrix
jobs, and remove the clean worktree and merged feature branch.
