# Hybrid Router v2 First Milestone Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver Schema v2, deterministic multi-intent routing, multi-scenario composition, a validated global DAG, Schema v1 compatibility, independent evaluation, and at least 80% contract coverage for core scenario skills.

**Architecture:** Preserve the current v1 deterministic router while adding focused v2 modules. `intent.py` decomposes tasks, `candidates.py` retrieves trusted scenarios, `composer.py` selects multiple scenarios, `compiler.py` creates the global DAG, and `compatibility.py` supplies stable identity and v1 conversion. `cli.py` chooses the v1 or v2 pipeline through `--schema-version`; runtime execution remains owned by the host.

**Tech Stack:** Python 3.11+, standard-library dataclasses and JSON, `unittest`, JSON Schema, existing catalog and bundle JSON, Ruff, GitHub Actions.

---

## Scope

Included:

- Schema v2 task packs
- deterministic multi-intent decomposition
- multiple selected scenario bundles
- global dependency DAG
- explicit incomplete and blocked routes
- Schema v1 compatibility
- Contract v2 validation and coverage gates
- 100 independently reviewed multi-intent cases

Excluded until follow-on plans:

- local or remote semantic providers
- embeddings and LLM reranking
- execution-event ingestion and `replan`
- automatic contract approval
- autonomous shell, browser, network, connector, or publishing execution

## File Map

New runtime files:

- `src/onecode_skill_sanitizer/intent.py`
- `src/onecode_skill_sanitizer/candidates.py`
- `src/onecode_skill_sanitizer/composer.py`
- `src/onecode_skill_sanitizer/compiler.py`
- `src/onecode_skill_sanitizer/compatibility.py`
- `src/onecode_skill_sanitizer/contracts.py`

New validation and evaluation files:

- `schemas/intent-graph.schema.json`
- `schemas/task-pack-v2.schema.json`
- `schemas/contract-v2.schema.json`
- `evals/router-quality-v2.json`
- `evals/multi-intent-gold.json`
- `tests/test_intent.py`
- `tests/test_candidates.py`
- `tests/test_composer.py`
- `tests/test_compiler.py`
- `tests/test_compatibility.py`
- `tests/test_contracts.py`
- `tests/test_router_eval_v2.py`

Existing integration files:

- `src/onecode_skill_sanitizer/router.py`
- `src/onecode_skill_sanitizer/cli.py`
- `src/onecode_skill_sanitizer/validation.py`
- `tests/test_registry_cli.py`
- `tests/test_router.py`
- `tests/test_validation.py`
- `scripts/verify.sh`
- `README.md`
- `docs/smart-skill-router.md`
- `docs/agent-task-pack.md`
- `docs/router-development.md`
- `docs/operator-guide.md`
- `docs/architecture.md`

---

### Task 1: Freeze Schema v1 and Add Version Selection

**Files:**
- Modify: `src/onecode_skill_sanitizer/cli.py`
- Modify: `tests/test_registry_cli.py`
- Create: `evals/router-quality-v2.json`

- [ ] **Step 1: Write the failing v1 preservation test**

Add to `tests/test_registry_cli.py`:

```python
def test_smart_schema_v1_preserves_current_contract(self):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        exit_code = main(
            [
                "smart",
                "build a landing page and prepare launch checks",
                "--registry",
                "catalog",
                "--bundles",
                "bundles/index.json",
                "--schema-version",
                "1",
                "--format",
                "json",
            ]
        )
    payload = json.loads(out.getvalue())
    self.assertEqual(exit_code, 0)
    self.assertEqual(payload["schema_version"], 1)
    self.assertEqual(payload["router"]["mode"], "deterministic_mesh_router")
    self.assertEqual(payload["selected_scenario"]["id"], "website-build-launch")
    self.assertIn("selection_trace", payload)
    self.assertIn("completion_contract", payload)
```

- [ ] **Step 2: Run the test and verify it fails**

```bash
PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_smart_schema_v1_preserves_current_contract -v
```

Expected: FAIL because `--schema-version` is unknown.

- [ ] **Step 3: Add CLI version arguments**

Add to both `smart` and `task-pack` parsers:

```python
parser.add_argument("--schema-version", type=int, choices=[1, 2], default=2)
```

Until Task 5 wires v2, route both values through the current builder. Explicit
version 1 must preserve every current field.

- [ ] **Step 4: Copy the current evaluation corpus**

Create `evals/router-quality-v2.json` with:

```json
{
  "schema_version": 2,
  "dataset": "router-quality-v2-baseline",
  "split": "regression",
  "case_count": 43,
  "cases": []
}
```

Copy all 43 cases from `evals/router-quality.json` unchanged.

- [ ] **Step 5: Run the test and commit**

```bash
PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_smart_schema_v1_preserves_current_contract -v
git add src/onecode_skill_sanitizer/cli.py tests/test_registry_cli.py evals/router-quality-v2.json
git commit -m "test: freeze router schema v1 baseline"
```

Expected: PASS.

---

### Task 2: Add Intent Models and Deterministic Decomposition

**Files:**
- Create: `src/onecode_skill_sanitizer/intent.py`
- Create: `tests/test_intent.py`
- Create: `schemas/intent-graph.schema.json`

- [ ] **Step 1: Write failing intent tests**

Create `tests/test_intent.py` with four cases:

```python
import unittest

from onecode_skill_sanitizer.intent import decompose_task, normalize_task


class IntentTest(unittest.TestCase):
    def test_normalize_task_preserves_structured_context(self):
        normalized = normalize_task(
            "历史：之前在写官网\n当前任务：审计 skill 路由器\n过期上下文：发布旧版本"
        )
        self.assertEqual(normalized.current, "审计 skill 路由器")
        self.assertEqual(normalized.history, "之前在写官网")
        self.assertEqual(normalized.stale, "发布旧版本")
        self.assertEqual(normalized.stale_policy, "ignore_for_routing")

    def test_decompose_compound_release_task(self):
        graph = decompose_task("构建官网，同时审计 skill 路由器，验证通过后发布更新")
        self.assertEqual(
            [intent.task_type for intent in graph.intents],
            ["website_build", "skill_router_review", "open_source_release"],
        )
        self.assertEqual(graph.intents[2].depends_on, ("i1", "i2"))
        self.assertEqual(graph.validate(), [])

    def test_does_not_over_split_code_review_lifecycle(self):
        graph = decompose_task("审查代码并补强测试后合并 PR")
        self.assertEqual(len(graph.intents), 1)
        self.assertEqual(graph.intents[0].task_type, "code_review")

    def test_numbered_steps_create_release_dependencies(self):
        graph = decompose_task("1. 分析数据\n2. 生成报告\n3. 发布结果")
        self.assertEqual(len(graph.intents), 3)
        self.assertEqual(graph.intents[2].depends_on, ("i1", "i2"))
```

- [ ] **Step 2: Verify failure**

```bash
PYTHONPATH=src python3 -m unittest tests.test_intent -v
```

Expected: FAIL because `intent.py` is missing.

- [ ] **Step 3: Implement immutable models**

Create `NormalizedTask`, `Intent`, and `IntentGraph` frozen dataclasses.
`IntentGraph.validate()` must report unknown dependencies and cycles.
`to_json()` must convert tuples to JSON arrays.

Required signatures:

```python
def normalize_task(task: str) -> NormalizedTask: ...
def split_task_clauses(task: str) -> list[str]: ...
def classify_intent(clause: str, index: int) -> Intent: ...
def decompose_task(task: str) -> IntentGraph: ...
```

Reuse `split_current_intent_text()` and `build_task_profile()` from `router.py`.

- [ ] **Step 4: Implement bounded splitting rules**

Recognize:

- numbered and bulleted lists
- `同时`, `以及`, semicolons, and standalone English `and`
- explicit release phrases such as `验证通过后发布`
- coupled lifecycle exceptions such as `审查代码并补强测试后合并 PR`

Do not split every `后`, `并`, or `and`. Release intents depend on all preceding
intents unless a fixture declares a narrower dependency.

- [ ] **Step 5: Add the intent JSON Schema**

Use JSON Schema 2020-12. Require non-empty intents, IDs matching
`^i[1-9][0-9]*$`, source in `deterministic|semantic|hybrid`, confidence from 0
through 1, string arrays, and `additionalProperties: false` on each intent.

- [ ] **Step 6: Verify and commit**

```bash
PYTHONPATH=src python3 -m unittest tests.test_intent tests.test_router -v
python3 -m json.tool schemas/intent-graph.schema.json >/dev/null
git add src/onecode_skill_sanitizer/intent.py tests/test_intent.py schemas/intent-graph.schema.json
git commit -m "feat: add deterministic multi-intent decomposition"
```

---

### Task 3: Retrieve and Compose Multiple Scenarios

**Files:**
- Create: `src/onecode_skill_sanitizer/candidates.py`
- Create: `src/onecode_skill_sanitizer/composer.py`
- Create: `tests/test_candidates.py`
- Create: `tests/test_composer.py`
- Modify: `src/onecode_skill_sanitizer/router.py`

- [ ] **Step 1: Write failing candidate tests**

Verify the compound fixture maps `i1`, `i2`, and `i3` first to:

```text
website-build-launch
skill-router-quality-review
open-source-release
```

Verify `继续做完它` returns no scenario candidate.

- [ ] **Step 2: Write failing composition tests**

Verify the compound fixture selects all three scenarios in intent order with
`status == "complete"`. Verify the vague fixture has no selections,
`uncovered_intents == ("i1",)`, and `status == "incomplete"`.

- [ ] **Step 3: Run both test modules**

```bash
PYTHONPATH=src python3 -m unittest tests.test_candidates tests.test_composer -v
```

Expected: FAIL because the modules are missing.

- [ ] **Step 4: Expose explicit profile construction**

Add to `router.py`:

```python
def build_profile_for_task_type(task: str, task_type: str) -> dict:
    profile = build_task_profile(task)
    if profile["task_type"] == task_type:
        return profile
    configured = next(
        (item for item in SCENARIO_PROFILES if item["task_type"] == task_type),
        None,
    )
    if configured is None:
        return profile
    return {
        "task_type": configured["task_type"],
        "primary_domain": configured["primary_domain"],
        "secondary_domains": list(configured["secondary_domains"]),
        "artifact_types": list(configured["artifact_types"]),
        "risk_flags": list(configured["risk_flags"]),
        "required_capabilities": list(configured["required_capabilities"]),
        "matched_signal_score": max(1, profile["matched_signal_score"]),
    }
```

- [ ] **Step 5: Implement candidate retrieval**

Create frozen `ScenarioCandidate` with `intent_id`, `scenario_id`, normalized
`score`, and `deterministic_score`. For each non-general intent, score only
trusted bundles with `score_bundle_for_profile()`, sort descending, and retain a
bounded top N.

- [ ] **Step 6: Implement the initial composer**

Create frozen `ScenarioSelection` and `ScenarioComposition`. Select the best
trusted candidate per intent, merge equal scenario IDs, preserve intent order,
and record uncovered intents. Keep the interface compatible with a later greedy
set-cover implementation.

- [ ] **Step 7: Verify and commit**

```bash
PYTHONPATH=src python3 -m unittest tests.test_candidates tests.test_composer tests.test_router -v
git add src/onecode_skill_sanitizer/candidates.py src/onecode_skill_sanitizer/composer.py tests/test_candidates.py tests/test_composer.py src/onecode_skill_sanitizer/router.py
git commit -m "feat: compose trusted scenarios per intent"
```

---

### Task 4: Compile and Validate the Global DAG

**Files:**
- Create: `src/onecode_skill_sanitizer/compiler.py`
- Create: `tests/test_compiler.py`

- [ ] **Step 1: Write failing DAG tests**

Test that release nodes receive incoming dependencies from both website and
router-review intents. Add a test-only reverse dependency and verify the route
becomes `blocked`, `acyclic == false`, with reason `dependency_cycle`.

- [ ] **Step 2: Verify failure**

```bash
PYTHONPATH=src python3 -m unittest tests.test_compiler -v
```

- [ ] **Step 3: Build nodes and scenario-order edges**

Create one node per selected intent and ordered scenario Skill:

```python
{
    "id": f"skill:{intent_id}:{skill_name}",
    "intent_ids": [intent_id],
    "scenario_ids": [scenario_id],
    "skill": skill_name,
    "stage": pipeline_stage_for_skill(skill_name),
    "host_action": skill_name.startswith("execution-"),
}
```

Connect adjacent skills with `scenario_order` edges.

- [ ] **Step 4: Add cross-intent edges and cycle detection**

Connect terminal nodes of every prerequisite intent to root nodes of the
 dependent intent using `intent_dependency`. Implement Kahn cycle detection.
Return:

```python
{
    "schema_version": 2,
    "status": "ready" if acyclic else "blocked",
    "acyclic": acyclic,
    "nodes": nodes,
    "edges": edges,
    "reason_codes": [] if acyclic else ["dependency_cycle"],
}
```

Never silently turn a cyclic graph into a successful stage fallback.

- [ ] **Step 5: Verify and commit**

```bash
PYTHONPATH=src python3 -m unittest tests.test_compiler tests.test_router -v
git add src/onecode_skill_sanitizer/compiler.py tests/test_compiler.py
git commit -m "feat: compile global multi-scenario dag"
```

---

### Task 5: Assemble Schema v2 and Preserve Schema v1

**Files:**
- Create: `src/onecode_skill_sanitizer/compatibility.py`
- Create: `tests/test_compatibility.py`
- Create: `schemas/task-pack-v2.schema.json`
- Modify: `src/onecode_skill_sanitizer/cli.py`
- Modify: `tests/test_registry_cli.py`
- Modify: `src/onecode_skill_sanitizer/__init__.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Write failing compatibility tests**

Test that canonical JSON key order produces the same `sha256:` route ID. Test
that converting a two-scenario v2 payload selects the highest-scoring primary
scenario and records dropped scenarios and cross-scenario edges.

- [ ] **Step 2: Write failing v2 CLI tests**

Add tests asserting:

- the compound fixture returns Schema v2 and the three scenarios
- graph status is ready
- provider used is `none`
- host execution mode is `method_only`
- vague tasks are incomplete with no selected scenarios

- [ ] **Step 3: Run the tests**

```bash
PYTHONPATH=src python3 -m unittest tests.test_compatibility -v
PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_smart_schema_v2_routes_compound_task tests.test_registry_cli.RegistryCliTest.test_smart_schema_v2_marks_vague_task_incomplete -v
```

Expected: FAIL until v2 assembly exists.

- [ ] **Step 4: Implement compatibility helpers**

Implement:

```python
def build_route_id(inputs: dict) -> str: ...
def to_legacy_v1(payload: dict) -> dict: ...
```

`to_legacy_v1()` must add:

```json
{
  "compatibility_loss": {
    "multi_intent_dropped": true,
    "scenarios_dropped": [],
    "cross_scenario_edges_dropped": 0
  }
}
```

- [ ] **Step 5: Implement `build_task_pack_v2()`**

The builder verifies the registry, runs Tasks 2–4, loads selected trusted Skill
pack items, and returns every approved v2 field. Until semantic providers are
implemented, use:

```python
"provider": {
    "requested": "none",
    "used": "none",
    "fallback_reason": "semantic_provider_not_enabled_in_first_milestone",
}
```

Use this fixed boundary:

```python
"host_execution_protocol": {
    "mode": "method_only",
    "runtime_boundary": "The host runtime controls permissions and execution.",
    "node_statuses": [
        "pending", "ready", "running", "waiting_approval",
        "completed", "failed", "blocked", "skipped",
    ],
}
```

- [ ] **Step 6: Route CLI by requested schema**

Version 2 calls the v2 builder. Version 1 keeps the existing complete v1 path.
Add a v2 Markdown renderer for intents, scenarios, uncovered intents, graph
status, and safety boundary.

- [ ] **Step 7: Add package version and task-pack schema**

Set project and package version to `0.2.0`. Create
`schemas/task-pack-v2.schema.json`, reference the intent graph schema, require
all approved top-level fields, and disallow unknown top-level fields.

- [ ] **Step 8: Verify and commit**

```bash
PYTHONPATH=src python3 -m unittest tests.test_compatibility -v
PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_smart_schema_v1_preserves_current_contract tests.test_registry_cli.RegistryCliTest.test_smart_schema_v2_routes_compound_task tests.test_registry_cli.RegistryCliTest.test_smart_schema_v2_marks_vague_task_incomplete -v
python3 -m json.tool schemas/task-pack-v2.schema.json >/dev/null
git add src/onecode_skill_sanitizer/compatibility.py tests/test_compatibility.py src/onecode_skill_sanitizer/cli.py tests/test_registry_cli.py schemas/task-pack-v2.schema.json src/onecode_skill_sanitizer/__init__.py pyproject.toml
git commit -m "feat: expose hybrid router task pack v2"
```

---

### Task 6: Add Contract v2 and Core Coverage Gate

**Files:**
- Create: `src/onecode_skill_sanitizer/contracts.py`
- Create: `tests/test_contracts.py`
- Create: `schemas/contract-v2.schema.json`
- Modify: `src/onecode_skill_sanitizer/validation.py`
- Modify: `tests/test_validation.py`
- Modify: `src/onecode_skill_sanitizer/cli.py`
- Modify: core `catalog/*/*/skill.json`
- Modify: `scripts/verify.sh`

- [ ] **Step 1: Write failing Contract v2 tests**

Add validation tests for a complete v2 contract and rejection of
`retry_policy: execute_automatically`. Add coverage tests using two bundle
skills where one has a usable contract, expecting ratio `0.5`.

- [ ] **Step 2: Run tests and verify failure**

```bash
PYTHONPATH=src python3 -m unittest tests.test_validation tests.test_contracts -v
```

- [ ] **Step 3: Extend validation**

Allow and validate:

```text
schema_version
optional_context
approval_classes
estimated_cost
idempotent
retry_policy
```

Rules:

- version absent, 1, or 2
- string lists for optional context and approvals
- integer cost fields `time`, `tokens`, and `runtime`, each 0–5
- boolean idempotent
- retry policy `host_decides`, `never`, or `safe_once`

Use stable issue IDs ending in `version`, `cost`, `idempotent`, and
`retry-policy`.

- [ ] **Step 4: Implement coverage calculation and command**

`contract_coverage(registry, bundles_index, scenario_ids=None)` returns counts,
ratio, and missing names. Add `contract-check` with repeatable `--scenario` and
`--minimum-ratio`; exit 2 below threshold.

- [ ] **Step 5: Add Contract v2 JSON Schema**

Require version, stage, and capability vector for newly migrated v2 contracts.
Python validation remains backward compatible with existing v1 contracts.

- [ ] **Step 6: Migrate the core set**

Use exactly these scenarios:

```text
website-build-launch
code-review-hardening
codebase-change-lifecycle
skill-router-quality-review
open-source-release
rag-agent-knowledge-app
document-to-knowledge-base
security-agent-guardrails
```

Add usable v2 contracts to at least 80% of their unique Skills. Derive concrete
artifacts from each Skill's current workflow and verifier expectations. Add
runtime approval classes only where applicable:

```text
browser_automation
network_access
publication
shell_execution
dependency_install
paid_provider
destructive_action
```

- [ ] **Step 7: Reseal and add the CI gate**

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer reindex --registry catalog
PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check --registry catalog --bundles bundles/index.json --references external-references/index.json --claude-skills-candidate-map docs/claude-skills-candidate-map.json
```

Add a `contract-check` command with all eight `--scenario` values and
`--minimum-ratio 0.80` to `scripts/verify.sh`.

- [ ] **Step 8: Verify and commit**

```bash
PYTHONPATH=src python3 -m unittest tests.test_validation tests.test_contracts -v
python3 -m json.tool schemas/contract-v2.schema.json >/dev/null
bash scripts/verify.sh
git add src/onecode_skill_sanitizer/contracts.py tests/test_contracts.py src/onecode_skill_sanitizer/validation.py tests/test_validation.py src/onecode_skill_sanitizer/cli.py schemas/contract-v2.schema.json catalog scripts/verify.sh
git commit -m "feat: add contract v2 coverage gate"
```

---

### Task 7: Add Independent Multi-Intent Evaluation

**Files:**
- Create: `evals/multi-intent-gold.json`
- Create: `tests/test_router_eval_v2.py`
- Modify: `src/onecode_skill_sanitizer/cli.py`
- Modify: `scripts/verify.sh`

- [ ] **Step 1: Create exactly 100 independently reviewed cases**

Distribution:

- 40 compound multi-scenario tasks
- 20 sequential dependency tasks
- 15 vague or context-dependent tasks
- 10 negative tasks selecting no scenario
- 10 multilingual, typo, or paraphrase tasks
- 5 safety-sensitive compound tasks

Each case contains ID, task, ordered expected intents, expected scenarios,
required dependency edges, and forbidden scenarios. Labels must not be generated
from router output.

- [ ] **Step 2: Write failing evaluator tests**

Test exact dataset count and require metrics:

```text
multi_intent_exact_match
scenario_precision
scenario_recall
scenario_f1
forbidden_scenario_false_positive_rate
dependency_edge_recall
dag_validity
```

- [ ] **Step 3: Implement `evaluate_router_v2()`**

For every case, build a v2 route, compare ordered intent types, compare scenario
sets, enforce forbidden scenarios, compare dependency edges, and validate graph
status. Use explicit zero-denominator handling.

- [ ] **Step 4: Add `router-eval-v2`**

Arguments:

```text
--eval required
--registry catalog
--bundles bundles/index.json
```

Print JSON. Exit 2 for dataset/schema errors or unexpected invalid DAGs. Add the
command to `scripts/verify.sh`.

- [ ] **Step 5: Verify and commit**

```bash
PYTHONPATH=src python3 -m unittest tests.test_router_eval_v2 -v
PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval-v2 --eval evals/multi-intent-gold.json --registry catalog --bundles bundles/index.json
bash scripts/verify.sh
git add evals/multi-intent-gold.json tests/test_router_eval_v2.py src/onecode_skill_sanitizer/cli.py scripts/verify.sh
git commit -m "test: add independent multi-intent evaluation"
```

---

### Task 8: Document, Verify, and Close the Milestone

**Files:**
- Modify: `README.md`
- Modify: `docs/smart-skill-router.md`
- Modify: `docs/agent-task-pack.md`
- Modify: `docs/router-development.md`
- Modify: `docs/operator-guide.md`
- Modify: `docs/architecture.md`
- Modify: `docs/delivery-readiness-report.md`
- Create: `docs/hybrid-router-v2-first-milestone-report.md`
- Modify: `scripts/verify.sh`

- [ ] **Step 1: Document the exact product boundary**

Use:

```text
Schema v2 decomposes and composes multiple trusted workflows, but remains
method-only. It does not execute selected skills or grant runtime permissions.
```

Document v1/v2 commands, `contract-check`, and `router-eval-v2`.

- [ ] **Step 2: Document Schema v2 fields and states**

Cover every field from the approved design. Include complete, incomplete, and
blocked examples. State that v1 compatibility drops secondary intents and
scenarios.

- [ ] **Step 3: Document contributor gates**

Require independent gold labels, multi-intent fixtures for decomposition
changes, contract coverage for new bundle skills, deterministic tests without a
provider, and blocked output for cyclic graphs.

- [ ] **Step 4: Finish verification coverage**

Ensure `scripts/verify.sh` validates all three new schemas, v1 evaluation, v2
evaluation, and the 80% core contract gate.

- [ ] **Step 5: Run release evidence**

```bash
python3 --version
python3 -m ruff check .
bash scripts/verify.sh
PYTHONPATH=src python3 -m onecode_skill_sanitizer smart "构建官网，同时审计 skill 路由器，验证通过后发布更新" --schema-version 2 --format json > /tmp/hybrid-router-v2-acceptance.json
PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval-v2 --eval evals/multi-intent-gold.json --registry catalog --bundles bundles/index.json > /tmp/hybrid-router-v2-eval.json
```

- [ ] **Step 6: Assert acceptance output**

```bash
python3 - <<'PY'
import json

route = json.load(open("/tmp/hybrid-router-v2-acceptance.json", encoding="utf-8"))
evaluation = json.load(open("/tmp/hybrid-router-v2-eval.json", encoding="utf-8"))

assert route["schema_version"] == 2
assert [item["scenario"] for item in route["selected_scenarios"]] == [
    "website-build-launch",
    "skill-router-quality-review",
    "open-source-release",
]
assert route["execution_graph"]["acyclic"] is True
assert route["host_execution_protocol"]["mode"] == "method_only"
assert evaluation["metrics"]["dag_validity"] == 1.0
print("hybrid router v2 first milestone acceptance: ok")
PY
```

- [ ] **Step 7: Write the evidence report**

Record exact commands, exit codes, test count, v1 compatibility, compound-task
result, contract ratio, v2 metrics, known errors, pending provider work, pending
replanning work, and the method-only boundary. Do not claim semantic routing is
complete.

- [ ] **Step 8: Final verification and commit**

```bash
bash scripts/verify.sh
git status --short
git add README.md docs scripts/verify.sh
git commit -m "docs: close hybrid router v2 first milestone"
```

---

## Completion Gate

The milestone is complete only when:

- Schema v2 is the default for `smart`.
- Schema v1 remains available and current v1 evaluations pass.
- The mandatory compound task selects all three scenarios.
- Release depends on both preceding intent paths.
- Vague tasks are incomplete rather than falsely routed.
- Cyclic global graphs are blocked.
- Core scenario Contract coverage is at least 80%.
- The independent dataset contains exactly 100 cases.
- New schemas, tests, lint, maintenance checks, v1 evaluation, v2 evaluation,
  and verification commands pass.
- Documentation consistently states the method-only boundary.

## Follow-On Plans

After this gate passes:

1. `hybrid-router-v2-semantic-providers`: provider protocol, local HTTP,
   OpenAI-compatible structured output, privacy policy, semantic reranking,
   deterministic fallback, and confidence calibration.
2. `hybrid-router-v2-host-replanning`: execution event schema, transition
   validation, ready-node calculation, approval propagation, method-only
   `replan`, and host integration fixtures.

Do not begin either plan before the deterministic milestone passes.
