# High-Frequency UI Specialist Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote the existing `design-ui-review` skill to a protected specialist playbook for high-frequency UI creation, redesign, review, and polish.

**Architecture:** Keep the current skill name, overlap ownership, bundles, and router behavior. Deepen the catalog body through one on-demand reference, use the existing depth policy and auxiliary hash mechanism, then synchronize the registry and historical batch index without changing the public Schema v1 task-pack contract.

**Tech Stack:** Markdown skill instructions, JSON catalog policy/manifests, Python `unittest`, OneCode sanitizer CLI, SHA-256 registry and batch validation, Git.

---

Run commands from the isolated worktree with:

```bash
cd .worktrees/high-frequency-ui-specialist
export PATH=/tmp/safe-agent-skills-structural-venv/bin:$PATH
```

The baseline is commit `d3eca50`; `scripts/verify.sh` runs 343 tests.

### Task 1: Promote UI Review To Specialist Depth

**Files:**

- Create: `catalog/design/design-ui-review/references/ui-design-playbook.md`
- Modify: `catalog/design/design-ui-review/SKILL.md`
- Modify: `catalog/design/design-ui-review/skill.json`
- Modify: `catalog/design/design-ui-review/SANITIZATION_REPORT.json`
- Modify: `catalog/depth-policy.json`
- Modify: `catalog/index.json`
- Modify: `tests/test_skill_depth.py`

- [ ] **Step 1: Write the failing real-catalog specialist test**

Add this test to `SkillDepthTest`:

```python
def test_real_ui_review_is_specialist_with_protected_reference(self):
    report = audit_catalog_depth(ROOT / "catalog", ROOT / "catalog/depth-policy.json")
    ui_report = next(item for item in report["skills"] if item["name"] == "design-ui-review")
    skill_dir = ROOT / "catalog/design/design-ui-review"
    manifest = json.loads((skill_dir / "skill.json").read_text(encoding="utf-8"))

    self.assertEqual(ui_report["depth_class"], "specialist")
    self.assertEqual(ui_report["reference_count"], 1)
    self.assertIn("Decision Guidance", ui_report["sections"])
    self.assertIn("Evidence Minimum", ui_report["sections"])
    self.assertIn("References", ui_report["sections"])
    self.assertEqual(ui_report["warnings"], [])
    self.assertEqual(
        manifest["hashes"]["auxiliary_sha256"],
        auxiliary_content_sha256(skill_dir),
    )
```

Import `audit_catalog_depth` beside `analyze_skill` at the top of the test file.

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
PYTHONPATH=src python -m unittest \
  tests.test_skill_depth.SkillDepthTest.test_real_ui_review_is_specialist_with_protected_reference -v
```

Expected: FAIL because the policy currently classifies `design-ui-review` as
`routing_card` and the skill has no reference asset.

- [ ] **Step 3: Add the focused UI design reference**

Create `references/ui-design-playbook.md` with these sections and decisions:

```markdown
# UI Design Playbook

Use this guide when a task requires implementation-level UI creation or a
substantial visual pass. Preserve the host project's product behavior and
technical stack unless the request explicitly changes them.

## Product And Framework Fit

- For data-heavy React admin tools, prefer the existing app stack; use Refine
  only when a new resource-oriented foundation is actually needed, and use
  shadcn/ui or existing source-owned primitives for the presentation layer.
- For Vue admin products, retain the existing Vue system; consider Soybean
  Admin only for new admin foundations that need its routing and permissions.
- For marketing, documentation, and GEO sites, prefer semantic Astro or the
  repository's existing framework. Treat AstroWind as a starter, not a visual
  identity.
- For React SaaS component systems, choose source-owned shadcn/ui and Radix
  when long-term control matters; choose HeroUI when delivery speed matters
  more than owning every primitive.
- Use Motion for React for state meaning and continuity. Keep Magic UI or
  Aceternity UI to selective landing-page accents, never dense work surfaces.

## Source Of Truth And Implementation Order

Read `DESIGN.md` first. If it is absent, record audience, product tone,
density, typography, semantic colors, surfaces, component states, motion, and
accessibility in a concise design brief before broad visual changes. Implement
tokens first, shared primitives second, representative flows third, and only
then sweep page-level drift.

## State And Responsive Coverage

Cover default, hover, focus, active, selected, disabled, loading, empty, error,
and success states that exist in the workflow. Check content fit, keyboard
reachability, reduced motion, contrast, and stable layouts at narrow mobile
and wide desktop viewports.

## Visual Verification

Verify the primary workflow with rendered desktop and mobile screenshots.
Check page silhouette, component family, hierarchy, overflow, and state
feedback. When rendering is unavailable, name the unverified routes, states,
and viewports instead of claiming visual completion.
```

- [ ] **Step 4: Deepen `SKILL.md` without duplicating narrow skills**

Update the frontmatter description to trigger on creating and redesigning as
well as reviewing UI. Add `## Decision Guidance`, `## Evidence Minimum`, and
`## References` sections. The guidance must:

- classify work as `focused_review`, `system_restyle`, `new_interface`, or
  `product_redesign`;
- preserve behavior and information architecture unless redesign is explicit;
- require a visual source of truth, product/audience context, target workflows,
  viewport targets, state coverage, and verification evidence;
- direct full implementation work to
  `references/ui-design-playbook.md`;
- retain host approval for installs, network access, publishing, credentials,
  and production actions.

- [ ] **Step 5: Classify and reseal the specialist**

Add this sorted policy entry:

```json
"design-ui-review": "specialist"
```

Then run:

```bash
PYTHONPATH=src python -m onecode_skill_sanitizer reseal-content \
  catalog/design/design-ui-review
PYTHONPATH=src python -m onecode_skill_sanitizer reindex --registry catalog
```

Expected: `skill.json` and its sanitization report receive the new body,
auxiliary, and manifest hashes; unrelated reports remain unchanged.

- [ ] **Step 6: Verify GREEN and catalog integrity**

Run:

```bash
PYTHONPATH=src python -m unittest tests.test_skill_depth tests.test_registry -v
PYTHONPATH=src python -m onecode_skill_sanitizer depth-check \
  --catalog catalog --policy catalog/depth-policy.json
PYTHONPATH=src python -m onecode_skill_sanitizer verify --registry catalog
PYTHONPATH=src python -m onecode_skill_sanitizer schema-check --registry catalog
```

Expected: 168 routing cards, 4 specialists, 0 depth errors/warnings; registry
reports 172 skills, 166 trusted, and 0 tampered; schema check passes.

- [ ] **Step 7: Commit the specialist upgrade**

```bash
git add catalog/design/design-ui-review catalog/depth-policy.json \
  catalog/index.json tests/test_skill_depth.py
git commit -m "feat: deepen high-frequency ui design skill"
```

### Task 2: Synchronize Historical Batch Evidence

**Files:**

- Modify: `batches/index.json`

- [ ] **Step 1: Confirm the expected batch mismatch before regeneration**

Run:

```bash
PYTHONPATH=src python -m onecode_skill_sanitizer batch-check \
  --batches batches --catalog catalog --index batches/index.json
```

Expected: exit 2 with one `batch-index-catalog-hash-mismatch` for the evolved
`design-ui-review` canonical body.

- [ ] **Step 2: Rebuild while preserving promotion history**

Run:

```bash
PYTHONPATH=src python -m onecode_skill_sanitizer batch-compact \
  --batches batches --catalog catalog --index batches/index.json \
  --source-commit 89322c2
```

Expected: 471 items, 303 active drafts, 168 promoted. The existing
`design-ui-review/PROMOTED.md` remains, its source hash and source commit remain
unchanged, while the index records the new catalog hash and
`content_match: false`.

- [ ] **Step 3: Verify batch integrity and review the narrow diff**

Run:

```bash
PYTHONPATH=src python -m onecode_skill_sanitizer batch-check \
  --batches batches --catalog catalog --index batches/index.json
git diff -- batches/index.json
```

Expected: batch check exits 0 with 471 items and 167 compacted records. The
index diff changes only `design-ui-review.catalog_sha256` and
`design-ui-review.content_match`.

- [ ] **Step 4: Commit the synchronized index**

```bash
git add batches/index.json
git commit -m "chore: sync ui specialist batch evidence"
```

### Task 3: Update Maintained Policy And Closure Evidence

**Files:**

- Modify: `docs/skill-depth-policy.md`
- Modify: `docs/maintenance-log.md`
- Modify: `docs/structural-maintainability-closure-report-2026-07-11.md`

- [ ] **Step 1: Update maintained documentation**

Document `design-ui-review` as the fourth specialist and the first specialist
chosen explicitly by high-frequency usage. Record these final values:

- 168 routing cards and 4 specialists;
- 4 specialist reference assets;
- 471 batch items and 167 historical compactions;
- 5 promoted records whose historical body differs from the current catalog;
- 159 Markdown files under `docs/` after the approved spec and this plan;
- 344 tests, assuming only the new depth regression is added;
- 43 of 43 router evaluation cases;
- 172 catalog skills, 166 trusted, 0 tampered, 0 unknown provenance.

Add the UI reseal command to `docs/skill-depth-policy.md` and explain that
high-frequency task evidence is a valid reason to promote a routing card to a
specialist.

- [ ] **Step 2: Run focused documentation and compatibility checks**

```bash
PYTHONPATH=src python -m unittest tests.test_documentation -v
PYTHONPATH=src python -m unittest \
  tests.test_router_cli.RouterCliTest.test_smart_schema_v1_preserves_current_contract \
  tests.test_router_cli.RouterCliTest.test_task_pack_mesh_schema_v1_preserves_current_contract_shape -v
git diff --check
```

Expected: all checks pass and the Schema v1 payload-shape hash remains
unchanged.

- [ ] **Step 3: Run the complete verification suite**

```bash
PATH=/tmp/safe-agent-skills-structural-venv/bin:$PATH bash scripts/verify.sh
```

Expected: exit 0 with 344 tests passing and all router, registry, schema,
batch, depth, contract, JSON, documentation, and private-path gates passing.

- [ ] **Step 4: Correct recorded metrics if verification differs**

Compare the actual test total, router-eval total, docs count, and depth counts
with the maintained documents. Update only mismatched measured values, rerun
the affected checks, and do not retain predicted values that differ from fresh
evidence.

- [ ] **Step 5: Commit the maintenance evidence**

```bash
git add docs/skill-depth-policy.md docs/maintenance-log.md \
  docs/structural-maintainability-closure-report-2026-07-11.md
git commit -m "docs: record high-frequency ui specialist"
```

### Task 4: Verify, Integrate, And Publish

**Files:** none beyond committed work.

- [ ] **Step 1: Verify committed feature HEAD**

```bash
PATH=/tmp/safe-agent-skills-structural-venv/bin:$PATH bash scripts/verify.sh
git status --short --branch
git log --oneline d3eca50..HEAD
```

Expected: verification exits 0 and the feature worktree is clean.

- [ ] **Step 2: Integrate the confirmed feature**

Use `superpowers:finishing-a-development-branch`. Fast-forward local `main`
to `feat/high-frequency-ui-specialist`, rerun `scripts/verify.sh` on `main`, and
push `main` to `origin` without force.

- [ ] **Step 3: Confirm GitHub verification and clean up**

Watch the triggered GitHub Actions Verify run until completion. After all
Python matrix jobs pass, remove the clean feature worktree and delete the
merged local feature branch.
