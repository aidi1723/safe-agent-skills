# Auto Orchestration Pipeline Plan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a method-only `pipeline_plan` orchestration contract to `smart` and scenario `task-pack` output.

**Architecture:** Implement a focused `build_pipeline_plan(...)` helper in `src/onecode_skill_sanitizer/router.py`, reuse existing route outputs, and attach the returned plan in `route_scenario_task` and `route_mesh_task`. Keep `execution_graph` unchanged for compatibility and add Markdown/docs coverage for hosts that want stage, gate, approval, and verification guidance.

**Tech Stack:** Python 3.11+ standard library, `unittest`, existing `onecode_skill_sanitizer` CLI/router modules, Markdown docs.

---

## File Structure

- Modify `src/onecode_skill_sanitizer/router.py`
  - Add fixed stage vocabulary, stage metadata, runtime-sensitive action detection, scenario-specific stage mappings, fallback stage mapping, and `build_pipeline_plan(...)`.
  - Attach `pipeline_plan` to scenario and mesh router return dictionaries.
- Modify `src/onecode_skill_sanitizer/cli.py`
  - Copy `routed["pipeline_plan"]` into JSON task packs for `router_mode == "scenario"` and `router_mode == "mesh"`.
  - Render a concise `Pipeline Plan` section in Markdown output.
  - Add pipeline guidance to `agent_instructions` without changing simple router output.
- Modify `tests/test_router.py`
  - Add unit coverage for direct `build_pipeline_plan(...)` behavior.
- Modify `tests/test_registry_cli.py`
  - Add CLI regression coverage for scenario router JSON, smart JSON, Markdown rendering, and simple router backward compatibility.
- Modify `docs/smart-skill-router.md`
  - Document the new `pipeline_plan` output field and method-only boundary.
- Modify `docs/agent-task-pack.md`
  - Document `pipeline_plan` for scenario task packs and host-agent use.
- Optionally modify `README.md`
  - Add one short mention if the existing router section needs it after docs are updated.

## Task 1: Add Router Unit Tests For `pipeline_plan`

**Files:**
- Modify: `tests/test_router.py`
- Modify later: `src/onecode_skill_sanitizer/router.py`

- [ ] **Step 1: Import `build_pipeline_plan` in router tests**

In `tests/test_router.py`, update the import block:

```python
from onecode_skill_sanitizer.router import (
    build_capability_coverage,
    build_contract_graph,
    build_execution_graph,
    build_execution_plan,
    build_pipeline_plan,
    build_selection_explanations,
    build_task_profile,
    parse_invariant_capabilities,
    route_mesh_task,
    route_scenario_task,
    score_bundle_for_profile,
)
```

- [ ] **Step 2: Add a scenario-specific plan test**

Add this test method to `RouterTest` after `test_route_scenario_task_selects_skill_router_quality_review_bundle`:

```python
    def test_build_pipeline_plan_for_skill_router_quality_review(self):
        profile = build_task_profile("复查 safe-agent-skills 项目是否达到智能选择和自动搭配 skill 的目标")
        bundle = {
            "id": "skill-router-quality-review",
            "name": "Skill Router Quality Review",
            "safety_boundary": "Skills provide method only; runtime permissions remain controlled by the host agent.",
        }
        skills = [
            {"name": "ai-opensquilla-metaskill-workflow", "match_score": 0},
            {"name": "ai-opensquilla-token-routing-pattern", "match_score": 0},
            {"name": "ai-tool-schema-protocol-check", "match_score": 0},
            {"name": "ai-output-schema-eval", "match_score": 0},
            {"name": "code-test-regression", "match_score": 0},
            {"name": "engineering-ci-troubleshoot", "match_score": 0},
        ]
        coverage = [
            {
                "capability": "skill_selection_quality",
                "required": True,
                "status": "covered",
                "skill": "ai-opensquilla-token-routing-pattern",
                "preferred_skills": ["ai-opensquilla-token-routing-pattern"],
            }
        ]

        plan = build_pipeline_plan(
            task="复查 safe-agent-skills 项目是否达到智能选择和自动搭配 skill 的目标",
            task_profile=profile,
            selected_bundle=bundle,
            selected_skills=skills,
            coverage=coverage,
            execution_graph={},
            invariants=None,
        )

        self.assertEqual(plan["id"], "skill-router-quality-review")
        self.assertEqual(plan["mode"], "method_only")
        self.assertEqual(plan["source"], "trusted_scenario_bundle")
        self.assertIn("runtime permissions", plan["runtime_boundary"])
        self.assertEqual(
            [stage["id"] for stage in plan["stages"]],
            ["preflight", "planning", "review", "verification", "handoff"],
        )
        self.assertIn("ai-opensquilla-metaskill-workflow", plan["stages"][0]["skills"])
        self.assertIn("ai-tool-schema-protocol-check", plan["stages"][2]["skills"])
        self.assertIn("code-test-regression", plan["stages"][3]["skills"])
        for stage in plan["stages"]:
            self.assertIn("id", stage)
            self.assertIn("name", stage)
            self.assertIn("purpose", stage)
            self.assertIn("skills", stage)
            self.assertIn("inputs", stage)
            self.assertIn("outputs", stage)
            self.assertIn("gate", stage)
            self.assertIn("verification", stage)
            self.assertIn("condition", stage["gate"])
            self.assertIn("failure_action", stage["gate"])
```

- [ ] **Step 3: Add a general fallback plan test**

Add this test method after the previous new test:

```python
    def test_build_pipeline_plan_general_fallback_does_not_invent_scenario(self):
        profile = build_task_profile("帮我看一下这个事情是否合理")
        skills = [
            {"name": "ai-opensquilla-metaskill-workflow", "match_score": 12},
            {"name": "research-source-check", "match_score": 4},
        ]

        plan = build_pipeline_plan(
            task="帮我看一下这个事情是否合理",
            task_profile=profile,
            selected_bundle={},
            selected_skills=skills,
            coverage=[],
            execution_graph={},
            invariants=None,
        )

        self.assertEqual(plan["id"], "general")
        self.assertEqual(plan["name"], "General")
        self.assertEqual(plan["source"], "direct_skill_selection")
        self.assertEqual(plan["mode"], "method_only")
        self.assertEqual(plan["low_confidence_note"], "No trusted scenario matched; use direct selected skills only.")
        self.assertEqual([stage["id"] for stage in plan["stages"]], ["source", "planning", "handoff"])
        self.assertIn("research-source-check", plan["stages"][0]["skills"])
        self.assertIn("ai-opensquilla-metaskill-workflow", plan["stages"][1]["skills"])
        self.assertEqual(plan["approval_gates"], [])
```

- [ ] **Step 4: Add a runtime-sensitive approval gate test**

Add this test method after the previous new test:

```python
    def test_build_pipeline_plan_marks_video_runtime_approval_gates(self):
        profile = build_task_profile("Copywriting 写文案，Content Strategy 规划内容矩阵，Remotion 实现一句话灵感到成片")
        bundle = {
            "id": "content-video-production",
            "name": "Content Video Production",
            "safety_boundary": "Programmatic video execution needs separate runtime and license review.",
        }
        skills = [
            {"name": "content-strategy-matrix", "match_score": 0},
            {"name": "media-video-script-review", "match_score": 0},
            {"name": "media-remotion-video-production-boundary", "match_score": 0},
            {"name": "media-asset-review", "match_score": 0},
            {"name": "execution-publish-check", "match_score": 0},
        ]

        plan = build_pipeline_plan(
            task="Copywriting 写文案，Content Strategy 规划内容矩阵，Remotion 实现一句话灵感到成片",
            task_profile=profile,
            selected_bundle=bundle,
            selected_skills=skills,
            coverage=[],
            execution_graph={},
            invariants=None,
        )

        approval_required = {
            item
            for gate in plan["approval_gates"]
            for item in gate["required_for"]
        }
        self.assertIn("media rendering", approval_required)
        self.assertIn("file upload or publication", approval_required)
        self.assertIn("dependency install", approval_required)
        self.assertIn("paid model or provider call", approval_required)
        self.assertIn("media-remotion-video-production-boundary", [skill for stage in plan["stages"] for skill in stage["skills"]])
```

- [ ] **Step 5: Run tests to verify they fail**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_router
```

Expected: FAIL with `ImportError: cannot import name 'build_pipeline_plan'` or equivalent missing function error.

- [ ] **Step 6: Commit failing tests**

```bash
git add tests/test_router.py
git commit -m "test: add pipeline plan router expectations"
```

## Task 2: Implement `build_pipeline_plan`

**Files:**
- Modify: `src/onecode_skill_sanitizer/router.py`
- Test: `tests/test_router.py`

- [ ] **Step 1: Add stage constants near existing graph constants**

In `src/onecode_skill_sanitizer/router.py`, place this code after `STAGE_GATE_BY_STAGE`:

```python
PIPELINE_STAGE_ORDER = ["preflight", "source", "planning", "production", "review", "verification", "handoff"]

PIPELINE_STAGE_INFO = {
    "preflight": {
        "name": "Preflight",
        "purpose": "Confirm task scope, safety boundary, required inputs, and missing information.",
        "inputs": ["user_task", "task_profile", "invariants"],
        "outputs": ["scope_summary", "missing_inputs", "runtime_boundary"],
        "condition": "Required inputs are known or explicitly marked missing.",
        "failure_action": "stop_and_request_missing_inputs",
        "verification": ["trusted skill status checked", "runtime boundary recorded"],
    },
    "source": {
        "name": "Source",
        "purpose": "Inventory source material, provenance, citations, and retrieved context.",
        "inputs": ["user_task", "task_profile"],
        "outputs": ["source_inventory", "provenance_notes", "source_risks"],
        "condition": "Required sources are identified or source gaps are recorded.",
        "failure_action": "record_source_gap_and_stop_if_source_is_required",
        "verification": ["source provenance checked", "citation or evidence gaps recorded"],
    },
    "planning": {
        "name": "Planning",
        "purpose": "Decompose the task, choose the method, and define the output contract.",
        "inputs": ["task_profile", "coverage", "selected_skills"],
        "outputs": ["work_plan", "output_contract", "unresolved_assumptions"],
        "condition": "Plan covers required capabilities or missing capabilities are recorded.",
        "failure_action": "revise_plan_or_mark_missing_capability",
        "verification": ["required capability coverage reviewed", "selected skill rationale recorded"],
    },
    "production": {
        "name": "Production",
        "purpose": "Apply method-only execution guidance under host-controlled permissions.",
        "inputs": ["work_plan", "selected_skills"],
        "outputs": ["draft_artifact_or_method_notes", "execution_boundary_notes"],
        "condition": "Host approval boundaries are respected before any runtime action.",
        "failure_action": "stop_before_runtime_action_and_request_approval",
        "verification": ["runtime boundary checked", "approval-sensitive actions identified"],
    },
    "review": {
        "name": "Review",
        "purpose": "Check safety, quality, compliance, schema, rights, and review risks.",
        "inputs": ["draft_artifact_or_method_notes", "coverage"],
        "outputs": ["review_findings", "risk_notes", "correction_targets"],
        "condition": "Required review risks are recorded with correction targets.",
        "failure_action": "return_to_planning_or_production_with_findings",
        "verification": ["review findings are specific", "safety and compliance boundaries preserved"],
    },
    "verification": {
        "name": "Verification",
        "purpose": "Run or plan tests, checks, schema validation, and evidence capture.",
        "inputs": ["review_findings", "selected_skills"],
        "outputs": ["verification_evidence", "failed_checks", "residual_risks"],
        "condition": "Verification evidence is recorded or unavailable checks are explained.",
        "failure_action": "record_failed_check_and_stop_before_success_claim",
        "verification": ["test or check command recorded when available", "residual risk stated"],
    },
    "handoff": {
        "name": "Handoff",
        "purpose": "Summarize outputs, unresolved risks, and next approval boundary.",
        "inputs": ["verification_evidence", "review_findings", "runtime_boundary"],
        "outputs": ["final_summary", "unresolved_risks", "next_approval_boundary"],
        "condition": "Handoff includes evidence, risks, and method-only boundary.",
        "failure_action": "revise_handoff_until_boundary_and_risks_are_explicit",
        "verification": ["unresolved risks listed", "method-only boundary repeated"],
    },
}
```

- [ ] **Step 2: Add scenario-specific stage maps**

Place this code after the constants from Step 1:

```python
SCENARIO_STAGE_SKILLS = {
    "content-video-production": {
        "preflight": ["content-strategy-matrix", "content-seo-brief"],
        "planning": ["content-brand-voice-boundary", "media-video-script-review"],
        "production": ["media-remotion-video-production-boundary"],
        "review": ["content-editorial-review", "content-claims-compliance-filter", "media-asset-review"],
        "verification": ["execution-publish-check"],
    },
    "skill-router-quality-review": {
        "preflight": ["ai-opensquilla-metaskill-workflow"],
        "planning": ["ai-opensquilla-token-routing-pattern", "ai-langchain-agent-orchestration"],
        "review": ["ai-tool-schema-protocol-check", "ai-pydantic-schema-contract", "ai-output-schema-eval"],
        "verification": ["code-test-regression", "engineering-ci-troubleshoot"],
        "handoff": ["ai-rule-failure-log-synthesis", "security-supply-chain-review"],
    },
}

RUNTIME_APPROVAL_RULES = [
    {
        "required_for": "dependency install",
        "signals": ["install", "dependency", "npm", "pip", "package", "remotion", "ffmpeg", "安装", "依赖"],
    },
    {
        "required_for": "shell command execution",
        "signals": ["shell", "command", "execute", "script", "bash", "命令", "脚本", "执行"],
    },
    {
        "required_for": "browser automation",
        "signals": ["browser", "playwright", "screenshot", "浏览器", "截图"],
    },
    {
        "required_for": "network access",
        "signals": ["network", "web", "crawl", "download", "upload", "api", "联网", "下载", "上传"],
    },
    {
        "required_for": "MCP server exposure",
        "signals": ["mcp"],
    },
    {
        "required_for": "proxy/wrapper startup",
        "signals": ["proxy", "wrapper", "wrap", "代理"],
    },
    {
        "required_for": "account or API-key use",
        "signals": ["api key", "account", "credential", "token", "apikey", "密钥", "账号", "凭证"],
    },
    {
        "required_for": "file upload or publication",
        "signals": ["publish", "upload", "release", "上线", "发布", "上传"],
    },
    {
        "required_for": "media rendering",
        "signals": ["render", "video", "media", "remotion", "ffmpeg", "成片", "视频", "渲染"],
    },
    {
        "required_for": "paid model or provider call",
        "signals": ["paid", "provider", "openai", "anthropic", "elevenlabs", "fal", "model", "付费", "模型"],
    },
    {
        "required_for": "destructive filesystem or git action",
        "signals": ["delete", "remove", "reset", "overwrite", "rm", "删除", "重置", "覆盖"],
    },
]
```

- [ ] **Step 3: Add helper functions before `build_execution_graph`**

Place this code before `build_execution_graph`:

```python
def pipeline_stage_for_skill(skill_name: str) -> str:
    if any(marker in skill_name for marker in ["test", "check", "verify", "ci-troubleshoot", "publish-check"]):
        return "verification"
    if skill_name.startswith(("research-", "data-", "office-")):
        return "source"
    if skill_name.startswith(("business-", "ai-", "commerce-")):
        return "planning"
    if skill_name.startswith(("security-", "compliance-", "content-claims")):
        return "review"
    if skill_name.startswith(("design-", "content-", "code-", "media-asset")):
        return "review"
    if skill_name.startswith(("execution-", "engineering-", "media-remotion")):
        return "production"
    return "production"


def selected_skill_names(selected_skills: list[dict]) -> list[str]:
    names = []
    for skill in selected_skills:
        name = skill.get("name", "")
        if name and name not in names:
            names.append(name)
    return names


def scenario_stage_skill_map(bundle_id: str, skill_names: list[str]) -> dict[str, list[str]]:
    stage_map = {stage: [] for stage in PIPELINE_STAGE_ORDER}
    explicit = SCENARIO_STAGE_SKILLS.get(bundle_id, {})
    assigned = set()
    for stage in PIPELINE_STAGE_ORDER:
        for name in explicit.get(stage, []):
            if name in skill_names and name not in assigned:
                stage_map[stage].append(name)
                assigned.add(name)
    for name in skill_names:
        if name in assigned:
            continue
        stage_map[pipeline_stage_for_skill(name)].append(name)
    return {stage: names for stage, names in stage_map.items() if names}


def approval_gate_text(task: str, bundle: dict, skills: list[dict]) -> str:
    parts = [task, bundle.get("id", ""), bundle.get("name", ""), bundle.get("scenario", ""), bundle.get("safety_boundary", "")]
    parts.extend(skill.get("name", "") for skill in skills)
    parts.extend(skill.get("description", "") for skill in skills)
    return normalize_task_text(" ".join(parts))


def build_approval_gates(task: str, bundle: dict, skills: list[dict]) -> list[dict]:
    text = approval_gate_text(task, bundle, skills)
    required_for = []
    for rule in RUNTIME_APPROVAL_RULES:
        if any(normalize_task_text(signal) in text for signal in rule["signals"]):
            required_for.append(rule["required_for"])
    if not required_for:
        return []
    return [
        {
            "stage": "production",
            "required_for": required_for,
            "owner": "host_runtime_or_operator",
        }
    ]


def build_pipeline_stage(stage_id: str, skills: list[str], unresolved_risks: list[str] | None = None) -> dict:
    info = PIPELINE_STAGE_INFO[stage_id]
    stage = {
        "id": stage_id,
        "name": info["name"],
        "purpose": info["purpose"],
        "skills": skills,
        "inputs": list(info["inputs"]),
        "outputs": list(info["outputs"]),
        "gate": {
            "id": f"{stage_id}_complete",
            "condition": info["condition"],
            "failure_action": info["failure_action"],
        },
        "verification": list(info["verification"]),
    }
    if unresolved_risks:
        stage["unresolved_risks"] = unresolved_risks
    return stage
```

- [ ] **Step 4: Add `build_pipeline_plan` before `route_scenario_task`**

Place this code after `build_selection_explanations`:

```python
def build_pipeline_plan(
    task: str,
    task_profile: dict,
    selected_bundle: dict,
    selected_skills: list[dict],
    coverage: list[dict],
    execution_graph: dict | None = None,
    invariants: list[str] | str | None = None,
) -> dict:
    skill_names = selected_skill_names(selected_skills)
    bundle_id = selected_bundle.get("id", "")
    source = "trusted_scenario_bundle" if bundle_id else "direct_skill_selection"
    plan_id = bundle_id or "general"
    plan_name = selected_bundle.get("name") or (selected_bundle.get("id") if bundle_id else "General")
    runtime_boundary = selected_bundle.get("safety_boundary") or "Skills provide method only; host runtime controls permissions."
    stage_skill_map = scenario_stage_skill_map(bundle_id, skill_names)
    missing_required = [
        item["capability"]
        for item in coverage
        if item.get("required", True) and item.get("status") == "missing"
    ]
    handoff_risks = []
    if missing_required:
        handoff_risks.append("Missing required capabilities: " + ", ".join(missing_required))
    if not bundle_id:
        handoff_risks.append("No trusted scenario matched; use direct selected skills only.")

    stages = [
        build_pipeline_stage(stage, skills)
        for stage, skills in stage_skill_map.items()
        if stage != "handoff" and skills
    ]
    stages.sort(key=lambda stage: PIPELINE_STAGE_ORDER.index(stage["id"]))
    stages.append(build_pipeline_stage("handoff", stage_skill_map.get("handoff", []), handoff_risks or None))

    plan = {
        "schema_version": 1,
        "id": plan_id,
        "name": plan_name,
        "mode": "method_only",
        "source": source,
        "runtime_boundary": runtime_boundary,
        "stages": stages,
        "approval_gates": build_approval_gates(task, selected_bundle, selected_skills),
    }
    if not bundle_id:
        plan["low_confidence_note"] = "No trusted scenario matched; use direct selected skills only."
    return plan
```

- [ ] **Step 5: Run router unit tests**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_router
```

Expected: tests from Task 1 pass or expose a concrete mismatch in stage ordering/gates.

- [ ] **Step 6: Fix any mismatch with minimal changes**

If the content-video approval test does not include a required approval item, update only `RUNTIME_APPROVAL_RULES` signal lists. If stage placement differs, update only `SCENARIO_STAGE_SKILLS` or `pipeline_stage_for_skill`.

- [ ] **Step 7: Commit implementation**

```bash
git add src/onecode_skill_sanitizer/router.py
git commit -m "feat: add method-only pipeline plan builder"
```

## Task 3: Attach `pipeline_plan` To Scenario And Mesh Router Output

**Files:**
- Modify: `src/onecode_skill_sanitizer/router.py`
- Test: `tests/test_router.py`

- [ ] **Step 1: Add pipeline plan assertion to existing scenario route test**

In `tests/test_router.py`, update `test_route_scenario_task_selects_skill_router_quality_review_bundle` by adding:

```python
        self.assertEqual(routed["pipeline_plan"]["id"], "skill-router-quality-review")
        self.assertEqual(routed["pipeline_plan"]["mode"], "method_only")
        self.assertEqual(routed["pipeline_plan"]["source"], "trusted_scenario_bundle")
```

- [ ] **Step 2: Add pipeline plan assertion to general route test**

In `test_general_task_profile_does_not_select_scenario_bundle`, add:

```python
        self.assertEqual(routed["pipeline_plan"]["id"], "general")
        self.assertEqual(routed["pipeline_plan"]["source"], "direct_skill_selection")
```

- [ ] **Step 3: Add mesh route test for pipeline plan**

Add this test near existing mesh tests in `tests/test_router.py`:

```python
    def test_route_mesh_task_includes_pipeline_plan(self):
        bundle = {
            "id": "skill-router-quality-review",
            "name": "Skill Router Quality Review",
            "scenario": "Review skill router quality, automatic selection, and bundle composition behavior.",
            "status": "trusted",
            "task_signals": ["safe-agent-skills", "skill router", "智能选择", "自动搭配"],
            "skills": [
                "ai-opensquilla-metaskill-workflow",
                "ai-opensquilla-token-routing-pattern",
                "ai-tool-schema-protocol-check",
                "code-test-regression",
            ],
            "required_capabilities": [
                {"id": "skill_selection_quality", "required": True, "preferred_skills": ["ai-opensquilla-token-routing-pattern"]},
                {"id": "bundle_quality", "required": True, "preferred_skills": ["ai-opensquilla-metaskill-workflow"]},
                {"id": "routing_contract", "required": True, "preferred_skills": ["ai-tool-schema-protocol-check"]},
                {"id": "regression_test", "required": True, "preferred_skills": ["code-test-regression"]},
            ],
            "execution_order": [
                "ai-opensquilla-metaskill-workflow",
                "ai-opensquilla-token-routing-pattern",
                "ai-tool-schema-protocol-check",
                "code-test-regression",
            ],
            "safety_boundary": "Skills provide method only; runtime permissions remain controlled by the host agent.",
        }
        selected = [{"name": name, "match_score": 0} for name in bundle["skills"]]

        routed = route_mesh_task(
            task="复查 safe-agent-skills 项目是否达到智能选择和自动搭配 skill 的目标",
            invariants=None,
            selected_skills=selected,
            bundles_index={"bundles": [bundle]},
            trusted_skill_names={skill["name"] for skill in selected},
            overlap_groups=None,
            max_skills=8,
            strategy="balanced",
        )

        self.assertEqual(routed["pipeline_plan"]["id"], "skill-router-quality-review")
        self.assertEqual(routed["pipeline_plan"]["mode"], "method_only")
        self.assertEqual(routed["pipeline_plan"]["source"], "trusted_scenario_bundle")
```

- [ ] **Step 4: Run tests to verify they fail**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_router
```

Expected: FAIL because `pipeline_plan` is not yet present in `routed`.

- [ ] **Step 5: Attach `pipeline_plan` in `route_scenario_task`**

In `route_scenario_task`, after `execution_plan` and `explanations` are built, add:

```python
    pipeline_plan = build_pipeline_plan(
        task=task,
        task_profile=profile,
        selected_bundle=selected_bundle,
        selected_skills=routed_skills,
        coverage=coverage,
        execution_graph=None,
        invariants=None,
    )
```

Then add this key to the returned dictionary:

```python
        "pipeline_plan": pipeline_plan,
```

- [ ] **Step 6: Attach `pipeline_plan` in `route_mesh_task`**

In `route_mesh_task`, before the final `return`, assign:

```python
    execution_graph = (
        final_graph
        if final_graph.get("mode") == "contract" and final_graph.get("acyclic", True)
        else build_execution_graph(routed_skills)
    )
    pipeline_plan = build_pipeline_plan(
        task=task,
        task_profile=profile,
        selected_bundle=selected_bundle,
        selected_skills=routed_skills,
        coverage=coverage,
        execution_graph=execution_graph,
        invariants=invariants,
    )
```

Then replace the existing inline `"execution_graph": ...` expression with:

```python
        "execution_graph": execution_graph,
        "pipeline_plan": pipeline_plan,
```

- [ ] **Step 7: Run router tests**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_router
```

Expected: PASS.

- [ ] **Step 8: Commit routed output changes**

```bash
git add src/onecode_skill_sanitizer/router.py tests/test_router.py
git commit -m "feat: attach pipeline plan to router outputs"
```

## Task 4: Expose `pipeline_plan` In CLI JSON And Markdown

**Files:**
- Modify: `src/onecode_skill_sanitizer/cli.py`
- Modify: `tests/test_registry_cli.py`

- [ ] **Step 1: Add CLI JSON assertions for scenario router**

In `tests/test_registry_cli.py`, update `test_real_catalog_scenario_router_selects_skill_router_quality_review_bundle` by adding:

```python
        self.assertEqual(task_pack["pipeline_plan"]["id"], "skill-router-quality-review")
        self.assertEqual(task_pack["pipeline_plan"]["mode"], "method_only")
        self.assertEqual(task_pack["pipeline_plan"]["source"], "trusted_scenario_bundle")
        self.assertTrue(task_pack["pipeline_plan"]["stages"])
```

- [ ] **Step 2: Add CLI JSON assertions for smart router**

In `test_real_catalog_smart_router_selects_skill_router_quality_review_bundle`, add:

```python
        self.assertEqual(task_pack["pipeline_plan"]["id"], "skill-router-quality-review")
        self.assertEqual(task_pack["pipeline_plan"]["mode"], "method_only")
        self.assertTrue(task_pack["pipeline_plan"]["stages"])
```

- [ ] **Step 3: Add simple router backward compatibility assertion**

In `test_task_pack_simple_router_remains_backward_compatible`, add:

```python
            self.assertNotIn("pipeline_plan", task_pack)
```

- [ ] **Step 4: Add Markdown rendering test**

Add this test near other real catalog router tests:

```python
    def test_smart_markdown_renders_pipeline_plan(self):
        task_pack_out = io.StringIO()
        with contextlib.redirect_stdout(task_pack_out):
            task_pack_code = main(
                [
                    "smart",
                    "复查 safe-agent-skills 项目是否达到智能选择和自动搭配 skill 的目标",
                    "--registry",
                    "catalog",
                    "--bundles",
                    "bundles/index.json",
                    "--max-skills",
                    "8",
                    "--format",
                    "markdown",
                ]
            )

        self.assertEqual(task_pack_code, 0)
        markdown = task_pack_out.getvalue()
        self.assertIn("## Pipeline Plan", markdown)
        self.assertIn("- id: `skill-router-quality-review`", markdown)
        self.assertIn("### Preflight", markdown)
        self.assertIn("method-only", markdown.lower())
```

- [ ] **Step 5: Run CLI tests to verify they fail**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_registry_cli
```

Expected: FAIL because `pipeline_plan` is not copied into task packs or rendered yet.

- [ ] **Step 6: Copy `pipeline_plan` into mesh task packs**

In `build_task_pack`, inside the `router_mode == "mesh"` task pack dictionary, add:

```python
            "pipeline_plan": routed["pipeline_plan"],
```

Place it near `"execution_graph": routed["execution_graph"],`.

- [ ] **Step 7: Copy `pipeline_plan` into scenario task packs**

In `build_task_pack`, inside the `router_mode == "scenario"` task pack dictionary, add:

```python
            "pipeline_plan": routed["pipeline_plan"],
```

Place it near `"execution_plan": routed["execution_plan"],`.

- [ ] **Step 8: Add pipeline guidance to `build_agent_instructions`**

In `build_agent_instructions`, after the capability coverage block and before `Selected skills:`, add:

```python
    if router_context and router_context.get("pipeline_plan"):
        plan = router_context["pipeline_plan"]
        lines.extend(["Pipeline plan:"])
        lines.append(f"- id: {plan.get('id', 'general')}")
        lines.append(f"- mode: {plan.get('mode', 'method_only')}")
        lines.append(f"- boundary: {plan.get('runtime_boundary', 'Skills provide method only.')}")
        for stage in plan.get("stages", []):
            skill_list = ", ".join(stage.get("skills", [])) or "no selected skills"
            lines.append(f"- {stage['id']}: {stage['purpose']} Skills: {skill_list}. Gate: {stage['gate']['condition']}")
        lines.append("")
```

- [ ] **Step 9: Render pipeline plan in Markdown**

In `render_task_pack_markdown`, after the `Execution Graph` block and before `Selection Explanations`, add:

```python
        if task_pack.get("pipeline_plan"):
            plan = task_pack["pipeline_plan"]
            lines.extend(
                [
                    "",
                    "## Pipeline Plan",
                    "",
                    f"- id: `{plan.get('id', '')}`",
                    f"- mode: `{plan.get('mode', '')}`",
                    f"- source: `{plan.get('source', '')}`",
                    f"- boundary: {plan.get('runtime_boundary', '')}",
                    "",
                ]
            )
            for stage in plan.get("stages", []):
                lines.extend(
                    [
                        f"### {stage['name']}",
                        "",
                        f"- id: `{stage['id']}`",
                        f"- purpose: {stage['purpose']}",
                        f"- skills: {', '.join(f'`{name}`' for name in stage.get('skills', [])) or 'none'}",
                        f"- gate: {stage['gate']['condition']}",
                        f"- failure action: `{stage['gate']['failure_action']}`",
                        "",
                    ]
                )
            if plan.get("approval_gates"):
                lines.extend(["### Approval Gates", ""])
                for gate in plan["approval_gates"]:
                    lines.append(
                        f"- `{gate['stage']}` requires `{gate['owner']}` approval for: {', '.join(gate.get('required_for', []))}"
                    )
                lines.append("")
```

- [ ] **Step 10: Run CLI tests**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_registry_cli
```

Expected: PASS.

- [ ] **Step 11: Commit CLI exposure**

```bash
git add src/onecode_skill_sanitizer/cli.py tests/test_registry_cli.py
git commit -m "feat: expose pipeline plan in task packs"
```

## Task 5: Update Documentation

**Files:**
- Modify: `docs/smart-skill-router.md`
- Modify: `docs/agent-task-pack.md`
- Modify: `README.md` if needed

- [ ] **Step 1: Update smart router output docs**

In `docs/smart-skill-router.md`, in the `Output` list, add:

```markdown
- `pipeline_plan`
```

After the execution graph paragraph, add:

```markdown
`pipeline_plan` is a method-only orchestration contract layered on top of the
selected trusted skills. It groups selected skills into stages such as
`preflight`, `source`, `planning`, `production`, `review`, `verification`, and
`handoff`; each stage includes inputs, outputs, a gate condition, verification
notes, and failure handling guidance. The plan is advisory: it does not execute
tools or grant runtime permissions.
```

- [ ] **Step 2: Update agent task pack docs**

In `docs/agent-task-pack.md`, add a section near the router/scenario output description:

```markdown
## Pipeline Plan

Scenario and smart router task packs include `pipeline_plan`, a method-only
stage contract for host agents. Hosts can use it to decide what to do first,
what evidence to collect before moving to the next stage, and which actions
require operator or host-runtime approval.

The field does not grant permissions. Dependency installation, shell commands,
browser automation, network access, MCP/proxy startup, account or API-key use,
file upload, media rendering, paid provider calls, and destructive filesystem
or git actions remain controlled by the host runtime and operator policy.
```

- [ ] **Step 3: Update README only if examples mention output fields**

If the README router section lists `execution_graph` fields, add `pipeline_plan` to that same list. Use this exact sentence:

```markdown
`pipeline_plan` adds method-only stage contracts with gates, verification notes,
approval boundaries, and handoff risks while preserving the existing
`execution_graph` field for compatibility.
```

- [ ] **Step 4: Run docs grep for consistency**

Run:

```bash
rg -n "pipeline_plan|execution_graph|method-only|runtime permissions" README.md docs/smart-skill-router.md docs/agent-task-pack.md
```

Expected: output shows `pipeline_plan` documented in smart router and agent task pack docs.

- [ ] **Step 5: Commit docs**

```bash
git add docs/smart-skill-router.md docs/agent-task-pack.md README.md
git commit -m "docs: describe method-only pipeline plans"
```

If `README.md` was not changed, omit it from `git add`.

## Task 6: Final Verification

**Files:**
- Verify only, no planned edits.

- [ ] **Step 1: Run focused router tests**

```bash
PYTHONPATH=src python3 -m unittest tests.test_router
```

Expected: PASS.

- [ ] **Step 2: Run focused CLI tests**

```bash
PYTHONPATH=src python3 -m unittest tests.test_registry_cli
```

Expected: PASS.

- [ ] **Step 3: Verify catalog integrity**

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry catalog
```

Expected: JSON with `"status": "ok"` and `"tampered_count": 0`.

- [ ] **Step 4: Verify schema integrity**

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer schema-check --registry catalog
```

Expected: JSON with `"status": "ok"`.

- [ ] **Step 5: Verify maintain check**

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check --registry catalog --bundles bundles/index.json --references external-references/index.json
```

Expected: JSON with `"status": "ok"`.

- [ ] **Step 6: Inspect git status**

```bash
git status --short
```

Expected: only known pre-existing untracked user files remain, or a clean tree if those files were handled outside this plan.

## Self-Review Notes

- Spec coverage: The plan covers `pipeline_plan`, method-only mode, stage vocabulary, scenario mapping, general fallback, approval gates, JSON output, Markdown output, docs, and verification.
- Compatibility: Simple router output remains unchanged and explicitly tested with `assertNotIn("pipeline_plan", task_pack)`.
- Runtime boundary: The implementation adds approval metadata only; it does not add external tools, execution, proxies, MCP servers, or model calls.
- Risk: Approval gate detection is deterministic signal matching. It is intentionally conservative and advisory, not an enforcement layer.
