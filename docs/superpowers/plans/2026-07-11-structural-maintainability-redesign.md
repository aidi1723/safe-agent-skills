# Structural Maintainability Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redistribute core code into focused modules, make batch and documentation lifecycle explicit, add risk-aware skill-depth governance, and publish a verified compatibility-preserving release.

**Architecture:** Keep `cli.py` and `router.py` as public compatibility facades while moving cohesive pure functions into flat owner modules. Add deterministic batch and skill-depth audits whose read-only checks run in `scripts/verify.sh`; compact only byte-identical promoted batch bodies and preserve catalog/provenance hashes.

**Tech Stack:** Python 3.11+, standard library `argparse`, `json`, `pathlib`, `hashlib`, `unittest`, JSON Schema 2020-12, Ruff, Markdown, Git.

---

Run all commands from the structural worktree:

```bash
cd /Users/aidi/大字典/safe-agent-skills/.worktrees/structural-maintainability
export PATH=/tmp/safe-agent-skills-structural-venv/bin:$PATH
```

The clean baseline is commit `b44cb4d`; `scripts/verify.sh` runs 321 tests.

### Task 1: Extract Task-Pack Rendering

**Files:**

- Create: `src/onecode_skill_sanitizer/rendering.py`
- Create: `tests/test_rendering.py`
- Modify: `src/onecode_skill_sanitizer/cli.py:1293-1980`

- [ ] **Step 1: Write the failing public-boundary test**

```python
from onecode_skill_sanitizer import cli
from onecode_skill_sanitizer import rendering


class RenderingBoundaryTest(unittest.TestCase):
    def test_cli_reexports_rendering_functions(self):
        self.assertIs(cli.render_task_pack_markdown, rendering.render_task_pack_markdown)
        self.assertIs(cli.render_task_pack_v2_markdown, rendering.render_task_pack_v2_markdown)
        self.assertIs(cli.markdown_safe_line, rendering.markdown_safe_line)
        self.assertIs(cli.project_legacy_contracts, rendering.project_legacy_contracts)
```

- [ ] **Step 2: Verify the test fails because the module does not exist**

Run: `python -m unittest tests.test_rendering -v`

Expected: `ImportError` for `onecode_skill_sanitizer.rendering`.

- [ ] **Step 3: Move rendering implementation without semantic edits**

Create `rendering.py` with `from __future__ import annotations` and `import
html`, then move the complete existing definitions of
`render_task_pack_markdown()`, `render_task_pack_v2_markdown()`,
`markdown_safe_line()`, and `project_legacy_contracts()` from `cli.py` without
changing their bodies, order, escaping, or trailing-newline behavior.

Replace those definitions in `cli.py` with compatibility imports:

```python
from .rendering import markdown_safe_line
from .rendering import project_legacy_contracts
from .rendering import render_task_pack_markdown
from .rendering import render_task_pack_v2_markdown
```

Do not introduce wrappers here: identity-based compatibility tests require
direct imports, and output tests protect the exact existing bodies.

- [ ] **Step 4: Run focused output and compatibility tests**

Run:

```bash
python -m unittest tests.test_rendering -v
python -m unittest tests.test_registry_cli.RegistryCliTest.test_task_pack_outputs_markdown -v
python -m unittest tests.test_registry_cli.RegistryCliTest.test_smart_schema_v2_matches_strict_top_level_schema_and_markdown -v
```

Expected: all tests pass and existing output assertions remain unchanged.

- [ ] **Step 5: Commit the rendering boundary**

```bash
git add src/onecode_skill_sanitizer/cli.py src/onecode_skill_sanitizer/rendering.py tests/test_rendering.py
git commit -m "refactor: extract task pack rendering"
```

### Task 2: Extract Bulk Candidate Workflows

**Files:**

- Create: `src/onecode_skill_sanitizer/bulk.py`
- Create: `tests/test_bulk.py`
- Modify: `src/onecode_skill_sanitizer/cli.py:2827-3327`

- [ ] **Step 1: Write a failing bulk-module contract test**

```python
from onecode_skill_sanitizer import bulk
from onecode_skill_sanitizer import cli


class BulkBoundaryTest(unittest.TestCase):
    def test_cli_reexports_bulk_builders(self):
        self.assertIs(cli.build_claude_skills_bulk_plan, bulk.build_claude_skills_bulk_plan)
        self.assertIs(cli.build_claude_skills_bulk_drafts, bulk.build_claude_skills_bulk_drafts)
        self.assertIs(cli.build_claude_skills_bulk_assessment, bulk.build_claude_skills_bulk_assessment)
```

- [ ] **Step 2: Verify RED**

Run: `python -m unittest tests.test_bulk -v`

Expected: import failure because `bulk.py` is absent.

- [ ] **Step 3: Move the complete bulk function family**

Move the functions from `claude_skills_candidate_action()` through
`build_claude_skills_bulk_assessment()` into `bulk.py`. Keep CLI-only handlers
in `cli.py`. Use these module imports:

```python
from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import Path


WriteJson = Callable[[Path, dict], None]
```

Add a fifth `write_json_file: WriteJson` parameter to
`bulk.build_claude_skills_bulk_drafts()`. Preserve its existing body and replace
its two calls to `write_json` with calls to `write_json_file`; do not import
`cli.py`, which would create a circular dependency.

The CLI compatibility wrapper keeps the old four-argument API:

```python
def build_claude_skills_bulk_drafts(candidate_map_path, out_dir, batch_size, batch_index):
    return bulk.build_claude_skills_bulk_drafts(
        candidate_map_path,
        out_dir,
        batch_size,
        batch_index,
        write_json,
    )
```

Re-export the remaining pure builders directly.

- [ ] **Step 4: Run bulk regressions and Ruff**

Run:

```bash
python -m unittest tests.test_bulk -v
python -m unittest \
  tests.test_registry_cli.RegistryCliTest.test_claude_skills_bulk_plan_batches_all_non_converted_candidates \
  tests.test_registry_cli.RegistryCliTest.test_claude_skills_bulk_draft_generates_local_review_drafts_for_batch \
  tests.test_registry_cli.RegistryCliTest.test_claude_skills_bulk_assess_ranks_drafts_before_catalog_promotion -v
python -m ruff check src/onecode_skill_sanitizer/cli.py src/onecode_skill_sanitizer/bulk.py tests/test_bulk.py
```

Expected: pass with identical draft and assessment payloads.

- [ ] **Step 5: Commit**

```bash
git add src/onecode_skill_sanitizer/cli.py src/onecode_skill_sanitizer/bulk.py tests/test_bulk.py
git commit -m "refactor: extract bulk skill workflows"
```

### Task 3: Extract Registry Ownership

**Files:**

- Create: `src/onecode_skill_sanitizer/registry.py`
- Create: `tests/test_registry.py`
- Modify: `src/onecode_skill_sanitizer/cli.py:208-401,2094-2287,3739-3812`

- [ ] **Step 1: Write failing registry API tests**

```python
from onecode_skill_sanitizer import cli, registry


class RegistryBoundaryTest(unittest.TestCase):
    def test_cli_reexports_registry_operations(self):
        self.assertIs(cli.load_manifest, registry.load_manifest)
        self.assertIs(cli.build_registry_index, registry.build_registry_index)
        self.assertIs(cli.verify_registry, registry.verify_registry)

    def test_reseal_content_updates_body_and_manifest_hashes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = make_trusted_skill(Path(temp_dir))
            (skill_dir / "SKILL.md").write_text("# Changed\n", encoding="utf-8")
            manifest = registry.reseal_skill_content(skill_dir)
            self.assertEqual(
                manifest["hashes"]["sanitized_sha256"],
                text_sha256("# Changed\n"),
            )
            self.assertEqual(manifest["hashes"]["manifest_sha256"], manifest_sha256(manifest))
```

- [ ] **Step 2: Verify RED**

Run: `python -m unittest tests.test_registry -v`

Expected: import failure for `registry.py`.

- [ ] **Step 3: Move registry IO, verification, and status functions**

Move unchanged registry functions into `registry.py`, with injected clock for
status mutation and explicit content resealing:

```python
def reseal_skill_content(skill_dir: Path) -> dict:
    manifest = load_manifest(skill_dir)
    skill_path = skill_dir / "SKILL.md"
    if not skill_path.is_file():
        raise ValueError(f"missing skill body: {skill_path}")
    manifest["hashes"]["sanitized_sha256"] = text_sha256(
        skill_path.read_text(encoding="utf-8")
    )
    seal_manifest(manifest)
    write_json(skill_dir / "skill.json", manifest)
    report_path = skill_dir / "SANITIZATION_REPORT.json"
    if report_path.is_file():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report.setdefault("hashes", {})["sanitized_sha256"] = manifest["hashes"]["sanitized_sha256"]
        report["hashes"]["manifest_sha256"] = manifest["hashes"]["manifest_sha256"]
        write_json(report_path, report)
    return manifest
```

Keep command handlers in `cli.py`, delegating to registry operations. Preserve
old imports through direct re-exports.

- [ ] **Step 4: Run registry and schema regressions**

Run:

```bash
python -m unittest tests.test_registry -v
python -m unittest tests.test_validation tests.test_workflow_cli -v
python -m unittest \
  tests.test_registry_cli.RegistryCliTest.test_verify_registry_reports_clean_trusted_skills \
  tests.test_registry_cli.RegistryCliTest.test_reindex_rebuilds_registry_index_from_manifests \
  tests.test_registry_cli.RegistryCliTest.test_schema_check_validates_real_catalog -v
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/onecode_skill_sanitizer/cli.py src/onecode_skill_sanitizer/registry.py tests/test_registry.py
git commit -m "refactor: extract registry ownership"
```

### Task 4: Extract Task-Pack Assembly, Router Evaluation, and Command Handlers

**Files:**

- Create: `src/onecode_skill_sanitizer/task_packs.py`
- Create: `src/onecode_skill_sanitizer/router_evaluation.py`
- Create: `src/onecode_skill_sanitizer/commands.py`
- Create: `tests/test_cli_boundaries.py`
- Modify: `src/onecode_skill_sanitizer/cli.py:323-2094,2170-2827,3682-3812`

- [ ] **Step 1: Write failing facade and command-dispatch tests**

```python
from onecode_skill_sanitizer import cli, commands, router_evaluation, task_packs


class CliBoundaryTest(unittest.TestCase):
    def test_cli_reexports_task_pack_builders(self):
        self.assertIs(cli.build_task_pack, task_packs.build_task_pack)
        self.assertIs(cli.build_task_pack_v2, task_packs.build_task_pack_v2)
        self.assertIs(cli.build_agent_instructions, task_packs.build_agent_instructions)

    def test_cli_reexports_router_evaluation(self):
        self.assertIs(cli.run_router_eval, router_evaluation.run_router_eval)
        self.assertIs(cli.load_router_eval, router_evaluation.load_router_eval)

    def test_parser_dispatches_to_commands_module(self):
        args = cli.build_parser().parse_args(["list", "--registry", "catalog"])
        self.assertIs(args.func, commands.list_command)
```

- [ ] **Step 2: Verify RED**

Run: `python -m unittest tests.test_cli_boundaries -v`

Expected: import failure because the three owner modules are absent.

- [ ] **Step 3: Move pure task-pack assembly**

Move the complete function families for skill selection, trusted skill-pack
loading, bundle selection, agent instructions, acceptance/completion contracts,
Schema v1 task-pack assembly, Schema v2 task-pack assembly, capability
resolution, invariant graph extension, graph normalization, routing status,
and bounded v2 errors into `task_packs.py`. Keep function bodies unchanged
except for imports from `rendering.py`, `registry.py`, and existing routing
modules. The public module surface is:

```python
__all__ = [
    "build_acceptance_criteria",
    "build_agent_instructions",
    "build_completion_contract",
    "build_task_pack",
    "build_task_pack_v2",
    "load_skill_pack_item",
    "load_trusted_skill_pack_items",
    "select_bundles_for_task",
    "select_skills_for_task",
    "task_taxonomy_from_profile",
]
```

Directly import and re-export every previously public moved name from `cli.py`.

- [ ] **Step 4: Move router evaluation ownership**

Move `load_router_eval()`, validation/annotation/quality-summary helpers,
`run_router_eval()`, and `router_eval_trace_summary()` into
`router_evaluation.py`. Import v2 evaluation functions from the existing
`router_eval_v2.py`; do not move or duplicate them. Re-export the moved names
from `cli.py`.

- [ ] **Step 5: Move command handlers behind a dependency-safe module**

Move all functions whose names end in `_command`, plus `maintain_check()`, into
`commands.py`. Each handler imports operations from `bulk`, `registry`,
`router_evaluation`, `task_packs`, `validation`, and other owner modules. It
must never import `cli.py`. Keep `build_parser()`, numeric argument validators,
provenance argument wiring, and `main()` in `cli.py`; update parser defaults to
reference `commands.<name>_command`.

For the three status aliases, keep explicit delegates:

```python
def approve_command(args: argparse.Namespace) -> int:
    return registry.set_status_command(args, "trusted")


def reject_command(args: argparse.Namespace) -> int:
    return registry.set_status_command(args, "rejected")


def disable_command(args: argparse.Namespace) -> int:
    return registry.set_status_command(args, "disabled")
```

Import and re-export command handlers from `cli.py` to preserve current tests
and external callers.

- [ ] **Step 6: Run task-pack, eval, parser, and full CLI regressions**

Run:

```bash
python -m unittest tests.test_cli_boundaries -v
python -m unittest tests.test_registry_cli tests.test_router_eval_v2 -q
PYTHONPATH=src python -m onecode_skill_sanitizer --help >/tmp/cli-help.txt
PYTHONPATH=src python -m onecode_skill_sanitizer smart \
  "build a landing page and prepare launch checks" --format json >/tmp/smart.json
```

Expected: tests and both CLI invocations pass; `smart.json` is valid JSON.

- [ ] **Step 7: Commit**

```bash
git add src/onecode_skill_sanitizer/cli.py src/onecode_skill_sanitizer/commands.py \
  src/onecode_skill_sanitizer/task_packs.py \
  src/onecode_skill_sanitizer/router_evaluation.py tests/test_cli_boundaries.py
git commit -m "refactor: separate cli assembly and commands"
```

### Task 5: Extract Router Profiles and Execution Graphs

**Files:**

- Create: `src/onecode_skill_sanitizer/routing_profiles.py`
- Create: `src/onecode_skill_sanitizer/routing_execution.py`
- Create: `tests/test_routing_boundaries.py`
- Modify: `src/onecode_skill_sanitizer/router.py:1-952,1673-2228`

- [ ] **Step 1: Write failing compatibility tests**

```python
from onecode_skill_sanitizer import router
from onecode_skill_sanitizer import routing_execution, routing_profiles


class RoutingBoundaryTest(unittest.TestCase):
    def test_router_reexports_profile_api(self):
        self.assertIs(router.build_task_profile, routing_profiles.build_task_profile)
        self.assertIs(router.score_bundle_for_profile, routing_profiles.score_bundle_for_profile)

    def test_router_reexports_execution_api(self):
        self.assertIs(router.build_execution_graph, routing_execution.build_execution_graph)
        self.assertIs(router.build_contract_graph, routing_execution.build_contract_graph)
        self.assertIs(router.build_contract_diagnostics, routing_execution.build_contract_diagnostics)
```

- [ ] **Step 2: Verify RED**

Run: `python -m unittest tests.test_routing_boundaries -v`

Expected: import failure for the two new modules.

- [ ] **Step 3: Move profile constants and profile functions**

Move signal dictionaries, capability preferences, normalization, structured
context parsing, task profile construction, and bundle scoring to
`routing_profiles.py`. Its public surface is:

```python
__all__ = [
    "CAPABILITY_SKILL_PREFERENCES",
    "PIPELINE_STAGE_ORDER",
    "build_capability_coverage",
    "build_execution_plan",
    "build_selection_explanations",
    "build_selection_quality",
    "build_selection_trace",
    "build_task_profile",
    "normalize_task_text",
    "parse_structured_context_text",
    "score_bundle_for_profile",
]
```

Move bodies unchanged and import/re-export these names from `router.py`.

- [ ] **Step 4: Move stage, approval, and graph functions**

Move the stage maps and functions from `execution_role_for_stage()` through
`contract_sorted_skill_names()` into `routing_execution.py`. Pass task-profile
helpers as normal imports from `routing_profiles.py`; do not import
`router.py`. Re-export these functions from `router.py`.

- [ ] **Step 5: Run router regressions and evals**

Run:

```bash
python -m unittest tests.test_routing_boundaries tests.test_router -v
python -m unittest tests.test_router_eval_v2 -q
PYTHONPATH=src python -m onecode_skill_sanitizer router-eval \
  --eval evals/router-quality.json --registry catalog --bundles bundles/index.json >/tmp/router-eval.json
PYTHONPATH=src python -m onecode_skill_sanitizer router-eval-v2 \
  --eval evals/multi-intent-gold.json >/tmp/router-eval-v2.json
```

Expected: tests pass and both eval commands exit 0.

- [ ] **Step 6: Commit**

```bash
git add src/onecode_skill_sanitizer/router.py \
  src/onecode_skill_sanitizer/routing_profiles.py \
  src/onecode_skill_sanitizer/routing_execution.py \
  tests/test_routing_boundaries.py
git commit -m "refactor: split router responsibilities"
```

### Task 6: Split the Registry CLI Test Module

**Files:**

- Create: `tests/registry_cli_helpers.py`
- Create: `tests/test_bulk_cli.py`
- Create: `tests/test_catalog_maintenance_cli.py`
- Create: `tests/test_router_cli.py`
- Modify: `tests/test_registry_cli.py`

- [ ] **Step 1: Record the exact test inventory before moving methods**

Run:

```bash
python -m unittest tests.test_registry_cli -q
python -m unittest discover -s tests -q
```

Expected: the registry module and full suite pass. Record discovered counts in
the plan checklist before moving code.

- [ ] **Step 2: Extract shared fixture builders**

Create `registry_cli_helpers.py` with only reusable filesystem fixture helpers:

```python
def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]
```

Do not create a shared base `TestCase`; each test module must remain independently
collectable.

- [ ] **Step 3: Move tests by ownership without editing assertions**

Move complete test methods and their direct imports:

- bulk plan/draft/assessment and candidate-map tests to `test_bulk_cli.py`
- maintain/schema/reference/verify/status/catalog-integrity tests to
  `test_catalog_maintenance_cli.py`
- task-pack/smart/scenario/eval tests to `test_router_cli.py`
- import/list/inspect/select and parser-boundary tests remain in
  `test_registry_cli.py`

- [ ] **Step 4: Verify no tests were lost or duplicated**

Run:

```bash
rg '^    def test_' tests/test_*cli.py | sed 's/.*def //' | sort > /tmp/after-cli-tests.txt
test "$(sort /tmp/after-cli-tests.txt | uniq -d | wc -l | tr -d ' ')" = "0"
python -m unittest discover -s tests -q
```

Expected: zero duplicate names and the full suite count is at least the Task 6
baseline count.

- [ ] **Step 5: Commit**

```bash
git add tests/test_registry_cli.py tests/registry_cli_helpers.py \
  tests/test_bulk_cli.py tests/test_catalog_maintenance_cli.py tests/test_router_cli.py
git commit -m "test: split registry cli regression suite"
```

### Task 7: Add Batch Lifecycle Governance and Compact Duplicates

**Files:**

- Create: `src/onecode_skill_sanitizer/batch_lifecycle.py`
- Create: `schemas/batch-index.schema.json`
- Create: `tests/test_batch_lifecycle.py`
- Create: `batches/README.md`
- Create: `batches/index.json`
- Create: `batches/*/*/PROMOTED.md` for byte-identical promoted entries
- Modify: `src/onecode_skill_sanitizer/cli.py`
- Modify: `scripts/verify.sh`
- Remove: byte-identical promoted `batches/*/*/SKILL.md` files only

- [ ] **Step 1: Write lifecycle and compaction tests**

```python
class BatchLifecycleTest(unittest.TestCase):
    def test_inventory_classifies_draft_promoted_and_mismatch(self):
        inventory = build_batch_index(batch_root, catalog_root, source_commit="abc123")
        statuses = {item["name"]: item["lifecycle"] for item in inventory["items"]}
        self.assertEqual(statuses["draft-skill"], "active_draft")
        self.assertEqual(statuses["same-skill"], "promoted")
        self.assertEqual(statuses["changed-skill"], "promoted")
        self.assertFalse(next(i for i in inventory["items"] if i["name"] == "changed-skill")["content_match"])

    def test_compaction_only_replaces_byte_identical_promoted_body(self):
        result = compact_promoted_bodies(index, batch_root, catalog_root)
        self.assertEqual(result["compacted"], ["same-skill"])
        self.assertTrue((same_dir / "PROMOTED.md").is_file())
        self.assertFalse((same_dir / "SKILL.md").exists())
        self.assertTrue((changed_dir / "SKILL.md").is_file())
```

- [ ] **Step 2: Verify RED**

Run: `python -m unittest tests.test_batch_lifecycle -v`

Expected: import failure for `batch_lifecycle.py`.

- [ ] **Step 3: Implement deterministic inventory and validation**

Implement public functions `build_batch_index(batch_root, catalog_root,
source_commit)`, `validate_batch_index(index, batch_root, catalog_root)`, and
`compact_promoted_bodies(index, batch_root, catalog_root)` with sorted paths
and SHA-256 content hashes. Define the lifecycle values exactly as follows:

```python
LIFECYCLE_VALUES = {"active_draft", "review_ready", "promoted", "superseded"}
```

Each item records `name`, `batch`, `lifecycle`, `body_path`, `canonical_path`,
`source_sha256`, `catalog_sha256`, `content_match`, `source_commit`, and
`compacted`. `PROMOTED.md` uses only those recorded values.

- [ ] **Step 4: Add CLI commands and schema**

Add:

```text
batch-check --batches batches --catalog catalog --index batches/index.json
batch-compact --batches batches --catalog catalog --index batches/index.json --source-commit SHA
```

`batch-check` is read-only and exits 2 on findings. `batch-compact` requires the
explicit source commit and writes deterministic JSON and promotion records.
Define `schemas/batch-index.schema.json` with closed item objects and the four
lifecycle enum values.

- [ ] **Step 5: Generate and compact the real inventory**

Run:

```bash
PYTHONPATH=src python -m onecode_skill_sanitizer batch-compact \
  --batches batches --catalog catalog --index batches/index.json \
  --source-commit b44cb4d
PYTHONPATH=src python -m onecode_skill_sanitizer batch-check \
  --batches batches --catalog catalog --index batches/index.json
```

Expected: 471 total items, 168 promoted, 303 active drafts, 167 compacted
byte-identical bodies, and one retained promoted mismatch.

- [ ] **Step 6: Add batch-check to repository verification**

Append to `scripts/verify.sh`:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer batch-check \
  --batches batches \
  --catalog catalog \
  --index batches/index.json >/dev/null
python3 -m json.tool schemas/batch-index.schema.json >/dev/null
```

- [ ] **Step 7: Run lifecycle and existing bulk tests**

Run:

```bash
python -m unittest tests.test_batch_lifecycle tests.test_bulk_cli -v
PYTHONPATH=src python -m onecode_skill_sanitizer maintain-check \
  --registry catalog --bundles bundles/index.json \
  --references external-references/index.json \
  --claude-skills-candidate-map docs/claude-skills-candidate-map.json
```

Expected: pass; catalog files and trust state are unchanged.

- [ ] **Step 8: Commit**

```bash
git add src/onecode_skill_sanitizer/batch_lifecycle.py src/onecode_skill_sanitizer/cli.py \
  schemas/batch-index.schema.json tests/test_batch_lifecycle.py scripts/verify.sh batches
git commit -m "feat: govern batch lifecycle and compact promotions"
```

### Task 8: Establish the Documentation Source of Truth

**Files:**

- Create: `docs/index.md`
- Create: `docs/history.md`
- Create: `tests/test_documentation.py`
- Modify: `README.md:65-178`
- Modify: `docs/architecture.md`
- Modify: `docs/module-boundary-refactor-plan.md`

- [ ] **Step 1: Write failing documentation navigation tests**

```python
class DocumentationTest(unittest.TestCase):
    def test_readme_points_to_documentation_index(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("[Documentation Index](docs/index.md)", readme)

    def test_primary_document_links_resolve(self):
        for path in [ROOT / "README.md", ROOT / "docs/index.md", ROOT / "docs/history.md"]:
            for target in markdown_local_links(path):
                self.assertTrue((path.parent / target).resolve().exists(), f"broken link: {path} -> {target}")
```

- [ ] **Step 2: Verify RED**

Run: `python -m unittest tests.test_documentation -v`

Expected: failure because `docs/index.md` and `docs/history.md` do not exist.

- [ ] **Step 3: Create the normative index and history map**

`docs/index.md` must contain the five approved sections: Start Here, Current
Architecture And Behavior, Operator And Maintainer Guides, Catalog And Skill
Authoring, and Historical Records. `docs/history.md` groups dated updates,
closure reports, batch records, and superpowers specs/plans without presenting
them as current behavior.

- [ ] **Step 4: Trim README chronology and update architecture**

Replace the long Latest/Previous/Earlier block with links to `docs/index.md`,
`docs/catalog-overview.md`, `docs/router-development.md`, and
`docs/history.md`. Document the new module and batch boundaries in
`architecture.md`; update progress and line targets in
`module-boundary-refactor-plan.md`.

- [ ] **Step 5: Verify links and commit**

Run:

```bash
python -m unittest tests.test_documentation -v
git diff --check
```

Expected: all primary local links resolve.

```bash
git add README.md docs/index.md docs/history.md docs/architecture.md \
  docs/module-boundary-refactor-plan.md tests/test_documentation.py
git commit -m "docs: establish current truth navigation"
```

### Task 9: Add Skill-Depth Governance and Deepen Representative Skills

**Files:**

- Create: `src/onecode_skill_sanitizer/skill_depth.py`
- Create: `catalog/depth-policy.json`
- Create: `docs/skill-depth-policy.md`
- Create: `tests/test_skill_depth.py`
- Create: `catalog/security/security-supply-chain-review/references/review-checklist.md`
- Create: `catalog/compliance/compliance-privacy-check/references/privacy-evidence-guide.md`
- Create: `catalog/engineering/engineering-build-release/references/release-gates.md`
- Modify: the three corresponding `SKILL.md`, `skill.json`, and `SANITIZATION_REPORT.json` files
- Modify: `schemas/skill-manifest.schema.json`
- Modify: `src/onecode_skill_sanitizer/validation.py`
- Modify: `src/onecode_skill_sanitizer/registry.py`
- Modify: `src/onecode_skill_sanitizer/cli.py`
- Modify: `scripts/verify.sh`
- Modify: `catalog/index.json`

- [ ] **Step 1: Write failing depth and auxiliary-integrity tests**

```python
class SkillDepthTest(unittest.TestCase):
    def test_specialist_without_reference_is_warning(self):
        report = audit_skill(skill_dir, {"depth_class": "specialist"})
        self.assertIn("specialist-missing-reference", [i["id"] for i in report["warnings"]])

    def test_auxiliary_hash_changes_with_reference_content(self):
        first = auxiliary_content_sha256(skill_dir)
        (skill_dir / "references" / "guide.md").write_text("changed\n", encoding="utf-8")
        self.assertNotEqual(first, auxiliary_content_sha256(skill_dir))

    def test_verify_registry_reports_auxiliary_tampering(self):
        report = verify_registry(registry_dir)
        self.assertIn("auxiliary-content-mismatch", [i["id"] for i in report["issues"]])
```

- [ ] **Step 2: Verify RED**

Run: `python -m unittest tests.test_skill_depth -v`

Expected: missing `skill_depth` module and auxiliary hash function.

- [ ] **Step 3: Implement deterministic depth audit**

Implement `analyze_skill(skill_dir, policy)` and
`audit_catalog_depth(catalog_dir, policy_path)` using exactly these supported
classes: `DEPTH_CLASSES = {"routing_card", "playbook", "specialist"}`.

Reports include words, workflow steps, structural sections, examples, decision
guidance, failure handling, reference/script counts, errors, and warnings.
Thresholds remain warnings; invalid depth classes and missing required sections
are errors.

- [ ] **Step 4: Protect auxiliary content integrity**

Add optional `hashes.auxiliary_sha256` to the manifest schema. Implement a
canonical hash over sorted relative paths and bytes under `references/` and
`scripts/`. `verify_registry()` checks the value when present. Extend
`reseal_skill_content()` to set or remove it based on actual auxiliary files.

- [ ] **Step 5: Add `depth-check` and policy**

Add CLI command:

```text
depth-check --catalog catalog --policy catalog/depth-policy.json
```

`catalog/depth-policy.json` assigns the three representative skills to
`specialist`; all others default to `routing_card`. Add the read-only check and
JSON syntax validation to `scripts/verify.sh`.

- [ ] **Step 6: Deepen three representative skills**

Add decision criteria, evidence expectations, failure/escalation paths, and a
`## References` section to each selected SKILL. Keep legal, production, network,
and credential actions behind host approval. Add one focused on-demand guide
per skill, then reseal content:

```bash
PYTHONPATH=src python -m onecode_skill_sanitizer reseal-content \
  catalog/security/security-supply-chain-review
PYTHONPATH=src python -m onecode_skill_sanitizer reseal-content \
  catalog/compliance/compliance-privacy-check
PYTHONPATH=src python -m onecode_skill_sanitizer reseal-content \
  catalog/engineering/engineering-build-release
PYTHONPATH=src python -m onecode_skill_sanitizer reindex --registry catalog
```

- [ ] **Step 7: Run depth, integrity, and catalog checks**

Run:

```bash
python -m unittest tests.test_skill_depth tests.test_validation tests.test_registry -v
PYTHONPATH=src python -m onecode_skill_sanitizer depth-check \
  --catalog catalog --policy catalog/depth-policy.json
PYTHONPATH=src python -m onecode_skill_sanitizer verify --registry catalog
PYTHONPATH=src python -m onecode_skill_sanitizer schema-check --registry catalog
```

Expected: no errors; warnings are reported but do not fail. The three specialist
skills have valid auxiliary hashes and remain trusted.

- [ ] **Step 8: Commit**

```bash
git add src/onecode_skill_sanitizer/skill_depth.py src/onecode_skill_sanitizer/validation.py \
  src/onecode_skill_sanitizer/registry.py src/onecode_skill_sanitizer/cli.py \
  schemas/skill-manifest.schema.json catalog docs/skill-depth-policy.md \
  tests/test_skill_depth.py scripts/verify.sh
git commit -m "feat: add risk-aware skill depth governance"
```

### Task 10: Verify, Measure, Report, and Publish

**Files:**

- Create: `docs/structural-maintainability-closure-report-2026-07-11.md`
- Modify: `docs/maintenance-log.md`
- Modify: `README.md`

- [ ] **Step 1: Capture after metrics**

Run:

```bash
wc -l src/onecode_skill_sanitizer/cli.py src/onecode_skill_sanitizer/router.py \
  tests/test_registry_cli.py
find batches -name SKILL.md | wc -l
find batches -name PROMOTED.md | wc -l
find docs -name '*.md' | wc -l
find catalog -path '*/references/*' -type f | wc -l
git diff b44cb4d --stat
```

Expected: core and test hotspots are materially smaller; 167 promotion records
replace identical batch bodies; three catalog reference assets exist.

- [ ] **Step 2: Run the complete verification suite**

Run: `PATH=/tmp/safe-agent-skills-structural-venv/bin:$PATH bash scripts/verify.sh`

Expected: exit 0 with all tests passing, Ruff clean, router evaluations passing,
catalog maintenance/schema/contracts valid, batch lifecycle valid, and depth
policy valid.

- [ ] **Step 3: Write the closure report**

Record exact before/after module lines, test count, batch lifecycle counts,
documentation structure, deepened skills, verification output, compatibility
guarantees, residual risks, and follow-up recommendations. Update the
maintenance log and README current-update link.

- [ ] **Step 4: Verify documentation and repository state**

Run:

```bash
python -m unittest tests.test_documentation -v
git diff --check
git status --short
```

Expected: documentation tests pass, no whitespace errors, and only expected
report files are uncommitted.

- [ ] **Step 5: Commit the completion report**

```bash
git add README.md docs/maintenance-log.md \
  docs/structural-maintainability-closure-report-2026-07-11.md
git commit -m "docs: close structural maintainability redesign"
```

- [ ] **Step 6: Run final verification from committed HEAD**

Run:

```bash
PATH=/tmp/safe-agent-skills-structural-venv/bin:$PATH bash scripts/verify.sh
git status --short --branch
git log --oneline b44cb4d..HEAD
```

Expected: verification exits 0 and the feature branch is clean.

- [ ] **Step 7: Integrate and push**

Use `superpowers:finishing-a-development-branch`. Because the user explicitly
requested updating the GitHub repository, merge the verified feature branch
into local `main`, rerun verification on `main`, and push `main` to `origin`.
Do not force-push.
