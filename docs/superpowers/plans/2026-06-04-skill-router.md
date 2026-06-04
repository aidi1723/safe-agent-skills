# Skill Router Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an opt-in deterministic scenario router for `task-pack` so agents receive scenario-aware skill bundles, capability coverage, execution order, and selection explanations.

**Architecture:** Keep the current simple selector as the compatibility path in `cli.py`. Add a focused `router.py` module that derives task profiles, scores scenario bundles, maps required capabilities to trusted skills, and returns router metadata. `task-pack --router scenario` will call this module after registry verification and before output rendering.

**Tech Stack:** Python 3.11 standard library only, existing `unittest` suite, existing JSON bundle and catalog files, no network calls and no external model calls.

---

## File Structure

- Create `src/onecode_skill_sanitizer/router.py`
  - Owns deterministic scenario routing.
  - Exposes pure functions that are easy to unit test:
    - `normalize_task_text`
    - `build_task_profile`
    - `score_bundle_for_profile`
    - `build_capability_coverage`
    - `build_execution_plan`
    - `build_selection_explanations`
    - `route_scenario_task`
- Modify `src/onecode_skill_sanitizer/cli.py`
  - Add `--router simple|scenario` and `--max-skills`.
  - Keep current behavior for `--router simple`.
  - Add router output fields to `task-pack` for scenario mode.
  - Render router sections in Markdown.
- Modify `bundles/index.json`
  - Add optional `task_signals`, `required_capabilities`, and `execution_order` for current 9 bundles.
  - Preserve current fields and bundle compatibility.
- Modify `docs/agent-task-pack.md`
  - Document `--router scenario`, new output fields, and safety boundary.
- Modify `docs/agent-compatible-skill-bundles.md`
  - Document bundle metadata and cross-agent router use.
- Test `tests/test_registry_cli.py`
  - Add tests for CLI behavior and backward compatibility.
- Create `tests/test_router.py`
  - Add focused pure-function tests for task profiling, bundle scoring, coverage, execution plan, and safety exclusions.

---

### Task 1: Add Router Pure Functions

**Files:**
- Create: `src/onecode_skill_sanitizer/router.py`
- Test: `tests/test_router.py`

- [ ] **Step 1: Write failing router tests**

Create `tests/test_router.py`:

```python
import unittest

from onecode_skill_sanitizer.router import (
    build_capability_coverage,
    build_execution_plan,
    build_selection_explanations,
    build_task_profile,
    route_scenario_task,
    score_bundle_for_profile,
)


class RouterTest(unittest.TestCase):
    def test_build_task_profile_detects_website_launch(self):
        profile = build_task_profile("build a product website and prepare launch checks")

        self.assertEqual(profile["task_type"], "website_build")
        self.assertEqual(profile["primary_domain"], "web")
        self.assertIn("design", profile["secondary_domains"])
        self.assertIn("website", profile["artifact_types"])
        self.assertIn("public_release", profile["risk_flags"])
        self.assertIn("ui_review", profile["required_capabilities"])
        self.assertIn("publish_check", profile["required_capabilities"])

    def test_score_bundle_prefers_matching_scenario(self):
        profile = build_task_profile("review generated code and harden tests before accepting the PR")
        code_bundle = {
            "id": "code-review-hardening",
            "scenario": "Review generated code, pull requests, bug fixes, or automation changes before acceptance.",
            "task_signals": ["code review", "pull request", "generated code", "bug fix", "refactor"],
        }
        website_bundle = {
            "id": "website-build-launch",
            "scenario": "Build or polish a website, landing page, dashboard, or product page.",
            "task_signals": ["website", "landing page", "launch"],
        }

        self.assertGreater(
            score_bundle_for_profile(code_bundle, profile),
            score_bundle_for_profile(website_bundle, profile),
        )

    def test_build_capability_coverage_marks_covered_and_missing(self):
        bundle = {
            "required_capabilities": [
                {
                    "id": "ui_review",
                    "required": True,
                    "preferred_skills": ["design-ui-review"],
                },
                {
                    "id": "seo_copy",
                    "required": True,
                    "preferred_skills": ["content-seo-brief"],
                },
            ]
        }
        skill_names = {"design-ui-review"}

        coverage = build_capability_coverage(bundle, skill_names)

        self.assertEqual(coverage[0]["capability"], "ui_review")
        self.assertEqual(coverage[0]["status"], "covered")
        self.assertEqual(coverage[0]["skill"], "design-ui-review")
        self.assertEqual(coverage[1]["capability"], "seo_copy")
        self.assertEqual(coverage[1]["status"], "missing")
        self.assertEqual(coverage[1]["skill"], "")

    def test_build_execution_plan_uses_bundle_order_and_selected_skills(self):
        bundle = {
            "execution_order": [
                "business-requirements-brief",
                "design-ui-review",
                "content-seo-brief",
            ]
        }
        selected_skills = [
            {"name": "content-seo-brief"},
            {"name": "design-ui-review"},
        ]

        plan = build_execution_plan(bundle, selected_skills)

        self.assertEqual([step["skill"] for step in plan], ["design-ui-review", "content-seo-brief"])
        self.assertEqual(plan[0]["order"], 1)
        self.assertIn("Apply", plan[0]["instruction"])

    def test_build_selection_explanations_assigns_roles(self):
        bundle = {"id": "website-build-launch", "name": "Website Build Launch"}
        coverage = [
            {"capability": "ui_review", "status": "covered", "skill": "design-ui-review"},
            {"capability": "seo_copy", "status": "covered", "skill": "content-seo-brief"},
        ]
        selected_skills = [{"name": "design-ui-review"}, {"name": "content-seo-brief"}]

        explanations = build_selection_explanations(bundle, selected_skills, coverage)

        self.assertEqual(explanations[0]["name"], "website-build-launch")
        self.assertEqual(explanations[0]["type"], "bundle")
        skill_explanations = [item for item in explanations if item["type"] == "skill"]
        self.assertEqual({item["name"] for item in skill_explanations}, {"design-ui-review", "content-seo-brief"})
        self.assertTrue(all(item["confidence"] > 0 for item in skill_explanations))

    def test_route_scenario_task_selects_bundle_skills_first(self):
        bundles_index = {
            "bundles": [
                {
                    "id": "website-build-launch",
                    "name": "Website Build Launch",
                    "scenario": "Build or polish a website and prepare it for release.",
                    "status": "trusted",
                    "task_signals": ["website", "launch"],
                    "skills": ["business-requirements-brief", "design-ui-review", "content-seo-brief"],
                    "required_capabilities": [
                        {"id": "requirements", "required": True, "preferred_skills": ["business-requirements-brief"]},
                        {"id": "ui_review", "required": True, "preferred_skills": ["design-ui-review"]},
                        {"id": "seo_copy", "required": True, "preferred_skills": ["content-seo-brief"]},
                    ],
                    "execution_order": ["business-requirements-brief", "design-ui-review", "content-seo-brief"],
                    "expected_output": ["launch checklist"],
                    "safety_boundary": "Skills provide method only.",
                }
            ]
        }
        selected = [
            {"name": "content-seo-brief", "match_score": 8},
            {"name": "design-ui-review", "match_score": 9},
            {"name": "business-requirements-brief", "match_score": 7},
        ]

        routed = route_scenario_task(
            task="build a product website and prepare launch checks",
            selected_skills=selected,
            bundles_index=bundles_index,
            trusted_skill_names={"business-requirements-brief", "design-ui-review", "content-seo-brief"},
            max_skills=5,
        )

        self.assertEqual(routed["router"]["mode"], "deterministic_scenario_router")
        self.assertEqual(routed["selected_scenario"]["id"], "website-build-launch")
        self.assertEqual([skill["name"] for skill in routed["skills"]], [
            "business-requirements-brief",
            "design-ui-review",
            "content-seo-brief",
        ])
        self.assertEqual([step["skill"] for step in routed["execution_plan"]], [
            "business-requirements-brief",
            "design-ui-review",
            "content-seo-brief",
        ])
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_router -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'onecode_skill_sanitizer.router'` or missing function import errors.

- [ ] **Step 3: Implement router module**

Create `src/onecode_skill_sanitizer/router.py`:

```python
from __future__ import annotations

import re
from typing import Iterable


ROUTER_VERSION = 1


SCENARIO_PROFILES = [
    {
        "task_type": "website_build",
        "primary_domain": "web",
        "secondary_domains": ["business", "design", "content", "engineering", "execution"],
        "artifact_types": ["website", "copy", "release_checklist"],
        "risk_flags": ["public_release"],
        "required_capabilities": [
            "requirements",
            "engineering_release",
            "ui_review",
            "design_consistency",
            "seo_copy",
            "browser_verification",
            "publish_check",
        ],
        "signals": ["website", "landing page", "official site", "dashboard", "launch", "publish"],
    },
    {
        "task_type": "code_review",
        "primary_domain": "code",
        "secondary_domains": ["security", "engineering", "ai"],
        "artifact_types": ["code", "review_report", "test_plan"],
        "risk_flags": ["code_execution", "supply_chain"],
        "required_capabilities": ["code_review", "regression_test", "schema_contract", "supply_chain_review", "ci_check"],
        "signals": ["code review", "pull request", "pr", "generated code", "bug fix", "refactor", "tests"],
    },
    {
        "task_type": "agent_security",
        "primary_domain": "security",
        "secondary_domains": ["ai", "compliance", "execution"],
        "artifact_types": ["agent_policy", "risk_report"],
        "risk_flags": ["prompt_injection", "tool_permission", "privacy"],
        "required_capabilities": ["prompt_injection_review", "output_guardrail", "io_scanning", "privacy_check"],
        "signals": ["prompt injection", "connector", "tool permission", "agent safety", "guardrail", "sandbox"],
    },
    {
        "task_type": "document_knowledge_base",
        "primary_domain": "data",
        "secondary_domains": ["office", "ai", "research"],
        "artifact_types": ["markdown", "chunks", "knowledge_base"],
        "risk_flags": ["source_quality"],
        "required_capabilities": ["file_conversion", "document_partition", "rag_plan", "retrieval", "source_check"],
        "signals": ["pdf", "document", "markdown", "knowledge base", "docs", "office file"],
    },
    {
        "task_type": "rag_agent",
        "primary_domain": "ai",
        "secondary_domains": ["data", "research", "security"],
        "artifact_types": ["rag_design", "retrieval_plan", "citation_contract"],
        "risk_flags": ["source_grounding", "prompt_injection"],
        "required_capabilities": ["agent_orchestration", "rag_plan", "vector_retrieval", "schema_contract", "citation_check"],
        "signals": ["rag", "retrieval", "vector", "citation", "knowledge agent"],
    },
    {
        "task_type": "data_analysis",
        "primary_domain": "data",
        "secondary_domains": ["office", "research"],
        "artifact_types": ["analysis_report", "chart_plan"],
        "risk_flags": ["data_quality"],
        "required_capabilities": ["data_quality", "table_analysis", "visualization", "spreadsheet_cleanup", "source_check"],
        "signals": ["dataset", "spreadsheet", "chart", "data analysis", "table", "report"],
    },
    {
        "task_type": "open_source_release",
        "primary_domain": "execution",
        "secondary_domains": ["security", "compliance", "content", "research"],
        "artifact_types": ["repository", "release_notes", "public_docs"],
        "risk_flags": ["public_release", "license"],
        "required_capabilities": ["publish_check", "supply_chain_review", "license_review", "editorial_review"],
        "signals": ["open source", "release", "github", "publish repo", "public repository"],
    },
    {
        "task_type": "content_seo",
        "primary_domain": "content",
        "secondary_domains": ["research"],
        "artifact_types": ["article", "seo_brief", "social_copy"],
        "risk_flags": ["public_claims"],
        "required_capabilities": ["seo_copy", "editorial_review", "source_check", "social_post"],
        "signals": ["article", "seo", "social", "public content", "blog", "post"],
    },
    {
        "task_type": "commerce_growth",
        "primary_domain": "commerce",
        "secondary_domains": ["content", "business"],
        "artifact_types": ["listing", "keyword_plan", "buyer_reply"],
        "risk_flags": ["buyer_communication"],
        "required_capabilities": ["listing", "keyword_plan", "inquiry_reply", "editorial_review"],
        "signals": ["listing", "keyword", "inquiry", "trade", "buyer", "marketplace"],
    },
]


def normalize_task_text(task: str) -> str:
    text = task.lower().replace("-", " ").replace("_", " ")
    return re.sub(r"\s+", " ", text).strip()


def _signal_score(text: str, signals: Iterable[str]) -> int:
    score = 0
    for signal in signals:
        normalized_signal = normalize_task_text(signal)
        if normalized_signal and normalized_signal in text:
            score += 4 if " " in normalized_signal else 2
    return score


def build_task_profile(task: str) -> dict:
    text = normalize_task_text(task)
    best = max(SCENARIO_PROFILES, key=lambda profile: (_signal_score(text, profile["signals"]), profile["task_type"]))
    score = _signal_score(text, best["signals"])
    if score <= 0:
        best = {
            "task_type": "general",
            "primary_domain": "general",
            "secondary_domains": [],
            "artifact_types": [],
            "risk_flags": [],
            "required_capabilities": [],
            "signals": [],
        }
    return {
        "task_type": best["task_type"],
        "primary_domain": best["primary_domain"],
        "secondary_domains": list(best["secondary_domains"]),
        "artifact_types": list(best["artifact_types"]),
        "risk_flags": list(best["risk_flags"]),
        "required_capabilities": list(best["required_capabilities"]),
        "matched_signal_score": score,
    }


def score_bundle_for_profile(bundle: dict, task_profile: dict) -> int:
    text_parts = [
        bundle.get("id", ""),
        bundle.get("name", ""),
        bundle.get("scenario", ""),
        " ".join(bundle.get("task_signals", [])),
    ]
    haystack = normalize_task_text(" ".join(text_parts))
    score = 0
    task_type = task_profile.get("task_type", "")
    if task_type != "general" and task_type.replace("_", "-") in bundle.get("id", ""):
        score += 8
    for capability in task_profile.get("required_capabilities", []):
        if capability.replace("_", " ") in haystack or capability in haystack:
            score += 2
    score += _signal_score(haystack, task_profile.get("artifact_types", []))
    score += _signal_score(haystack, task_profile.get("secondary_domains", []))
    for signal in bundle.get("task_signals", []):
        if signal in haystack:
            score += 1
    return score


def build_capability_coverage(bundle: dict, selected_skill_names: set[str]) -> list[dict]:
    coverage = []
    for capability in bundle.get("required_capabilities", []):
        capability_id = capability.get("id", "")
        preferred = capability.get("preferred_skills", [])
        selected = next((skill_name for skill_name in preferred if skill_name in selected_skill_names), "")
        coverage.append(
            {
                "capability": capability_id,
                "required": bool(capability.get("required", True)),
                "status": "covered" if selected else "missing",
                "skill": selected,
                "preferred_skills": preferred,
            }
        )
    return coverage


def build_execution_plan(bundle: dict, selected_skills: list[dict]) -> list[dict]:
    selected_by_name = {skill["name"]: skill for skill in selected_skills}
    ordered_names = [name for name in bundle.get("execution_order", []) if name in selected_by_name]
    for skill in selected_skills:
        if skill["name"] not in ordered_names:
            ordered_names.append(skill["name"])
    return [
        {
            "order": index,
            "skill": name,
            "instruction": f"Apply `{name}` guidance, then record evidence and unresolved assumptions.",
        }
        for index, name in enumerate(ordered_names, start=1)
    ]


def build_selection_explanations(bundle: dict, selected_skills: list[dict], coverage: list[dict]) -> list[dict]:
    explanations = [
        {
            "type": "bundle",
            "name": bundle.get("id", ""),
            "role": "scenario",
            "confidence": 0.9,
            "matched_capabilities": [item["capability"] for item in coverage if item["status"] == "covered"],
            "selection_reason": f"Selected `{bundle.get('name', bundle.get('id', ''))}` as the closest trusted scenario bundle.",
        }
    ]
    coverage_by_skill: dict[str, list[str]] = {}
    for item in coverage:
        if item["skill"]:
            coverage_by_skill.setdefault(item["skill"], []).append(item["capability"])
    for skill in selected_skills:
        matched = coverage_by_skill.get(skill["name"], [])
        explanations.append(
            {
                "type": "skill",
                "name": skill["name"],
                "role": "core" if matched else "supplemental",
                "confidence": 0.85 if matched else 0.6,
                "matched_capabilities": matched,
                "selection_reason": (
                    f"Selected `{skill['name']}` to cover {', '.join(matched)}."
                    if matched
                    else f"Selected `{skill['name']}` as supplemental trusted guidance."
                ),
            }
        )
    return explanations


def route_scenario_task(
    task: str,
    selected_skills: list[dict],
    bundles_index: dict,
    trusted_skill_names: set[str],
    max_skills: int,
) -> dict:
    profile = build_task_profile(task)
    trusted_bundles = [
        bundle
        for bundle in bundles_index.get("bundles", [])
        if bundle.get("status") == "trusted" and set(bundle.get("skills", [])).issubset(trusted_skill_names)
    ]
    selected_bundle = max(
        trusted_bundles,
        key=lambda bundle: (score_bundle_for_profile(bundle, profile), bundle.get("id", "")),
        default={},
    )
    if selected_bundle and score_bundle_for_profile(selected_bundle, profile) <= 0:
        selected_bundle = {}

    selected_by_name = {skill["name"]: skill for skill in selected_skills}
    ordered_names: list[str] = []
    if selected_bundle:
        for name in selected_bundle.get("execution_order", selected_bundle.get("skills", [])):
            if name in selected_by_name and name not in ordered_names:
                ordered_names.append(name)
        for capability in selected_bundle.get("required_capabilities", []):
            for name in capability.get("preferred_skills", []):
                if name in selected_by_name and name not in ordered_names:
                    ordered_names.append(name)
    for skill in selected_skills:
        if skill["name"] not in ordered_names:
            ordered_names.append(skill["name"])
    routed_skills = [selected_by_name[name] for name in ordered_names[:max_skills]]
    coverage = build_capability_coverage(selected_bundle, {skill["name"] for skill in routed_skills}) if selected_bundle else []
    execution_plan = build_execution_plan(selected_bundle, routed_skills) if selected_bundle else build_execution_plan({}, routed_skills)
    explanations = build_selection_explanations(selected_bundle, routed_skills, coverage) if selected_bundle else []
    return {
        "router": {"mode": "deterministic_scenario_router", "version": ROUTER_VERSION},
        "task_profile": profile,
        "selected_scenario": {
            "id": selected_bundle.get("id", ""),
            "name": selected_bundle.get("name", selected_bundle.get("id", "")),
            "match_score": score_bundle_for_profile(selected_bundle, profile) if selected_bundle else 0,
        },
        "skills": routed_skills,
        "bundles": [selected_bundle] if selected_bundle else [],
        "coverage": coverage,
        "execution_plan": execution_plan,
        "selection_explanations": explanations,
    }
```

- [ ] **Step 4: Run router tests**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_router -v
```

Expected: all `RouterTest` tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/onecode_skill_sanitizer/router.py tests/test_router.py
git commit -m "Add deterministic skill router core"
```

---

### Task 2: Add Scenario Router CLI Output

**Files:**
- Modify: `src/onecode_skill_sanitizer/cli.py`
- Test: `tests/test_registry_cli.py`

- [ ] **Step 1: Write failing CLI tests**

Append to `RegistryCliTest` in `tests/test_registry_cli.py`:

```python
    def test_task_pack_scenario_router_outputs_profile_plan_and_explanations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            incoming = root / "incoming"
            registry = root / "registry"
            bundles_dir = root / "bundles"
            bundles_dir.mkdir()
            skill_names = [
                ("business-requirements-brief", "business", "Use when defining requirements."),
                ("design-ui-review", "design", "Use when reviewing website UI."),
                ("content-seo-brief", "content", "Use when preparing SEO copy."),
                ("execution-publish-check", "execution", "Use when checking publish readiness."),
            ]
            for name, category, description in skill_names:
                skill = incoming / name
                skill.mkdir(parents=True)
                (skill / "SKILL.md").write_text(
                    "\n".join(
                        [
                            "---",
                            f"name: {name}",
                            f"description: {description}",
                            "---",
                            f"# {name}",
                            "",
                            "## Safe Workflow",
                            "1. Follow bounded workflow.",
                            "",
                            "## Expected Output",
                            "- evidence",
                            "",
                            "## Verifier Expectations",
                            "- verification notes",
                        ]
                    ),
                    encoding="utf-8",
                )
                (skill / "skill.json").write_text(
                    json.dumps(
                        {
                            "taxonomy": {
                                "category": category,
                                "subcategory": f"{category}.test",
                                "task_intent": description,
                                "artifact_type": "workflow",
                                "collection_priority": "P1",
                            }
                        }
                    ),
                    encoding="utf-8",
                )
            main(
                [
                    "import",
                    str(incoming),
                    "--registry",
                    str(registry),
                    "--source-url",
                    "https://github.com/example/skills",
                    "--author",
                    "example-team",
                    "--license",
                    "MIT",
                    "--reference",
                    "https://github.com/example/skills",
                    "--collected-by",
                    "onecode-test",
                ]
            )
            for name, category, _ in skill_names:
                main(["approve", str(registry / category / name)])
            (bundles_dir / "index.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "bundle_count": 1,
                        "bundles": [
                            {
                                "id": "website-build-launch",
                                "name": "Website Build Launch",
                                "scenario": "Build or polish a website and prepare it for release.",
                                "status": "trusted",
                                "task_signals": ["website", "launch"],
                                "skills": [name for name, _, _ in skill_names],
                                "required_capabilities": [
                                    {"id": "requirements", "required": True, "preferred_skills": ["business-requirements-brief"]},
                                    {"id": "ui_review", "required": True, "preferred_skills": ["design-ui-review"]},
                                    {"id": "seo_copy", "required": True, "preferred_skills": ["content-seo-brief"]},
                                    {"id": "publish_check", "required": True, "preferred_skills": ["execution-publish-check"]},
                                ],
                                "execution_order": [name for name, _, _ in skill_names],
                                "expected_output": ["release checklist"],
                                "safety_boundary": "Skills provide method only.",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            task_pack_out = io.StringIO()
            with contextlib.redirect_stdout(task_pack_out):
                task_pack_code = main(
                    [
                        "task-pack",
                        "build a product website and prepare launch checks",
                        "--registry",
                        str(registry),
                        "--include-bundles",
                        "--bundles",
                        str(bundles_dir / "index.json"),
                        "--router",
                        "scenario",
                        "--max-skills",
                        "4",
                    ]
                )

            self.assertEqual(task_pack_code, 0)
            task_pack = json.loads(task_pack_out.getvalue())
            self.assertEqual(task_pack["router"]["mode"], "deterministic_scenario_router")
            self.assertEqual(task_pack["task_profile"]["task_type"], "website_build")
            self.assertEqual(task_pack["selected_scenario"]["id"], "website-build-launch")
            self.assertEqual(task_pack["bundle_count"], 1)
            self.assertEqual(task_pack["bundles"][0]["id"], "website-build-launch")
            self.assertEqual([step["skill"] for step in task_pack["execution_plan"]], [name for name, _, _ in skill_names])
            self.assertTrue(task_pack["coverage"])
            self.assertTrue(task_pack["selection_explanations"])
            self.assertIn("Execution plan:", task_pack["agent_instructions"])

    def test_task_pack_simple_router_remains_backward_compatible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            incoming = root / "incoming"
            registry = root / "registry"
            skill = incoming / "design-dashboard"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "\n".join(
                    [
                        "---",
                        "name: design-dashboard",
                        "description: Use when polishing dashboard UI layout.",
                        "---",
                        "# Design Dashboard",
                        "",
                        "## Safe Workflow",
                        "1. Inspect dashboard.",
                        "",
                        "## Verifier Expectations",
                        "- screenshot check",
                    ]
                ),
                encoding="utf-8",
            )
            main(
                [
                    "import",
                    str(incoming),
                    "--registry",
                    str(registry),
                    "--source-url",
                    "https://github.com/example/design-dashboard",
                    "--author",
                    "example-team",
                    "--license",
                    "MIT",
                    "--reference",
                    "https://github.com/example/design-dashboard",
                    "--collected-by",
                    "onecode-test",
                ]
            )
            main(["approve", str(registry / "design" / "design-dashboard")])

            task_pack_out = io.StringIO()
            with contextlib.redirect_stdout(task_pack_out):
                task_pack_code = main(
                    [
                        "task-pack",
                        "polish this dashboard interface",
                        "--registry",
                        str(registry),
                        "--router",
                        "simple",
                    ]
                )

            self.assertEqual(task_pack_code, 0)
            task_pack = json.loads(task_pack_out.getvalue())
            self.assertNotIn("router", task_pack)
            self.assertEqual(task_pack["skills"][0]["name"], "design-dashboard")
```

- [ ] **Step 2: Run CLI tests to verify they fail**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_task_pack_scenario_router_outputs_profile_plan_and_explanations tests.test_registry_cli.RegistryCliTest.test_task_pack_simple_router_remains_backward_compatible -v
```

Expected: FAIL because `--router` and `--max-skills` are unknown arguments.

- [ ] **Step 3: Modify CLI imports**

In `src/onecode_skill_sanitizer/cli.py`, add near existing imports:

```python
from .router import route_scenario_task
```

- [ ] **Step 4: Add router parameters to `build_task_pack`**

Change the `build_task_pack` signature:

```python
def build_task_pack(
    registry_dir: Path,
    task: str,
    top: int,
    include_review_required: bool,
    include_bundles: bool = False,
    bundles_path: Path | None = None,
    router_mode: str = "simple",
    max_skills: int | None = None,
) -> dict:
```

Inside `build_task_pack`, after loading `skills` and before returning, add:

```python
    if router_mode == "scenario":
        bundle_index_path = bundles_path or Path("bundles/index.json")
        bundles_index = load_bundles_index(bundle_index_path)
        routed = route_scenario_task(
            task=task,
            selected_skills=skills,
            bundles_index=bundles_index,
            trusted_skill_names=trusted_skill_names(registry_dir),
            max_skills=max_skills or top,
        )
        skills = routed["skills"]
        bundles = select_bundles_for_task(registry_dir, bundle_index_path, task, skills)
        if routed["selected_scenario"].get("id"):
            scenario_id = routed["selected_scenario"]["id"]
            bundles = [bundle for bundle in bundles if bundle["id"] == scenario_id] or bundles
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
            "router": routed["router"],
            "task_profile": routed["task_profile"],
            "selected_scenario": routed["selected_scenario"],
            "coverage": routed["coverage"],
            "execution_plan": routed["execution_plan"],
            "selection_explanations": routed["selection_explanations"],
        }
        task_pack["agent_instructions"] = build_agent_instructions(task, skills, bundles, task_pack)
        return task_pack
```

Before the scenario routing block, use a wider candidate pool so `--max-skills`
is not silently limited by the compatibility `--top` default:

```python
    candidate_limit = max(top, max_skills or top) if router_mode == "scenario" else top
    selected = select_skills_for_task(registry_dir, task_taxonomy, task, include_review_required)[:candidate_limit]
    skills = [load_skill_pack_item(registry_dir, entry) for entry in selected]
```

Then remove the earlier fixed `[:top]` selection lines from `build_task_pack`.

Leave the existing simple return path unchanged except for passing the optional fourth argument to `build_agent_instructions`.

- [ ] **Step 5: Extend `build_agent_instructions` for router metadata**

Change signature:

```python
def build_agent_instructions(task: str, skills: list[dict], bundles: list[dict] | None = None, router_context: dict | None = None) -> str:
```

Before `Selected skills:`, add:

```python
    if router_context and router_context.get("execution_plan"):
        lines.extend(["Execution plan:"])
        for step in router_context["execution_plan"]:
            lines.append(f"- {step['order']}. {step['skill']}: {step['instruction']}")
        lines.append("")
    if router_context and router_context.get("coverage"):
        lines.extend(["Capability coverage:"])
        for item in router_context["coverage"]:
            skill = item.get("skill") or "missing"
            lines.append(f"- {item['capability']}: {item['status']} by {skill}")
        lines.append("")
```

- [ ] **Step 6: Extend Markdown rendering**

In `render_task_pack_markdown`, after `## Safety Boundary`, add conditional sections:

```python
    if task_pack.get("router"):
        lines.extend(
            [
                "",
                "## Task Profile",
                "",
                f"- router: `{task_pack['router']['mode']}`",
                f"- task type: `{task_pack['task_profile']['task_type']}`",
                f"- primary domain: `{task_pack['task_profile']['primary_domain']}`",
                "",
                "## Selected Scenario",
                "",
                f"- id: `{task_pack['selected_scenario'].get('id', '')}`",
                f"- score: `{task_pack['selected_scenario'].get('match_score', 0)}`",
                "",
                "## Capability Coverage",
                "",
            ]
        )
        for item in task_pack.get("coverage", []):
            lines.append(f"- `{item['capability']}`: {item['status']} by `{item.get('skill') or 'missing'}`")
        lines.extend(["", "## Execution Plan", ""])
        for step in task_pack.get("execution_plan", []):
            lines.append(f"{step['order']}. `{step['skill']}` - {step['instruction']}")
        lines.extend(["", "## Selection Explanations", ""])
        for item in task_pack.get("selection_explanations", []):
            lines.append(f"- `{item['name']}` ({item['type']}, {item['role']}): {item['selection_reason']}")
```

- [ ] **Step 7: Add CLI arguments**

In `build_parser`, add to `task_pack_parser`:

```python
    task_pack_parser.add_argument("--router", choices=["simple", "scenario"], default="simple")
    task_pack_parser.add_argument("--max-skills", type=int)
```

Pass arguments from `task_pack_command`:

```python
        args.router,
        args.max_skills,
```

- [ ] **Step 8: Run targeted CLI tests**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_task_pack_scenario_router_outputs_profile_plan_and_explanations tests.test_registry_cli.RegistryCliTest.test_task_pack_simple_router_remains_backward_compatible -v
```

Expected: both tests pass.

- [ ] **Step 9: Commit**

```bash
git add src/onecode_skill_sanitizer/cli.py tests/test_registry_cli.py
git commit -m "Add scenario router task-pack mode"
```

---

### Task 3: Add Bundle Metadata For Scenario Routing

**Files:**
- Modify: `bundles/index.json`
- Test: `tests/test_registry_cli.py`

- [ ] **Step 1: Write failing real-catalog routing tests**

Append to `RegistryCliTest`:

```python
    def test_real_catalog_scenario_router_selects_website_bundle(self):
        task_pack_out = io.StringIO()
        with contextlib.redirect_stdout(task_pack_out):
            task_pack_code = main(
                [
                    "task-pack",
                    "build a product website and prepare launch checks",
                    "--registry",
                    "catalog",
                    "--include-bundles",
                    "--bundles",
                    "bundles/index.json",
                    "--router",
                    "scenario",
                    "--max-skills",
                    "8",
                ]
            )

        self.assertEqual(task_pack_code, 0)
        task_pack = json.loads(task_pack_out.getvalue())
        self.assertEqual(task_pack["selected_scenario"]["id"], "website-build-launch")
        self.assertEqual(task_pack["bundles"][0]["id"], "website-build-launch")
        self.assertIn("design-ui-review", [skill["name"] for skill in task_pack["skills"]])
        self.assertIn("execution-publish-check", [skill["name"] for skill in task_pack["skills"]])
        self.assertIn("ui_review", [item["capability"] for item in task_pack["coverage"]])

    def test_real_catalog_scenario_router_selects_rag_bundle(self):
        task_pack_out = io.StringIO()
        with contextlib.redirect_stdout(task_pack_out):
            task_pack_code = main(
                [
                    "task-pack",
                    "design a RAG document agent with vector retrieval and citation checks",
                    "--registry",
                    "catalog",
                    "--include-bundles",
                    "--bundles",
                    "bundles/index.json",
                    "--router",
                    "scenario",
                    "--max-skills",
                    "8",
                ]
            )

        self.assertEqual(task_pack_code, 0)
        task_pack = json.loads(task_pack_out.getvalue())
        self.assertEqual(task_pack["selected_scenario"]["id"], "rag-agent-knowledge-app")
        self.assertEqual(task_pack["bundles"][0]["id"], "rag-agent-knowledge-app")
        self.assertIn("data-qdrant-vector-retrieval", [skill["name"] for skill in task_pack["skills"]])
        self.assertIn("citation_check", [item["capability"] for item in task_pack["coverage"]])
```

- [ ] **Step 2: Run tests to verify they fail or partially fail**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_real_catalog_scenario_router_selects_website_bundle tests.test_registry_cli.RegistryCliTest.test_real_catalog_scenario_router_selects_rag_bundle -v
```

Expected: FAIL until bundle metadata and router selection are aligned with real catalog.

- [ ] **Step 3: Add website bundle metadata**

In `bundles/index.json`, add to `website-build-launch`:

```json
"task_signals": ["website", "landing page", "official site", "dashboard", "launch", "publish"],
"required_capabilities": [
  {"id": "requirements", "required": true, "preferred_skills": ["business-requirements-brief"]},
  {"id": "engineering_release", "required": true, "preferred_skills": ["engineering-build-release"]},
  {"id": "ui_review", "required": true, "preferred_skills": ["design-ui-review"]},
  {"id": "design_consistency", "required": true, "preferred_skills": ["design-system-consistency"]},
  {"id": "seo_copy", "required": true, "preferred_skills": ["content-seo-brief"]},
  {"id": "browser_verification", "required": true, "preferred_skills": ["execution-browser-check", "execution-playwright-browser-automation"]},
  {"id": "publish_check", "required": true, "preferred_skills": ["execution-publish-check"]},
  {"id": "social_post", "required": false, "preferred_skills": ["content-social-post"]}
],
"execution_order": [
  "business-requirements-brief",
  "engineering-build-release",
  "design-ui-review",
  "design-system-consistency",
  "content-seo-brief",
  "execution-browser-check",
  "execution-playwright-browser-automation",
  "execution-publish-check",
  "content-social-post"
]
```

- [ ] **Step 4: Add RAG bundle metadata**

Add to `rag-agent-knowledge-app`:

```json
"task_signals": ["rag", "retrieval", "vector", "citation", "knowledge agent", "document agent"],
"required_capabilities": [
  {"id": "requirements", "required": true, "preferred_skills": ["business-requirements-brief"]},
  {"id": "agent_orchestration", "required": true, "preferred_skills": ["ai-langchain-agent-orchestration"]},
  {"id": "rag_plan", "required": true, "preferred_skills": ["ai-llamaindex-rag-knowledge-workflow", "data-haystack-rag-pipeline"]},
  {"id": "vector_retrieval", "required": true, "preferred_skills": ["data-qdrant-vector-retrieval"]},
  {"id": "schema_contract", "required": true, "preferred_skills": ["ai-pydantic-schema-contract", "ai-output-schema-eval"]},
  {"id": "citation_check", "required": true, "preferred_skills": ["research-source-check"]},
  {"id": "prompt_injection_review", "required": false, "preferred_skills": ["security-prompt-injection-review"]}
],
"execution_order": [
  "business-requirements-brief",
  "ai-langchain-agent-orchestration",
  "ai-llamaindex-rag-knowledge-workflow",
  "data-haystack-rag-pipeline",
  "data-qdrant-vector-retrieval",
  "ai-pydantic-schema-contract",
  "ai-output-schema-eval",
  "research-source-check",
  "security-prompt-injection-review"
]
```

- [ ] **Step 5: Add metadata for the remaining seven bundles**

Add similar metadata:

```json
{
  "id": "code-review-hardening",
  "task_signals": ["code review", "pull request", "generated code", "bug fix", "refactor", "tests"],
  "required_capabilities": [
    {"id": "code_review", "required": true, "preferred_skills": ["code-review-risk"]},
    {"id": "regression_test", "required": true, "preferred_skills": ["code-test-regression"]},
    {"id": "schema_contract", "required": false, "preferred_skills": ["ai-pydantic-schema-contract", "ai-output-schema-eval"]},
    {"id": "supply_chain_review", "required": true, "preferred_skills": ["security-supply-chain-review"]},
    {"id": "sandbox_boundary", "required": false, "preferred_skills": ["execution-e2b-sandbox-boundary"]},
    {"id": "ci_check", "required": true, "preferred_skills": ["engineering-ci-troubleshoot"]}
  ],
  "execution_order": ["code-review-risk", "code-test-regression", "ai-pydantic-schema-contract", "ai-output-schema-eval", "security-supply-chain-review", "execution-e2b-sandbox-boundary", "engineering-ci-troubleshoot"]
}
```

```json
{
  "id": "security-agent-guardrails",
  "task_signals": ["prompt injection", "connector", "tool permission", "agent safety", "guardrail", "sandbox"],
  "required_capabilities": [
    {"id": "prompt_injection_review", "required": true, "preferred_skills": ["security-prompt-injection-review"]},
    {"id": "output_guardrail", "required": true, "preferred_skills": ["security-guardrails-output-validation", "ai-outlines-structured-generation"]},
    {"id": "io_scanning", "required": true, "preferred_skills": ["security-llm-guard-io-scanning"]},
    {"id": "supply_chain_review", "required": false, "preferred_skills": ["security-supply-chain-review"]},
    {"id": "privacy_check", "required": true, "preferred_skills": ["compliance-privacy-check"]}
  ],
  "execution_order": ["security-prompt-injection-review", "security-guardrails-output-validation", "security-llm-guard-io-scanning", "ai-outlines-structured-generation", "security-supply-chain-review", "compliance-privacy-check"]
}
```

```json
{
  "id": "document-to-knowledge-base",
  "task_signals": ["pdf", "document", "markdown", "knowledge base", "docs", "office file"],
  "required_capabilities": [
    {"id": "source_inventory", "required": true, "preferred_skills": ["office-pdf-report"]},
    {"id": "file_conversion", "required": true, "preferred_skills": ["data-markitdown-file-to-markdown", "data-marker-pdf-markdown-review"]},
    {"id": "document_partition", "required": true, "preferred_skills": ["data-unstructured-document-partition"]},
    {"id": "rag_plan", "required": true, "preferred_skills": ["ai-llamaindex-rag-knowledge-workflow", "data-haystack-rag-pipeline"]},
    {"id": "retrieval", "required": false, "preferred_skills": ["data-qdrant-vector-retrieval"]},
    {"id": "source_check", "required": true, "preferred_skills": ["research-source-check"]}
  ],
  "execution_order": ["office-pdf-report", "data-markitdown-file-to-markdown", "data-marker-pdf-markdown-review", "data-unstructured-document-partition", "ai-llamaindex-rag-knowledge-workflow", "data-haystack-rag-pipeline", "data-qdrant-vector-retrieval", "research-source-check", "office-docx-brief"]
}
```

```json
{
  "id": "data-analysis-report",
  "task_signals": ["dataset", "spreadsheet", "chart", "data analysis", "table", "report"],
  "required_capabilities": [
    {"id": "data_quality", "required": true, "preferred_skills": ["data-quality-audit"]},
    {"id": "table_analysis", "required": true, "preferred_skills": ["data-table-analysis"]},
    {"id": "visualization", "required": true, "preferred_skills": ["data-visualization-plan"]},
    {"id": "spreadsheet_cleanup", "required": false, "preferred_skills": ["office-spreadsheet-cleanup"]},
    {"id": "source_check", "required": true, "preferred_skills": ["research-source-check"]},
    {"id": "report_brief", "required": true, "preferred_skills": ["office-docx-brief"]}
  ],
  "execution_order": ["data-quality-audit", "data-table-analysis", "data-visualization-plan", "office-spreadsheet-cleanup", "research-source-check", "office-docx-brief"]
}
```

```json
{
  "id": "open-source-release",
  "task_signals": ["open source", "release", "github", "publish repo", "public repository"],
  "required_capabilities": [
    {"id": "publish_check", "required": true, "preferred_skills": ["execution-publish-check"]},
    {"id": "supply_chain_review", "required": true, "preferred_skills": ["security-supply-chain-review"]},
    {"id": "license_review", "required": true, "preferred_skills": ["compliance-terms-review"]},
    {"id": "editorial_review", "required": true, "preferred_skills": ["content-editorial-review"]},
    {"id": "social_post", "required": false, "preferred_skills": ["content-social-post"]},
    {"id": "source_check", "required": true, "preferred_skills": ["research-source-check"]}
  ],
  "execution_order": ["execution-publish-check", "security-supply-chain-review", "compliance-terms-review", "content-editorial-review", "research-source-check", "content-social-post"]
}
```

```json
{
  "id": "content-seo-publication",
  "task_signals": ["article", "seo", "social", "public content", "blog", "post"],
  "required_capabilities": [
    {"id": "seo_copy", "required": true, "preferred_skills": ["content-seo-brief"]},
    {"id": "editorial_review", "required": true, "preferred_skills": ["content-editorial-review"]},
    {"id": "prompt_pattern", "required": false, "preferred_skills": ["content-prompt-engineering-patterns"]},
    {"id": "source_check", "required": true, "preferred_skills": ["research-source-check"]},
    {"id": "social_post", "required": true, "preferred_skills": ["content-social-post"]}
  ],
  "execution_order": ["content-seo-brief", "research-source-check", "content-editorial-review", "content-prompt-engineering-patterns", "content-social-post"]
}
```

```json
{
  "id": "commerce-listing-growth",
  "task_signals": ["listing", "keyword", "inquiry", "trade", "buyer", "marketplace"],
  "required_capabilities": [
    {"id": "listing", "required": true, "preferred_skills": ["commerce-icbu-listing"]},
    {"id": "keyword_plan", "required": true, "preferred_skills": ["commerce-product-keyword-plan"]},
    {"id": "inquiry_reply", "required": true, "preferred_skills": ["commerce-inquiry-reply"]},
    {"id": "editorial_review", "required": false, "preferred_skills": ["content-editorial-review"]},
    {"id": "requirements", "required": false, "preferred_skills": ["business-requirements-brief"]}
  ],
  "execution_order": ["business-requirements-brief", "commerce-icbu-listing", "commerce-product-keyword-plan", "content-editorial-review", "commerce-inquiry-reply"]
}
```

- [ ] **Step 6: Run JSON validation through existing CLI**

Run:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check --registry catalog --bundles bundles/index.json
```

Expected: JSON result with `"status": "ok"`.

- [ ] **Step 7: Run real-catalog routing tests**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_real_catalog_scenario_router_selects_website_bundle tests.test_registry_cli.RegistryCliTest.test_real_catalog_scenario_router_selects_rag_bundle -v
```

Expected: both tests pass.

- [ ] **Step 8: Commit**

```bash
git add bundles/index.json tests/test_registry_cli.py
git commit -m "Add scenario routing metadata to bundles"
```

---

### Task 4: Update Public Docs For Scenario Router

**Files:**
- Modify: `docs/agent-task-pack.md`
- Modify: `docs/agent-compatible-skill-bundles.md`
- Modify: `README.md`

- [ ] **Step 1: Update `docs/agent-task-pack.md`**

Add after `Bundle-Aware Output`:

```markdown
## Scenario Router

Use `--router scenario` when the host agent should receive a task-aware skill
composition rather than a simple match-score list.

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer task-pack \
  "build a product website and prepare launch checks" \
  --registry catalog \
  --include-bundles \
  --bundles bundles/index.json \
  --router scenario \
  --max-skills 8 \
  --format json
```

Scenario router output adds:

- `router`
- `task_profile`
- `selected_scenario`
- `coverage`
- `execution_plan`
- `selection_explanations`

The router is deterministic. It does not call an external model, does not
execute selected skills, and does not grant runtime permissions.
```

- [ ] **Step 2: Update `docs/agent-compatible-skill-bundles.md`**

Add under `Scenario Bundles`:

```markdown
Scenario bundles can include optional router metadata:

- `task_signals`: words or phrases that identify the scenario
- `required_capabilities`: capabilities that should be covered by selected skills
- `execution_order`: recommended skill order for host-agent planning

When `task-pack --router scenario` is used, the router chooses the closest
trusted bundle, maps capabilities to trusted skills, and emits an execution
plan. This keeps the agent's task flow more consistent than selecting skills
by keyword overlap alone.
```

- [ ] **Step 3: Update `README.md` local CLI section**

Add one command example after the existing `task-pack --include-bundles` paragraph:

```markdown
For more precise task-aware composition, use the deterministic scenario router:

```bash
onecode-skill-sanitizer task-pack "build a product website and prepare launch checks" \
  --registry ./registry \
  --include-bundles \
  --bundles ./bundles/index.json \
  --router scenario \
  --max-skills 8 \
  --format json
```
```

- [ ] **Step 4: Run docs whitespace check**

Run:

```bash
git diff --check
```

Expected: no output, exit code 0.

- [ ] **Step 5: Commit**

```bash
git add README.md docs/agent-task-pack.md docs/agent-compatible-skill-bundles.md
git commit -m "Document scenario skill router"
```

---

### Task 5: Full Verification And Publish

**Files:**
- Verify all modified files.

- [ ] **Step 1: Run full verification**

Run:

```bash
bash scripts/verify.sh
```

Expected:

```text
Ran at least 30 tests
OK
```

- [ ] **Step 2: Run registry verification**

Run:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry catalog
```

Expected JSON includes:

```json
{
  "status": "ok",
  "skill_count": 75,
  "trusted_count": 70,
  "tampered_count": 0,
  "unknown_provenance_count": 0
}
```

- [ ] **Step 3: Run bundle maintenance check**

Run:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check --registry catalog --bundles bundles/index.json
```

Expected JSON includes:

```json
{
  "status": "ok",
  "bundle_validation": {
    "bundle_count": 9,
    "trusted_bundle_count": 9,
    "issues": []
  }
}
```

- [ ] **Step 4: Run sample scenario router commands**

Run:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer task-pack \
  "build a product website and prepare launch checks" \
  --registry catalog \
  --include-bundles \
  --bundles bundles/index.json \
  --router scenario \
  --max-skills 8 \
  --format json
```

Expected JSON includes:

```json
"selected_scenario": {
  "id": "website-build-launch"
}
```

Run:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer task-pack \
  "design a RAG document agent with vector retrieval and citation checks" \
  --registry catalog \
  --include-bundles \
  --bundles bundles/index.json \
  --router scenario \
  --max-skills 8 \
  --format json
```

Expected JSON includes:

```json
"selected_scenario": {
  "id": "rag-agent-knowledge-app"
}
```

- [ ] **Step 5: Run diff whitespace check**

Run:

```bash
git diff --check HEAD
```

Expected: no output, exit code 0.

- [ ] **Step 6: Check status**

Run:

```bash
git status --short --branch
```

Expected: branch is ahead of `origin/main` with no unstaged files.

- [ ] **Step 7: Push**

Run:

```bash
git push origin main
```

Expected: push succeeds and updates `https://github.com/aidi1723/safe-agent-skills`.

---

## Self-Review

Spec coverage:

- Task profile: Task 1 and Task 2.
- Scenario bundle-first routing: Task 1, Task 2, Task 3.
- Capability coverage: Task 1, Task 2, Task 3.
- Supplemental skill ordering and max skill limit: Task 1 and Task 2.
- Execution plan: Task 1 and Task 2.
- Selection explanations: Task 1 and Task 2.
- Safety boundary and no execution authority: Task 2 and Task 4.
- Backward compatibility: Task 2.
- Public docs: Task 4.
- Verification and publish: Task 5.

Placeholder scan:

- This plan contains no deferred filler items or undefined later work.
- Every code-touching task includes concrete code or exact JSON snippets.
- Every verification step includes an exact command and expected result.

Type consistency:

- Router mode string is `deterministic_scenario_router` in both tests and implementation.
- CLI option values are `simple` and `scenario`.
- Output fields match the design spec: `router`, `task_profile`, `selected_scenario`, `coverage`, `execution_plan`, `selection_explanations`.
