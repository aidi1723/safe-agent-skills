# Smart Skill Selection Execution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic selection-quality metadata and completion contracts so task packs guide host agents toward better skill choice, evidence capture, and final handoff.

**Architecture:** Extend the existing router and CLI output without replacing current fields. `router.py` will own route quality, role labeling, and deterministic acceptance/completion helpers; `cli.py` will include those helpers in JSON and Markdown task packs; catalog maintenance will remain metadata-only until governance checks pass.

**Tech Stack:** Python 3.11 standard library, `unittest`, existing `onecode_skill_sanitizer` CLI, JSON registry files, Bash verification script.

---

## File Structure

- Modify `src/onecode_skill_sanitizer/router.py`
  - Add execution role mapping.
  - Add `build_selection_quality`.
  - Enrich `build_selection_explanations`.
  - Include `selection_quality` in scenario and mesh route results.
- Modify `src/onecode_skill_sanitizer/cli.py`
  - Add `build_acceptance_criteria`.
  - Add `build_completion_contract`.
  - Include both fields in simple, scenario, and mesh task packs.
  - Render selection quality, acceptance criteria, and completion contract in Markdown and `agent_instructions`.
- Modify `tests/test_router.py`
  - Add unit tests for selection quality and execution role labeling.
- Modify `tests/test_registry_cli.py`
  - Add CLI/task-pack tests for JSON and Markdown contract output.
  - Add metadata-only `claude-skills` reference validation test.
- Modify `external-references/index.json`
  - Add metadata-only `claude-skills` reference.
  - Increment `reference_count`.
- Create `docs/catalog-overview.md`
  - Add public catalog overview after router/task-pack work is verified.
- Run `bash scripts/verify.sh`.

---

### Task 1: Add Router Selection Quality And Role Tests

**Files:**
- Modify: `tests/test_router.py`
- Modify later: `src/onecode_skill_sanitizer/router.py`

- [ ] **Step 1: Import the new helpers in router tests**

Update the import block in `tests/test_router.py`:

```python
from onecode_skill_sanitizer.router import (
    build_capability_coverage,
    build_contract_graph,
    build_execution_graph,
    build_execution_plan,
    build_pipeline_plan,
    build_selection_explanations,
    build_selection_quality,
    build_task_profile,
    execution_role_for_stage,
    parse_invariant_capabilities,
    route_mesh_task,
    route_scenario_task,
    score_bundle_for_profile,
)
```

- [ ] **Step 2: Add failing tests for quality and role metadata**

Add these tests near the existing `build_selection_explanations` and route tests in `tests/test_router.py`:

```python
    def test_build_selection_quality_reports_required_coverage_and_warnings(self):
        bundle = {"id": "code-review-hardening", "name": "Code Review Hardening"}
        coverage = [
            {
                "capability": "code_review",
                "required": True,
                "status": "covered",
                "skill": "code-review-risk",
                "preferred_skills": ["code-review-risk"],
            },
            {
                "capability": "supply_chain_review",
                "required": True,
                "status": "missing",
                "skill": "",
                "preferred_skills": ["security-supply-chain-review"],
            },
            {
                "capability": "schema_contract",
                "required": False,
                "status": "missing",
                "skill": "",
                "preferred_skills": ["ai-output-schema-eval"],
            },
        ]

        quality = build_selection_quality(
            task_profile={"task_type": "code_review", "matched_signal_score": 8},
            selected_bundle=bundle,
            selected_scenario={"id": "code-review-hardening", "match_score": 12},
            coverage=coverage,
            pruned_skills=["code-dead-path-cleanup-review"],
        )

        self.assertEqual(quality["confidence"], "medium")
        self.assertEqual(quality["covered_required_count"], 1)
        self.assertEqual(quality["missing_required_count"], 1)
        self.assertEqual(quality["required_count"], 2)
        self.assertAlmostEqual(quality["coverage_ratio"], 0.5)
        self.assertFalse(quality["low_confidence"])
        self.assertIn("Missing required capability: supply_chain_review", quality["warnings"])
        self.assertEqual(quality["pruned_skills"], ["code-dead-path-cleanup-review"])

    def test_build_selection_quality_marks_general_fallback_low_confidence(self):
        quality = build_selection_quality(
            task_profile={"task_type": "general", "matched_signal_score": 0},
            selected_bundle={},
            selected_scenario={"id": "", "match_score": 0},
            coverage=[],
            pruned_skills=[],
        )

        self.assertEqual(quality["confidence"], "low")
        self.assertTrue(quality["low_confidence"])
        self.assertEqual(quality["coverage_ratio"], 0)
        self.assertIn("No trusted scenario matched; using direct selected skills only.", quality["warnings"])

    def test_selection_explanations_include_execution_roles(self):
        bundle = {
            "id": "skill-router-quality-review",
            "name": "Skill Router Quality Review",
        }
        skills = [
            {"name": "ai-opensquilla-metaskill-workflow", "match_score": 0},
            {"name": "ai-tool-schema-protocol-check", "match_score": 0},
            {"name": "code-test-regression", "match_score": 0},
        ]
        coverage = [
            {
                "capability": "bundle_quality",
                "required": True,
                "status": "covered",
                "skill": "ai-opensquilla-metaskill-workflow",
                "preferred_skills": ["ai-opensquilla-metaskill-workflow"],
            },
            {
                "capability": "routing_contract",
                "required": True,
                "status": "covered",
                "skill": "ai-tool-schema-protocol-check",
                "preferred_skills": ["ai-tool-schema-protocol-check"],
            },
            {
                "capability": "regression_test",
                "required": True,
                "status": "covered",
                "skill": "code-test-regression",
                "preferred_skills": ["code-test-regression"],
            },
        ]

        explanations = build_selection_explanations(bundle, skills, coverage)
        by_name = {item["name"]: item for item in explanations}

        self.assertEqual(by_name["ai-opensquilla-metaskill-workflow"]["execution_role"], "preflight")
        self.assertEqual(by_name["ai-tool-schema-protocol-check"]["execution_role"], "reviewer")
        self.assertEqual(by_name["code-test-regression"]["execution_role"], "verifier")
        self.assertEqual(execution_role_for_stage("production"), "producer")
```

- [ ] **Step 3: Run the focused router tests and confirm failure**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_router.RouterTest.test_build_selection_quality_reports_required_coverage_and_warnings tests.test_router.RouterTest.test_build_selection_quality_marks_general_fallback_low_confidence tests.test_router.RouterTest.test_selection_explanations_include_execution_roles -v
```

Expected: FAIL because `build_selection_quality` and `execution_role_for_stage` are not defined yet.

- [ ] **Step 4: Commit failing tests**

```bash
git add tests/test_router.py
git commit -m "test: cover smart route selection quality"
```

---

### Task 2: Implement Router Selection Quality And Role Labels

**Files:**
- Modify: `src/onecode_skill_sanitizer/router.py`
- Test: `tests/test_router.py`

- [ ] **Step 1: Add execution role mapping helpers**

In `src/onecode_skill_sanitizer/router.py`, add these helpers after `PIPELINE_STAGE_INFO`:

```python
EXECUTION_ROLE_BY_STAGE = {
    "preflight": "preflight",
    "source": "reviewer",
    "planning": "planner",
    "production": "producer",
    "execution": "producer",
    "review": "reviewer",
    "verification": "verifier",
    "handoff": "handoff",
}


def execution_role_for_stage(stage: str) -> str:
    return EXECUTION_ROLE_BY_STAGE.get(stage, "supplemental")


def execution_role_for_skill(skill_name: str, bundle_id: str = "", skill_names: list[str] | None = None) -> str:
    if skill_names is None:
        skill_names = [skill_name]
    stage_map = scenario_stage_skill_map(bundle_id, skill_names)
    for stage, names in stage_map.items():
        if skill_name in names:
            return execution_role_for_stage(stage)
    return execution_role_for_stage(pipeline_stage_for_skill(skill_name))
```

- [ ] **Step 2: Add selection quality helper**

Add this helper before `route_scenario_task`:

```python
def build_selection_quality(
    task_profile: dict,
    selected_bundle: dict,
    selected_scenario: dict,
    coverage: list[dict],
    pruned_skills: list[str] | None = None,
) -> dict:
    required_items = [item for item in coverage if item.get("required", True)]
    covered_required = [item for item in required_items if item.get("status") == "covered"]
    missing_required = [item for item in required_items if item.get("status") == "missing"]
    required_count = len(required_items)
    coverage_ratio = round(len(covered_required) / required_count, 2) if required_count else 0
    warnings = []
    if not selected_bundle:
        warnings.append("No trusted scenario matched; using direct selected skills only.")
    for item in missing_required:
        warnings.append(f"Missing required capability: {item.get('capability', '')}")

    route_score = int(selected_scenario.get("match_score", 0) or 0)
    matched_signal_score = int(task_profile.get("matched_signal_score", 0) or 0)
    low_confidence = not selected_bundle or bool(missing_required) or matched_signal_score <= 0
    if not selected_bundle or matched_signal_score <= 0:
        confidence = "low"
    elif missing_required or coverage_ratio < 0.8 or route_score < 8:
        confidence = "medium"
    else:
        confidence = "high"

    score = round(
        min(
            1.0,
            (coverage_ratio * 0.7)
            + (min(route_score, 20) / 20 * 0.2)
            + (min(matched_signal_score, 20) / 20 * 0.1),
        ),
        2,
    )
    if confidence == "low":
        score = min(score, 0.49)
    elif confidence == "medium":
        score = min(max(score, 0.5), 0.79)
    else:
        score = max(score, 0.8)

    return {
        "confidence": confidence,
        "score": score,
        "required_count": required_count,
        "covered_required_count": len(covered_required),
        "missing_required_count": len(missing_required),
        "coverage_ratio": coverage_ratio,
        "low_confidence": low_confidence,
        "warnings": warnings,
        "pruned_skills": list(pruned_skills or []),
    }
```

- [ ] **Step 3: Enrich selection explanations**

Update the skill loop in `build_selection_explanations` so each skill item includes `execution_role`:

```python
    bundle_id = bundle.get("id", "")
    skill_names = selected_skill_names(selected_skills)
    for skill in selected_skills:
        matched = coverage_by_skill.get(skill["name"], [])
        execution_role = execution_role_for_skill(skill["name"], bundle_id, skill_names)
        explanations.append(
            {
                "type": "skill",
                "name": skill["name"],
                "role": "core" if matched else "supplemental",
                "execution_role": execution_role,
                "confidence": 0.85 if matched else 0.6,
                "matched_capabilities": matched,
                "selection_reason": (
                    f"Selected `{skill['name']}` as {execution_role} guidance to cover {', '.join(matched)}."
                    if matched
                    else f"Selected `{skill['name']}` as supplemental trusted guidance."
                ),
            }
        )
```

Also add `execution_role: "planner"` to the bundle explanation:

```python
            "execution_role": "planner",
```

- [ ] **Step 4: Include selection quality in scenario route results**

In `route_scenario_task`, build the selected scenario dict once:

```python
    selected_scenario = {
        "id": selected_bundle.get("id", ""),
        "name": selected_bundle.get("name", selected_bundle.get("id", "")),
        "match_score": score_bundle_for_profile(selected_bundle, profile) if selected_bundle else 0,
    }
    selection_quality = build_selection_quality(
        task_profile=profile,
        selected_bundle=selected_bundle,
        selected_scenario=selected_scenario,
        coverage=coverage,
        pruned_skills=[],
    )
```

Return `selected_scenario` and add:

```python
        "selection_quality": selection_quality,
```

- [ ] **Step 5: Include selection quality in mesh route results**

In `route_mesh_task`, build the selected scenario dict once:

```python
    selected_scenario = {
        "id": selected_bundle.get("id", ""),
        "name": selected_bundle.get("name", selected_bundle.get("id", "")),
        "match_score": score_bundle_for_profile(selected_bundle, profile) if selected_bundle else 0,
    }
    selection_quality = build_selection_quality(
        task_profile=profile,
        selected_bundle=selected_bundle,
        selected_scenario=selected_scenario,
        coverage=coverage,
        pruned_skills=pruned_names,
    )
```

Return `selected_scenario` and add:

```python
        "selection_quality": selection_quality,
```

- [ ] **Step 6: Run focused router tests**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_router.RouterTest.test_build_selection_quality_reports_required_coverage_and_warnings tests.test_router.RouterTest.test_build_selection_quality_marks_general_fallback_low_confidence tests.test_router.RouterTest.test_selection_explanations_include_execution_roles -v
```

Expected: PASS.

- [ ] **Step 7: Run all router tests**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_router -v
```

Expected: PASS.

- [ ] **Step 8: Commit implementation**

```bash
git add src/onecode_skill_sanitizer/router.py tests/test_router.py
git commit -m "feat: add route selection quality metadata"
```

---

### Task 3: Add Task-Pack Completion Contract Tests

**Files:**
- Modify: `tests/test_registry_cli.py`
- Modify later: `src/onecode_skill_sanitizer/cli.py`

- [ ] **Step 1: Add JSON task-pack contract assertions**

In `test_task_pack_outputs_json_for_trusted_matching_skills`, after existing safety boundary assertions, add:

```python
            self.assertIn("acceptance_criteria", task_pack)
            self.assertIn("completion_contract", task_pack)
            self.assertIn(
                "Record selected trusted skills before execution.",
                task_pack["acceptance_criteria"],
            )
            self.assertIn(
                "selected_skills",
                task_pack["completion_contract"]["final_response_must_include"],
            )
            self.assertIn(
                "verification_performed",
                task_pack["completion_contract"]["final_response_must_include"],
            )
            self.assertIn("Completion contract:", task_pack["agent_instructions"])
```

- [ ] **Step 2: Add Markdown task-pack contract assertions**

In `test_task_pack_outputs_markdown`, after existing Markdown assertions, add:

```python
            self.assertIn("## Acceptance Criteria", markdown)
            self.assertIn("## Completion Contract", markdown)
            self.assertIn("Record selected trusted skills before execution.", markdown)
            self.assertIn("selected_skills", markdown)
            self.assertIn("verification_performed", markdown)
```

- [ ] **Step 3: Add scenario task-pack selection quality assertions**

In `test_real_catalog_scenario_router_selects_website_bundle`, after building the result, add assertions for:

```python
        self.assertIn("selection_quality", result)
        self.assertIn(result["selection_quality"]["confidence"], {"high", "medium"})
        self.assertGreater(result["selection_quality"]["coverage_ratio"], 0)
        self.assertIn("acceptance_criteria", result)
        self.assertIn("completion_contract", result)
```

If the test currently stores the output under a different variable name, apply these assertions to that decoded task-pack dict.

- [ ] **Step 4: Run focused CLI tests and confirm failure**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_task_pack_outputs_json_for_trusted_matching_skills tests.test_registry_cli.RegistryCliTest.test_task_pack_outputs_markdown tests.test_registry_cli.RegistryCliTest.test_real_catalog_scenario_router_selects_website_bundle -v
```

Expected: FAIL because task packs do not expose the new fields yet.

- [ ] **Step 5: Commit failing tests**

```bash
git add tests/test_registry_cli.py
git commit -m "test: cover task pack completion contract"
```

---

### Task 4: Implement Task-Pack Acceptance Criteria And Completion Contract

**Files:**
- Modify: `src/onecode_skill_sanitizer/cli.py`
- Test: `tests/test_registry_cli.py`

- [ ] **Step 1: Add acceptance criteria helper**

In `src/onecode_skill_sanitizer/cli.py`, add this function before `build_task_pack`:

```python
def build_acceptance_criteria(task_pack_context: dict) -> list[str]:
    criteria = [
        "Record selected trusted skills before execution.",
        "Preserve the method-only safety boundary for all runtime actions.",
    ]
    if task_pack_context.get("selected_scenario", {}).get("id"):
        criteria.append("Record selected scenario and why it matched the task.")
    if task_pack_context.get("pipeline_plan"):
        criteria.append("Complete every pipeline stage gate or record the failed gate.")
    if task_pack_context.get("coverage"):
        criteria.append("Record required capability coverage and missing required capabilities.")
    if task_pack_context.get("invariant_capabilities"):
        criteria.append("Preserve invariant capabilities throughout execution.")
    if task_pack_context.get("pipeline_plan", {}).get("approval_gates"):
        criteria.append("Stop before approval-required runtime actions until the host runtime or operator approves them.")
    criteria.append("Record verification evidence before claiming completion.")
    criteria.append("List unresolved assumptions and residual risks in the handoff.")
    return list(dict.fromkeys(criteria))
```

- [ ] **Step 2: Add completion contract helper**

Add this function after `build_acceptance_criteria`:

```python
def build_completion_contract(task_pack_context: dict) -> dict:
    stop_conditions = [
        "required input missing",
        "registry verification failed",
        "approval-required runtime action blocked",
        "required capability missing and no fallback exists",
    ]
    quality = task_pack_context.get("selection_quality", {})
    if quality.get("low_confidence"):
        stop_conditions.append("low-confidence route requires explicit residual-risk handoff")
    if quality.get("missing_required_count", 0):
        stop_conditions.append("missing required capabilities must be reported before completion")
    return {
        "final_response_must_include": [
            "selected_scenario",
            "selected_skills",
            "verification_performed",
            "unresolved_assumptions",
            "residual_risks",
        ],
        "stop_conditions": list(dict.fromkeys(stop_conditions)),
        "evidence_requirements": [
            "commands or checks run",
            "schema or format checks",
            "source or provenance checks when relevant",
            "failed or unavailable checks",
        ],
    }
```

- [ ] **Step 3: Render completion contract in agent instructions**

In `build_agent_instructions`, after the pipeline plan block and before `Selected skills:`, add:

```python
    if router_context and router_context.get("acceptance_criteria"):
        lines.extend(["Acceptance criteria:"])
        for criterion in router_context["acceptance_criteria"]:
            lines.append(f"- {criterion}")
        lines.append("")
    if router_context and router_context.get("completion_contract"):
        contract = router_context["completion_contract"]
        lines.extend(["Completion contract:"])
        lines.append("- final response must include: " + ", ".join(contract.get("final_response_must_include", [])))
        lines.append("- stop conditions: " + ", ".join(contract.get("stop_conditions", [])))
        lines.append("- evidence requirements: " + ", ".join(contract.get("evidence_requirements", [])))
        lines.append("")
```

- [ ] **Step 4: Add fields to scenario and mesh task packs**

In each scenario and mesh branch in `build_task_pack`, after creating the `task_pack` dict and before calling `build_agent_instructions`, add:

```python
        task_pack["acceptance_criteria"] = build_acceptance_criteria(task_pack)
        task_pack["completion_contract"] = build_completion_contract(task_pack)
        task_pack["agent_instructions"] = build_agent_instructions(task, skills, bundles, task_pack)
```

Remove the previous direct assignment that called `build_agent_instructions` before these fields existed.

- [ ] **Step 5: Add fields to simple task packs**

In the simple router return branch, replace the immediate return with:

```python
    task_pack = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "task": task,
        "task_taxonomy": task_taxonomy,
        "skill_count": len(skills),
        "bundle_count": len(bundles),
        "safety_boundary": "Only use trusted skills by default. Skills provide method and verification guidance, not runtime permissions.",
        "registry_verification": verification,
        "skills": skills,
        "bundles": bundles,
    }
    task_pack["acceptance_criteria"] = build_acceptance_criteria(task_pack)
    task_pack["completion_contract"] = build_completion_contract(task_pack)
    task_pack["agent_instructions"] = build_agent_instructions(task, skills, bundles, task_pack)
    return task_pack
```

- [ ] **Step 6: Render new fields in Markdown**

In `render_task_pack_markdown`, after selection explanations and before selected skills, add:

```python
    if task_pack.get("selection_quality"):
        quality = task_pack["selection_quality"]
        lines.extend(
            [
                "",
                "## Selection Quality",
                "",
                f"- confidence: `{quality.get('confidence', 'low')}`",
                f"- score: `{quality.get('score', 0)}`",
                f"- coverage ratio: `{quality.get('coverage_ratio', 0)}`",
                f"- low confidence: `{quality.get('low_confidence', False)}`",
            ]
        )
        for warning in quality.get("warnings", []):
            lines.append(f"- warning: {warning}")
    if task_pack.get("acceptance_criteria"):
        lines.extend(["", "## Acceptance Criteria", ""])
        for criterion in task_pack["acceptance_criteria"]:
            lines.append(f"- {criterion}")
    if task_pack.get("completion_contract"):
        contract = task_pack["completion_contract"]
        lines.extend(["", "## Completion Contract", ""])
        lines.append("- final response must include: " + ", ".join(contract.get("final_response_must_include", [])))
        lines.append("- stop conditions: " + ", ".join(contract.get("stop_conditions", [])))
        lines.append("- evidence requirements: " + ", ".join(contract.get("evidence_requirements", [])))
```

- [ ] **Step 7: Run focused CLI tests**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_task_pack_outputs_json_for_trusted_matching_skills tests.test_registry_cli.RegistryCliTest.test_task_pack_outputs_markdown tests.test_registry_cli.RegistryCliTest.test_real_catalog_scenario_router_selects_website_bundle -v
```

Expected: PASS.

- [ ] **Step 8: Run registry CLI tests**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_registry_cli -v
```

Expected: PASS.

- [ ] **Step 9: Commit task-pack implementation**

```bash
git add src/onecode_skill_sanitizer/cli.py tests/test_registry_cli.py
git commit -m "feat: add task pack completion contract"
```

---

### Task 5: Add Claude-Skills Metadata-Only Reference

**Files:**
- Modify: `external-references/index.json`
- Modify: `tests/test_registry_cli.py`

- [ ] **Step 1: Add test that real references include claude-skills safely**

Add this test near the existing reference-check tests in `tests/test_registry_cli.py`:

```python
    def test_real_external_references_include_claude_skills_metadata_only(self):
        reference_out = io.StringIO()
        with contextlib.redirect_stdout(reference_out):
            reference_code = main(["reference-check", "--references", "external-references/index.json"])

        self.assertEqual(reference_code, 0)
        result = json.loads(reference_out.getvalue())
        self.assertEqual(result["status"], "ok")
        references = json.loads(Path("external-references/index.json").read_text(encoding="utf-8"))["references"]
        claude_skills = next((item for item in references if item["name"] == "claude-skills"), None)

        self.assertIsNotNone(claude_skills)
        self.assertEqual(claude_skills["adoption_status"], "reference_only")
        self.assertTrue(claude_skills["metadata_only"])
        self.assertIn("multi_agent_distribution", claude_skills["claimed_capabilities"])
        self.assertIn("Do not install", claude_skills["runtime_permission_notes"])
```

- [ ] **Step 2: Run the new test and confirm failure**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_real_external_references_include_claude_skills_metadata_only -v
```

Expected: FAIL because `claude-skills` is not in `external-references/index.json`.

- [ ] **Step 3: Add the reference entry**

In `external-references/index.json`, increment `reference_count` from `10` to `11` and append this object to the `references` array:

```json
{
  "adoption_status": "reference_only",
  "author": "alirezarezvani",
  "captured_at": "2026-07-02",
  "claimed_capabilities": [
    "large_skill_template_library",
    "multi_agent_distribution",
    "domain_packaging",
    "companion_cli_scripts",
    "persona_and_command_patterns"
  ],
  "license": "MIT",
  "metadata_only": true,
  "name": "claude-skills",
  "project_category": "multi_agent_skill_library_reference",
  "review_notes": "Public GitHub skill library with README claims of 354 skills across many domains and support for 13 coding agents. Useful as a product-packaging, coverage-gap, and distribution-pattern reference. Popularity and upstream skill count are not treated as trust evidence.",
  "runtime_permission_notes": "Reference only. Do not install, copy, execute, convert, or promote upstream skills into trusted status without per-skill license review, sanitization, hash recording, schema validation, and operator approval.",
  "source_type": "github_reference",
  "source_url": "https://github.com/alirezarezvani/claude-skills",
  "taxonomy_categories": [
    "ai.context-engineering",
    "engineering.workflow",
    "business.operations",
    "security.supply_chain"
  ]
}
```

- [ ] **Step 4: Run reference tests**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_reference_check_accepts_metadata_only_external_references tests.test_registry_cli.RegistryCliTest.test_real_external_references_include_claude_skills_metadata_only -v
```

Expected: PASS.

- [ ] **Step 5: Run reference check**

Run:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer reference-check --references external-references/index.json
```

Expected: JSON output with `"status": "ok"` and `"reference_count": 11`.

- [ ] **Step 6: Commit reference update**

```bash
git add external-references/index.json tests/test_registry_cli.py
git commit -m "docs: record claude skills reference"
```

---

### Task 6: Add Catalog Overview Maintenance Document

**Files:**
- Create: `docs/catalog-overview.md`
- Modify: `README.md`

- [ ] **Step 1: Create catalog overview document**

Create `docs/catalog-overview.md` with this content:

```markdown
# Catalog Overview

Safe-Agent-Skills is organized around trusted, method-only skills selected by
the router. The recommended user entry remains the single `safe-agent-router`
skill, not manual installation of every catalog skill.

## Current Baseline

- 114 catalog skills
- 108 trusted skills
- 13 trusted scenario bundles
- 15 top-level categories
- trusted-only default routing
- provenance, hash, schema, and maintain checks before publication

## Domain Map

| Domain | Use For | Example Command |
| --- | --- | --- |
| `ai` | agent planning, routing, schemas, RAG, output validation | `onecode-skill-sanitizer task-pack "design a RAG document agent" --registry catalog --include-bundles --bundles bundles/index.json --router scenario` |
| `code` | code review, debugging, regression tests, refactor safety | `onecode-skill-sanitizer task-pack "review generated code and harden tests" --registry catalog --include-bundles --bundles bundles/index.json --router scenario` |
| `design` | UI review, design-system consistency, responsive checks | `onecode-skill-sanitizer task-pack "polish a product dashboard UI" --registry catalog --include-bundles --bundles bundles/index.json --router scenario` |
| `security` | prompt injection, supply chain, guardrails, secret redaction | `onecode-skill-sanitizer task-pack "review an agent workflow for connector permissions" --registry catalog --include-bundles --bundles bundles/index.json --router scenario` |
| `content` | SEO briefs, editorial checks, claims compliance, social posts | `onecode-skill-sanitizer task-pack "draft and fact check an SEO blog post" --registry catalog --include-bundles --bundles bundles/index.json --router scenario` |
| `data` | data quality, table analysis, document-to-knowledge workflows | `onecode-skill-sanitizer task-pack "clean spreadsheet data and prepare chart notes" --registry catalog --include-bundles --bundles bundles/index.json --router scenario` |
| `commerce` | marketplace listings, keyword plans, buyer replies | `onecode-skill-sanitizer task-pack "prepare marketplace listing keywords" --registry catalog --include-bundles --bundles bundles/index.json --router scenario` |
| `research` | source checks, citation maps, paper synthesis, freshness review | `onecode-skill-sanitizer task-pack "synthesize a paper with source checks" --registry catalog --include-bundles --bundles bundles/index.json --router scenario` |

## Maintenance Priorities

The next catalog expansion should happen after router and task-pack contract
improvements are verified. Priority gaps are finance, project management,
business operations, commercial workflows, and research operations.

External libraries such as `claude-skills` are reference-only. Do not install,
copy, execute, or trust upstream skills without per-skill review.
```

- [ ] **Step 2: Link catalog overview from README**

In `README.md`, after the public baseline bullet list, add:

```markdown

For a domain-oriented map of the catalog and example router commands, see
[Catalog Overview](docs/catalog-overview.md).
```

- [ ] **Step 3: Run Markdown/private path scans**

Run:

```bash
rg -n "TO""DO|FIX""ME|PLACE[H]OLDER|T[B]D|待""定" docs/catalog-overview.md README.md
```

Expected: no output and exit code `1`.

Run:

```bash
rg -n '/[U]sers/|大[字]典|/one[ ]code/' docs/catalog-overview.md README.md
```

Expected: no output and exit code `1`.

- [ ] **Step 4: Commit docs**

```bash
git add docs/catalog-overview.md README.md
git commit -m "docs: add catalog overview"
```

---

### Task 7: Full Verification And Final Fixes

**Files:**
- May modify files touched above only if verification finds issues.

- [ ] **Step 1: Run compile and unit tests**

Run:

```bash
PYTHONPATH=src python3 -m compileall src tests
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Expected: compile succeeds and all tests pass.

- [ ] **Step 2: Run maintained verification script**

Run:

```bash
bash scripts/verify.sh
```

Expected: exits `0`.

- [ ] **Step 3: Inspect task-pack output manually**

Run:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer task-pack "复查 safe-agent-skills 项目是否达到智能选择和自动搭配 skill 的目标" --registry catalog --include-bundles --bundles bundles/index.json --router mesh --format json > /tmp/safe-agent-smart-pack.json
python3 -m json.tool /tmp/safe-agent-smart-pack.json >/dev/null
```

Expected: both commands exit `0`.

Run:

```bash
rg -n '"selection_quality"|"acceptance_criteria"|"completion_contract"' /tmp/safe-agent-smart-pack.json
```

Expected: output includes all three field names.

- [ ] **Step 4: Check final git status**

Run:

```bash
git status --short
```

Expected: only intentional tracked changes from this plan are present. Pre-existing untracked Chinese audit report files may remain and must not be added unless the user asks.

- [ ] **Step 5: Commit verification fixes if any**

If Step 1 or Step 2 required fixes, commit them:

```bash
git add src/onecode_skill_sanitizer/router.py src/onecode_skill_sanitizer/cli.py tests/test_router.py tests/test_registry_cli.py external-references/index.json docs/catalog-overview.md README.md
git commit -m "fix: stabilize smart skill execution contract"
```

If no fixes were needed, skip this commit.

- [ ] **Step 6: Final handoff**

Report:

- selected scenario bundle used for this work: `skill-router-quality-review`
- selected skills from the task pack
- verification commands and results
- files changed
- remaining risks, especially that `claude-skills` is reference-only and no upstream skills were imported or executed
