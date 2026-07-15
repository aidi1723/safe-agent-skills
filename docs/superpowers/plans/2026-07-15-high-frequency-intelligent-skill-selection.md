# High-Frequency Intelligent Skill Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an opt-in Router v3 that decides whether specialized guidance is needed, selects the minimum useful set from seven high-frequency trusted catalog Skills, constructs evidence-backed dependencies, and abstains or asks for clarification when evidence is insufficient.

**Architecture:** Keep v1 and v2 frozen. Route v3 through a dedicated pipeline: current-intent Need Gate, cohort-only deterministic recall, optional candidate-bounded semantic reranking, marginal capability composition, real dependency compilation, confidence gating, and strict task-pack v3 serialization. `safe-agent-router` remains the eighth cohort entry and user-facing gateway; it is not a candidate that can recursively select itself.

**Tech Stack:** Python 3.11 standard library, dataclasses and protocols, JSON Schema Draft 2020-12 through the existing `dev` extra, `unittest`, Bash release checks, JSON catalog and evaluation fixtures.

---

## File Structure

### Create

- `src/onecode_skill_sanitizer/need_gate.py`
  - Own the seven-Skill candidate allowlist, the eight-entry scope record, current-intent constraints, negation, explanation-only and inventory-only suppression, required capability extraction, and `none` / `single` / `composite` / `clarify` need decisions.
- `src/onecode_skill_sanitizer/skill_candidates.py`
  - Load and validate reviewed runtime routing examples, derive cohort profiles from existing `SKILL.md` and `skill.json` sources, recall Top-K trusted candidates, and emit decomposed deterministic evidence.
- `src/onecode_skill_sanitizer/semantic_provider.py`
  - Define the injectable semantic provider protocol, redact provider requests, bind requests to the deterministic candidate scope, strictly validate complete responses, and return deterministic fallback records.
- `src/onecode_skill_sanitizer/skill_selection.py`
  - Combine scores, enforce hard exclusions and conflicts, select only marginally useful Skills, resolve capability gaps, build artifact/order/verification edges, detect cycles, and compute confidence and routing status.
- `src/onecode_skill_sanitizer/task_pack_v3.py`
  - Orchestrate the v3 stages, build stable route identity including reviewed-example content, load selected Skill instructions, emit the strict v3 payload, and report v3-to-v2/v1 compatibility loss.
- `src/onecode_skill_sanitizer/router_eval_v3.py`
  - Strictly load the isolated held-out dataset, compute retrieval/composition/DAG/status metrics, enforce acceptance gates, and evaluate externally supplied selected-pack versus oracle task outcomes.
- `schemas/semantic-rerank-response.schema.json`
  - Define the provider response contract used by tests and adapter authors.
- `schemas/task-pack-v3.schema.json`
  - Define the strict opt-in task-pack contract and reject unknown top-level, provider, candidate, selection, confidence, and graph fields.
- `catalog/routing-examples.json`
  - Store only operator-reviewed positive, near-miss, negation, explanation-only, and composition examples for the seven catalog candidates; include `safe-agent-router` only in the declared eight-entry scope.
- `evals/high-frequency-skill-selection.json`
  - Store exactly 120 held-out validation/final-test cases, isolated from runtime loading.
- `tests/test_need_gate.py`
  - Cover need decisions, current-versus-stale context, exclusions, multilingual negation, explanation-only requests, and explicit Skill requests.
- `tests/test_skill_candidates.py`
  - Cover cohort integrity, reviewed-example validation, out-of-cohort rejection, Top-K ranking, adjacent-Skill discrimination, and deterministic evidence.
- `tests/test_semantic_provider.py`
  - Cover accepted shadow responses and whole-response rejection for timeout, unknown, duplicate, partial, non-numeric, non-finite, out-of-range, and malformed results.
- `tests/test_skill_selection.py`
  - Cover marginal capability selection, conflict handling, exact sets, incomplete/clarify/none/blocked states, real dependency edges, parallel nodes, and cycles.
- `tests/test_task_pack_v3_cli.py`
  - Cover v3 CLI opt-in, schema validation, route identity, Markdown escaping, selected instructions, bounded errors, and unchanged v1/v2 defaults.
- `tests/test_router_eval_v3.py`
  - Cover the exact 120-case contract, metric math, acceptance thresholds, final-test isolation, and task-level oracle comparison.

### Modify

- `src/onecode_skill_sanitizer/commands.py:361-452,541-582`
  - Dispatch schema v3 without changing v1/v2 branches; add bounded v3 and v3-evaluation commands.
- `src/onecode_skill_sanitizer/cli.py:1-145,199-267`
  - Re-export v3 boundaries, accept schema version 3, expose `--routing-examples`, and register `router-eval-v3` plus `router-task-eval-v3`.
- `src/onecode_skill_sanitizer/rendering.py:99-179`
  - Render v3 need, selection, confidence, provider, graph, diagnostics, and safety sections using single-line escaping.
- `src/onecode_skill_sanitizer/compatibility.py:1-220`
  - Add stable v3 compatibility-loss reporting without changing existing `to_legacy_v1` behavior.
- `tests/test_cli_boundaries.py:1-30`
  - Assert v3 builder/evaluator ownership and CLI re-exports.
- `tests/test_router_cli.py:850-900`
  - Cover the repository-local `safe-agent-router` wrapper with explicit v3 opt-in while preserving its v2 default.
- `integrations/skills/safe-agent-router/scripts/task_pack.sh:1-48`
  - Accept `--schema-version 2|3` and `--routing-examples`; keep schema 2 as the default.
- `integrations/skills/safe-agent-router/SKILL.md:1-113`
  - Document the v3 opt-in contract, first-class `none` and `clarify` results, candidate-bounded semantic shadow mode, and the unchanged method-only permission boundary.
- `scripts/verify.sh:1-170`
  - Validate the two new schemas and runtime examples, run v3 held-out gates, keep the 100-case v2 evaluation, and assert no runtime module references the held-out file.
- `README.md:300-380`, `docs/router-development.md`, `docs/agent-task-pack.md`, `docs/index.md`
  - Document v3 scope, commands, output states, evaluation evidence, rollout status, and link the maintained design and plan.

### Explicitly Unchanged

- The seven catalog `SKILL.md` bodies and manifests remain source-of-truth inputs in this milestone. Their recently deepened workflows are not rewritten merely to tune the evaluator. Selection improvements for them live in reviewed routing examples and v3 policy.
- `src/onecode_skill_sanitizer/candidates.py`, `composer.py`, and `compiler.py` remain the v2 scenario pipeline.
- `schemas/task-pack-v2.schema.json`, `evals/multi-intent-gold.json`, and v1/v2 snapshots remain frozen.
- No community runtime package, model router, connector, credential path, or execution engine is imported.

## Fixed Contracts

Use these names consistently in every task:

```python
HIGH_FREQUENCY_ENTRY_NAMES = (
    "safe-agent-router",
    "codebase-explore-map",
    "code-review-risk",
    "code-test-regression",
    "execution-browser-check",
    "research-source-check",
    "design-ui-review",
    "security-supply-chain-review",
)

HIGH_FREQUENCY_SKILL_NAMES = HIGH_FREQUENCY_ENTRY_NAMES[1:]
NEED_DECISIONS = {"none", "single", "composite", "clarify"}
ROUTING_STATUSES = {"none", "complete", "clarify", "incomplete", "blocked"}
SEMANTIC_MODES = {"none", "shadow", "influence"}
```

The public builder signature is:

```python
def build_task_pack_v3(
    registry_dir: Path,
    task: str,
    bundles_path: Path,
    routing_examples_path: Path,
    *,
    max_candidates: int = 3,
    semantic_provider: SemanticProvider | None = None,
    semantic_mode: str = "shadow",
) -> dict[str, Any]:
    raise NotImplementedError("task-pack v3 pipeline is not complete")
```

`semantic_mode="influence"` is a programmatic boundary only in this milestone. The CLI and `safe-agent-router` wrapper expose deterministic v3; injected Python API providers may run in shadow mode. No public command exposes influence mode until a separate release decision records all gates as passing.

---

### Task 1: Freeze Compatibility And Add V3 CLI Boundaries

**Files:**
- Modify: `tests/test_cli_boundaries.py`
- Create: `tests/test_task_pack_v3_cli.py`
- Modify later: `src/onecode_skill_sanitizer/cli.py`
- Modify later: `src/onecode_skill_sanitizer/commands.py`

- [ ] **Step 1: Add failing boundary tests**

Add to `tests/test_cli_boundaries.py`:

```python
from onecode_skill_sanitizer import router_eval_v3
from onecode_skill_sanitizer import task_pack_v3


def test_cli_reexports_v3_router_boundaries(self):
    self.assertIs(cli.build_task_pack_v3, task_pack_v3.build_task_pack_v3)
    self.assertIs(cli.evaluate_router_v3, router_eval_v3.evaluate_router_v3)
    self.assertIs(cli.load_eval_dataset_v3, router_eval_v3.load_eval_dataset_v3)
```

Create `tests/test_task_pack_v3_cli.py` with the parser freeze tests:

```python
from __future__ import annotations

import unittest

from onecode_skill_sanitizer.cli import build_parser


class TaskPackV3CliTest(unittest.TestCase):
    def test_v3_is_opt_in_and_v2_remains_default(self):
        parser = build_parser()
        default = parser.parse_args(["smart", "review this patch"])
        explicit = parser.parse_args(["smart", "review this patch", "--schema-version", "3"])
        task_pack = parser.parse_args(
            ["task-pack", "review this patch", "--registry", "catalog", "--schema-version", "3"]
        )

        self.assertEqual(default.schema_version, 2)
        self.assertEqual(explicit.schema_version, 3)
        self.assertEqual(task_pack.schema_version, 3)
        self.assertEqual(explicit.routing_examples, "catalog/routing-examples.json")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run RED**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_cli_boundaries tests.test_task_pack_v3_cli -v
```

Expected: FAIL because `task_pack_v3`, `router_eval_v3`, schema choice `3`, and `routing_examples` do not exist.

- [ ] **Step 3: Add only parser and import boundaries**

In `src/onecode_skill_sanitizer/cli.py`, add direct re-exports and extend both schema choices:

```python
from .router_eval_v3 import evaluate_router_v3 as evaluate_router_v3
from .router_eval_v3 import load_eval_dataset_v3 as load_eval_dataset_v3
from .task_pack_v3 import build_task_pack_v3 as build_task_pack_v3

# On both smart_parser and task_pack_parser:
parser.add_argument("--schema-version", type=int, choices=[1, 2, 3], default=2)
parser.add_argument("--routing-examples", default="catalog/routing-examples.json")
```

Create importable modules with their final public signatures and explicit feature errors so the boundary is real but cannot silently route:

```python
# src/onecode_skill_sanitizer/task_pack_v3.py
from __future__ import annotations

from pathlib import Path
from typing import Any


def build_task_pack_v3(
    registry_dir: Path,
    task: str,
    bundles_path: Path,
    routing_examples_path: Path,
    *,
    max_candidates: int = 3,
    semantic_provider: object | None = None,
    semantic_mode: str = "shadow",
) -> dict[str, Any]:
    raise NotImplementedError("task-pack v3 pipeline is not complete")
```

```python
# src/onecode_skill_sanitizer/router_eval_v3.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


def load_eval_dataset_v3(path: Path) -> list[dict[str, Any]]:
    raise NotImplementedError("router v3 evaluation loader is not complete")


def evaluate_router_v3(
    cases: list[dict[str, Any]],
    route_builder: Callable[[dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    raise NotImplementedError("router v3 evaluation is not complete")
```

- [ ] **Step 4: Run GREEN and frozen regression tests**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_cli_boundaries tests.test_task_pack_v3_cli -v
PYTHONPATH=src python3 -m unittest tests.test_task_pack_v2_cli tests.test_router_eval_v2 -v
```

Expected: PASS; the second command preserves all existing v2 behavior.

- [ ] **Step 5: Commit**

```bash
git add src/onecode_skill_sanitizer/cli.py src/onecode_skill_sanitizer/task_pack_v3.py src/onecode_skill_sanitizer/router_eval_v3.py tests/test_cli_boundaries.py tests/test_task_pack_v3_cli.py
git commit -m "test: freeze router compatibility before v3"
```

---

### Task 2: Add Reviewed Runtime Routing Examples

**Files:**
- Create: `catalog/routing-examples.json`
- Create: `tests/test_skill_candidates.py`
- Create: `src/onecode_skill_sanitizer/skill_candidates.py`

- [ ] **Step 1: Add the failing example-loader tests**

Create `tests/test_skill_candidates.py`:

```python
from __future__ import annotations

import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from onecode_skill_sanitizer.skill_candidates import (
    HIGH_FREQUENCY_ENTRY_NAMES,
    HIGH_FREQUENCY_SKILL_NAMES,
    RoutingExampleError,
    load_routing_examples,
)


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "catalog/routing-examples.json"


class SkillCandidateTest(unittest.TestCase):
    def test_runtime_examples_are_reviewed_and_limited_to_the_fixed_cohort(self):
        examples = load_routing_examples(EXAMPLES)
        classes = Counter(example["example_class"] for example in examples)

        self.assertEqual(HIGH_FREQUENCY_ENTRY_NAMES[0], "safe-agent-router")
        self.assertEqual(len(HIGH_FREQUENCY_ENTRY_NAMES), 8)
        self.assertEqual(len(HIGH_FREQUENCY_SKILL_NAMES), 7)
        self.assertGreaterEqual(len(examples), 35)
        self.assertGreaterEqual(classes["positive"], 21)
        self.assertGreaterEqual(classes["near_miss"], 7)
        self.assertEqual(
            {name for example in examples for name in example["required_skills"]},
            set(HIGH_FREQUENCY_SKILL_NAMES),
        )
        self.assertTrue(all(example["review"]["status"] == "approved" for example in examples))
        self.assertTrue(all(example["review"]["generated_from_router"] is False for example in examples))

    def test_loader_rejects_unreviewed_out_of_cohort_and_overlapping_labels(self):
        payload = json.loads(EXAMPLES.read_text(encoding="utf-8"))
        mutations = (
            lambda item: item["review"].update(status="draft"),
            lambda item: item.update(required_skills=["execution-publish-check"]),
            lambda item: item.update(forbidden_skills=item["required_skills"]),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate), tempfile.TemporaryDirectory() as temp_dir:
                changed = json.loads(json.dumps(payload))
                mutate(changed["examples"][0])
                path = Path(temp_dir) / "routing-examples.json"
                path.write_text(json.dumps(changed), encoding="utf-8")
                with self.assertRaises(RoutingExampleError):
                    load_routing_examples(path)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run RED**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_skill_candidates -v
```

Expected: FAIL because the loader, constants, and runtime example file do not exist.

- [ ] **Step 3: Create the reviewed runtime fixture**

Create `catalog/routing-examples.json` with this strict top-level shape:

```json
{
  "schema_version": 1,
  "scope": {
    "entry_names": [
      "safe-agent-router",
      "codebase-explore-map",
      "code-review-risk",
      "code-test-regression",
      "execution-browser-check",
      "research-source-check",
      "design-ui-review",
      "security-supply-chain-review"
    ],
    "candidate_names": [
      "codebase-explore-map",
      "code-review-risk",
      "code-test-regression",
      "execution-browser-check",
      "research-source-check",
      "design-ui-review",
      "security-supply-chain-review"
    ]
  },
  "examples": []
}
```

Populate `examples` with these 35 approved records. Every record has exactly `id`, `query`, `expected_need`, `required_skills`, `forbidden_skills`, `intent_labels`, `capability_labels`, `example_class`, and `review`. Use `{"status":"approved","reviewed_at":"2026-07-15","reviewer_role":"operator_review","source_classification":"local_curated","generated_from_router":false}` for `review` on every record.

| ID | Class | Query | Need | Required | Forbidden | Capability labels |
| --- | --- | --- | --- | --- | --- | --- |
| rt-explore-01 | positive | Map this unfamiliar repository before we change the auth flow. | single | codebase-explore-map | code-review-risk | code.explore |
| rt-explore-02 | positive | 先梳理这个陌生代码库的入口、模块和测试命令。 | single | codebase-explore-map | code-review-risk | code.explore |
| rt-explore-03 | positive | Where does request validation live and what consumes it? | single | codebase-explore-map | code-review-risk | code.explore |
| rt-review-01 | positive | Review this patch for bugs and missing edge cases. | single | code-review-risk | code-test-regression | code.review |
| rt-review-02 | positive | 审查这个 PR 是否有回归风险，不要直接改代码。 | single | code-review-risk | code-test-regression | code.review |
| rt-review-03 | positive | Find correctness problems in the current diff. | single | code-review-risk | codebase-explore-map | code.review |
| rt-test-01 | positive | Add a regression test that fails on the old parser bug. | single | code-test-regression | code-review-risk | code.test |
| rt-test-02 | positive | 为这次修复补一个能证明旧行为失败的回归测试。 | single | code-test-regression | code-review-risk | code.test |
| rt-test-03 | positive | Choose the smallest reliable test boundary for this defect. | single | code-test-regression | code-review-risk | code.test |
| rt-browser-01 | positive | Open the page in a real browser and verify the checkout flow. | single | execution-browser-check | design-ui-review | execution.browser_check |
| rt-browser-02 | positive | 用浏览器跑一遍表单并截图记录失败状态。 | single | execution-browser-check | design-ui-review | execution.browser_check |
| rt-browser-03 | positive | Smoke test the visible route, URL, and DOM state. | single | execution-browser-check | design-ui-review | execution.browser_check |
| rt-research-01 | positive | Verify these claims against current primary sources with citations. | single | research-source-check | codebase-explore-map | research.source |
| rt-research-02 | positive | 全网查证这组事实，优先官方和一手资料。 | single | research-source-check | codebase-explore-map | research.source |
| rt-research-03 | positive | Check whether this statistic is still current and cite the source. | single | research-source-check | security-supply-chain-review | research.source |
| rt-design-01 | positive | Review this dashboard's hierarchy, spacing, states, and responsive layout. | single | design-ui-review | execution-browser-check | design.ui_review |
| rt-design-02 | positive | 优化现有后台页面的视觉一致性和可访问性。 | single | design-ui-review | execution-browser-check | design.ui_review |
| rt-design-03 | positive | Critique the UI composition without running a browser flow. | single | design-ui-review | execution-browser-check | design.ui_review |
| rt-supply-01 | positive | Audit this npm package's provenance and install scripts before adoption. | single | security-supply-chain-review | code-review-risk | security.supply_chain |
| rt-supply-02 | positive | 引入这个社区 Skill 前检查来源、许可证和权限风险。 | single | security-supply-chain-review | research-source-check | security.supply_chain |
| rt-supply-03 | positive | Review the plugin maintainer and update-chain risk. | single | security-supply-chain-review | code-review-risk | security.supply_chain |
| rt-near-01 | near_miss | The repository is already mapped; review only the supplied diff for defects. | single | code-review-risk | codebase-explore-map | code.review |
| rt-near-02 | near_miss | Do not review the whole patch; only add the failing regression case. | single | code-test-regression | code-review-risk | code.test |
| rt-near-03 | near_miss | Do not critique visual design; just run the existing UI flow in a browser. | single | execution-browser-check | design-ui-review | execution.browser_check |
| rt-near-04 | near_miss | 不要打开浏览器，只评审间距、层级和响应式布局。 | single | design-ui-review | execution-browser-check | design.ui_review |
| rt-near-05 | near_miss | Search the local repository for the owner; no web research or citations. | single | codebase-explore-map | research-source-check | code.explore |
| rt-near-06 | near_miss | Verify the public claim, not the package's install-chain security. | single | research-source-check | security-supply-chain-review | research.source |
| rt-near-07 | near_miss | Audit package provenance only; this is not a general code review. | single | security-supply-chain-review | code-review-risk | security.supply_chain |
| rt-none-01 | explanation_only | Explain what code-review-risk is; do not invoke it. | none | none | code-review-risk | none |
| rt-none-02 | negation | 不需要 Skill，只告诉我当前目录名。 | none | none | all seven candidates | none |
| rt-compose-01 | composition | Map the unfamiliar repo, then review the auth diff. | composite | codebase-explore-map, code-review-risk | none | code.explore, code.review |
| rt-compose-02 | composition | Review the patch and add regression coverage for confirmed defects. | composite | code-review-risk, code-test-regression | none | code.review, code.test |
| rt-compose-03 | composition | Polish the UI, then verify the result in a browser at mobile and desktop sizes. | composite | design-ui-review, execution-browser-check | none | design.ui_review, execution.browser_check |
| rt-compose-04 | composition | Research the community package and audit its provenance before we adopt it. | composite | research-source-check, security-supply-chain-review | none | research.source, security.supply_chain |
| rt-compose-05 | composition | 先梳理陌生代码库，再补回归测试，最后浏览器验证页面。 | composite | codebase-explore-map, code-test-regression, execution-browser-check | none | code.explore, code.test, execution.browser_check |

For each row, use the listed capabilities as both `intent_labels` and `capability_labels`; use an empty array where the table says `none`, and expand `all seven candidates` to `HIGH_FREQUENCY_SKILL_NAMES` in file order.

- [ ] **Step 4: Implement strict loading**

Create `src/onecode_skill_sanitizer/skill_candidates.py` with the constants and a loader that checks exact keys, unique IDs and queries, approved review metadata, enum values, non-overlapping required/forbidden sets, and cohort membership:

```python
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any


HIGH_FREQUENCY_ENTRY_NAMES = (
    "safe-agent-router",
    "codebase-explore-map",
    "code-review-risk",
    "code-test-regression",
    "execution-browser-check",
    "research-source-check",
    "design-ui-review",
    "security-supply-chain-review",
)
HIGH_FREQUENCY_SKILL_NAMES = HIGH_FREQUENCY_ENTRY_NAMES[1:]
EXAMPLE_CLASSES = {"positive", "near_miss", "negation", "explanation_only", "composition"}
NEED_DECISIONS = {"none", "single", "composite", "clarify"}
EXAMPLE_KEYS = {
    "id", "query", "expected_need", "required_skills", "forbidden_skills",
    "intent_labels", "capability_labels", "example_class", "review",
}


class RoutingExampleError(ValueError):
    pass


def load_routing_examples(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "scope", "examples"}:
        raise RoutingExampleError("routing examples must use the strict top-level contract")
    if payload["schema_version"] != 1:
        raise RoutingExampleError("routing examples schema_version must be 1")
    scope = payload["scope"]
    if scope != {
        "entry_names": list(HIGH_FREQUENCY_ENTRY_NAMES),
        "candidate_names": list(HIGH_FREQUENCY_SKILL_NAMES),
    }:
        raise RoutingExampleError("routing example scope does not match the fixed cohort")
    examples = payload["examples"]
    if not isinstance(examples, list):
        raise RoutingExampleError("routing examples must be a list")
    seen_ids: set[str] = set()
    seen_queries: set[str] = set()
    for index, item in enumerate(examples):
        if not isinstance(item, dict) or set(item) != EXAMPLE_KEYS:
            raise RoutingExampleError(f"example[{index}] has an invalid field set")
        if not isinstance(item["id"], str) or not item["id"] or item["id"] in seen_ids:
            raise RoutingExampleError(f"example[{index}] id must be unique")
        query = item["query"]
        normalized_query = " ".join(query.casefold().split()) if isinstance(query, str) else ""
        if not normalized_query or normalized_query in seen_queries:
            raise RoutingExampleError(f"example[{index}] query must be unique")
        if item["expected_need"] not in NEED_DECISIONS or item["example_class"] not in EXAMPLE_CLASSES:
            raise RoutingExampleError(f"example[{index}] enum value is invalid")
        required = _strict_string_list(item["required_skills"], f"example[{index}].required_skills")
        forbidden = _strict_string_list(item["forbidden_skills"], f"example[{index}].forbidden_skills")
        if not set(required + forbidden).issubset(HIGH_FREQUENCY_SKILL_NAMES):
            raise RoutingExampleError(f"example[{index}] references an out-of-cohort skill")
        if set(required) & set(forbidden):
            raise RoutingExampleError(f"example[{index}] labels overlap")
        _strict_string_list(item["intent_labels"], f"example[{index}].intent_labels")
        _strict_string_list(item["capability_labels"], f"example[{index}].capability_labels")
        review = item["review"]
        if not isinstance(review, dict) or review.get("status") != "approved":
            raise RoutingExampleError(f"example[{index}] is not approved")
        if review.get("generated_from_router") is not False:
            raise RoutingExampleError(f"example[{index}] must not be generated from router output")
        if not all(isinstance(review.get(key), str) and review[key] for key in (
            "reviewed_at", "reviewer_role", "source_classification"
        )):
            raise RoutingExampleError(f"example[{index}] review metadata is incomplete")
        seen_ids.add(item["id"])
        seen_queries.add(normalized_query)
    return examples


def _strict_string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise RoutingExampleError(f"{field} must contain nonempty strings")
    if len(value) != len(set(value)):
        raise RoutingExampleError(f"{field} must not contain duplicates")
    return value
```

- [ ] **Step 5: Run GREEN and commit**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_skill_candidates -v
python3 -m json.tool catalog/routing-examples.json >/dev/null
```

Expected: PASS.

```bash
git add catalog/routing-examples.json src/onecode_skill_sanitizer/skill_candidates.py tests/test_skill_candidates.py
git commit -m "feat: add reviewed high-frequency routing examples"
```

---

### Task 3: Implement The Current-Intent Need Gate

**Files:**
- Create: `tests/test_need_gate.py`
- Create: `src/onecode_skill_sanitizer/need_gate.py`
- Reuse: `src/onecode_skill_sanitizer/intent.py`

- [ ] **Step 1: Write failing need-decision tests**

Create `tests/test_need_gate.py`:

```python
from __future__ import annotations

import unittest

from onecode_skill_sanitizer.intent import normalize_task
from onecode_skill_sanitizer.need_gate import decide_skill_need


class NeedGateTest(unittest.TestCase):
    def test_none_for_greeting_inventory_explanation_and_negation(self):
        cases = (
            ("hi", "no_specialized_need"),
            ("list the seven high-frequency skills; do not invoke them", "inventory_only"),
            ("解释 code-review-risk 是什么，不要使用它", "explanation_only"),
            ("do not use any skill; just answer yes", "all_candidates_excluded"),
        )
        for task, reason in cases:
            with self.subTest(task=task):
                decision = decide_skill_need(normalize_task(task))
                self.assertEqual(decision["decision"], "none")
                self.assertIn(reason, decision["reason_codes"])
                self.assertEqual(decision["required_capabilities"], [])

    def test_single_and_composite_capabilities_are_distinct(self):
        single = decide_skill_need(normalize_task("review this patch for regressions"))
        composite = decide_skill_need(
            normalize_task("polish the dashboard, then verify it in a real browser")
        )

        self.assertEqual(single["decision"], "single")
        self.assertEqual(single["required_capabilities"], ["code.review"])
        self.assertEqual(composite["decision"], "composite")
        self.assertEqual(
            composite["required_capabilities"],
            ["design.ui_review", "execution.browser_check"],
        )

    def test_current_request_overrides_stale_history(self):
        normalized = normalize_task(
            "Earlier we planned browser testing. Current request: only review the patch; do not open a browser."
        )
        decision = decide_skill_need(normalized)

        self.assertEqual(decision["required_capabilities"], ["code.review"])
        self.assertIn("execution-browser-check", decision["excluded_skills"])

    def test_specialized_but_ambiguous_request_clarifies(self):
        for task in ("check the UI", "\u770b\u4e00\u4e0b\u8fd9\u4e2a\u53d8\u66f4", "review the package"):
            with self.subTest(task=task):
                decision = decide_skill_need(normalize_task(task))
                self.assertEqual(decision["decision"], "clarify")
                self.assertEqual(decision["reason_codes"], ["adjacent_capability_ambiguous"])

    def test_conflicting_explicit_skill_constraint_clarifies(self):
        decision = decide_skill_need(
            normalize_task("Use design-ui-review and do not use design-ui-review")
        )
        self.assertEqual(decision["decision"], "clarify")
        self.assertEqual(decision["reason_codes"], ["conflicting_explicit_constraint"])

    def test_missing_inputs_and_risk_derived_verification_are_structured(self):
        missing = decide_skill_need(
            normalize_task("Add regression coverage, but the behavior under test is unknown")
        )
        risky = decide_skill_need(normalize_task("Fix this shared parser bug"))

        self.assertEqual(missing["missing_inputs"], ["behavior_or_change_under_test"])
        self.assertEqual(risky["mandatory_capabilities"], ["code.test"])
        self.assertIn("code.test", risky["required_capabilities"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run RED**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_need_gate -v
```

Expected: FAIL because `need_gate.py` does not exist.

- [ ] **Step 3: Implement the deterministic gate**

Create `src/onecode_skill_sanitizer/need_gate.py`. Use normalized current text only for routing. Keep regexes narrow and auditable:

```python
from __future__ import annotations

import re
from typing import Any

from .intent import NormalizedTask
from .skill_candidates import HIGH_FREQUENCY_SKILL_NAMES


CAPABILITY_SKILL = {
    "code.explore": "codebase-explore-map",
    "code.review": "code-review-risk",
    "code.test": "code-test-regression",
    "execution.browser_check": "execution-browser-check",
    "research.source": "research-source-check",
    "design.ui_review": "design-ui-review",
    "security.supply_chain": "security-supply-chain-review",
}
CAPABILITY_PATTERNS = {
    "code.explore": re.compile(r"unfamiliar repo|map (?:the )?repo|repository map|repository orientation|source ownership|data flow|entry points?|where does|architecture|\u964c\u751f\u4ee3\u7801\u5e93|\u68b3\u7406.*(?:\u4ee3\u7801\u5e93|repo|\u5165\u53e3|\u6a21\u5757)|(?:\u4ee3\u7801\u5e93|repo).*(?:\u6620\u5c04|\u68b3\u7406)|\u8c03\u7528\u94fe", re.I),
    "code.review": re.compile(r"review (?:this |the )?(?:diff|patch|pr|code)|code review|pr.*review|risk[- ]review|code delta|find (?:bugs|defects)|check this change.*(?:concurrency|cleanup|regression)|\u5ba1\u67e5.*(?:diff|PR|\u8865\u4e01|\u4ee3\u7801)|\u8bc4\u5ba1.*(?:\u7f3a\u9677|\u4ee3\u7801|\u8865\u4e01|\u53d8\u66f4)|\u4ee3\u7801\u53d8\u66f4.*(?:\u95ee\u9898|\u98ce\u9669)|\u56de\u5f52\u98ce\u9669", re.I),
    "code.test": re.compile(r"regression test|test coverage|failing test|test boundary|contract test|old behavior.*fail|red[- ]green|\u56de\u5f52\u6d4b\u8bd5|\u8865.*\u6d4b\u8bd5|\u5931\u8d25\u7528\u4f8b", re.I),
    "execution.browser_check": re.compile(r"real browser|browser (?:check|flow|test)|playwright|screenshot|DOM state|canvas|console error|\u6d4f\u89c8\u5668.*(?:\u9a8c\u8bc1|\u68c0\u67e5|\u8dd1|\u622a\u56fe|\u590d\u73b0)|\u6253\u5f00.*\u9875\u9762", re.I),
    "research.source": re.compile(r"primary sources?|official (?:sources?|documentation|records?)|citations?|fact[- ]check|verify (?:the |these )?claims?|research (?:the )?(?:claims|sources|package|community skill)|standards?.*evidence|web research|\u5168\u7f51\u641c\u7d22|\u4e00\u624b\u8d44\u6599|\u5b98\u65b9\u8d44\u6599|\u6743\u5a01\u6765\u6e90|\u67e5\u8bc1|\u6838\u5b9e|\u5f15\u7528|\u4e8b\u5b9e\u6838\u67e5", re.I),
    "design.ui_review": re.compile(r"polish (?:the )?UI|review (?:the )?(?:UI|dashboard|layout)|visual hierarchy|spacing|responsive layout|accessibility|\u4f18\u5316.*(?:UI|\u9875\u9762|\u754c\u9762)|\u89c6\u89c9\u4e00\u81f4|\u54cd\u5e94\u5f0f\u5e03\u5c40|\u53ef\u8bbf\u95ee\u6027", re.I),
    "security.supply_chain": re.compile(r"supply[- ]chain|package (?:provenance|trust|before adoption)|install scripts?|plugin maintainer|community skill|dependency (?:risk|provenance|trust)|connector.*permissions?|\u4f9b\u5e94\u94fe|\u5305.*(?:\u6765\u6e90|\u4fe1\u4efb)|\u793e\u533a Skill|\u63d2\u4ef6.*\u98ce\u9669|connector.*\u6743\u9650|\u8bb8\u53ef\u8bc1.*\u6743\u9650", re.I),
}
EXPLANATION_RE = re.compile(r"\b(?:explain|what is|describe)\b|\u89e3\u91ca|\u662f\u4ec0\u4e48|\u4ecb\u7ecd", re.I)
INVENTORY_RE = re.compile(r"\b(?:list|show)\b.*\bskills?\b|\u5217\u51fa.*Skill|\u6709\u54ea\u4e9b.*Skill", re.I)
NEGATION_PREFIX = r"(?:do not|don't|never|no need to|\u4e0d\u8981|\u522b|\u4e0d\u9700\u8981|\u65e0\u9700|\u5148\u4e0d)"
GENERIC_SKILL_EXCLUSION_RE = re.compile(
    rf"{NEGATION_PREFIX}\s+(?:use|invoke|\u4f7f\u7528|\u8c03\u7528)?\s*(?:any|all|\u4efb\u4f55|\u6240\u6709)?\s*skills?",
    re.I,
)
MISSING_INPUT_PATTERNS = {
    "target_page_or_flow": re.compile(
        r"(?:target|page|url|flow).*(?:missing|unknown)|\u6ca1\u6709.*(?:\u9875\u9762|URL|\u5730\u5740|\u6d41\u7a0b)|"
        r"(?:\u9875\u9762|URL|\u5730\u5740|\u6d41\u7a0b).*(?:\u7f3a\u5931|\u4e0d\u77e5\u9053)",
        re.I,
    ),
    "behavior_or_change_under_test": re.compile(
        r"behavior under test.*(?:missing|unknown)|(?:behavior|change).*(?:not known|unspecified)|"
        r"\u5f85\u6d4b.*(?:\u884c\u4e3a|\u53d8\u66f4).*(?:\u7f3a\u5931|\u4e0d\u660e)",
        re.I,
    ),
}
MANDATORY_TEST_RE = re.compile(
    r"\b(?:fix|implement|change)\b.*\b(?:bug|shared contract|parser)\b|"
    r"\u4fee\u590d.*(?:bug|\u5171\u4eab\u5951\u7ea6|\u89e3\u6790\u5668)",
    re.I,
)
NON_ACTION_BROWSER_RE = re.compile(r"screenshot (?:is )?attached|\u622a\u56fe(?:\u5df2)?\u9644", re.I)
AMBIGUOUS_SPECIALIZED_RE = re.compile(
    r"(?:check|review|\u770b\u770b|\u68c0\u67e5)(?: the| this)? ui[\s.!?\u3002\uff01\uff1f]*|"
    r"(?:check|review) (?:this |the )?(?:change|package)[\s.!?]*|"
    r"\u770b\u4e00\u4e0b\u8fd9\u4e2a\u53d8\u66f4|\u68c0\u67e5\u8fd9\u4e2a\u5305",
    re.I,
)


def decide_skill_need(normalized: NormalizedTask) -> dict[str, Any]:
    current = normalized.current.strip()
    folded = current.casefold()
    explicit = [name for name in HIGH_FREQUENCY_SKILL_NAMES if name.casefold() in folded]
    exact_excluded = [
        name for name in HIGH_FREQUENCY_SKILL_NAMES
        if re.search(rf"{NEGATION_PREFIX}[^.;\n\u3002\uff1b]{{0,24}}{re.escape(name)}", current, re.I)
    ]
    if GENERIC_SKILL_EXCLUSION_RE.search(current):
        excluded = list(HIGH_FREQUENCY_SKILL_NAMES)
    else:
        excluded = list(exact_excluded)
        for capability, skill in CAPABILITY_SKILL.items():
            if _capability_negated(current, capability) and skill not in excluded:
                excluded.append(skill)
    capabilities = [
        capability for capability, pattern in CAPABILITY_PATTERNS.items()
        if pattern.search(current)
        and not _capability_negated(current, capability)
        and CAPABILITY_SKILL[capability] not in excluded
    ]
    if NON_ACTION_BROWSER_RE.search(current) and "execution.browser_check" in capabilities:
        capabilities.remove("execution.browser_check")
    reason_codes: list[str] = []
    explanation_only = bool(EXPLANATION_RE.search(current) and explicit and not capabilities)
    inventory_only = bool(INVENTORY_RE.search(current) and not capabilities)
    if not current or current.casefold() in {"hi", "hello", "thanks", "thank you", "\u4f60\u597d", "\u8c22\u8c22"}:
        reason_codes.append("no_specialized_need")
    elif inventory_only:
        reason_codes.append("inventory_only")
    elif explanation_only:
        reason_codes.append("explanation_only")
    elif not capabilities and set(excluded) == set(HIGH_FREQUENCY_SKILL_NAMES):
        reason_codes.append("all_candidates_excluded")
    elif explicit and set(explicit).issubset(excluded):
        return _decision(
            "clarify", [], explicit, excluded, ["conflicting_explicit_constraint"],
            False, False, [], [], [],
        )
    elif not capabilities and AMBIGUOUS_SPECIALIZED_RE.search(current):
        return _decision(
            "clarify", [], explicit, excluded, ["adjacent_capability_ambiguous"],
            False, False, [], [], [],
        )
    elif not capabilities and not explicit:
        reason_codes.append("no_specialized_need")
    if reason_codes:
        return _decision(
            "none", [], explicit, excluded, reason_codes,
            explanation_only, inventory_only, [], [], [],
        )
    for name in explicit:
        capability = next((key for key, value in CAPABILITY_SKILL.items() if value == name), "")
        if capability and name not in excluded and capability not in capabilities:
            capabilities.append(capability)
    missing_inputs = [
        field for field, pattern in MISSING_INPUT_PATTERNS.items() if pattern.search(current)
    ]
    mandatory_capabilities = ["code.test"] if MANDATORY_TEST_RE.search(current) else []
    for capability in mandatory_capabilities:
        if capability not in capabilities:
            capabilities.append(capability)
    decision = "single" if len(capabilities) == 1 else "composite"
    return _decision(
        decision, capabilities, explicit, excluded, ["specialized_need_detected"],
        False, False, missing_inputs, mandatory_capabilities, [],
    )


def _capability_negated(text: str, capability: str) -> bool:
    skill = CAPABILITY_SKILL[capability]
    aliases = {
        "code.explore": r"map|explore|\u68b3\u7406|\u6620\u5c04",
        "code.review": r"review|audit|\u5ba1\u67e5|\u8bc4\u5ba1",
        "code.test": r"test|\u6d4b\u8bd5",
        "execution.browser_check": r"browser|playwright|\u6d4f\u89c8\u5668",
        "research.source": r"research|citations?|claims?|facts?|\u641c\u7d22|\u5f15\u7528|\u67e5\u8bc1|\u6838\u5b9e|\u4e3b\u5f20|\u4e8b\u5b9e",
        "design.ui_review": r"design|ui review|\u8bbe\u8ba1|\u89c6\u89c9\u8bc4\u5ba1",
        "security.supply_chain": r"supply[- ]chain|provenance|package scripts?|install scripts?|\u4f9b\u5e94\u94fe|\u6765\u6e90\u5ba1\u8ba1|\u5305\u811a\u672c",
    }[capability]
    return bool(re.search(rf"{NEGATION_PREFIX}[^.;\n\u3002\uff1b]{{0,18}}(?:{aliases}|{re.escape(skill)})", text, re.I))


def _decision(
    decision: str,
    capabilities: list[str],
    explicit: list[str],
    excluded: list[str],
    reasons: list[str],
    explanation_only: bool,
    inventory_only: bool,
    missing_inputs: list[str],
    mandatory_capabilities: list[str],
    policy_block_reasons: list[str],
) -> dict[str, Any]:
    return {
        "decision": decision,
        "specialized_need": decision != "none",
        "required_capabilities": capabilities,
        "explicit_skills": explicit,
        "excluded_skills": excluded,
        "explanation_only": explanation_only,
        "inventory_only": inventory_only,
        "missing_inputs": missing_inputs,
        "mandatory_capabilities": mandatory_capabilities,
        "policy_block_reasons": policy_block_reasons,
        "reason_codes": reasons,
    }
```

- [ ] **Step 4: Run GREEN and broader intent regression**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_need_gate tests.test_intent -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/onecode_skill_sanitizer/need_gate.py tests/test_need_gate.py
git commit -m "feat: add current-intent skill need gate"
```

---

### Task 4: Recall Trusted Cohort Candidates With Auditable Evidence

**Files:**
- Modify: `tests/test_skill_candidates.py`
- Modify: `src/onecode_skill_sanitizer/skill_candidates.py`
- Read only: the seven cohort `SKILL.md` and `skill.json` files

- [ ] **Step 1: Add failing profile and retrieval tests**

Append to `tests/test_skill_candidates.py`:

```python
from onecode_skill_sanitizer.intent import normalize_task
from onecode_skill_sanitizer.need_gate import decide_skill_need
from onecode_skill_sanitizer.skill_candidates import load_cohort_profiles, retrieve_skill_candidates


    def test_profiles_come_only_from_trusted_catalog_sources(self):
        profiles = load_cohort_profiles(ROOT / "catalog")

        self.assertEqual(tuple(profiles), HIGH_FREQUENCY_SKILL_NAMES)
        self.assertTrue(all(profile["status"] == "trusted" for profile in profiles.values()))
        self.assertTrue(all(profile["description"].startswith("Use when") for profile in profiles.values()))
        self.assertTrue(all(profile["capabilities"] for profile in profiles.values()))

    def test_retrieval_returns_top_three_with_decomposed_evidence(self):
        task = normalize_task("review this patch and add a regression test")
        need = decide_skill_need(task)
        candidates = retrieve_skill_candidates(
            task,
            need,
            load_cohort_profiles(ROOT / "catalog"),
            load_routing_examples(EXAMPLES),
            top_k=3,
        )

        self.assertEqual([item["skill"] for item in candidates[:2]], ["code-review-risk", "code-test-regression"])
        self.assertTrue(all(0 <= item["deterministic_score"] <= 1 for item in candidates))
        self.assertTrue(all(item["positive_evidence"] for item in candidates[:2]))
        self.assertIn("code.review", candidates[0]["matched_capabilities"])

    def test_near_miss_and_explicit_exclusion_cannot_win(self):
        task = normalize_task("Do not critique design; run the existing UI flow in a browser")
        need = decide_skill_need(task)
        candidates = retrieve_skill_candidates(
            task,
            need,
            load_cohort_profiles(ROOT / "catalog"),
            load_routing_examples(EXAMPLES),
            top_k=3,
        )
        by_name = {item["skill"]: item for item in candidates}

        self.assertEqual(candidates[0]["skill"], "execution-browser-check")
        self.assertTrue(by_name["design-ui-review"]["excluded"])
        self.assertIn("explicit_exclusion", by_name["design-ui-review"]["reason_codes"])
```

- [ ] **Step 2: Run RED**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_skill_candidates -v
```

Expected: FAIL because profile loading and candidate retrieval are missing.

- [ ] **Step 3: Implement profile loading and deterministic scoring**

Add these public records and functions to `skill_candidates.py`:

```python
from dataclasses import asdict, dataclass
import math
import re

from .intent import NormalizedTask
from .task_packs import extract_frontmatter_description


@dataclass(frozen=True)
class SkillCandidate:
    skill: str
    registry_path: str
    status: str
    description: str
    deterministic_score: float
    semantic_score: float | None
    final_score: float
    matched_intents: tuple[str, ...]
    matched_capabilities: tuple[str, ...]
    matched_examples: tuple[str, ...]
    positive_evidence: tuple[dict[str, Any], ...]
    penalties: tuple[dict[str, Any], ...]
    exclusions: tuple[str, ...]
    excluded: bool
    selected: bool
    reason_codes: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


def load_cohort_profiles(registry_dir: Path) -> dict[str, dict[str, Any]]:
    index = json.loads((registry_dir / "index.json").read_text(encoding="utf-8"))
    indexed = {item["name"]: item for item in index["skills"] if isinstance(item, dict)}
    profiles: dict[str, dict[str, Any]] = {}
    for name in HIGH_FREQUENCY_SKILL_NAMES:
        item = indexed.get(name)
        if not isinstance(item, dict) or item.get("status") != "trusted":
            raise RoutingExampleError(f"cohort skill is not trusted: {name}")
        skill_dir = registry_dir / item["registry_path"]
        manifest = json.loads((skill_dir / "skill.json").read_text(encoding="utf-8"))
        skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        contract = manifest.get("contract") if isinstance(manifest.get("contract"), dict) else {}
        profiles[name] = {
            "name": name,
            "status": "trusted",
            "registry_path": item["registry_path"],
            "description": extract_frontmatter_description(skill_text),
            "task_intent": manifest["taxonomy"]["task_intent"],
            "subcategory": manifest["taxonomy"]["subcategory"],
            "capabilities": list(contract.get("capability_vector", [])),
            "requires_context": list(contract.get("requires_context", [])),
            "produces_artifacts": list(contract.get("produces_artifacts", [])),
            "produces_evidence": list(contract.get("produces_evidence", [])),
            "requires_after": list(contract.get("requires_after", [])),
            "conflicts_with": list(contract.get("conflicts_with", [])),
            "excludes": list(contract.get("excludes", [])),
        }
    return profiles


def retrieve_skill_candidates(
    normalized: NormalizedTask,
    need: dict[str, Any],
    profiles: dict[str, dict[str, Any]],
    examples: list[dict[str, Any]],
    *,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 7:
        raise ValueError("top_k must be an integer from 1 to 7")
    query_tokens = _tokens(normalized.current)
    records: list[dict[str, Any]] = []
    for name in HIGH_FREQUENCY_SKILL_NAMES:
        profile = profiles[name]
        matched_capabilities = sorted(set(profile["capabilities"]) & set(need["required_capabilities"]))
        explicit = name in need["explicit_skills"]
        excluded = name in need["excluded_skills"]
        description_tokens = _tokens(f"{profile['description']} {profile['task_intent']}")
        description_similarity = _jaccard(query_tokens, description_tokens)
        positive_examples = _matching_examples(query_tokens, examples, name, "required_skills")
        negative_examples = _matching_examples(query_tokens, examples, name, "forbidden_skills")
        positive_similarity = max((score for score, _ in positive_examples), default=0.0)
        negative_similarity = max((score for score, _ in negative_examples), default=0.0)
        evidence = []
        if matched_capabilities:
            evidence.append({"type": "capability", "value": matched_capabilities, "weight": 0.55})
        if explicit:
            evidence.append({"type": "explicit_skill", "value": name, "weight": 1.0})
        if description_similarity:
            evidence.append({"type": "description", "value": round(description_similarity, 6), "weight": 0.15})
        if positive_similarity:
            evidence.append({"type": "reviewed_example", "value": positive_examples[0][1], "weight": 0.30})
        penalties = []
        if negative_similarity:
            penalties.append({"type": "near_miss", "value": negative_examples[0][1], "weight": -0.65})
        score = 1.0 if explicit else min(
            1.0,
            0.55 * bool(matched_capabilities) + 0.15 * description_similarity + 0.30 * positive_similarity,
        )
        score = max(0.0, score - 0.65 * negative_similarity)
        reasons = []
        exclusions = []
        if excluded:
            score = 0.0
            exclusions.append("explicit_exclusion")
            reasons.append("explicit_exclusion")
        if not math.isfinite(score):
            raise ValueError("deterministic score must be finite")
        records.append(
            SkillCandidate(
                skill=name,
                registry_path=profile["registry_path"],
                status="trusted",
                description=profile["description"],
                deterministic_score=round(score, 6),
                semantic_score=None,
                final_score=round(score, 6),
                matched_intents=tuple(need["required_capabilities"]),
                matched_capabilities=tuple(matched_capabilities),
                matched_examples=tuple(item[1] for item in positive_examples[:3]),
                positive_evidence=tuple(evidence),
                penalties=tuple(penalties),
                exclusions=tuple(exclusions),
                excluded=excluded,
                selected=False,
                reason_codes=tuple(reasons or (["deterministic_candidate"] if score > 0 else ["no_positive_evidence"])),
            ).to_json()
        )
    records.sort(key=lambda item: (-item["deterministic_score"], item["skill"]))
    admitted_names = {item["skill"] for item in records[:top_k]}
    admitted_names.update(
        item["skill"]
        for item in records
        if item["matched_capabilities"]
        or item["skill"] in need["explicit_skills"]
        or item["skill"] in need["excluded_skills"]
    )
    admitted = [item for item in records if item["skill"] in admitted_names]
    return admitted


def _tokens(text: str) -> set[str]:
    latin = re.findall(r"[a-z0-9][a-z0-9_-]+", text.casefold())
    han = re.findall(r"[\u4e00-\u9fff]{2,}", text)
    han_bigrams = [token[index:index + 2] for token in han for index in range(len(token) - 1)]
    return set(latin + han_bigrams)


def _jaccard(left: set[str], right: set[str]) -> float:
    return len(left & right) / len(left | right) if left or right else 0.0


def _matching_examples(
    query_tokens: set[str],
    examples: list[dict[str, Any]],
    skill: str,
    label: str,
) -> list[tuple[float, str]]:
    matches = [(_jaccard(query_tokens, _tokens(item["query"])), item["id"]) for item in examples if skill in item[label]]
    return sorted((item for item in matches if item[0] > 0), key=lambda item: (-item[0], item[1]))
```

- [ ] **Step 4: Run GREEN**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_skill_candidates tests.test_need_gate -v
```

Expected: PASS with only the seven trusted candidates represented.

- [ ] **Step 5: Commit**

```bash
git add src/onecode_skill_sanitizer/skill_candidates.py tests/test_skill_candidates.py
git commit -m "feat: recall trusted high-frequency skill candidates"
```

---

### Task 5: Add The Candidate-Bounded Semantic Provider Boundary

**Files:**
- Create: `schemas/semantic-rerank-response.schema.json`
- Create: `tests/test_semantic_provider.py`
- Create: `src/onecode_skill_sanitizer/semantic_provider.py`

- [ ] **Step 1: Write failing provider tests**

Create `tests/test_semantic_provider.py` with a callable fixture provider and table-driven invalid outputs:

```python
from __future__ import annotations

import math
import unittest

from onecode_skill_sanitizer.semantic_provider import rerank_candidates


class FakeProvider:
    name = "fake"
    model_or_adapter = "fixture-v1"

    def __init__(self, response):
        self.response = response
        self.requests = []

    def rerank(self, request):
        self.requests.append(request)
        if isinstance(self.response, BaseException):
            raise self.response
        return self.response


def candidates():
    return [
        {"skill": "design-ui-review", "deterministic_score": 0.7, "semantic_score": None, "final_score": 0.7},
        {"skill": "execution-browser-check", "deterministic_score": 0.6, "semantic_score": None, "final_score": 0.6},
    ]


class SemanticProviderTest(unittest.TestCase):
    def test_shadow_records_scores_without_changing_final_order(self):
        provider = FakeProvider({
            "status": "ok",
            "scores": [
                {"skill": "design-ui-review", "score": 0.1, "confidence": 0.8},
                {"skill": "execution-browser-check", "score": 0.9, "confidence": 0.8},
            ],
        })
        routed, record = rerank_candidates("review the UI", {}, candidates(), provider, mode="shadow")

        self.assertEqual([item["skill"] for item in routed], ["design-ui-review", "execution-browser-check"])
        self.assertEqual([item["semantic_score"] for item in routed], [0.1, 0.9])
        self.assertEqual([item["final_score"] for item in routed], [0.7, 0.6])
        self.assertEqual(record["response_status"], "accepted_shadow")
        self.assertRegex(record["candidate_scope_hash"], r"^sha256:[0-9a-f]{64}$")

    def test_invalid_response_rejects_every_semantic_score(self):
        invalid = (
            TimeoutError("timed out"),
            {"status": "ok", "scores": [{"skill": "unknown", "score": 0.5, "confidence": 0.5}]},
            {"status": "ok", "scores": [
                {"skill": "design-ui-review", "score": 0.5, "confidence": 0.5},
                {"skill": "design-ui-review", "score": 0.6, "confidence": 0.5},
            ]},
            {"status": "ok", "scores": [{"skill": "design-ui-review", "score": 0.5, "confidence": 0.5}]},
            {"status": "ok", "scores": [
                {"skill": "design-ui-review", "score": math.nan, "confidence": 0.5},
                {"skill": "execution-browser-check", "score": 0.5, "confidence": 0.5},
            ]},
            {"status": "ok", "scores": [
                {"skill": "design-ui-review", "score": 1.2, "confidence": 0.5},
                {"skill": "execution-browser-check", "score": 0.5, "confidence": 0.5},
            ]},
        )
        for response in invalid:
            with self.subTest(response=response):
                routed, record = rerank_candidates(
                    "review the UI", {}, candidates(), FakeProvider(response), mode="shadow"
                )
                self.assertTrue(all(item["semantic_score"] is None for item in routed))
                self.assertEqual([item["final_score"] for item in routed], [0.7, 0.6])
                self.assertNotEqual(record["fallback_reason"], "none")
                self.assertTrue(record["validation_reason_codes"])

    def test_low_confidence_influence_retains_deterministic_order(self):
        provider = FakeProvider({
            "status": "ok",
            "scores": [
                {"skill": "design-ui-review", "score": 0.1, "confidence": 0.4},
                {"skill": "execution-browser-check", "score": 0.9, "confidence": 0.4},
            ],
        })
        routed, record = rerank_candidates(
            "review the UI", {}, candidates(), provider, mode="influence"
        )

        self.assertEqual([item["skill"] for item in routed], ["design-ui-review", "execution-browser-check"])
        self.assertEqual([item["final_score"] for item in routed], [0.7, 0.6])
        self.assertTrue(all(item["semantic_score"] is None for item in routed))
        self.assertEqual(record["fallback_reason"], "low_semantic_confidence")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run RED**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_semantic_provider -v
```

Expected: FAIL because the provider boundary does not exist.

- [ ] **Step 3: Add the strict response schema**

Create `schemas/semantic-rerank-response.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://onecode.local/schemas/semantic-rerank-response.schema.json",
  "type": "object",
  "required": ["status", "scores"],
  "properties": {
    "status": {"const": "ok"},
    "scores": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["skill", "score", "confidence"],
        "properties": {
          "skill": {"type": "string", "minLength": 1},
          "score": {"type": "number", "minimum": 0, "maximum": 1},
          "confidence": {"type": "number", "minimum": 0, "maximum": 1}
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": false
}
```

- [ ] **Step 4: Implement protocol, redaction, scope binding, and fallback**

Create `src/onecode_skill_sanitizer/semantic_provider.py`:

```python
from __future__ import annotations

import math
from typing import Any, Protocol

from .compatibility import build_canonical_content_hash, redact_route_identity_text


class SemanticProvider(Protocol):
    name: str
    model_or_adapter: str

    def rerank(self, request: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


def rerank_candidates(
    current_intent: str,
    constraints: dict[str, Any],
    candidates: list[dict[str, Any]],
    provider: SemanticProvider | None,
    *,
    mode: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    names = [item["skill"] for item in candidates]
    request = {
        "current_intent": redact_route_identity_text(current_intent),
        "constraints": constraints,
        "candidates": [
            {
                "skill": item["skill"],
                "description": item.get("description", ""),
                "deterministic_score": item["deterministic_score"],
                "matched_capabilities": item.get("matched_capabilities", []),
            }
            for item in candidates
        ],
    }
    scope_hash = build_canonical_content_hash(request["candidates"])
    if provider is None or mode == "none" or len(candidates) < 2:
        return candidates, _record(
            "none", "none", "none", "not_requested", scope_hash, [], "not_requested"
        )
    requested = provider.name
    try:
        response = provider.rerank(request)
    except Exception as exc:
        return _clear_semantic(candidates), _record(
            requested, "none", provider.model_or_adapter, "provider_failure", scope_hash,
            [f"provider_exception:{type(exc).__name__}"],
        )
    reasons = _validate_response(response, names)
    if reasons:
        return _clear_semantic(candidates), _record(
            requested, "none", provider.model_or_adapter, "invalid_provider_response", scope_hash, reasons,
        )
    if mode == "influence" and min(item["confidence"] for item in response["scores"]) < 0.60:
        return _clear_semantic(candidates), _record(
            requested, "none", provider.model_or_adapter,
            "low_semantic_confidence", scope_hash, ["low_semantic_confidence"],
        )
    semantic = {item["skill"]: item["score"] for item in response["scores"]}
    reranked = []
    for item in candidates:
        updated = dict(item)
        updated["semantic_score"] = semantic[item["skill"]]
        if mode == "influence":
            updated["final_score"] = round(0.75 * item["deterministic_score"] + 0.25 * semantic[item["skill"]], 6)
        reranked.append(updated)
    if mode == "influence":
        reranked.sort(key=lambda item: (-item["final_score"], -item["deterministic_score"], item["skill"]))
    status = "accepted_shadow" if mode == "shadow" else "accepted_influence"
    return reranked, _record(requested, requested, provider.model_or_adapter, "none", scope_hash, [], status)


def _validate_response(response: Any, names: list[str]) -> list[str]:
    if not isinstance(response, dict) or set(response) != {"status", "scores"} or response.get("status") != "ok":
        return ["schema_mismatch"]
    scores = response.get("scores")
    if not isinstance(scores, list):
        return ["schema_mismatch"]
    response_names = [item.get("skill") for item in scores if isinstance(item, dict)]
    if len(response_names) != len(scores):
        return ["schema_mismatch"]
    if len(response_names) != len(set(response_names)):
        return ["duplicate_candidate"]
    if set(response_names) != set(names):
        return ["candidate_scope_mismatch"]
    for item in scores:
        if set(item) != {"skill", "score", "confidence"}:
            return ["schema_mismatch"]
        for field in ("score", "confidence"):
            value = item[field]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                return [f"invalid_{field}"]
            if not 0 <= value <= 1:
                return [f"out_of_range_{field}"]
    return []


def _clear_semantic(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleared = []
    for item in candidates:
        updated = dict(item)
        updated["semantic_score"] = None
        updated["final_score"] = updated["deterministic_score"]
        cleared.append(updated)
    return cleared


def _record(
    requested: str,
    used: str,
    adapter: str,
    fallback: str,
    scope_hash: str,
    reasons: list[str],
    status: str = "rejected_fallback",
) -> dict[str, Any]:
    return {
        "requested": requested,
        "used": used,
        "model_or_adapter": adapter,
        "fallback_reason": fallback,
        "candidate_scope_hash": scope_hash,
        "response_status": status,
        "validation_reason_codes": reasons,
    }
```

- [ ] **Step 5: Run GREEN and schema check**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_semantic_provider -v
python3 -m json.tool schemas/semantic-rerank-response.schema.json >/dev/null
```

Expected: PASS; every invalid semantic result falls back to deterministic scores for the entire candidate set.

- [ ] **Step 6: Commit**

```bash
git add schemas/semantic-rerank-response.schema.json src/onecode_skill_sanitizer/semantic_provider.py tests/test_semantic_provider.py
git commit -m "feat: bound semantic reranking to trusted candidates"
```

---

### Task 6: Compose The Minimum Skill Set And Real DAG

**Files:**
- Create: `tests/test_skill_selection.py`
- Create: `src/onecode_skill_sanitizer/skill_selection.py`

- [ ] **Step 1: Write failing composition tests**

Create `tests/test_skill_selection.py` using small profile and candidate factories. Cover these exact behaviors:

```python
from __future__ import annotations

import unittest

from onecode_skill_sanitizer.skill_selection import compose_skill_selection


def profile(name, capability, *, requires=(), produces=(), evidence=(), after=(), conflicts=()):
    return {
        "name": name,
        "capabilities": [capability],
        "requires_context": list(requires),
        "produces_artifacts": list(produces),
        "produces_evidence": list(evidence),
        "requires_after": list(after),
        "conflicts_with": list(conflicts),
        "excludes": [],
    }


def candidate(name, capability, score):
    return {
        "skill": name,
        "deterministic_score": score,
        "semantic_score": None,
        "final_score": score,
        "matched_capabilities": [capability],
        "selected": False,
        "excluded": False,
        "reason_codes": ["deterministic_candidate"],
    }


class SkillSelectionTest(unittest.TestCase):
    def test_selects_only_marginal_capability_contributors(self):
        need = {
            "decision": "composite",
            "required_capabilities": ["code.review", "code.test"],
            "explicit_skills": [],
            "excluded_skills": [],
        }
        candidates = [
            candidate("code-review-risk", "code.review", 0.9),
            candidate("code-test-regression", "code.test", 0.8),
            candidate("codebase-explore-map", "code.explore", 0.7),
        ]
        profiles = {
            "code-review-risk": profile("code-review-risk", "code.review"),
            "code-test-regression": profile("code-test-regression", "code.test"),
            "codebase-explore-map": profile("codebase-explore-map", "code.explore"),
        }

        result = compose_skill_selection(need, candidates, profiles, explicit_order=[])

        self.assertEqual(result["selected_skill_names"], ["code-review-risk", "code-test-regression"])
        self.assertEqual(result["rejected_adjacent_candidates"], ["codebase-explore-map"])
        self.assertEqual(result["execution_graph"]["edges"], [])

    def test_artifact_requirement_and_explicit_order_create_only_real_edges(self):
        need = {
            "decision": "composite",
            "required_capabilities": ["design.ui_review", "execution.browser_check"],
            "explicit_skills": [],
            "excluded_skills": [],
        }
        candidates = [
            candidate("design-ui-review", "design.ui_review", 0.9),
            candidate("execution-browser-check", "execution.browser_check", 0.8),
        ]
        profiles = {
            "design-ui-review": profile("design-ui-review", "design.ui_review", evidence=("ui_review_report",)),
            "execution-browser-check": profile(
                "execution-browser-check", "execution.browser_check", requires=("ui_review_report",)
            ),
        }

        result = compose_skill_selection(
            need, candidates, profiles,
            explicit_order=[("design-ui-review", "execution-browser-check")],
        )

        self.assertEqual(result["routing_status"], "complete")
        self.assertEqual(result["execution_graph"]["edges"], [{
            "from": "skill:design-ui-review",
            "to": "skill:execution-browser-check",
            "type": "artifact_dependency",
            "evidence": "ui_review_report",
        }])

    def test_uncovered_capability_is_incomplete_and_cycle_is_blocked(self):
        missing = compose_skill_selection(
            {"decision": "single", "required_capabilities": ["code.test"], "explicit_skills": [], "excluded_skills": []},
            [],
            {},
            explicit_order=[],
        )
        self.assertEqual(missing["routing_status"], "incomplete")
        self.assertEqual(missing["missing_capabilities"], ["code.test"])

        missing_input = compose_skill_selection(
            {
                "decision": "single",
                "required_capabilities": ["code.test"],
                "explicit_skills": [],
                "excluded_skills": [],
                "missing_inputs": ["behavior_or_change_under_test"],
            },
            [candidate("code-test-regression", "code.test", 0.9)],
            {"code-test-regression": profile("code-test-regression", "code.test")},
            explicit_order=[],
        )
        self.assertEqual(missing_input["routing_status"], "incomplete")
        self.assertEqual(
            missing_input["capability_resolution"]["missing_inputs"],
            ["behavior_or_change_under_test"],
        )

        profiles = {
            "a": profile("a", "code.review", after=("b",)),
            "b": profile("b", "code.test", after=("a",)),
        }
        cyclic = compose_skill_selection(
            {"decision": "composite", "required_capabilities": ["code.review", "code.test"], "explicit_skills": [], "excluded_skills": []},
            [candidate("a", "code.review", 0.9), candidate("b", "code.test", 0.8)],
            profiles,
            explicit_order=[],
        )
        self.assertEqual(cyclic["routing_status"], "blocked")
        self.assertIn("dependency_cycle", cyclic["execution_graph"]["reason_codes"])

    def test_close_conflicting_candidates_require_clarification(self):
        profiles = {
            "a": profile("a", "design.ui_review", conflicts=("b",)),
            "b": profile("b", "design.ui_review", conflicts=("a",)),
        }
        result = compose_skill_selection(
            {"decision": "single", "required_capabilities": ["design.ui_review"], "explicit_skills": [], "excluded_skills": []},
            [candidate("a", "design.ui_review", 0.70), candidate("b", "design.ui_review", 0.68)],
            profiles,
            explicit_order=[],
        )
        self.assertEqual(result["routing_status"], "clarify")
        self.assertEqual(
            result["selection"]["clarification_reason"],
            "conflicting_candidates_low_margin",
        )

    def test_risk_derived_verifier_gets_a_mandatory_precondition_edge(self):
        result = compose_skill_selection(
            {
                "decision": "composite",
                "required_capabilities": ["code.review", "code.test"],
                "mandatory_capabilities": ["code.test"],
                "explicit_skills": [], "excluded_skills": [],
            },
            [candidate("code-review-risk", "code.review", 0.9), candidate("code-test-regression", "code.test", 0.8)],
            {
                "code-review-risk": profile("code-review-risk", "code.review"),
                "code-test-regression": profile("code-test-regression", "code.test"),
            },
            explicit_order=[],
        )
        self.assertEqual(result["execution_graph"]["edges"], [{
            "from": "skill:code-review-risk", "to": "skill:code-test-regression",
            "type": "mandatory_verification_precondition",
            "evidence": "risk_derived_verification",
        }])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run RED**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_skill_selection -v
```

Expected: FAIL because the composition module does not exist.

- [ ] **Step 3: Implement greedy marginal coverage, conflict policy, and DAG compilation**

Create `src/onecode_skill_sanitizer/skill_selection.py` with these public rules:

```python
from __future__ import annotations

from collections import defaultdict, deque
from typing import Any


SELECTION_THRESHOLD = 0.35
CLARIFY_MARGIN = 0.08


def compose_skill_selection(
    need: dict[str, Any],
    candidates: list[dict[str, Any]],
    profiles: dict[str, dict[str, Any]],
    *,
    explicit_order: list[tuple[str, str]],
) -> dict[str, Any]:
    if need.get("policy_block_reasons"):
        graph = _empty_graph("blocked")
        graph["acyclic"] = False
        graph["reason_codes"] = list(need["policy_block_reasons"])
        graph["details"] = ["routing policy rejected the explicit request"]
        return _result(
            "blocked", [], candidates, list(need["required_capabilities"]), [],
            "", graph, _confidence(candidates, "blocked"),
            failure_reason=need["policy_block_reasons"][0],
        )
    if need["decision"] == "none":
        result = _result(
            "none", [], candidates, [], [], "", _empty_graph("ready"),
            _confidence(candidates, "none"),
        )
        result["selection"]["abstention_reason"] = need["reason_codes"][0]
        return result
    if need["decision"] == "clarify":
        return _result(
            "clarify", [], candidates, [], [], need["reason_codes"][0],
            _empty_graph("ready"), _confidence(candidates, "clarify"),
        )

    required = list(dict.fromkeys(need["required_capabilities"]))
    uncovered = set(required)
    selected: list[str] = []
    contributions: list[dict[str, Any]] = []
    conflict_resolutions: list[dict[str, Any]] = []
    eligible = [item for item in candidates if not item.get("excluded") and item["final_score"] >= SELECTION_THRESHOLD]
    for item in eligible:
        name = item["skill"]
        profile = profiles[name]
        marginal = sorted(uncovered & set(profile["capabilities"]))
        explicitly_requested = name in need["explicit_skills"]
        if not marginal and not explicitly_requested:
            continue
        conflict = next((other for other in selected if _conflicts(name, other, profiles)), "")
        if conflict:
            other_score = next(candidate["final_score"] for candidate in candidates if candidate["skill"] == conflict)
            if abs(item["final_score"] - other_score) < CLARIFY_MARGIN:
                result = _result(
                    "clarify", [], candidates, required, [], "conflicting_candidates_low_margin",
                    _empty_graph("ready"), _confidence(candidates, "clarify"),
                )
                result["selection"]["conflict_resolutions"] = [{
                    "winner": "", "rejected": name,
                    "reason": "insufficient_margin", "margin": abs(item["final_score"] - other_score),
                }]
                return result
            conflict_resolutions.append({
                "winner": conflict, "rejected": name,
                "reason": "higher_deterministic_score", "margin": abs(item["final_score"] - other_score),
            })
            continue
        selected.append(name)
        uncovered.difference_update(marginal)
        reason = "marginal_capability_coverage"
        if set(marginal) & set(need.get("mandatory_capabilities", [])):
            reason = "mandatory_verification"
        elif explicitly_requested and not marginal:
            reason = "explicit_user_request"
        contributions.append({
            "skill": name,
            "capabilities": marginal,
            "reason": reason,
        })
    selected = _include_required_producers(
        selected,
        profiles,
        contributions,
        {item["skill"] for item in eligible},
    )
    missing = sorted(uncovered)
    mandatory_skills = {
        name for name in selected
        if set(profiles[name]["capabilities"]) & set(need.get("mandatory_capabilities", []))
    }
    graph = _compile_graph(selected, profiles, explicit_order, mandatory_skills)
    if graph["status"] == "blocked":
        status = "blocked"
    elif missing or need.get("missing_inputs"):
        status = "incomplete"
    else:
        status = "complete"
    rejected = [item["skill"] for item in candidates if item["skill"] not in selected and not item.get("excluded")]
    result = _result(
        status, selected, candidates, required, missing, "", graph,
        _confidence(candidates, status),
        missing_inputs=list(need.get("missing_inputs", [])),
        failure_reason=(
            "dependency_cycle" if status == "blocked"
            else "missing_required_input" if need.get("missing_inputs")
            else "missing_capability" if missing
            else ""
        ),
    )
    result["selection"]["marginal_contributions"] = contributions
    result["selection"]["rejected_adjacent_candidates"] = rejected
    result["selection"]["conflict_resolutions"] = conflict_resolutions
    return result


def _include_required_producers(
    selected: list[str],
    profiles: dict[str, dict[str, Any]],
    contributions: list[dict[str, Any]],
    admitted_names: set[str],
) -> list[str]:
    expanded = list(selected)
    produced_by = defaultdict(list)
    for name, profile in profiles.items():
        for artifact in profile.get("produces_artifacts", []) + profile.get("produces_evidence", []):
            produced_by[artifact].append(name)
    for target in list(expanded):
        for required in profiles[target].get("requires_context", []):
            producers = sorted(name for name in produced_by[required] if name in selected)
            if producers:
                continue
            eligible = sorted(
                name for name in produced_by[required]
                if name in profiles and name in admitted_names
            )
            if len(eligible) == 1 and eligible[0] not in expanded:
                expanded.append(eligible[0])
                contributions.append({"skill": eligible[0], "capabilities": [], "reason": f"required_artifact:{required}"})
    return expanded


def _compile_graph(
    selected: list[str],
    profiles: dict[str, dict[str, Any]],
    explicit_order: list[tuple[str, str]],
    mandatory_skills: set[str],
) -> dict[str, Any]:
    nodes = [{"id": f"skill:{name}", "skill": name, "parallel": True} for name in selected]
    edges: list[dict[str, str]] = []
    for target in selected:
        requirements = set(profiles[target].get("requires_context", []))
        for source in selected:
            if source == target:
                continue
            produced = set(profiles[source].get("produces_artifacts", [])) | set(profiles[source].get("produces_evidence", []))
            for artifact in sorted(requirements & produced):
                edges.append({"from": f"skill:{source}", "to": f"skill:{target}", "type": "artifact_dependency", "evidence": artifact})
        for source in profiles[target].get("requires_after", []):
            if source in selected:
                edges.append({"from": f"skill:{source}", "to": f"skill:{target}", "type": "requires_after", "evidence": source})
    for source, target in explicit_order:
        if source in selected and target in selected and not any(
            edge["from"] == f"skill:{source}" and edge["to"] == f"skill:{target}" for edge in edges
        ):
            edges.append({"from": f"skill:{source}", "to": f"skill:{target}", "type": "explicit_user_order", "evidence": "current_request"})
    for verifier in sorted(mandatory_skills):
        for source in selected:
            if source != verifier and not any(
                edge["from"] == f"skill:{source}" and edge["to"] == f"skill:{verifier}"
                for edge in edges
            ):
                edges.append({
                    "from": f"skill:{source}",
                    "to": f"skill:{verifier}",
                    "type": "mandatory_verification_precondition",
                    "evidence": "risk_derived_verification",
                })
    edges = sorted({(edge["from"], edge["to"], edge["type"], edge["evidence"]): edge for edge in edges}.values(), key=lambda edge: (edge["from"], edge["to"], edge["type"], edge["evidence"]))
    edge_nodes = {edge["from"] for edge in edges} | {edge["to"] for edge in edges}
    for node in nodes:
        node["parallel"] = node["id"] not in edge_nodes
    acyclic = _is_acyclic([node["id"] for node in nodes], edges)
    return {
        "status": "ready" if acyclic else "blocked",
        "acyclic": acyclic,
        "nodes": nodes if acyclic else [],
        "edges": edges if acyclic else [],
        "reason_codes": [] if acyclic else ["dependency_cycle"],
        "details": [] if acyclic else ["selected skill dependency graph contains a cycle"],
    }


def _is_acyclic(node_ids: list[str], edges: list[dict[str, str]]) -> bool:
    indegree = {node_id: 0 for node_id in node_ids}
    outgoing: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        outgoing[edge["from"]].append(edge["to"])
        indegree[edge["to"]] += 1
    ready = deque(sorted(node_id for node_id, degree in indegree.items() if degree == 0))
    visited = 0
    while ready:
        node_id = ready.popleft()
        visited += 1
        for target in sorted(outgoing[node_id]):
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
    return visited == len(node_ids)


def _conflicts(left: str, right: str, profiles: dict[str, dict[str, Any]]) -> bool:
    left_conflicts = set(profiles[left].get("conflicts_with", [])) | set(profiles[left].get("excludes", []))
    right_conflicts = set(profiles[right].get("conflicts_with", [])) | set(profiles[right].get("excludes", []))
    return right in left_conflicts or left in right_conflicts


def _empty_graph(status: str) -> dict[str, Any]:
    return {
        "status": status,
        "acyclic": status != "blocked",
        "nodes": [],
        "edges": [],
        "reason_codes": [],
        "details": [],
    }


def _confidence(candidates: list[dict[str, Any]], status: str) -> dict[str, Any]:
    scores = sorted(
        (float(item["final_score"]) for item in candidates if not item.get("excluded")),
        reverse=True,
    )
    top = scores[0] if scores else 0.0
    runner_up = scores[1] if len(scores) > 1 else 0.0
    margin = max(0.0, top - runner_up)
    if status in {"blocked", "clarify", "incomplete", "none"}:
        level = "low"
    elif top >= 0.75 and (len(scores) == 1 or margin >= CLARIFY_MARGIN):
        level = "high"
    else:
        level = "medium"
    reasons = [f"routing_status:{status}"]
    if margin < CLARIFY_MARGIN and len(scores) > 1:
        reasons.append("low_score_margin")
    return {
        "overall": round(top, 6),
        "level": level,
        "top_score": round(top, 6),
        "runner_up_score": round(runner_up, 6),
        "margin": round(margin, 6),
        "selection_threshold": SELECTION_THRESHOLD,
        "clarify_margin": CLARIFY_MARGIN,
        "reason_codes": reasons,
    }


def _result(
    status: str,
    selected: list[str],
    candidates: list[dict[str, Any]],
    required: list[str],
    missing: list[str],
    clarification_reason: str,
    graph: dict[str, Any],
    confidence: dict[str, Any],
    *,
    missing_inputs: list[str] | None = None,
    failure_reason: str = "",
) -> dict[str, Any]:
    missing_inputs = list(missing_inputs or [])
    covered = [capability for capability in required if capability not in missing]
    abstention_reason = "no_specialized_need" if status == "none" else ""
    return {
        "routing_status": status,
        "selected_skill_names": list(selected),
        "missing_capabilities": list(missing),
        "selection": {
            "selected_skill_names": list(selected),
            "selected_skills": [],
            "marginal_contributions": [],
            "rejected_adjacent_candidates": [
                item["skill"] for item in candidates if item["skill"] not in selected
            ],
            "conflict_resolutions": [],
            "clarification_reason": clarification_reason,
            "abstention_reason": abstention_reason,
            "failure_reason": failure_reason,
        },
        "capability_resolution": {
            "required_capabilities": list(required),
            "covered_capabilities": covered,
            "missing_capabilities": list(missing),
            "missing_inputs": missing_inputs,
            "covered_count": len(covered),
            "missing_count": len(missing),
            "status": "complete" if not missing and not missing_inputs else "incomplete",
        },
        "execution_graph": graph,
        "confidence": confidence,
    }
```

Keep status precedence `blocked` > `incomplete` > `clarify` > `none` > `complete`.

- [ ] **Step 4: Run GREEN**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_skill_selection -v
```

Expected: PASS; the first test proves that scenario or bundle membership cannot add a third Skill, and independent nodes have no synthetic serial edge.

- [ ] **Step 5: Commit**

```bash
git add src/onecode_skill_sanitizer/skill_selection.py tests/test_skill_selection.py
git commit -m "feat: compose minimal skill sets with real dependencies"
```

---

### Task 7: Build And Validate Strict Task-Pack V3

**Files:**
- Create: `schemas/task-pack-v3.schema.json`
- Modify: `src/onecode_skill_sanitizer/task_pack_v3.py`
- Modify: `src/onecode_skill_sanitizer/compatibility.py`
- Modify: `tests/test_task_pack_v3_cli.py`
- Modify: `tests/test_compatibility.py`

- [ ] **Step 1: Add failing builder, schema, route-ID, and compatibility tests**

Add to `tests/test_task_pack_v3_cli.py`:

```python
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from onecode_skill_sanitizer.task_pack_v3 import build_task_pack_v3


ROOT = Path(__file__).resolve().parents[1]


    def test_builder_emits_strict_v3_selection_and_parallel_graph(self):
        payload = build_task_pack_v3(
            ROOT / "catalog",
            "review this patch and add a regression test",
            ROOT / "bundles/index.json",
            ROOT / "catalog/routing-examples.json",
        )
        schema = json.loads((ROOT / "schemas/task-pack-v3.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(payload)

        self.assertEqual(payload["schema_version"], 3)
        self.assertEqual(payload["need_decision"]["decision"], "composite")
        self.assertEqual(
            [item["name"] for item in payload["selection"]["selected_skills"]],
            ["code-review-risk", "code-test-regression"],
        )
        self.assertEqual(payload["execution_graph"]["edges"], [])
        self.assertEqual(payload["provider"]["used"], "none")

    def test_none_is_a_first_class_successful_abstention(self):
        payload = build_task_pack_v3(
            ROOT / "catalog", "Explain what code-review-risk is; do not invoke it.",
            ROOT / "bundles/index.json", ROOT / "catalog/routing-examples.json",
        )
        self.assertEqual(payload["routing_status"], "none")
        self.assertEqual(payload["selection"]["selected_skills"], [])
        self.assertEqual(payload["execution_graph"]["nodes"], [])

    def test_route_id_changes_with_runtime_examples_but_not_timestamp(self):
        first = build_task_pack_v3(
            ROOT / "catalog", "review this patch", ROOT / "bundles/index.json",
            ROOT / "catalog/routing-examples.json",
        )
        second = build_task_pack_v3(
            ROOT / "catalog", "review this patch", ROOT / "bundles/index.json",
            ROOT / "catalog/routing-examples.json",
        )
        self.assertEqual(first["route_id"], second["route_id"])
        self.assertNotEqual(first["generated_at"], "")
        with tempfile.TemporaryDirectory() as temp_dir:
            changed_examples = json.loads(
                (ROOT / "catalog/routing-examples.json").read_text(encoding="utf-8")
            )
            changed_examples["examples"][0]["query"] += " Include ownership evidence."
            changed_path = Path(temp_dir) / "routing-examples.json"
            changed_path.write_text(json.dumps(changed_examples), encoding="utf-8")
            changed = build_task_pack_v3(
                ROOT / "catalog", "review this patch", ROOT / "bundles/index.json",
                changed_path,
            )
        self.assertNotEqual(first["route_id"], changed["route_id"])
```

Add to `tests/test_compatibility.py`:

```python
from onecode_skill_sanitizer.compatibility import v3_compatibility_report


    def test_v3_compatibility_report_names_skill_selection_loss(self):
        report = v3_compatibility_report({
            "need_decision": {"decision": "composite"},
            "selection": {"selected_skills": [{"name": "code-review-risk"}, {"name": "code-test-regression"}]},
            "provider": {"used": "fake"},
            "confidence": {"level": "medium"},
            "execution_graph": {"edges": [{"type": "artifact_dependency"}]},
        })

        self.assertFalse(report["v2"]["lossless"])
        self.assertIn("skill_level_selection", report["v2"]["losses"])
        self.assertIn("semantic_provider_evidence", report["v1"]["losses"])
        self.assertIn("confidence_and_abstention", report["v1"]["losses"])
```

- [ ] **Step 2: Run RED**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_task_pack_v3_cli tests.test_compatibility -v
```

Expected: FAIL because the schema, completed builder, and compatibility report are missing.

- [ ] **Step 3: Create the strict v3 schema**

Create `schemas/task-pack-v3.schema.json`. Set top-level `additionalProperties` to `false`, require exactly the approved top-level fields plus `generated_at`, and use these enums:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://onecode.local/schemas/task-pack-v3.schema.json",
  "title": "OneCode Task Pack v3",
  "type": "object",
  "required": [
    "schema_version", "generated_at", "route_id", "routing_mode", "routing_status",
    "provider", "normalized_task", "need_decision", "intent_graph", "candidates",
    "selection", "capability_resolution", "execution_graph", "confidence",
    "host_execution_protocol", "routing_metrics", "registry_verification", "compatibility"
  ],
  "properties": {
    "schema_version": {"const": 3},
    "generated_at": {"type": "string", "minLength": 1},
    "route_id": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
    "routing_mode": {"enum": ["deterministic", "semantic_shadow", "hybrid"]},
    "routing_status": {"enum": ["none", "complete", "clarify", "incomplete", "blocked"]},
    "provider": {"$ref": "#/$defs/provider"},
    "normalized_task": {"$ref": "#/$defs/normalizedTask"},
    "need_decision": {"$ref": "#/$defs/needDecision"},
    "intent_graph": {"type": "object"},
    "candidates": {"type": "array", "items": {"$ref": "#/$defs/candidate"}},
    "selection": {"$ref": "#/$defs/selection"},
    "capability_resolution": {"$ref": "#/$defs/capabilityResolution"},
    "execution_graph": {"$ref": "#/$defs/executionGraph"},
    "confidence": {"$ref": "#/$defs/confidence"},
    "host_execution_protocol": {"$ref": "#/$defs/hostProtocol"},
    "routing_metrics": {"type": "object"},
    "registry_verification": {"type": "object"},
    "compatibility": {"type": "object"}
  },
  "additionalProperties": false,
  "$defs": {
    "stringList": {"type": "array", "items": {"type": "string", "minLength": 1}, "uniqueItems": true},
    "provider": {
      "type": "object",
      "required": ["requested", "used", "model_or_adapter", "fallback_reason", "candidate_scope_hash", "response_status", "validation_reason_codes"],
      "properties": {
        "requested": {"type": "string", "minLength": 1},
        "used": {"type": "string", "minLength": 1},
        "model_or_adapter": {"type": "string", "minLength": 1},
        "fallback_reason": {"type": "string", "minLength": 1},
        "candidate_scope_hash": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
        "response_status": {"enum": ["not_requested", "accepted_shadow", "accepted_influence", "rejected_fallback"]},
        "validation_reason_codes": {"$ref": "#/$defs/stringList"}
      },
      "additionalProperties": false
    },
    "normalizedTask": {
      "type": "object",
      "required": ["raw", "current", "history", "stale", "stale_policy"],
      "properties": {
        "raw": {"type": "string"}, "current": {"type": "string"}, "history": {"type": "string"},
        "stale": {"type": "string"}, "stale_policy": {"type": "string"}
      },
      "additionalProperties": false
    },
    "needDecision": {
      "type": "object",
      "required": ["decision", "specialized_need", "required_capabilities", "explicit_skills", "excluded_skills", "explanation_only", "inventory_only", "missing_inputs", "mandatory_capabilities", "policy_block_reasons", "reason_codes"],
      "properties": {
        "decision": {"enum": ["none", "single", "composite", "clarify"]},
        "specialized_need": {"type": "boolean"},
        "required_capabilities": {"$ref": "#/$defs/stringList"},
        "explicit_skills": {"$ref": "#/$defs/stringList"},
        "excluded_skills": {"$ref": "#/$defs/stringList"},
        "explanation_only": {"type": "boolean"},
        "inventory_only": {"type": "boolean"},
        "missing_inputs": {"$ref": "#/$defs/stringList"},
        "mandatory_capabilities": {"$ref": "#/$defs/stringList"},
        "policy_block_reasons": {"$ref": "#/$defs/stringList"},
        "reason_codes": {"$ref": "#/$defs/stringList"}
      },
      "additionalProperties": false
    },
    "candidate": {
      "type": "object",
      "required": ["skill", "registry_path", "status", "description", "deterministic_score", "semantic_score", "final_score", "matched_intents", "matched_capabilities", "matched_examples", "positive_evidence", "penalties", "exclusions", "excluded", "selected", "reason_codes"],
      "properties": {
        "skill": {"type": "string", "minLength": 1},
        "registry_path": {"type": "string", "minLength": 1},
        "status": {"const": "trusted"},
        "description": {"type": "string", "minLength": 1},
        "deterministic_score": {"type": "number", "minimum": 0, "maximum": 1},
        "semantic_score": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
        "final_score": {"type": "number", "minimum": 0, "maximum": 1},
        "matched_intents": {"$ref": "#/$defs/stringList"},
        "matched_capabilities": {"$ref": "#/$defs/stringList"},
        "matched_examples": {"$ref": "#/$defs/stringList"},
        "positive_evidence": {"type": "array", "items": {"$ref": "#/$defs/scoreEvidence"}},
        "penalties": {"type": "array", "items": {"$ref": "#/$defs/scoreEvidence"}},
        "exclusions": {"$ref": "#/$defs/stringList"},
        "excluded": {"type": "boolean"},
        "selected": {"type": "boolean"},
        "reason_codes": {"$ref": "#/$defs/stringList"}
      },
      "additionalProperties": false
    },
    "scoreEvidence": {
      "type": "object",
      "required": ["type", "value", "weight"],
      "properties": {
        "type": {"type": "string", "minLength": 1},
        "value": {},
        "weight": {"type": "number", "minimum": -1, "maximum": 1}
      },
      "additionalProperties": false
    },
    "selection": {
      "type": "object",
      "required": ["need_decision", "selected_skill_names", "selected_skills", "marginal_contributions", "rejected_adjacent_candidates", "conflict_resolutions", "clarification_reason", "abstention_reason", "failure_reason"],
      "properties": {
        "need_decision": {"enum": ["none", "single", "composite", "clarify"]},
        "selected_skill_names": {"$ref": "#/$defs/stringList"},
        "selected_skills": {"type": "array", "items": {"type": "object", "required": ["name", "status", "registry_path"], "properties": {"name": {"type": "string"}, "status": {"const": "trusted"}, "registry_path": {"type": "string"}}, "additionalProperties": true},
        "marginal_contributions": {"type": "array", "items": {"type": "object", "required": ["skill", "capabilities", "reason"], "properties": {"skill": {"type": "string"}, "capabilities": {"$ref": "#/$defs/stringList"}, "reason": {"type": "string"}}, "additionalProperties": false},
        "rejected_adjacent_candidates": {"$ref": "#/$defs/stringList"},
        "conflict_resolutions": {"type": "array", "items": {"type": "object", "required": ["winner", "rejected", "reason", "margin"], "properties": {"winner": {"type": "string"}, "rejected": {"type": "string"}, "reason": {"enum": ["insufficient_margin", "higher_deterministic_score"]}, "margin": {"type": "number", "minimum": 0, "maximum": 1}}, "additionalProperties": false}},
        "clarification_reason": {"type": "string"},
        "abstention_reason": {"type": "string"},
        "failure_reason": {"type": "string"}
      },
      "additionalProperties": false
    },
    "capabilityResolution": {
      "type": "object",
      "required": ["required_capabilities", "covered_capabilities", "missing_capabilities", "missing_inputs", "covered_count", "missing_count", "status"],
      "properties": {
        "required_capabilities": {"$ref": "#/$defs/stringList"},
        "covered_capabilities": {"$ref": "#/$defs/stringList"},
        "missing_capabilities": {"$ref": "#/$defs/stringList"},
        "missing_inputs": {"$ref": "#/$defs/stringList"},
        "covered_count": {"type": "integer", "minimum": 0},
        "missing_count": {"type": "integer", "minimum": 0},
        "status": {"enum": ["complete", "incomplete"]}
      },
      "additionalProperties": false
    },
    "executionGraph": {
      "type": "object",
      "required": ["status", "acyclic", "nodes", "edges", "reason_codes", "details"],
      "properties": {
        "status": {"enum": ["ready", "blocked"]},
        "acyclic": {"type": "boolean"},
        "nodes": {"type": "array", "items": {"type": "object", "required": ["id", "skill", "parallel"], "properties": {"id": {"type": "string"}, "skill": {"type": "string"}, "parallel": {"type": "boolean"}}, "additionalProperties": false}},
        "edges": {"type": "array", "items": {"type": "object", "required": ["from", "to", "type", "evidence"], "properties": {"from": {"type": "string"}, "to": {"type": "string"}, "type": {"enum": ["artifact_dependency", "requires_after", "explicit_user_order", "mandatory_verification_precondition"]}, "evidence": {"type": "string"}}, "additionalProperties": false}},
        "reason_codes": {"$ref": "#/$defs/stringList"},
        "details": {"$ref": "#/$defs/stringList"}
      },
      "additionalProperties": false
    },
    "confidence": {
      "type": "object",
      "required": ["overall", "level", "top_score", "runner_up_score", "margin", "selection_threshold", "clarify_margin", "reason_codes"],
      "properties": {
        "overall": {"type": "number", "minimum": 0, "maximum": 1},
        "level": {"enum": ["low", "medium", "high"]},
        "top_score": {"type": "number", "minimum": 0, "maximum": 1},
        "runner_up_score": {"type": "number", "minimum": 0, "maximum": 1},
        "margin": {"type": "number", "minimum": 0, "maximum": 1},
        "selection_threshold": {"type": "number", "minimum": 0, "maximum": 1},
        "clarify_margin": {"type": "number", "minimum": 0, "maximum": 1},
        "reason_codes": {"$ref": "#/$defs/stringList"}
      },
      "additionalProperties": false
    },
    "hostProtocol": {
      "type": "object",
      "required": ["mode", "runtime_boundary", "node_statuses"],
      "properties": {
        "mode": {"const": "method_only"},
        "runtime_boundary": {"const": "The host runtime controls permissions and execution."},
        "node_statuses": {"type": "array", "items": {"enum": ["pending", "ready", "running", "waiting_approval", "completed", "failed", "blocked", "skipped"]}, "uniqueItems": true}
      },
      "additionalProperties": false
    }
  }
}
```

- [ ] **Step 4: Implement v3 orchestration and route identity**

Replace the feature error in `task_pack_v3.py` with stage calls in the approved order:

```python
import json
import re

from . import __version__
from .compatibility import build_canonical_content_hash, build_route_id, build_route_identity_payload, v3_compatibility_report
from .intent import decompose_task, normalize_task
from .need_gate import CAPABILITY_PATTERNS, CAPABILITY_SKILL, decide_skill_need
from .registry import load_registry_index, utc_now, verify_registry
from .semantic_provider import SemanticProvider, rerank_candidates
from .skill_candidates import (
    HIGH_FREQUENCY_ENTRY_NAMES,
    load_cohort_profiles,
    load_routing_examples,
    retrieve_skill_candidates,
)
from .skill_selection import compose_skill_selection
from .task_packs import load_skill_pack_item


def build_task_pack_v3(
    registry_dir: Path,
    task: str,
    bundles_path: Path,
    routing_examples_path: Path,
    *,
    max_candidates: int = 3,
    semantic_provider: SemanticProvider | None = None,
    semantic_mode: str = "shadow",
) -> dict[str, Any]:
    if not task.strip():
        raise ValueError("task must not be empty")
    if semantic_mode not in {"none", "shadow", "influence"}:
        raise ValueError("semantic_mode must be none, shadow, or influence")
    verification = verify_registry(registry_dir)
    if verification["status"] != "ok":
        raise SystemExit("registry verification failed; refusing to build task pack")
    normalized = normalize_task(task)
    intent_graph = decompose_task(task)
    need = decide_skill_need(normalized)
    examples = load_routing_examples(routing_examples_path)
    profiles = load_cohort_profiles(registry_dir)
    candidates = retrieve_skill_candidates(normalized, need, profiles, examples, top_k=max_candidates)
    active_provider = None if need["decision"] == "none" else semantic_provider
    candidates, provider_record = rerank_candidates(
        normalized.current, need, candidates, active_provider,
        mode="none" if active_provider is None else semantic_mode,
    )
    explicit_order = _extract_explicit_skill_order(normalized.current, need, candidates)
    composed = compose_skill_selection(need, candidates, profiles, explicit_order=explicit_order)
    registry_index = load_registry_index(registry_dir)
    entries = {entry["name"]: entry for entry in registry_index["skills"]}
    selected_items = [
        load_skill_pack_item(registry_dir, entries[name])
        for name in composed["selected_skill_names"]
    ]
    selected_names = set(composed["selected_skill_names"])
    traced_candidates = [
        {**candidate, "selected": candidate["skill"] in selected_names,
         "reason_codes": sorted(set(candidate["reason_codes"]) | ({"selected"} if candidate["skill"] in selected_names else {"rejected"}))}
        for candidate in candidates
    ]
    route_identity = {
        "base": build_route_identity_payload(
            current=normalized.current,
            history=normalized.history,
            stale=normalized.stale,
            stale_policy=normalized.stale_policy,
            invariants=[],
            capabilities=need["required_capabilities"],
            strategy="high_frequency_v3",
            provider_identifier=provider_record["used"],
            catalog_content_hash=build_canonical_content_hash(registry_index),
            bundle_content_hash=build_canonical_content_hash(
                json.loads(bundles_path.read_text(encoding="utf-8"))
            ),
            overlap_content_hash="none",
            router_version="high-frequency-intelligent-router-v3",
            package_version=__version__,
        ),
        "routing_examples_content_hash": build_canonical_content_hash(examples),
        "cohort_names": list(HIGH_FREQUENCY_ENTRY_NAMES),
        "constraints": {
            "excluded_skills": need["excluded_skills"],
            "missing_inputs": need["missing_inputs"],
            "mandatory_capabilities": need["mandatory_capabilities"],
        },
    }
    payload = {
        "schema_version": 3,
        "generated_at": utc_now(),
        "route_id": build_route_id(route_identity),
        "routing_mode": (
            "deterministic" if provider_record["used"] == "none"
            else "semantic_shadow" if semantic_mode == "shadow"
            else "hybrid"
        ),
        "routing_status": composed["routing_status"],
        "provider": provider_record,
        "normalized_task": normalized.to_json(),
        "need_decision": need,
        "intent_graph": intent_graph.to_json(),
        "candidates": traced_candidates,
        "selection": {
            **composed["selection"],
            "need_decision": need["decision"],
            "selected_skills": selected_items,
        },
        "capability_resolution": composed["capability_resolution"],
        "execution_graph": composed["execution_graph"],
        "confidence": composed["confidence"],
        "host_execution_protocol": {
            "mode": "method_only",
            "runtime_boundary": "The host runtime controls permissions and execution.",
            "node_statuses": ["pending", "ready", "running", "waiting_approval", "completed", "failed", "blocked", "skipped"],
        },
        "routing_metrics": {
            "candidate_count": len(traced_candidates),
            "selected_skill_count": len(selected_items),
            "required_capability_count": len(need["required_capabilities"]),
            "covered_capability_count": composed["capability_resolution"]["covered_count"],
            "runtime_example_count": len(examples),
            "cohort_candidate_count": len(profiles),
        },
        "registry_verification": {
            "catalog": verification,
            "routing_examples": {"status": "ok", "count": len(examples), "content_hash": build_canonical_content_hash(examples)},
        },
        "compatibility": {},
    }
    payload["compatibility"] = v3_compatibility_report(payload)
    return payload


def _extract_explicit_skill_order(
    current: str,
    need: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> list[tuple[str, str]]:
    order_signal = re.compile(
        r"\b(?:then|after|before)\b|\u7136\u540e|\u4e4b\u540e|\u4e4b\u524d|\u5148|\u518d|\u6700\u540e",
        re.I,
    )
    if not order_signal.search(current):
        return []
    admitted = {item["skill"] for item in candidates}
    required = set(need["required_capabilities"])
    positions = []
    for capability, pattern in CAPABILITY_PATTERNS.items():
        match = pattern.search(current)
        skill = CAPABILITY_SKILL[capability]
        if capability in required and match and skill in admitted:
            positions.append((match.start(), skill))
    ordered = list(dict.fromkeys(skill for _, skill in sorted(positions)))
    return list(zip(ordered, ordered[1:]))
```

This helper maps only current-request clause order to admitted candidate names. It never reads bundle `execution_order`.

- [ ] **Step 5: Add compatibility reporting without changing legacy projection**

Add to `compatibility.py`:

```python
def v3_compatibility_report(payload: dict[str, Any]) -> dict[str, Any]:
    source = payload if isinstance(payload, dict) else {}
    selection = _object(source.get("selection"))
    selected = _object_list(selection.get("selected_skills"))
    provider = _object(source.get("provider"))
    need = _object(source.get("need_decision"))
    losses = ["skill_level_selection"] if selected else []
    if isinstance(source.get("confidence"), dict) or need.get("decision") in {"none", "clarify"}:
        losses.append("confidence_and_abstention")
    if provider.get("used") not in {None, "", "none"}:
        losses.append("semantic_provider_evidence")
    if len(selected) > 1:
        losses.append("multi_skill_exact_set")
    return {
        "v2": {"lossless": not losses, "losses": sorted(set(losses))},
        "v1": {
            "lossless": False,
            "losses": sorted(set(losses) | {"candidate_trace", "marginal_capability_contributions", "real_dependency_evidence"}),
        },
    }
```

- [ ] **Step 6: Run GREEN, strict schema checks, and frozen compatibility**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_task_pack_v3_cli tests.test_compatibility -v
python3 -m json.tool schemas/task-pack-v3.schema.json >/dev/null
PYTHONPATH=src python3 -m unittest tests.test_task_pack_v2_cli tests.test_router_eval_v2 -v
```

Expected: PASS. The v2 suite must show no fixture or output changes.

- [ ] **Step 7: Commit**

```bash
git add schemas/task-pack-v3.schema.json src/onecode_skill_sanitizer/task_pack_v3.py src/onecode_skill_sanitizer/compatibility.py tests/test_task_pack_v3_cli.py tests/test_compatibility.py
git commit -m "feat: emit strict intelligent task pack v3"
```

---

### Task 8: Wire CLI, Markdown, And The Router Integration

**Files:**
- Modify: `src/onecode_skill_sanitizer/commands.py`
- Modify: `src/onecode_skill_sanitizer/cli.py`
- Modify: `src/onecode_skill_sanitizer/rendering.py`
- Modify: `tests/test_task_pack_v3_cli.py`
- Modify: `tests/test_router_cli.py`
- Modify: `integrations/skills/safe-agent-router/scripts/task_pack.sh`
- Modify: `integrations/skills/safe-agent-router/SKILL.md`

- [ ] **Step 1: Add failing JSON, Markdown, bounded-error, and wrapper tests**

Add this CLI test to `tests/test_task_pack_v3_cli.py`:

```python
import contextlib
import io

from onecode_skill_sanitizer.cli import main


    def test_smart_v3_json_and_markdown_are_bounded(self):
        json_out = io.StringIO()
        with contextlib.redirect_stdout(json_out):
            self.assertEqual(
                main(["smart", "review this patch", "--schema-version", "3", "--format", "json"]),
                0,
            )
        payload = json.loads(json_out.getvalue())
        schema = json.loads((ROOT / "schemas/task-pack-v3.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(payload)

        attack = "review this patch\n## Injected\n```html\n<span>unsafe</span>"
        markdown_out = io.StringIO()
        with contextlib.redirect_stdout(markdown_out):
            self.assertEqual(
                main(["smart", attack, "--schema-version", "3", "--format", "markdown"]),
                0,
            )
        markdown = markdown_out.getvalue()
        headings = [line for line in markdown.splitlines() if line.startswith("#")]
        self.assertEqual(headings, [
            "# OneCode Agent Task Pack v3", "## Task", "## Need Decision",
            "## Selected Skills", "## Confidence", "## Provider",
            "## Execution Graph", "## Routing Diagnostics", "## Safety Boundary",
        ])
        self.assertNotIn("## Injected", markdown)
        self.assertNotIn("```", markdown)
        self.assertNotIn("<span>", markdown)

    def test_v3_empty_task_has_bounded_json_error(self):
        out = io.StringIO()
        err = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            exit_code = main(["smart", "", "--schema-version", "3", "--format", "json"])
        payload = json.loads(out.getvalue())
        self.assertEqual(exit_code, 2)
        self.assertEqual(err.getvalue(), "")
        self.assertEqual(payload["error"]["code"], "invalid_input")
        self.assertNotIn("Traceback", out.getvalue())
```

Add to `tests/test_router_cli.py` beside the existing repository-local wrapper test:

```python
    def test_task_pack_script_supports_explicit_v3_without_changing_default(self):
        script = Path("integrations/skills/safe-agent-router/scripts/task_pack.sh").resolve()
        v3 = subprocess.run(
            ["sh", str(script), "review this patch", "--schema-version", "3", "--format", "json"],
            cwd=Path.cwd(), capture_output=True, text=True, check=False,
        )
        default = subprocess.run(
            ["sh", str(script), "review this patch", "--format", "json"],
            cwd=Path.cwd(), capture_output=True, text=True, check=False,
        )

        self.assertEqual(v3.returncode, 0, v3.stderr)
        self.assertEqual(default.returncode, 0, default.stderr)
        self.assertEqual(json.loads(v3.stdout)["schema_version"], 3)
        self.assertEqual(json.loads(default.stdout)["schema_version"], 2)
```

- [ ] **Step 2: Run RED**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_task_pack_v3_cli tests.test_router_cli.RouterCliTest.test_task_pack_script_supports_explicit_v3_without_changing_default -v
```

Expected: FAIL because commands still dispatch only v1/v2 and the wrapper rejects `--schema-version`.

- [ ] **Step 3: Add v3 command dispatch and bounded errors**

In `commands.py`, dispatch v3 before the frozen v2 branch in both command functions:

```python
def task_pack_command(args: argparse.Namespace) -> int:
    if args.schema_version == 3:
        return _run_v3_task_pack_command(args)
    if args.schema_version == 2:
        return _run_v2_task_pack_command(args)
    # Keep the existing v1 branch byte-for-byte except indentation.


def smart_command(args: argparse.Namespace) -> int:
    if args.schema_version == 3:
        return _run_v3_task_pack_command(args)
    if args.schema_version == 2:
        return _run_v2_task_pack_command(args)
    # Keep the existing v1 branch byte-for-byte except indentation.
```

Implement `_run_v3_task_pack_command` using `build_task_pack_v3`, JSON with `allow_nan=False`, `render_task_pack_v3_markdown`, and the same bounded exception classes as v2. JSON input errors use `{"schema_version":3,"status":"error","error":{"code":"invalid_input","message":"Routing input or assets are invalid."}}`; Markdown errors begin `# OneCode Task Pack v3 Error`; both return exit code `2` without stderr or traceback.

Use this command body; `_safe_v2_error` is already a version-neutral sanitizer despite its historical name:

```python
def _run_v3_task_pack_command(args: argparse.Namespace) -> int:
    try:
        payload = build_task_pack_v3(
            resolve_project_asset_path(args.registry),
            args.task,
            resolve_project_asset_path(args.bundles),
            resolve_project_asset_path(args.routing_examples),
            max_candidates=3,
        )
    except (json.JSONDecodeError, OSError, ValueError, SystemExit) as exc:
        error = _safe_v2_error(exc)
        if args.format == "markdown":
            print("\n".join([
                "# OneCode Task Pack v3 Error", "",
                f"- code: `{error['code']}`", f"- message: {error['message']}",
            ]))
        else:
            print(json.dumps(
                {"schema_version": 3, "status": "error", "error": error},
                indent=2, sort_keys=True, allow_nan=False,
            ))
        return 2
    if args.format == "markdown":
        print(render_task_pack_v3_markdown(payload))
    else:
        print(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False))
    return 0
```

- [ ] **Step 4: Add safe Markdown rendering**

In `rendering.py`, implement `render_task_pack_v3_markdown` entirely through `markdown_safe_line`:

```python
def render_task_pack_v3_markdown(task_pack: dict) -> str:
    need = task_pack["need_decision"]
    selection = task_pack["selection"]
    confidence = task_pack["confidence"]
    provider = task_pack["provider"]
    graph = task_pack["execution_graph"]
    contributions = {
        item["skill"]: item["reason"]
        for item in selection["marginal_contributions"]
    }
    lines = [
        "# OneCode Agent Task Pack v3", "", "## Task", "",
        markdown_safe_line(task_pack["normalized_task"]["current"]), "",
        "## Need Decision", "",
        f"- decision: {markdown_safe_line(need['decision'])}",
        f"- reasons: {markdown_safe_line(', '.join(need['reason_codes']) or 'none')}",
        "", "## Selected Skills", "",
    ]
    if selection["selected_skills"]:
        for skill in selection["selected_skills"]:
            reason = contributions.get(skill["name"], "selected")
            lines.append(f"- {markdown_safe_line(skill['name'])}: {markdown_safe_line(reason)}")
    else:
        lines.append("- none")
    lines.extend([
        "", "## Confidence", "",
        f"- level: {markdown_safe_line(confidence['level'])}",
        f"- score: {markdown_safe_line(confidence['overall'])}",
        f"- margin: {markdown_safe_line(confidence['margin'])}",
        "", "## Provider", "",
        f"- requested: {markdown_safe_line(provider['requested'])}",
        f"- used: {markdown_safe_line(provider['used'])}",
        f"- status: {markdown_safe_line(provider['response_status'])}",
        "", "## Execution Graph", "",
        f"- status: {markdown_safe_line(graph['status'])}",
        f"- nodes: {len(graph['nodes'])}",
        f"- edges: {len(graph['edges'])}",
        "", "## Routing Diagnostics", "",
        f"- routing status: {markdown_safe_line(task_pack['routing_status'])}",
        f"- missing capabilities: {markdown_safe_line(', '.join(task_pack['capability_resolution']['missing_capabilities']) or 'none')}",
        f"- missing inputs: {markdown_safe_line(', '.join(task_pack['capability_resolution']['missing_inputs']) or 'none')}",
        "", "## Safety Boundary", "",
        markdown_safe_line(task_pack["host_execution_protocol"]["runtime_boundary"]),
    ])
    return "\n".join(lines)
```

- [ ] **Step 5: Extend the wrapper with opt-in schema selection**

In `task_pack.sh`, initialize `SCHEMA_VERSION=2`, parse only `2` or `3`, parse an optional routing-example path, and pass both flags:

```sh
SCHEMA_VERSION=2
ROUTING_EXAMPLES=catalog/routing-examples.json

case "$1" in
  --schema-version)
    SCHEMA_VERSION=${2:-}
    case "$SCHEMA_VERSION" in 2|3) ;; *) printf '%s\n' "schema version must be 2 or 3" >&2; exit 2 ;; esac
    shift 2
    ;;
  --routing-examples)
    ROUTING_EXAMPLES=${2:-}
    shift 2
    ;;
esac

PYTHONPATH="$PROJECT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" exec python3 -m onecode_skill_sanitizer smart "$TASK" \
  --registry catalog \
  --bundles bundles/index.json \
  --max-skills "$MAX_SKILLS" \
  --schema-version "$SCHEMA_VERSION" \
  --routing-examples "$ROUTING_EXAMPLES" \
  --format "$FORMAT"
```

- [ ] **Step 6: Update the entry Skill after its RED behavior is recorded**

Keep its frontmatter description trigger-only. Update the command contract to state that schema 2 remains default and add:

```bash
safe-agent-router-task-pack "$USER_TASK" --schema-version 3 --format json
```

Document the v3 interpretation rules exactly:

- `none`: continue without loading a specialized catalog Skill.
- `clarify`: ask for the missing distinction; do not substitute an adjacent Skill.
- `incomplete`: report uncovered capability or missing producer.
- `blocked`: stop because policy, trust, or graph validity failed.
- `complete`: follow only the selected Skill nodes and graph edges.

State that semantic shadow scores are advisory, cannot introduce candidates, and do not grant permissions.

- [ ] **Step 7: Run GREEN and frozen defaults**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_task_pack_v3_cli tests.test_router_cli tests.test_cli_boundaries -v
PYTHONPATH=src python3 -m unittest tests.test_task_pack_v2_cli -v
```

Expected: PASS; wrapper default remains schema 2.

- [ ] **Step 8: Commit**

```bash
git add src/onecode_skill_sanitizer/commands.py src/onecode_skill_sanitizer/cli.py src/onecode_skill_sanitizer/rendering.py integrations/skills/safe-agent-router/scripts/task_pack.sh integrations/skills/safe-agent-router/SKILL.md tests/test_task_pack_v3_cli.py tests/test_router_cli.py tests/test_cli_boundaries.py
git commit -m "feat: expose opt-in intelligent router v3"
```

---

### Task 9: Add The Isolated 120-Case Held-Out Dataset

**Files:**
- Create: `evals/high-frequency-skill-selection.json`
- Create: `tests/test_router_eval_v3.py`
- Modify: `src/onecode_skill_sanitizer/router_eval_v3.py`

- [ ] **Step 1: Add failing dataset contract tests**

Create `tests/test_router_eval_v3.py`:

```python
from __future__ import annotations

import json
import unittest
from collections import Counter
from pathlib import Path

from onecode_skill_sanitizer.router_eval_v3 import load_eval_dataset_v3


ROOT = Path(__file__).resolve().parents[1]
EVAL_PATH = ROOT / "evals/high-frequency-skill-selection.json"
EXPECTED_CATEGORIES = {
    "single_positive": 48,
    "near_miss": 24,
    "no_skill": 16,
    "multi_skill": 16,
    "dependency_conflict": 16,
}


class RouterEvalV3Test(unittest.TestCase):
    def test_dataset_has_exact_distribution_and_balanced_splits(self):
        cases = load_eval_dataset_v3(EVAL_PATH)

        self.assertEqual(len(cases), 120)
        self.assertEqual(Counter(case["category"] for case in cases), EXPECTED_CATEGORIES)
        self.assertEqual(Counter(case["split"] for case in cases), {"validation": 60, "final_test": 60})
        for category, count in EXPECTED_CATEGORIES.items():
            self.assertEqual(
                Counter(case["category"] for case in cases if case["split"] == "validation")[category],
                count // 2,
            )
        self.assertEqual(len({case["id"] for case in cases}), 120)
        self.assertEqual(len({" ".join(case["query"].casefold().split()) for case in cases}), 120)

    def test_dataset_is_independently_labeled_and_not_runtime_loaded(self):
        payload = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
        self.assertEqual(payload["labeling"]["method"], "manual_review")
        self.assertEqual(payload["labeling"]["generated_from_router"], False)
        runtime_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (ROOT / "src/onecode_skill_sanitizer").glob("*.py")
            if path.name != "router_eval_v3.py"
        )
        self.assertNotIn("high-frequency-skill-selection.json", runtime_text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run RED**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_router_eval_v3 -v
```

Expected: FAIL because the dataset and strict loader are missing.

- [ ] **Step 3: Create the static held-out dataset**

Create a static JSON object with top-level fields `schema_version`, `cohort`, `labeling`, and `cases`. Set labeling to:

```json
{
  "method": "manual_review",
  "reviewer_role": "independent_dataset_review",
  "generated_from_router": false,
  "reviewed_at": "2026-07-15",
  "runtime_examples_visible_during_labeling": false
}
```

Every case has exactly:

```json
{
  "id": "hf-single-001",
  "split": "validation",
  "category": "single_positive",
  "query": "Map this unfamiliar monorepo before changing authentication.",
  "expected_need": "single",
  "expected_intents": ["code.explore"],
  "required_skills": ["codebase-explore-map"],
  "allowed_skills": [],
  "forbidden_skills": ["code-review-risk"],
  "expected_dependency_edges": [],
  "expected_status": "complete",
  "expected_reason": ""
}
```

Use IDs `hf-single-001` through `hf-single-048`, `hf-near-001` through `hf-near-024`, `hf-none-001` through `hf-none-016`, `hf-multi-001` through `hf-multi-016`, and `hf-dependency-001` through `hf-dependency-016`. Odd-numbered cases in every category are `validation`; even-numbered cases are `final_test`. Use the following exact query and label matrix; `A -> B` means the expected dependency edge `[A, B]`.

Single positives, 48 rows:

| Range | Required Skill | Queries in order |
| --- | --- | --- |
| 001-007 | codebase-explore-map | Map this unfamiliar monorepo before changing authentication.; 先找出这个陌生仓库的启动入口和模块边界。; Where is tenant validation owned and what consumes it?; Give me a compact repository map for this legacy service.; 这个 repo 太陌生，先梳理路由、状态和测试入口。; Trace the config data flow without reviewing a diff.; repo map pls, need entrypoints + owners before edits |
| 008-014 | code-review-risk | Review this patch for reachable correctness bugs.; 审查这个 PR 的回归风险和缺失测试。; Find defects in the supplied diff, findings only.; Check this change for concurrency and cleanup regressions.; 只评审补丁，不要直接实现修复。; risk-review the code delta for broken defaults; 看看这次代码变更有没有真实可触发的问题 |
| 015-021 | code-test-regression | Add a regression test for the parser bug.; 为已确认的缓存缺陷补失败用例。; Prove the old behavior fails before fixing it.; Choose the smallest reliable test boundary for this regression.; 只补测试覆盖，不做通用代码审查。; need a red-green regression case for this fix; 给这个 feature 补 contract test 和失败断言 |
| 022-028 | execution-browser-check | Run the checkout flow in a real browser.; 用浏览器检查表单并截图。; Smoke test this route and visible DOM state.; Playwright-check mobile navigation, no design critique.; 打开本地页面验证 URL、焦点和报错状态。; browser QA pls: login redirect + screenshot; 验证 canvas 不是空白并记录控制台错误 |
| 029-035 | research-source-check | Verify these claims against primary sources.; 全网搜索并用官方资料核实这组事实。; Check whether this statistic is current and cite it.; Find the applicable standard and map each claim to evidence.; 需要一手来源、发布日期和明确引用。; fact check this announcement, sources pls; 比较权威来源对这个争议数据的定义 |
| 036-042 | design-ui-review | Review the dashboard hierarchy and spacing.; 优化这个后台页面的视觉一致性。; Check UI states, typography, and accessibility.; Polish the responsive layout without opening a browser.; 评审移动端信息层级和内容溢出。; UI critique: density, surfaces, empty states; 让现有界面更专业但保留业务逻辑 |
| 043-048 | security-supply-chain-review | Audit this package before adoption.; 引入社区 Skill 前检查来源和许可证。; Review the plugin's install scripts and maintainer risk.; Check dependency provenance and update-chain exposure.; 评估这个 connector 的权限与供应链风险。; npm package trust review before install |

Near misses, 24 rows:

| ID | Query | Required | Forbidden |
| --- | --- | --- | --- |
| 001 | Repo is mapped; inspect only the current diff for defects. | code-review-risk | codebase-explore-map |
| 002 | 不用评审代码，只为已知 bug 补回归测试。 | code-test-regression | code-review-risk |
| 003 | Run the UI flow; do not critique its visual design. | execution-browser-check | design-ui-review |
| 004 | 不开浏览器，只评审页面层级、间距和状态。 | design-ui-review | execution-browser-check |
| 005 | Search local source ownership, not the public web. | codebase-explore-map | research-source-check |
| 006 | Verify the claim, not package provenance. | research-source-check | security-supply-chain-review |
| 007 | Audit dependency provenance, not general source correctness. | security-supply-chain-review | code-review-risk |
| 008 | Explain test strategy; do not create regression coverage. | none | code-test-regression |
| 009 | Screenshot is attached; critique visual hierarchy only. | design-ui-review | execution-browser-check |
| 010 | UI is approved; browser-smoke the form behavior only. | execution-browser-check | design-ui-review |
| 011 | 查仓库中的调用链，不需要联网查资料。 | codebase-explore-map | research-source-check |
| 012 | 查官方资料核实事实，不检查本地代码结构。 | research-source-check | codebase-explore-map |
| 013 | Review the PR; do not add or run tests. | code-review-risk | code-test-regression |
| 014 | Add the failing test; do not review unrelated diff lines. | code-test-regression | code-review-risk |
| 015 | Map architecture first; there is no patch to review yet. | codebase-explore-map | code-review-risk |
| 016 | A package name appears in prose; verify the factual claim only. | research-source-check | security-supply-chain-review |
| 017 | npm audit the source and license; no implementation review. | security-supply-chain-review | code-review-risk |
| 018 | 检查按钮在浏览器能否点击，不做视觉重设计。 | execution-browser-check | design-ui-review |
| 019 | 评审配色与布局，不执行真实浏览器。 | design-ui-review | execution-browser-check |
| 020 | This is a repository orientation request, not a code review. | codebase-explore-map | code-review-risk |
| 021 | Code review findings are ready; only write regression coverage. | code-test-regression | code-review-risk |
| 022 | Tests already pass; only review the risky diff. | code-review-risk | code-test-regression |
| 023 | Validate a vendor claim with citations, not its package scripts. | research-source-check | security-supply-chain-review |
| 024 | Validate package trust and permissions, not marketing claims. | security-supply-chain-review | research-source-check |

No-Skill, negation, and explanation-only, 16 rows: use queries `hi`, `谢谢`, `What time is it?`, `Explain what code-review-risk does; do not invoke it.`, `列出七个高频 Skill，不要执行。`, `Do not use any skill; return the word yes.`, `什么是浏览器检查 Skill？只解释。`, `Inventory the available skill names only.`, `Earlier we wanted UI review. Current request: say hello only.`, `不要研究来源，也不要检查供应链。`, `Explain the difference between design-ui-review and execution-browser-check.`, `Which skill would handle tests? Answer conceptually.`, `No browser, no design review, no code work; acknowledge receipt.`, `仅说明 safe-agent-router 的作用。`, `Summarize this sentence: skills are methods.`, and `确认`. Required skills are empty; forbidden skills are every named Skill mentioned by the query, or all seven for broad exclusions; status is `none`; reason is `explanation_only`, `inventory_only`, `all_candidates_excluded`, or `no_specialized_need` as applicable.

Multi-Skill, 16 rows:

| ID | Query | Required Skills |
| --- | --- | --- |
| 001 | Map the unfamiliar repo and review the auth patch. | codebase-explore-map, code-review-risk |
| 002 | 审查代码并为确认的问题补回归测试。 | code-review-risk, code-test-regression |
| 003 | Polish the UI and browser-check the final flow. | design-ui-review, execution-browser-check |
| 004 | Research the package and audit its supply chain. | research-source-check, security-supply-chain-review |
| 005 | 梳理仓库并为目标行为设计回归测试。 | codebase-explore-map, code-test-regression |
| 006 | Review UI quality and verify related claims with sources. | design-ui-review, research-source-check |
| 007 | Review the patch and smoke test its browser-visible behavior. | code-review-risk, execution-browser-check |
| 008 | 查证社区 Skill 的来源并做供应链风险审计。 | research-source-check, security-supply-chain-review |
| 009 | Map repo ownership, review the diff, and add regression tests. | codebase-explore-map, code-review-risk, code-test-regression |
| 010 | 优化页面、浏览器验证，并记录回归测试证据。 | design-ui-review, execution-browser-check, code-test-regression |
| 011 | Research primary sources, review package trust, and map its local integration. | research-source-check, security-supply-chain-review, codebase-explore-map |
| 012 | Review code and UI, then verify the visible state in browser. | code-review-risk, design-ui-review, execution-browser-check |
| 013 | repo map + regression test plan, no general review | codebase-explore-map, code-test-regression |
| 014 | PR risk review plus citation check for changed public claims | code-review-risk, research-source-check |
| 015 | 评审 UI 与代码风险，但不运行浏览器。 | design-ui-review, code-review-risk |
| 016 | Audit dependency trust and add a regression test for its adapter. | security-supply-chain-review, code-test-regression |

Dependency/conflict, 16 rows:

| ID | Query | Required Skills | Edge or reason |
| --- | --- | --- | --- |
| 001 | First map the repo, then review the patch. | codebase-explore-map, code-review-risk | codebase-explore-map -> code-review-risk |
| 002 | 先评审缺陷，确认后再补回归测试。 | code-review-risk, code-test-regression | code-review-risk -> code-test-regression |
| 003 | Review the UI, then browser-check the approved result. | design-ui-review, execution-browser-check | design-ui-review -> execution-browser-check |
| 004 | 先查一手来源，再审计社区包的供应链。 | research-source-check, security-supply-chain-review | research-source-check -> security-supply-chain-review |
| 005 | Map, then test, then browser-check the fixed page. | codebase-explore-map, code-test-regression, execution-browser-check | two chain edges |
| 006 | Review code first; after findings, review the affected UI. | code-review-risk, design-ui-review | code-review-risk -> design-ui-review |
| 007 | Verify the vendor claims before deciding package trust. | research-source-check, security-supply-chain-review | research-source-check -> security-supply-chain-review |
| 008 | 浏览器复现后，再补针对该行为的回归测试。 | execution-browser-check, code-test-regression | execution-browser-check -> code-test-regression |
| 009 | Check the UI. | none | clarify: adjacent_capability_ambiguous |
| 010 | 看一下这个变更。 | none | clarify: adjacent_capability_ambiguous |
| 011 | Use design-ui-review and do not use design-ui-review. | none | clarify: conflicting_explicit_constraint |
| 012 | Review the package, but it is unclear whether this means claims or provenance. | none | clarify: adjacent_capability_ambiguous |
| 013 | Browser-check the route, but the target page and URL are missing. | execution-browser-check | incomplete: missing_required_input |
| 014 | Add regression coverage, but the behavior under test is unknown. | code-test-regression | incomplete: missing_required_input |
| 015 | Review the code, then add regression tests, then browser-check the result. | code-review-risk, code-test-regression, execution-browser-check | two chain edges |
| 016 | Research the claims, then audit package trust, then add adapter regression coverage. | research-source-check, security-supply-chain-review, code-test-regression | two chain edges |

- [ ] **Step 4: Implement the strict dataset loader**

Replace the loader feature error in `router_eval_v3.py` with this strict contract. Do not import this module from runtime modules.

```python
from collections import Counter
import json

from .skill_candidates import HIGH_FREQUENCY_ENTRY_NAMES, HIGH_FREQUENCY_SKILL_NAMES


CASE_KEYS = {
    "id", "split", "category", "query", "expected_need", "expected_intents",
    "required_skills", "allowed_skills", "forbidden_skills",
    "expected_dependency_edges", "expected_status", "expected_reason",
}
CATEGORY_COUNTS = {
    "single_positive": 48,
    "near_miss": 24,
    "no_skill": 16,
    "multi_skill": 16,
    "dependency_conflict": 16,
}
NEED_VALUES = {"none", "single", "composite", "clarify"}
STATUS_VALUES = {"none", "complete", "clarify", "incomplete", "blocked"}


class DatasetValidationError(ValueError):
    pass


def load_eval_dataset_v3(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or set(payload) != {
        "schema_version", "cohort", "labeling", "cases"
    }:
        raise DatasetValidationError("v3 dataset has an invalid top-level contract")
    if payload["schema_version"] != 1:
        raise DatasetValidationError("v3 dataset schema_version must be 1")
    if payload["cohort"] != {
        "entry_names": list(HIGH_FREQUENCY_ENTRY_NAMES),
        "candidate_names": list(HIGH_FREQUENCY_SKILL_NAMES),
    }:
        raise DatasetValidationError("v3 dataset cohort does not match the fixed scope")
    if payload["labeling"] != {
        "method": "manual_review",
        "reviewer_role": "independent_dataset_review",
        "generated_from_router": False,
        "reviewed_at": "2026-07-15",
        "runtime_examples_visible_during_labeling": False,
    }:
        raise DatasetValidationError("v3 dataset labeling metadata is invalid")
    cases = payload["cases"]
    if not isinstance(cases, list):
        raise DatasetValidationError("v3 dataset cases must be a list")
    seen_ids: set[str] = set()
    seen_queries: set[str] = set()
    for index, case in enumerate(cases):
        _validate_eval_case(case, index, seen_ids, seen_queries)
    if len(cases) != 120 or Counter(case["category"] for case in cases) != CATEGORY_COUNTS:
        raise DatasetValidationError("v3 dataset count or category distribution is invalid")
    if Counter(case["split"] for case in cases) != {"validation": 60, "final_test": 60}:
        raise DatasetValidationError("v3 dataset split distribution is invalid")
    for category, count in CATEGORY_COUNTS.items():
        for split in ("validation", "final_test"):
            actual = sum(
                case["category"] == category and case["split"] == split
                for case in cases
            )
            if actual != count // 2:
                raise DatasetValidationError(
                    f"v3 dataset category {category} is not balanced across {split}"
                )
    return cases


def _validate_eval_case(
    case: Any,
    index: int,
    seen_ids: set[str],
    seen_queries: set[str],
) -> None:
    prefix = f"case[{index}]"
    if not isinstance(case, dict) or set(case) != CASE_KEYS:
        raise DatasetValidationError(f"{prefix} has an invalid field set")
    case_id = case["id"]
    if not isinstance(case_id, str) or not case_id or case_id in seen_ids:
        raise DatasetValidationError(f"{prefix}.id must be unique")
    query = case["query"]
    normalized_query = " ".join(query.casefold().split()) if isinstance(query, str) else ""
    if not normalized_query or normalized_query in seen_queries:
        raise DatasetValidationError(f"{prefix}.query must be unique")
    if case["split"] not in {"validation", "final_test"}:
        raise DatasetValidationError(f"{prefix}.split is invalid")
    if case["category"] not in CATEGORY_COUNTS:
        raise DatasetValidationError(f"{prefix}.category is invalid")
    if case["expected_need"] not in NEED_VALUES or case["expected_status"] not in STATUS_VALUES:
        raise DatasetValidationError(f"{prefix} need or status is invalid")
    _case_string_list(case["expected_intents"], f"{prefix}.expected_intents")
    required = _case_string_list(case["required_skills"], f"{prefix}.required_skills")
    allowed = _case_string_list(case["allowed_skills"], f"{prefix}.allowed_skills")
    forbidden = _case_string_list(case["forbidden_skills"], f"{prefix}.forbidden_skills")
    if not set(required + allowed + forbidden).issubset(HIGH_FREQUENCY_SKILL_NAMES):
        raise DatasetValidationError(f"{prefix} references an out-of-cohort candidate")
    if set(required) & set(forbidden) or set(allowed) & set(forbidden):
        raise DatasetValidationError(f"{prefix} required or allowed labels overlap forbidden labels")
    edges = case["expected_dependency_edges"]
    if not isinstance(edges, list):
        raise DatasetValidationError(f"{prefix}.expected_dependency_edges must be a list")
    normalized_edges: list[tuple[str, str]] = []
    for edge in edges:
        if not isinstance(edge, list) or len(edge) != 2 or any(
            not isinstance(endpoint, str) or not endpoint for endpoint in edge
        ):
            raise DatasetValidationError(f"{prefix} has a malformed dependency edge")
        pair = (edge[0], edge[1])
        if pair[0] == pair[1] or not set(pair).issubset(required):
            raise DatasetValidationError(f"{prefix} dependency edge endpoints are invalid")
        normalized_edges.append(pair)
    if len(normalized_edges) != len(set(normalized_edges)):
        raise DatasetValidationError(f"{prefix} dependency edges contain duplicates")
    if not isinstance(case["expected_reason"], str):
        raise DatasetValidationError(f"{prefix}.expected_reason must be a string")
    coherent = {
        "none": case["expected_need"] == "none",
        "clarify": case["expected_need"] == "clarify",
        "complete": case["expected_need"] in {"single", "composite"},
        "incomplete": case["expected_need"] in {"single", "composite"},
        "blocked": True,
    }[case["expected_status"]]
    if not coherent:
        raise DatasetValidationError(f"{prefix} need and status are incoherent")
    if case["expected_status"] in {"clarify", "incomplete", "blocked"} and not case["expected_reason"]:
        raise DatasetValidationError(f"{prefix} must name the non-complete reason")
    seen_ids.add(case_id)
    seen_queries.add(normalized_query)


def _case_string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise DatasetValidationError(f"{field} must contain nonempty strings")
    if len(value) != len(set(value)):
        raise DatasetValidationError(f"{field} must not contain duplicates")
    return value
```

- [ ] **Step 5: Run GREEN and commit**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_router_eval_v3 -v
python3 -m json.tool evals/high-frequency-skill-selection.json >/dev/null
```

Expected: PASS with exactly 120 independently labeled cases.

```bash
git add evals/high-frequency-skill-selection.json src/onecode_skill_sanitizer/router_eval_v3.py tests/test_router_eval_v3.py
git commit -m "test: add held-out high-frequency routing evaluation"
```

---

### Task 10: Implement V3 Metrics, CLI, And Acceptance Gates

**Files:**
- Modify: `src/onecode_skill_sanitizer/router_eval_v3.py`
- Modify: `src/onecode_skill_sanitizer/commands.py`
- Modify: `src/onecode_skill_sanitizer/cli.py`
- Modify: `tests/test_router_eval_v3.py`

- [ ] **Step 1: Add failing metric and gate tests**

Add this synthetic metric test to `tests/test_router_eval_v3.py`:

```python
from onecode_skill_sanitizer.router_eval_v3 import evaluate_router_v3


    def test_metric_math_uses_micro_counts_and_finite_empty_denominators(self):
        cases = [
            {
                "id": "multi", "split": "validation", "category": "multi_skill",
                "query": "review and test", "expected_need": "composite",
                "expected_intents": ["code.review", "code.test"],
                "required_skills": ["code-review-risk", "code-test-regression"],
                "allowed_skills": [], "forbidden_skills": ["execution-browser-check"],
                "expected_dependency_edges": [["code-review-risk", "code-test-regression"]],
                "expected_status": "complete", "expected_reason": "",
            },
            {
                "id": "none", "split": "validation", "category": "no_skill",
                "query": "hi", "expected_need": "none", "expected_intents": [],
                "required_skills": [], "allowed_skills": [],
                "forbidden_skills": ["design-ui-review"],
                "expected_dependency_edges": [], "expected_status": "none",
                "expected_reason": "no_specialized_need",
            },
        ]
        routes = {
            "multi": {
                "routing_status": "complete",
                "need_decision": {"decision": "composite", "required_capabilities": ["code.review", "code.test"]},
                "candidates": [
                    {"skill": "code-review-risk", "final_score": 0.9},
                    {"skill": "execution-browser-check", "final_score": 0.8},
                    {"skill": "code-test-regression", "final_score": 0.7},
                ],
                "selection": {"selected_skills": [
                    {"name": "code-review-risk"}, {"name": "execution-browser-check"},
                ], "clarification_reason": "", "abstention_reason": ""},
                "execution_graph": {
                    "status": "ready", "acyclic": True,
                    "nodes": [
                        {"id": "skill:code-review-risk", "skill": "code-review-risk"},
                        {"id": "skill:execution-browser-check", "skill": "execution-browser-check"},
                    ],
                    "edges": [], "reason_codes": [],
                },
            },
            "none": {
                "routing_status": "none",
                "need_decision": {"decision": "none", "required_capabilities": []},
                "candidates": [],
                "selection": {"selected_skills": [], "clarification_reason": "", "abstention_reason": "no_specialized_need"},
                "execution_graph": {
                    "status": "ready", "acyclic": True, "nodes": [], "edges": [], "reason_codes": [],
                },
            },
        }
        report = evaluate_router_v3(cases, route_builder=lambda case: routes[case["id"]])

        self.assertEqual(report["metrics"]["skill_precision"], 0.5)
        self.assertEqual(report["metrics"]["skill_recall"], 0.5)
        self.assertEqual(report["metrics"]["skill_f1"], 0.5)
        self.assertEqual(report["metrics"]["recall_at_3"], 1.0)
        self.assertEqual(report["metrics"]["top_1_accuracy"], 1.0)
        self.assertEqual(report["metrics"]["no_skill_accuracy"], 1.0)
        self.assertEqual(report["metrics"]["exact_selected_set_accuracy"], 0.5)
        self.assertEqual(report["metrics"]["multi_intent_exact_match"], 1.0)
        self.assertEqual(report["metrics"]["forbidden_skill_false_positive_rate"], 0.5)
        self.assertEqual(report["metrics"]["dependency_edge_recall"], 0.0)
        self.assertEqual(report["metrics"]["dag_validity"], 1.0)
        json.dumps(report, allow_nan=False)
```

Add a gate test with exact boundaries:

```python
from onecode_skill_sanitizer.router_eval_v3 import acceptance_gate


    def test_acceptance_gate_uses_confirmed_thresholds(self):
        passing = {
            "forbidden_skill_false_positive_rate": 0.019,
            "forbidden_scenario_false_positive_rate": 0.019,
            "dag_validity": 0.98,
            "dependency_edge_recall": 0.70,
            "multi_intent_exact_match": 0.92,
            "scenario_f1": 0.96,
            "skill_f1": 0.96,
            "recall_at_3": 0.95,
            "top_1_accuracy": 0.90,
            "no_skill_accuracy": 0.90,
            "exact_selected_set_accuracy": 0.85,
        }
        self.assertEqual(acceptance_gate(passing)["status"], "passed")
        failing = dict(passing, forbidden_skill_false_positive_rate=0.02)
        self.assertEqual(acceptance_gate(failing)["status"], "failed")
```

- [ ] **Step 2: Run RED**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_router_eval_v3 -v
```

Expected: FAIL because metric and gate functions are missing.

- [ ] **Step 3: Implement deterministic evaluation**

Implement `evaluate_router_v3` by comparing each case with `need_decision`, ordered `candidates`, `selection.selected_skills`, `execution_graph`, and `routing_status`. Treat malformed output, unknown candidate names, duplicated Skill names, invalid graph endpoints, non-finite scores, and unexpected cycles as evaluator errors rather than ordinary misses.

Use these exact threshold operators. `scenario_f1` is the legacy acceptance name for v3 intent/capability-set F1, while `skill_f1` measures the selected Skill names. `forbidden_scenario_false_positive_rate` is a compatibility alias for the cohort forbidden-Skill rate because v3 no longer emits scenario selections.

```python
ACCEPTANCE_THRESHOLDS = {
    "forbidden_skill_false_positive_rate": ("lt", 0.02),
    "forbidden_scenario_false_positive_rate": ("lt", 0.02),
    "dag_validity": ("ge", 0.98),
    "dependency_edge_recall": ("ge", 0.70),
    "multi_intent_exact_match": ("ge", 0.92),
    "scenario_f1": ("ge", 0.96),
    "skill_f1": ("ge", 0.96),
    "recall_at_3": ("ge", 0.95),
    "top_1_accuracy": ("ge", 0.90),
    "no_skill_accuracy": ("ge", 0.90),
    "exact_selected_set_accuracy": ("ge", 0.85),
}


class EvaluatorError(ValueError):
    pass


def evaluate_router_v3(
    cases: list[dict[str, Any]],
    route_builder: Callable[[dict[str, Any]], dict[str, Any]],
    *,
    redact_expected_labels: bool = False,
) -> dict[str, Any]:
    scored = []
    for case in cases:
        route = route_builder(case)
        scored.append(_score_case(case, route))
    metrics = _aggregate_metrics(scored)
    by_category = {
        category: _aggregate_metrics([item for item in scored if item["category"] == category])
        for category in sorted({item["category"] for item in scored})
    }
    by_split = {
        split: _aggregate_metrics([item for item in scored if item["split"] == split])
        for split in sorted({item["split"] for item in scored})
    }
    cases_out = []
    for item in scored:
        if redact_expected_labels:
            dimensions = []
            if item["expected_need"] != item["actual_need"]:
                dimensions.append("need_decision")
            if item["expected_status"] != item["actual_status"]:
                dimensions.append("routing_status")
            if set(item["required_skills"]) - set(item["actual_skills"]):
                dimensions.append("required_skill_recall")
            if set(item["actual_skills"]) & set(item["forbidden_skills"]):
                dimensions.append("forbidden_skill")
            if set(map(tuple, item["expected_edges"])) - set(map(tuple, item["actual_edges"])):
                dimensions.append("dependency_edge")
            cases_out.append({
                "id": item["id"], "category": item["category"],
                "passed": item["passed"], "failure_dimensions": dimensions,
            })
        else:
            cases_out.append(item)
    return {
        "status": "ok",
        "case_count": len(scored),
        "metrics": metrics,
        "metrics_by_category": by_category,
        "metrics_by_split": by_split,
        "acceptance": acceptance_gate(metrics),
        "cases": cases_out,
    }


def acceptance_gate(metrics: dict[str, float]) -> dict[str, Any]:
    checks = []
    for name, (operator, threshold) in ACCEPTANCE_THRESHOLDS.items():
        value = metrics.get(name)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            passed = False
        else:
            passed = value < threshold if operator == "lt" else value >= threshold
        checks.append({
            "metric": name, "operator": operator, "threshold": threshold,
            "value": value, "passed": passed,
        })
    return {"status": "passed" if all(item["passed"] for item in checks) else "failed", "checks": checks}


def _score_case(case: dict[str, Any], route: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(route, dict):
        raise EvaluatorError("route must be an object")
    need = route.get("need_decision")
    selection = route.get("selection")
    graph = route.get("execution_graph")
    candidates = route.get("candidates")
    if not all(isinstance(item, expected) for item, expected in (
        (need, dict), (selection, dict), (graph, dict), (candidates, list)
    )):
        raise EvaluatorError("route is missing a v3 routing record")
    candidate_names = [item.get("skill") for item in candidates if isinstance(item, dict)]
    if (
        len(candidate_names) != len(candidates)
        or any(not isinstance(name, str) or not name for name in candidate_names)
        or len(candidate_names) != len(set(candidate_names))
    ):
        raise EvaluatorError("candidate names must be unique strings")
    for item in candidates:
        score = item.get("final_score")
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score):
            raise EvaluatorError("candidate final scores must be finite numbers")
    selected_items = selection.get("selected_skills")
    if not isinstance(selected_items, list):
        raise EvaluatorError("selection.selected_skills must be a list")
    actual_skills = [item.get("name") for item in selected_items if isinstance(item, dict)]
    if (
        len(actual_skills) != len(selected_items)
        or any(not isinstance(name, str) or not name for name in actual_skills)
        or len(actual_skills) != len(set(actual_skills))
    ):
        raise EvaluatorError("selected Skill names must be unique strings")
    if not set(actual_skills).issubset(HIGH_FREQUENCY_SKILL_NAMES):
        raise EvaluatorError("selected Skills must remain inside the cohort")
    actual_intents = need.get("required_capabilities")
    if not isinstance(actual_intents, list) or any(not isinstance(item, str) for item in actual_intents):
        raise EvaluatorError("need capabilities must be strings")
    actual_edges, dag_valid = _skill_edges_and_dag(graph)
    required = set(case["required_skills"])
    allowed = set(case["allowed_skills"])
    selected = set(actual_skills)
    forbidden = set(case["forbidden_skills"])
    expected_edges = {tuple(edge) for edge in case["expected_dependency_edges"]}
    top_three = candidate_names[:3]
    expected_intents = set(case["expected_intents"])
    reason = (
        selection.get("clarification_reason")
        or selection.get("abstention_reason")
        or selection.get("failure_reason")
        or ""
    )
    passed = (
        required.issubset(selected)
        and selected.issubset(required | allowed)
        and not selected & forbidden
        and route.get("routing_status") == case["expected_status"]
        and (not case["expected_reason"] or reason == case["expected_reason"])
        and expected_edges.issubset(actual_edges)
    )
    return {
        "id": case["id"], "category": case["category"], "split": case["split"],
        "passed": passed,
        "required_skills": sorted(required), "allowed_skills": sorted(allowed),
        "forbidden_skills": sorted(forbidden), "actual_skills": actual_skills,
        "expected_intents": sorted(expected_intents), "actual_intents": sorted(set(actual_intents)),
        "expected_need": case["expected_need"], "actual_need": need.get("decision"),
        "expected_status": case["expected_status"], "actual_status": route.get("routing_status"),
        "expected_reason": case["expected_reason"], "actual_reason": reason,
        "top_three": top_three, "actual_edges": sorted(actual_edges),
        "expected_edges": sorted(expected_edges), "dag_valid": dag_valid,
    }


def _aggregate_metrics(items: list[dict[str, Any]]) -> dict[str, float]:
    if not items:
        return {name: 1.0 for name in (
            "skill_precision", "skill_recall", "skill_f1", "scenario_f1", "recall_at_3",
            "top_1_accuracy", "mean_reciprocal_rank", "no_skill_accuracy",
            "exact_selected_set_accuracy", "multi_intent_exact_match",
            "forbidden_skill_false_positive_rate", "forbidden_scenario_false_positive_rate",
            "dependency_edge_recall", "dag_validity", "status_accuracy",
        )}
    true_positive = false_positive = false_negative = 0
    intent_tp = intent_fp = intent_fn = 0
    recalled_at_three = required_total = 0
    reciprocal_rank_total = positive_case_count = top_one_correct = 0.0
    no_skill_total = no_skill_correct = 0
    exact = multi_total = multi_exact = 0
    forbidden_total = forbidden_hits = 0
    dependency_total = dependency_hits = 0
    dag_valid = status_correct = 0
    for item in items:
        required = set(item["required_skills"])
        allowed = set(item["allowed_skills"])
        actual = set(item["actual_skills"])
        accepted = required | allowed
        true_positive += len(actual & accepted)
        false_positive += len(actual - accepted)
        false_negative += len(required - actual)
        expected_intents = set(item["expected_intents"])
        actual_intents = set(item["actual_intents"])
        intent_tp += len(expected_intents & actual_intents)
        intent_fp += len(actual_intents - expected_intents)
        intent_fn += len(expected_intents - actual_intents)
        if required:
            positive_case_count += 1
            top_one_correct += bool(item["top_three"] and item["top_three"][0] in accepted)
            for skill in required:
                required_total += 1
                if skill in item["top_three"]:
                    recalled_at_three += 1
                    reciprocal_rank_total += 1 / (item["top_three"].index(skill) + 1)
        if item["expected_need"] == "none":
            no_skill_total += 1
            no_skill_correct += item["actual_need"] == "none"
        exact += required.issubset(actual) and actual.issubset(accepted)
        if len(item["expected_intents"]) > 1:
            multi_total += 1
            multi_exact += set(item["expected_intents"]) == set(item["actual_intents"])
        forbidden = set(item["forbidden_skills"])
        forbidden_total += len(forbidden)
        forbidden_hits += len(actual & forbidden)
        expected_edges = {tuple(edge) for edge in item["expected_edges"]}
        actual_edges = {tuple(edge) for edge in item["actual_edges"]}
        dependency_total += len(expected_edges)
        dependency_hits += len(expected_edges & actual_edges)
        dag_valid += item["dag_valid"]
        status_correct += item["expected_status"] == item["actual_status"]
    precision = _ratio(true_positive, true_positive + false_positive, 1.0)
    recall = _ratio(true_positive, true_positive + false_negative, 1.0)
    intent_precision = _ratio(intent_tp, intent_tp + intent_fp, 1.0)
    intent_recall = _ratio(intent_tp, intent_tp + intent_fn, 1.0)
    forbidden_rate = _ratio(forbidden_hits, forbidden_total, 0.0)
    return {
        "skill_precision": precision,
        "skill_recall": recall,
        "skill_f1": _f1(precision, recall),
        "scenario_f1": _f1(intent_precision, intent_recall),
        "recall_at_3": _ratio(recalled_at_three, required_total, 1.0),
        "top_1_accuracy": _ratio(top_one_correct, positive_case_count, 1.0),
        "mean_reciprocal_rank": _ratio(reciprocal_rank_total, required_total, 1.0),
        "no_skill_accuracy": _ratio(no_skill_correct, no_skill_total, 1.0),
        "exact_selected_set_accuracy": exact / len(items),
        "multi_intent_exact_match": _ratio(multi_exact, multi_total, 1.0),
        "forbidden_skill_false_positive_rate": forbidden_rate,
        "forbidden_scenario_false_positive_rate": forbidden_rate,
        "dependency_edge_recall": _ratio(dependency_hits, dependency_total, 1.0),
        "dag_validity": dag_valid / len(items),
        "status_accuracy": status_correct / len(items),
    }


def _skill_edges_and_dag(graph: dict[str, Any]) -> tuple[set[tuple[str, str]], bool]:
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise EvaluatorError("execution graph nodes and edges must be lists")
    skill_by_id = {}
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("id"), str) or not isinstance(node.get("skill"), str):
            raise EvaluatorError("execution graph node is malformed")
        if node["id"] in skill_by_id:
            raise EvaluatorError("execution graph node IDs must be unique")
        skill_by_id[node["id"]] = node["skill"]
    indegree = {node_id: 0 for node_id in skill_by_id}
    outgoing = {node_id: [] for node_id in skill_by_id}
    skill_edges = set()
    for edge in edges:
        if not isinstance(edge, dict) or edge.get("from") not in indegree or edge.get("to") not in indegree:
            raise EvaluatorError("execution graph edge is malformed")
        outgoing[edge["from"]].append(edge["to"])
        indegree[edge["to"]] += 1
        skill_edges.add((skill_by_id[edge["from"]], skill_by_id[edge["to"]]))
    ready = deque(sorted(node_id for node_id, degree in indegree.items() if degree == 0))
    visited = 0
    while ready:
        node_id = ready.popleft()
        visited += 1
        for target in sorted(outgoing[node_id]):
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
    computed = visited == len(indegree)
    declared = graph.get("acyclic")
    if not isinstance(declared, bool):
        raise EvaluatorError("execution graph acyclic must be boolean")
    blocked_cycle = (
        graph.get("status") == "blocked"
        and declared is False
        and "dependency_cycle" in graph.get("reason_codes", [])
        and not nodes and not edges
    )
    return skill_edges, blocked_cycle or declared == computed


def _ratio(numerator: float, denominator: float, empty: float) -> float:
    return empty if denominator == 0 else numerator / denominator


def _f1(precision: float, recall: float) -> float:
    return 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
```

Import `math`, `deque`, and `Callable` at module scope. `--split validation` may be used during calibration. `--split final_test` passes `redact_expected_labels=True`, so neither passing nor failing cases print expected labels.

- [ ] **Step 4: Add `router-eval-v3` command**

Register:

```bash
onecode-skill-sanitizer router-eval-v3 \
  --eval evals/high-frequency-skill-selection.json \
  --registry catalog \
  --bundles bundles/index.json \
  --routing-examples catalog/routing-examples.json \
  --split validation
```

In `commands.py` add:

```python
def router_eval_v3_command(args: argparse.Namespace) -> int:
    try:
        cases = [
            case for case in load_eval_dataset_v3(resolve_project_asset_path(args.eval))
            if case["split"] == args.split
        ]
        registry = resolve_project_asset_path(args.registry)
        bundles = resolve_project_asset_path(args.bundles)
        examples = resolve_project_asset_path(args.routing_examples)
        report = evaluate_router_v3(
            cases,
            route_builder=lambda case: build_task_pack_v3(
                registry, case["query"], bundles, examples
            ),
            redact_expected_labels=args.split == "final_test",
        )
    except (DatasetValidationError, EvaluatorError, OSError, ValueError, SystemExit) as exc:
        print(json.dumps(
            {"status": "error", "error": str(exc)},
            indent=2, sort_keys=True, allow_nan=False,
        ))
        return 2
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    return 0 if report["acceptance"]["status"] == "passed" else 1
```

In `cli.py` register:

```python
router_eval_v3_parser = subparsers.add_parser("router-eval-v3")
router_eval_v3_parser.add_argument("--eval", required=True)
router_eval_v3_parser.add_argument("--registry", default="catalog")
router_eval_v3_parser.add_argument("--bundles", default="bundles/index.json")
router_eval_v3_parser.add_argument("--routing-examples", default="catalog/routing-examples.json")
router_eval_v3_parser.add_argument("--split", choices=["validation", "final_test"], required=True)
router_eval_v3_parser.set_defaults(func=router_eval_v3_command)
```

The command returns `0` only when selected split gates pass, `1` for a valid report with failed quality gates, and `2` for invalid input or evaluator errors. Keep schema 3 opt-in; do not alter `router-eval-v2`.

- [ ] **Step 5: Run GREEN and record the untuned validation baseline**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_router_eval_v3 -v
PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval-v3 --eval evals/high-frequency-skill-selection.json --registry catalog --bundles bundles/index.json --routing-examples catalog/routing-examples.json --split validation
```

Expected: unit tests PASS. The validation command may return `1` at this point; save its JSON output to `/tmp/router-v3-validation-baseline.json` and do not inspect final-test case labels.

- [ ] **Step 6: Calibrate only against reviewed runtime examples and validation cases**

For each validation miss, classify it as `need_gate`, `candidate_recall`, `hard_exclusion`, `composition`, `dependency`, or `confidence`. Change the narrowest owning rule, add a unit regression case before the change, run RED, make the minimal change, and run GREEN. Do not add validation queries verbatim to runtime examples; add a semantically distinct reviewed example only when the miss demonstrates a reusable language pattern. Never open final-test per-case labels during this step.

- [ ] **Step 7: Run final held-out gate once after validation passes**

Run:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval-v3 --eval evals/high-frequency-skill-selection.json --registry catalog --bundles bundles/index.json --routing-examples catalog/routing-examples.json --split final_test
```

Expected: exit `0` with every confirmed metric gate passing. If it returns `1`, record failure categories without copying final-test queries into routing rules; return to a new reviewed design iteration rather than tuning on final labels.

- [ ] **Step 8: Commit**

```bash
git add src/onecode_skill_sanitizer/router_eval_v3.py src/onecode_skill_sanitizer/commands.py src/onecode_skill_sanitizer/cli.py tests/test_router_eval_v3.py catalog/routing-examples.json
git commit -m "feat: enforce intelligent router v3 quality gates"
```

---

### Task 11: Add Task-Level Selected-Pack Versus Oracle Evaluation

**Files:**
- Modify: `src/onecode_skill_sanitizer/router_eval_v3.py`
- Modify: `src/onecode_skill_sanitizer/commands.py`
- Modify: `src/onecode_skill_sanitizer/cli.py`
- Modify: `tests/test_router_eval_v3.py`

- [ ] **Step 1: Add failing task-outcome tests**

Use an external results contract so runtime selection never reads oracle artifacts. Add a test with three arms per case:

```python
from onecode_skill_sanitizer.router_eval_v3 import evaluate_task_outcomes


    def test_task_outcomes_protect_critical_oracle_assertions_and_pass_rate(self):
        outcomes = [
            {
                "case_id": "task-1",
                "assertions": [
                    {"id": "critical-contract", "critical": True, "v3": True, "oracle": True, "no_skill": False},
                    {"id": "secondary-note", "critical": False, "v3": False, "oracle": True, "no_skill": False},
                ],
                "contamination": {"v3_skill_evidence": True, "oracle_skill_evidence": True, "no_skill_skill_evidence": False},
            }
        ]
        report = evaluate_task_outcomes(outcomes)

        self.assertEqual(report["critical_oracle_regressions"], [])
        self.assertEqual(report["v3_pass_rate"], 0.5)
        self.assertEqual(report["oracle_pass_rate"], 1.0)
        self.assertEqual(report["status"], "failed")
```

- [ ] **Step 2: Run RED**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_router_eval_v3.RouterEvalV3Test.test_task_outcomes_protect_critical_oracle_assertions_and_pass_rate -v
```

Expected: FAIL because task outcome evaluation is missing.

- [ ] **Step 3: Implement the isolated outcome evaluator**

`evaluate_task_outcomes` must strictly validate unique case/assertion IDs and booleans; reject no-skill contamination; list any critical assertion where `oracle` is true and `v3` is false; and enforce both:

```python
ratio_gate = v3_pass_rate >= 0.95 * oracle_pass_rate
point_gate = oracle_pass_rate - v3_pass_rate <= 0.05
```

Implement it as:

```python
def evaluate_task_outcomes(outcomes: Any) -> dict[str, Any]:
    if not isinstance(outcomes, list) or not outcomes:
        raise DatasetValidationError("task outcomes must be a nonempty list")
    seen_cases: set[str] = set()
    assertion_count = v3_passed = oracle_passed = 0
    critical_regressions = []
    contaminated_cases = []
    for case_index, outcome in enumerate(outcomes):
        if not isinstance(outcome, dict) or set(outcome) != {
            "case_id", "assertions", "contamination"
        }:
            raise DatasetValidationError(f"task outcome[{case_index}] has invalid fields")
        case_id = outcome["case_id"]
        if not isinstance(case_id, str) or not case_id or case_id in seen_cases:
            raise DatasetValidationError(f"task outcome[{case_index}].case_id must be unique")
        contamination = outcome["contamination"]
        if not isinstance(contamination, dict) or set(contamination) != {
            "v3_skill_evidence", "oracle_skill_evidence", "no_skill_skill_evidence"
        } or any(not isinstance(value, bool) for value in contamination.values()):
            raise DatasetValidationError(f"task outcome[{case_index}] contamination record is invalid")
        if contamination["no_skill_skill_evidence"]:
            contaminated_cases.append(case_id)
        assertions = outcome["assertions"]
        if not isinstance(assertions, list) or not assertions:
            raise DatasetValidationError(f"task outcome[{case_index}] assertions must be nonempty")
        seen_assertions: set[str] = set()
        for assertion_index, assertion in enumerate(assertions):
            if not isinstance(assertion, dict) or set(assertion) != {
                "id", "critical", "v3", "oracle", "no_skill"
            }:
                raise DatasetValidationError(
                    f"task outcome[{case_index}].assertions[{assertion_index}] has invalid fields"
                )
            assertion_id = assertion["id"]
            if not isinstance(assertion_id, str) or not assertion_id or assertion_id in seen_assertions:
                raise DatasetValidationError(
                    f"task outcome[{case_index}] assertion IDs must be unique"
                )
            if any(not isinstance(assertion[field], bool) for field in (
                "critical", "v3", "oracle", "no_skill"
            )):
                raise DatasetValidationError(
                    f"task outcome[{case_index}] assertion outcomes must be booleans"
                )
            assertion_count += 1
            v3_passed += assertion["v3"]
            oracle_passed += assertion["oracle"]
            if assertion["critical"] and assertion["oracle"] and not assertion["v3"]:
                critical_regressions.append({"case_id": case_id, "assertion_id": assertion_id})
            seen_assertions.add(assertion_id)
        seen_cases.add(case_id)
    v3_pass_rate = v3_passed / assertion_count
    oracle_pass_rate = oracle_passed / assertion_count
    ratio_gate = v3_pass_rate >= 0.95 * oracle_pass_rate
    point_gate = oracle_pass_rate - v3_pass_rate <= 0.05
    passed = ratio_gate and point_gate and not critical_regressions and not contaminated_cases
    return {
        "status": "passed" if passed else "failed",
        "case_count": len(outcomes),
        "assertion_count": assertion_count,
        "v3_pass_rate": v3_pass_rate,
        "oracle_pass_rate": oracle_pass_rate,
        "ratio_gate": ratio_gate,
        "percentage_point_gate": point_gate,
        "critical_oracle_regressions": critical_regressions,
        "no_skill_contamination_cases": contaminated_cases,
    }
```

- [ ] **Step 4: Register an evidence-only CLI command**

Register `router-task-eval-v3 --results PATH`. It reads only operator-produced task outcome JSON and never invokes a model, browser, connector, network, account, or production action:

```python
def router_task_eval_v3_command(args: argparse.Namespace) -> int:
    try:
        path = resolve_project_asset_path(args.results)
        outcomes = json.loads(path.read_text(encoding="utf-8"))
        report = evaluate_task_outcomes(outcomes)
    except (json.JSONDecodeError, DatasetValidationError, OSError, ValueError) as exc:
        print(json.dumps(
            {"status": "error", "error": str(exc)},
            indent=2, sort_keys=True, allow_nan=False,
        ))
        return 2
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    return 0 if report["status"] == "passed" else 1
```

```python
router_task_eval_v3_parser = subparsers.add_parser("router-task-eval-v3")
router_task_eval_v3_parser.add_argument("--results", required=True)
router_task_eval_v3_parser.set_defaults(func=router_task_eval_v3_command)
```

Exit codes follow `router-eval-v3`: `0` passed, `1` valid but below gates, `2` invalid evidence.

- [ ] **Step 5: Run GREEN**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_router_eval_v3 -v
```

Expected: PASS.

- [ ] **Step 6: Produce task evidence before enabling semantic influence**

Using the host runtime's separately approved task-execution process, run representative cases in three isolated contexts: v3 selected pack, independently curated oracle pack, and clean no-Skill. Record only assertion booleans and contamination evidence in the strict result format; do not commit private prompts, credentials, user data, or raw agent traces. Run:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer router-task-eval-v3 --results /tmp/router-v3-task-outcomes.json
```

Expected: exit `0`, no critical oracle regression, v3 pass rate at least 95% of oracle, gap at most 5 percentage points, and no-Skill contamination false for every case. If host execution is not separately authorized or evidence is unavailable, leave semantic influence disabled and record `task_evaluation_missing` as the rollout blocker.

- [ ] **Step 7: Commit evaluator code only**

```bash
git add src/onecode_skill_sanitizer/router_eval_v3.py src/onecode_skill_sanitizer/commands.py src/onecode_skill_sanitizer/cli.py tests/test_router_eval_v3.py
git commit -m "feat: compare v3 task outcomes with oracle packs"
```

---

### Task 12: Close Documentation And Release Verification

**Files:**
- Modify: `scripts/verify.sh`
- Modify: `README.md`
- Modify: `docs/router-development.md`
- Modify: `docs/agent-task-pack.md`
- Modify: `docs/index.md`
- Modify: `tests/test_documentation.py`
- Modify: `tests/test_verify_script.py`

- [ ] **Step 1: Add failing verification-script and documentation tests**

Add to `tests/test_verify_script.py`:

```python
    def test_verify_script_runs_v3_schemas_isolation_and_both_held_out_splits(self):
        script = Path("scripts/verify.sh").read_text(encoding="utf-8")

        self.assertIn("schemas/semantic-rerank-response.schema.json", script)
        self.assertIn("schemas/task-pack-v3.schema.json", script)
        self.assertIn("catalog/routing-examples.json", script)
        self.assertIn("evals/high-frequency-skill-selection.json", script)
        self.assertIn("router-eval-v2", script)
        self.assertEqual(script.count("router-eval-v3"), 2)
        self.assertIn("--split validation", script)
        self.assertIn("--split final_test", script)
        self.assertIn("--glob '!router_eval_v3.py'", script)
```

Add to `tests/test_documentation.py`:

```python
    def test_v3_design_and_plan_are_linked_from_documentation_index(self):
        index = (ROOT / "docs/index.md").read_text(encoding="utf-8")
        design = "superpowers/specs/2026-07-15-high-frequency-intelligent-skill-selection-design.md"
        plan = "superpowers/plans/2026-07-15-high-frequency-intelligent-skill-selection.md"

        self.assertIn(design, index)
        self.assertIn(plan, index)
        self.assertTrue((ROOT / "docs" / design).is_file())
        self.assertTrue((ROOT / "docs" / plan).is_file())
```

- [ ] **Step 2: Run RED**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_verify_script tests.test_documentation -v
```

Expected: FAIL because the release script and docs do not reference v3.

- [ ] **Step 3: Extend the release script**

Add these deterministic checks to `scripts/verify.sh` after the existing v2 gate:

```bash
python3 -m json.tool schemas/semantic-rerank-response.schema.json >/dev/null
python3 -m json.tool schemas/task-pack-v3.schema.json >/dev/null
python3 -m json.tool catalog/routing-examples.json >/dev/null
python3 -m json.tool evals/high-frequency-skill-selection.json >/dev/null
PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval-v3 \
  --eval evals/high-frequency-skill-selection.json \
  --registry catalog \
  --bundles bundles/index.json \
  --routing-examples catalog/routing-examples.json \
  --split validation >/dev/null
PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval-v3 \
  --eval evals/high-frequency-skill-selection.json \
  --registry catalog \
  --bundles bundles/index.json \
  --routing-examples catalog/routing-examples.json \
  --split final_test >/dev/null
if command -v rg >/dev/null 2>&1; then
  if rg -n 'high-frequency-skill-selection[.]json' src/onecode_skill_sanitizer \
    --glob '!router_eval_v3.py'; then
    exit 1
  fi
else
  if grep -RInE --exclude='router_eval_v3.py' \
    'high-frequency-skill-selection[.]json' src/onecode_skill_sanitizer; then
    exit 1
  fi
fi
```

Do not add latency, token, or task-pack-size thresholds.

- [ ] **Step 4: Document current rollout truthfully**

Document:

- v3 is opt-in; v2 remains default.
- The intelligent cohort is the router entry plus seven candidates.
- Deterministic selection is active.
- Semantic providers are candidate-bounded and start in shadow mode.
- Influence mode remains unavailable through the public CLI until held-out and task-level gates pass.
- Skills are method guidance, not permission grants.
- Runtime examples are reviewed routing data; the 120 held-out cases are evaluator-only.
- Adding an eighth candidate requires a separate frequency, trust, examples, evaluation, and operator review decision.

- [ ] **Step 5: Run focused GREEN**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_verify_script tests.test_documentation -v
git diff --check
```

Expected: PASS and no whitespace errors.

- [ ] **Step 6: Run the complete release gate**

Use the already prepared dev environment:

```bash
PATH=/tmp/safe-agent-skills-structural-venv/bin:$PATH bash scripts/verify.sh
```

Expected: exit `0`; Ruff passes; all unit tests pass; registry, manifest, provenance, hashes, batches, depth, contracts, docs, v1, v2 100-case evaluation, and v3 120-case gates pass.

- [ ] **Step 7: Review changed scope and safety evidence**

Run:

```bash
git status --short
git diff --stat 13fe4de...HEAD
git diff --check 13fe4de...HEAD
rg -n 'MetaTool|Tool2Vec|OpenSquilla|SkillsBench|skill-scanner|agentskills' pyproject.toml src integrations
```

Expected: only the planned router/cohort/evaluation/docs files changed; no community runtime dependency or source code was imported; no untracked `uv.lock` is added.

- [ ] **Step 8: Commit**

```bash
git add scripts/verify.sh README.md docs/router-development.md docs/agent-task-pack.md docs/index.md tests/test_documentation.py tests/test_verify_script.py
git commit -m "docs: publish intelligent router v3 verification"
```

---

## Final Review Checklist

- [ ] Confirm all eight scoped entries are represented, with exactly seven catalog candidates and no recursive router candidate.
- [ ] Confirm v1 and v2 files, schemas, defaults, fixtures, and metrics are unchanged.
- [ ] Confirm no runtime import or path references `evals/high-frequency-skill-selection.json`.
- [ ] Confirm route identity includes catalog, bundles, reviewed routing examples, cohort, provider identity, normalized current intent, constraints, router version, and package version; it excludes timestamps and raw secrets.
- [ ] Confirm every candidate is trusted, in cohort, evidence-bearing, and unable to appear only through semantic output.
- [ ] Confirm invalid semantic output clears the entire semantic score set and preserves deterministic ordering.
- [ ] Confirm scenario membership and flat `execution_order` never select a Skill or create a dependency edge.
- [ ] Confirm every selected Skill has marginal capability, required artifact, mandatory verification, or explicit-user evidence.
- [ ] Confirm `none`, `clarify`, `incomplete`, and `blocked` never silently substitute an adjacent Skill.
- [ ] Confirm independent Skills remain parallel.
- [ ] Confirm all held-out metrics meet the confirmed thresholds and no final-test label was used for calibration.
- [ ] Confirm task-level oracle evidence passes before any public semantic-influence switch is proposed.
- [ ] Confirm `git diff --check` and `PATH=/tmp/safe-agent-skills-structural-venv/bin:$PATH bash scripts/verify.sh` pass from the feature worktree.

## Expected Deliverable

The finished branch provides an opt-in, auditable Router v3 for the eight-entry high-frequency scope. Its primary improvement is selection quality: fewer false Skill activations, better adjacent-Skill discrimination, minimal exact sets, truthful dependencies, and explicit abstention. It deliberately does not claim faster execution, lower token use, whole-catalog intelligence, semantic-provider autonomy, or additional runtime authority.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-15-high-frequency-intelligent-skill-selection.md`. Two execution options:

1. **Subagent-Driven (recommended)** - Use `superpowers:subagent-driven-development`, dispatch a fresh worker per task, and run specification then code-quality review between tasks.
2. **Inline Execution** - Use `superpowers:executing-plans` in the current worker, execute in reviewed batches, and stop at checkpoints.

Choose one approach before implementation begins.
