import contextlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


from onecode_skill_sanitizer.cli import main

from tests.registry_cli_helpers import ROUTER_SCHEMA_V1_SHAPE_SHA256
from tests.registry_cli_helpers import payload_shape_sha256


class RouterCliTest(unittest.TestCase):
    def test_contract_check_outputs_json_and_exits_two_below_threshold(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            exit_code = main(
                [
                    "contract-check",
                    "--registry",
                    "catalog",
                    "--bundles",
                    "bundles/index.json",
                    "--scenario",
                    "website-build-launch",
                    "--scenario",
                    "code-review-hardening",
                    "--scenario",
                    "codebase-change-lifecycle",
                    "--scenario",
                    "skill-router-quality-review",
                    "--scenario",
                    "open-source-release",
                    "--scenario",
                    "rag-agent-knowledge-app",
                    "--scenario",
                    "document-to-knowledge-base",
                    "--scenario",
                    "security-agent-guardrails",
                    "--minimum-ratio",
                    "1.0",
                ]
            )

        payload = json.loads(out.getvalue())
        self.assertNotRegex(out.getvalue(), r"\b(?:NaN|Infinity|-Infinity)\b")
        self.assertEqual(exit_code, 2)
        self.assertEqual(len(payload["scenario_ids"]), 8)
        self.assertLess(payload["coverage_ratio"], 1.0)

    def test_contract_check_rejects_invalid_threshold_and_scenario(self):
        with self.assertRaises(SystemExit):
            main(
                [
                    "contract-check",
                    "--registry",
                    "catalog",
                    "--bundles",
                    "bundles/index.json",
                    "--minimum-ratio",
                    "1.1",
                ]
            )
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            exit_code = main(
                [
                    "contract-check",
                    "--registry",
                    "catalog",
                    "--bundles",
                    "bundles/index.json",
                    "--scenario",
                    "not-a-scenario",
                ]
            )
        payload = json.loads(out.getvalue())
        self.assertEqual(exit_code, 2)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error"], "unknown scenario ids: not-a-scenario")

    def test_contract_check_rejects_nonfinite_thresholds_without_json_output(self):
        for value in ["nan", "inf", "-inf"]:
            with self.subTest(value=value):
                out = io.StringIO()
                with contextlib.redirect_stdout(out), self.assertRaises(SystemExit):
                    main(
                        [
                            "contract-check",
                            "--registry",
                            "catalog",
                            "--bundles",
                            "bundles/index.json",
                            f"--minimum-ratio={value}",
                        ]
                    )
                self.assertEqual(out.getvalue(), "")

    def test_contract_check_returns_json_error_for_malformed_inputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            registry = root / "catalog"
            registry.mkdir()
            (registry / "index.json").write_text(json.dumps({"skills": "abc"}), encoding="utf-8")
            bundles = root / "bundles.json"
            bundles.write_text(json.dumps({"bundles": []}), encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                exit_code = main(
                    [
                        "contract-check",
                        "--registry",
                        str(registry),
                        "--bundles",
                        str(bundles),
                    ]
                )

        payload = json.loads(out.getvalue())
        self.assertEqual(exit_code, 2)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error"], "registry index skills must be an array")

    def test_contract_check_returns_json_error_for_malformed_bundle_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            registry = root / "catalog"
            registry.mkdir()
            (registry / "index.json").write_text(json.dumps({"skills": []}), encoding="utf-8")
            bundles = root / "bundles.json"
            bundles.write_text("{not-json", encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                exit_code = main(["contract-check", "--registry", str(registry), "--bundles", str(bundles)])

        payload = json.loads(out.getvalue())
        self.assertEqual(exit_code, 2)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error"], f"invalid bundles index JSON: {bundles}")

    def test_contract_check_returns_json_error_for_missing_index_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            registry = root / "catalog"
            registry.mkdir()
            bundles = root / "bundles.json"
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                exit_code = main(["contract-check", "--registry", str(registry), "--bundles", str(bundles)])

        payload = json.loads(out.getvalue())
        self.assertEqual(exit_code, 2)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error"], f"invalid registry index JSON: {registry / 'index.json'}")

    def test_smart_missing_overlap_file_exits_concisely(self):
        missing = "/tmp/onecode-missing-overlap-groups.json"
        with self.assertRaises(SystemExit) as raised:
            main(["smart", "build site", "--overlap-groups", missing, "--schema-version", "1"])
        self.assertEqual(str(raised.exception), f"overlap groups file not found: {missing}")

    def test_task_pack_outputs_json_for_trusted_matching_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            incoming = root / "incoming"
            registry = root / "registry"
            design = incoming / "design-dashboard"
            office = incoming / "office-pdf"
            design.mkdir(parents=True)
            office.mkdir(parents=True)
            (design / "SKILL.md").write_text(
                "\n".join(
                    [
                        "---",
                        "name: design-dashboard",
                        "description: Use when polishing dashboard UI layout.",
                        "---",
                        "# Design Dashboard",
                        "",
                        "## When To Use",
                        "Use this skill for dashboard interface polish.",
                        "",
                        "## Safe Workflow",
                        "1. Inspect the target route.",
                        "2. Preserve business logic.",
                        "",
                        "## Expected Output",
                        "- UI findings",
                        "- screenshot notes",
                        "",
                        "## Verifier Expectations",
                        "- build check",
                        "- responsive screenshot check",
                        "",
                        "## Failure Handling",
                        "Report rendering blockers.",
                    ]
                ),
                encoding="utf-8",
            )
            (design / "skill.json").write_text(
                json.dumps(
                    {
                        "taxonomy": {
                            "category": "design",
                            "subcategory": "design.dashboard",
                            "task_intent": "polish dashboard interfaces",
                            "artifact_type": "interface",
                            "collection_priority": "P0",
                        },
                        "source": {
                            "type": "local_folder",
                            "url": "https://github.com/example/design-dashboard",
                            "author": "example-team",
                            "license": "MIT",
                            "reference": "https://github.com/example/design-dashboard",
                            "collected_by": "onecode-test",
                        },
                    }
                ),
                encoding="utf-8",
            )
            (office / "SKILL.md").write_text(
                "Use this workflow for PDF office reports.",
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
            main(["approve", str(registry / "design" / "design-dashboard")])

            task_pack_out = io.StringIO()
            with contextlib.redirect_stdout(task_pack_out):
                task_pack_code = main(
                    [
                        "task-pack",
                        "--schema-version",
                        "1",
                        "polish this dashboard interface",
                        "--registry",
                        str(registry),
                        "--top",
                        "1",
                    ]
                )

            self.assertEqual(task_pack_code, 0)
            task_pack = json.loads(task_pack_out.getvalue())
            self.assertEqual(task_pack["schema_version"], 1)
            self.assertEqual(task_pack["task"], "polish this dashboard interface")
            self.assertEqual(task_pack["skill_count"], 1)
            self.assertEqual(task_pack["skills"][0]["name"], "design-dashboard")
            self.assertEqual(task_pack["skills"][0]["status"], "trusted")
            self.assertIn("Use when polishing dashboard UI layout.", task_pack["skills"][0]["description"])
            self.assertIn("Inspect the target route.", task_pack["agent_instructions"])
            self.assertIn("responsive screenshot check", task_pack["agent_instructions"])
            self.assertIn("Only use trusted skills", task_pack["safety_boundary"])
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

    def test_task_pack_outputs_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            incoming = root / "incoming"
            registry = root / "registry"
            skill = incoming / "security-review"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "\n".join(
                    [
                        "---",
                        "name: security-review",
                        "description: Use when reviewing security risk.",
                        "---",
                        "# Security Review",
                        "",
                        "## When To Use",
                        "Use this skill for security review.",
                        "",
                        "## Safe Workflow",
                        "1. Review permissions.",
                        "",
                        "## Expected Output",
                        "- risk findings",
                        "",
                        "## Verifier Expectations",
                        "- policy check",
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
                    "https://github.com/example/security-review",
                    "--author",
                    "example-team",
                    "--license",
                    "MIT",
                    "--reference",
                    "https://github.com/example/security-review",
                    "--collected-by",
                    "onecode-test",
                ]
            )
            main(["approve", str(registry / "security" / "security-review")])

            task_pack_out = io.StringIO()
            with contextlib.redirect_stdout(task_pack_out):
                task_pack_code = main(
                    [
                        "task-pack",
                        "--schema-version",
                        "1",
                        "review security risk",
                        "--registry",
                        str(registry),
                        "--format",
                        "markdown",
                    ]
                )

            self.assertEqual(task_pack_code, 0)
            markdown = task_pack_out.getvalue()
            self.assertIn("# OneCode Agent Task Pack", markdown)
            self.assertIn("security-review", markdown)
            self.assertIn("Review permissions.", markdown)
            self.assertIn("policy check", markdown)
            self.assertIn("## Acceptance Criteria", markdown)
            self.assertIn("## Completion Contract", markdown)
            self.assertIn("Record selected trusted skills before execution.", markdown)
            self.assertIn("selected_skills", markdown)
            self.assertIn("verification_performed", markdown)

    def test_task_pack_never_selects_rejected_or_disabled_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            incoming = root / "incoming"
            registry = root / "registry"
            rejected = incoming / "security-rejected"
            disabled = incoming / "security-disabled"
            review = incoming / "security-review"
            rejected.mkdir(parents=True)
            disabled.mkdir(parents=True)
            review.mkdir(parents=True)
            for skill_dir in [rejected, disabled, review]:
                lines = [
                    "---",
                    f"name: {skill_dir.name}",
                    "description: Use when reviewing security risk.",
                    "---",
                    "# Security Review",
                    "",
                    "## Safe Workflow",
                    "1. Review permissions.",
                    "",
                    "## Verifier Expectations",
                    "- policy check",
                ]
                if skill_dir == review:
                    lines.append("Use API_KEY=abc1234567890SECRET only in a mocked fixture.")
                (skill_dir / "SKILL.md").write_text("\n".join(lines), encoding="utf-8")
            main(
                [
                    "import",
                    str(incoming),
                    "--registry",
                    str(registry),
                    "--source-url",
                    "https://github.com/example/security-skills",
                    "--author",
                    "example-team",
                    "--license",
                    "MIT",
                    "--reference",
                    "https://github.com/example/security-skills",
                    "--collected-by",
                    "onecode-test",
                ]
            )
            main(["reject", str(registry / "security" / "security-rejected")])
            main(["disable", str(registry / "security" / "security-disabled")])

            task_pack_out = io.StringIO()
            with contextlib.redirect_stdout(task_pack_out):
                task_pack_code = main(
                    [
                        "task-pack",
                        "--schema-version",
                        "1",
                        "review security risk",
                        "--registry",
                        str(registry),
                        "--include-review-required",
                    ]
                )

            self.assertEqual(task_pack_code, 0)
            task_pack = json.loads(task_pack_out.getvalue())
            names = [skill["name"] for skill in task_pack["skills"]]
            self.assertEqual(names, ["security-review"])

    def test_task_pack_can_include_matching_trusted_bundles(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            incoming = root / "incoming"
            registry = root / "registry"
            bundles_dir = root / "bundles"
            bundles_dir.mkdir()
            skill_names = [
                ("business-requirements-brief", "business", "Use when defining business requirements."),
                ("ai-langchain-agent-orchestration", "ai", "Use when designing agent orchestration."),
                ("ai-llamaindex-rag-knowledge-workflow", "ai", "Use when designing RAG document agents."),
                ("data-qdrant-vector-retrieval", "data", "Use when reviewing vector retrieval."),
                ("research-source-check", "research", "Use when checking source citations."),
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
                            "1. Keep evidence separate from generated claims.",
                            "",
                            "## Expected Output",
                            "- bounded plan",
                            "",
                            "## Verifier Expectations",
                            "- evidence check",
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
                        "bundle_count": 2,
                        "bundles": [
                            {
                                "id": "rag-agent-knowledge-app",
                                "name": "RAG Agent Knowledge App",
                                "scenario": "Design a source-grounded RAG document agent with vector retrieval and citations.",
                                "status": "trusted",
                                "skills": [name for name, _, _ in skill_names],
                                "expected_output": ["retrieval plan", "citation checks"],
                                "safety_boundary": "Skills provide method only.",
                            },
                            {
                                "id": "commerce-listing-growth",
                                "name": "Commerce Listing Growth",
                                "scenario": "Prepare marketplace listings and buyer communication.",
                                "status": "trusted",
                                "skills": ["business-requirements-brief"],
                                "expected_output": ["listing copy"],
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
                        "--schema-version",
                        "1",
                        "design a RAG document agent with vector retrieval and citation checks",
                        "--registry",
                        str(registry),
                        "--top",
                        "3",
                        "--include-bundles",
                        "--bundles",
                        str(bundles_dir / "index.json"),
                    ]
                )

            self.assertEqual(task_pack_code, 0)
            task_pack = json.loads(task_pack_out.getvalue())
            self.assertEqual(task_pack["bundle_count"], 1)
            self.assertEqual(task_pack["bundles"][0]["id"], "rag-agent-knowledge-app")
            self.assertNotIn("commerce-listing-growth", [bundle["id"] for bundle in task_pack["bundles"]])
            self.assertIn("RAG Agent Knowledge App", task_pack["agent_instructions"])

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
                                    {
                                        "id": "requirements",
                                        "required": True,
                                        "preferred_skills": ["business-requirements-brief"],
                                    },
                                    {"id": "ui_review", "required": True, "preferred_skills": ["design-ui-review"]},
                                    {"id": "seo_copy", "required": True, "preferred_skills": ["content-seo-brief"]},
                                    {
                                        "id": "publish_check",
                                        "required": True,
                                        "preferred_skills": ["execution-publish-check"],
                                    },
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
                        "--schema-version",
                        "1",
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

    def test_scenario_router_does_not_force_bundle_for_general_meta_review_task(self):
        task_pack_out = io.StringIO()
        with contextlib.redirect_stdout(task_pack_out):
            task_pack_code = main(
                [
                    "task-pack",
                    "--schema-version",
                    "1",
                    "帮我看一下这个事情是否合理",
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
        self.assertEqual(task_pack["task_profile"]["task_type"], "general")
        self.assertEqual(task_pack["selected_scenario"]["id"], "")
        self.assertEqual(task_pack["selected_scenario"]["match_score"], 0)
        self.assertEqual(task_pack["bundle_count"], 0)
        self.assertEqual(task_pack["bundles"], [])
        self.assertNotIn("website-build-launch", task_pack["agent_instructions"])

    def test_smart_router_does_not_force_bundle_for_general_meta_review_task(self):
        task_pack_out = io.StringIO()
        with contextlib.redirect_stdout(task_pack_out):
            task_pack_code = main(
                [
                    "smart",
                    "--schema-version",
                    "1",
                    "帮我看一下这个事情是否合理",
                    "--registry",
                    "catalog",
                    "--bundles",
                    "bundles/index.json",
                    "--max-skills",
                    "8",
                ]
            )

        self.assertEqual(task_pack_code, 0)
        task_pack = json.loads(task_pack_out.getvalue())
        self.assertEqual(task_pack["task_profile"]["task_type"], "general")
        self.assertEqual(task_pack["selected_scenario"]["id"], "")
        self.assertEqual(task_pack["selected_scenario"]["match_score"], 0)
        self.assertEqual(task_pack["bundle_count"], 0)
        self.assertEqual(task_pack["bundles"], [])
        self.assertNotIn("website-build-launch", task_pack["agent_instructions"])

    def test_scenario_router_does_not_match_pr_inside_prepare(self):
        task_pack_out = io.StringIO()
        with contextlib.redirect_stdout(task_pack_out):
            task_pack_code = main(
                [
                    "task-pack",
                    "--schema-version",
                    "1",
                    "prepare a meeting brief",
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
        self.assertNotEqual(task_pack["task_profile"]["task_type"], "code_review")
        self.assertNotEqual(task_pack["selected_scenario"]["id"], "code-review-hardening")
        self.assertNotIn("code-review-risk", [skill["name"] for skill in task_pack["skills"]])

    def test_real_catalog_scenario_router_selects_skill_router_quality_review_bundle(self):
        task_pack_out = io.StringIO()
        with contextlib.redirect_stdout(task_pack_out):
            task_pack_code = main(
                [
                    "task-pack",
                    "--schema-version",
                    "1",
                    "复查 safe-agent-skills 项目是否达到智能选择和自动搭配 skill 的目标",
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
        names = [skill["name"] for skill in task_pack["skills"]]
        self.assertEqual(task_pack["task_profile"]["task_type"], "skill_router_review")
        self.assertEqual(task_pack["selected_scenario"]["id"], "skill-router-quality-review")
        self.assertEqual(task_pack["bundle_count"], 1)
        self.assertEqual(task_pack["bundles"][0]["id"], "skill-router-quality-review")
        self.assertEqual(task_pack["pipeline_plan"]["id"], "skill-router-quality-review")
        self.assertEqual(task_pack["pipeline_plan"]["mode"], "method_only")
        self.assertEqual(task_pack["pipeline_plan"]["source"], "trusted_scenario_bundle")
        self.assertTrue(task_pack["pipeline_plan"]["stages"])
        self.assertIn("ai-opensquilla-metaskill-workflow", names)
        self.assertIn("ai-opensquilla-token-routing-pattern", names)
        self.assertIn("code-test-regression", names)
        self.assertEqual(task_pack["task_taxonomy"]["category"], "ai")
        self.assertEqual(task_pack["task_taxonomy"]["subcategory"], "ai.skill_router_review")
        self.assertEqual(task_pack["contract_diagnostics"]["graph_mode"], "contract")
        self.assertEqual(task_pack["contract_diagnostics"]["fallback_reason"], "")
        self.assertEqual(task_pack["contract_diagnostics"]["graph_issue_count"], 0)

    def test_real_catalog_scenario_router_covers_supply_chain_review_for_router_quality(self):
        task_pack_out = io.StringIO()
        with contextlib.redirect_stdout(task_pack_out):
            task_pack_code = main(
                [
                    "task-pack",
                    "--schema-version",
                    "1",
                    "复查 skill-router-quality-review 的 supply_chain_review coverage 缺口",
                    "--registry",
                    "catalog",
                    "--include-bundles",
                    "--bundles",
                    "bundles/index.json",
                    "--router",
                    "scenario",
                    "--max-skills",
                    "8",
                    "--format",
                    "json",
                ]
            )

        self.assertEqual(task_pack_code, 0)
        task_pack = json.loads(task_pack_out.getvalue())
        names = [skill["name"] for skill in task_pack["skills"]]
        coverage = {item["capability"]: item for item in task_pack["coverage"]}

        self.assertEqual(task_pack["selected_scenario"]["id"], "skill-router-quality-review")
        self.assertIn("security-supply-chain-review", names)
        self.assertEqual(coverage["supply_chain_review"]["status"], "covered")
        self.assertEqual(task_pack["selection_quality"]["missing_required_count"], 0)

    def test_task_pack_script_prefers_repository_local_project_over_stale_safe_agent_home(self):
        script = Path("integrations/skills/safe-agent-router/scripts/task_pack.sh").resolve()

        with tempfile.TemporaryDirectory() as tmp:
            stale_home = Path(tmp) / "stale-safe-agent-skills"
            (stale_home / "catalog").mkdir(parents=True)
            env = os.environ.copy()
            env["SAFE_AGENT_SKILLS_HOME"] = str(stale_home)

            result = subprocess.run(
                [
                    "sh",
                    str(script),
                    "复查 safe-agent-skills 项目是否达到智能选择和自动搭配 skill 的目标",
                    "--format",
                    "json",
                ],
                cwd=Path.cwd(),
                capture_output=True,
                env=env,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        task_pack = json.loads(result.stdout)
        self.assertEqual(task_pack["schema_version"], 2)
        self.assertEqual(task_pack["routing_mode"], "hybrid")
        self.assertEqual(task_pack["selected_scenarios"][0]["scenario_id"], "skill-router-quality-review")
        self.assertIn("execution_graph", task_pack)

    def test_task_pack_script_supports_explicit_v3_without_changing_default(self):
        script = Path("integrations/skills/safe-agent-router/scripts/task_pack.sh").resolve()
        default = subprocess.run(
            ["sh", str(script), "review this patch", "--format", "json"],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            check=False,
        )
        explicit_v3 = subprocess.run(
            [
                "sh",
                str(script),
                "review this patch",
                "--format",
                "json",
                "--routing-examples",
                "catalog/routing-examples.json",
                "--max-skills",
                "3",
                "--schema-version",
                "3",
            ],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(default.returncode, 0, default.stderr)
        self.assertEqual(json.loads(default.stdout)["schema_version"], 2)
        self.assertEqual(explicit_v3.returncode, 0, explicit_v3.stderr)
        self.assertEqual(json.loads(explicit_v3.stdout)["schema_version"], 3)

    def test_task_pack_script_rejects_unsupported_schema_and_missing_values(self):
        script = Path("integrations/skills/safe-agent-router/scripts/task_pack.sh").resolve()
        invalid_arguments = (
            ["--schema-version", "1"],
            ["--schema-version", "4"],
            ["--schema-version"],
            ["--routing-examples"],
        )
        for arguments in invalid_arguments:
            with self.subTest(arguments=arguments):
                result = subprocess.run(
                    ["sh", str(script), "review this patch", *arguments],
                    cwd=Path.cwd(),
                    capture_output=True,
                    text=True,
                    check=False,
                )

                self.assertEqual(result.returncode, 2)
                self.assertNotIn("Traceback", result.stderr)

    def test_real_catalog_scenario_router_routes_audit_followup_to_skill_router_bundle(self):
        task_pack_out = io.StringIO()
        with contextlib.redirect_stdout(task_pack_out):
            task_pack_code = main(
                [
                    "task-pack",
                    "--schema-version",
                    "1",
                    "继续，按照步骤，完成全部任务，以及审计报告给出的，更智能的解决方法",
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
        names = [skill["name"] for skill in task_pack["skills"]]
        self.assertEqual(task_pack["task_profile"]["task_type"], "skill_router_review")
        self.assertEqual(task_pack["selected_scenario"]["id"], "skill-router-quality-review")
        self.assertEqual(task_pack["pipeline_plan"]["id"], "skill-router-quality-review")
        self.assertIn("ai-opensquilla-metaskill-workflow", names)
        self.assertIn("ai-opensquilla-token-routing-pattern", names)
        self.assertNotEqual(task_pack["selected_scenario"]["id"], "data-analysis-report")

    def test_real_catalog_scenario_router_handles_real_world_regression_set(self):
        cases = [
            (
                "把剩余 claude-skills reference-only backlog 候选 skill 优化编排并纳入体系",
                "claude-skills-backlog-coverage",
            ),
            (
                "评估 claude skills candidate map 是否全部覆盖到 trusted 本地技能",
                "claude-skills-backlog-coverage",
            ),
            (
                "复查 safe-agent-skills 项目是否达到智能选择和自动搭配 skill 的目标",
                "skill-router-quality-review",
            ),
            (
                "优化技能库的自动推荐和任务编排能力",
                "skill-router-quality-review",
            ),
            (
                "继续，优化和编排sikll，继续补充和优化，做好记录和测试",
                "skill-router-quality-review",
            ),
            (
                "写好更新记录后，继续优化任务",
                "skill-router-quality-review",
            ),
            (
                "继续优化任务",
                "",
            ),
            (
                "優化技能庫的自動推薦和任務編排能力",
                "skill-router-quality-review",
            ),
            (
                "完善 skill 選擇與執行編排，避免錯誤調用不相關技能",
                "skill-router-quality-review",
            ),
            (
                "skill router quality review for bundle selection and task pack schema",
                "skill-router-quality-review",
            ),
            (
                "继续项目复查收尾，写好更新日志和 GitHub 更新说明，验证后发布",
                "skill-router-quality-review",
            ),
            (
                "build a product website and prepare launch checks",
                "website-build-launch",
            ),
            (
                "构建产品官网并准备上线发布检查",
                "website-build-launch",
            ),
            (
                "design a RAG document agent with vector retrieval and citation checks",
                "rag-agent-knowledge-app",
            ),
            (
                "设计一个带向量检索和引用检查的 RAG 知识代理",
                "rag-agent-knowledge-app",
            ),
            (
                "analyze a reference TikTok video, estimate media production cost, and plan an agentic Remotion render QA gate",
                "agentic-media-production",
            ),
            (
                "design long-term graph memory for agents with remember recall forget improve and tenant isolation",
                "agent-long-term-memory-governance",
            ),
            (
                "use an MCP code graph index for call graph exploration and git diff impact analysis",
                "codebase-graph-intelligence",
            ),
            (
                "把 PDF 文档转成知识库并做引用检查",
                "document-to-knowledge-base",
            ),
            (
                "convert office documents into markdown chunks for a searchable knowledge base",
                "document-to-knowledge-base",
            ),
            (
                "review generated code and harden tests before accepting the PR",
                "code-review-hardening",
            ),
            (
                "代码审查生成代码，补强测试后再合并 PR",
                "code-review-hardening",
            ),
            (
                "Explore 摸清项目地图，Debugger 定位疑难 bug，Test Engineer 完善回归测试",
                "codebase-change-lifecycle",
            ),
            (
                "Deep Interview 厘清模糊需求，Plan 拆解，多 agent 协同执行",
                "agent-planning-orchestration",
            ),
            (
                "Prepare marketplace listing keywords and buyer inquiry replies",
                "commerce-listing-growth",
            ),
            (
                "优化商品 listing 关键词，并准备买家询盘回复",
                "commerce-listing-growth",
            ),
            (
                "为医疗、金融、教育、制造和房地产客户设计一套行业 AI 应用方案，包含合规边界、数据质量和交付计划",
                "industry-application-orchestration",
            ),
            (
                "build an industry solution pack for healthcare, legal, finance, education, manufacturing, and SaaS users",
                "industry-application-orchestration",
            ),
            (
                "帮我看一下这个事情是否合理",
                "",
            ),
        ]

        for task, expected_scenario in cases:
            with self.subTest(task=task):
                task_pack_out = io.StringIO()
                with contextlib.redirect_stdout(task_pack_out):
                    task_pack_code = main(
                        [
                            "task-pack",
                            "--schema-version",
                            "1",
                            task,
                            "--registry",
                            "catalog",
                            "--include-bundles",
                            "--bundles",
                            "bundles/index.json",
                            "--router",
                            "scenario",
                            "--max-skills",
                            "10",
                        ]
                    )

                self.assertEqual(task_pack_code, 0)
                task_pack = json.loads(task_pack_out.getvalue())
                self.assertEqual(task_pack["selected_scenario"]["id"], expected_scenario)
                if expected_scenario:
                    self.assertEqual(task_pack["bundles"][0]["id"], expected_scenario)
                    self.assertEqual(task_pack["pipeline_plan"]["id"], expected_scenario)
                else:
                    self.assertEqual(task_pack["bundle_count"], 0)
                    self.assertEqual(task_pack["bundles"], [])

    def test_real_catalog_smart_router_selects_skill_router_quality_review_bundle(self):
        task_pack_out = io.StringIO()
        with contextlib.redirect_stdout(task_pack_out):
            task_pack_code = main(
                [
                    "smart",
                    "--schema-version",
                    "1",
                    "复查 safe-agent-skills 项目是否达到智能选择和自动搭配 skill 的目标",
                    "--registry",
                    "catalog",
                    "--bundles",
                    "bundles/index.json",
                    "--max-skills",
                    "8",
                ]
            )

        self.assertEqual(task_pack_code, 0)
        task_pack = json.loads(task_pack_out.getvalue())
        names = [skill["name"] for skill in task_pack["skills"]]
        self.assertEqual(task_pack["task_profile"]["task_type"], "skill_router_review")
        self.assertEqual(task_pack["selected_scenario"]["id"], "skill-router-quality-review")
        self.assertEqual(task_pack["bundle_count"], 1)
        self.assertEqual(task_pack["bundles"][0]["id"], "skill-router-quality-review")
        self.assertEqual(task_pack["pipeline_plan"]["id"], "skill-router-quality-review")
        self.assertEqual(task_pack["pipeline_plan"]["mode"], "method_only")
        self.assertTrue(task_pack["pipeline_plan"]["stages"])
        self.assertIn("ai-opensquilla-metaskill-workflow", names)
        self.assertIn("ai-opensquilla-token-routing-pattern", names)
        self.assertEqual(names[:2], ["ai-opensquilla-metaskill-workflow", "ai-opensquilla-token-routing-pattern"])
        self.assertTrue(task_pack["execution_graph"]["acyclic"])
        execution_order = [step["skill"] for step in task_pack["execution_plan"]]
        self.assertLess(execution_order.index("security-supply-chain-review"), execution_order.index("code-test-regression"))
        self.assertGreater(execution_order.index("ai-rule-failure-log-synthesis"), execution_order.index("engineering-ci-troubleshoot"))

    def test_smart_markdown_renders_pipeline_plan(self):
        task_pack_out = io.StringIO()
        with contextlib.redirect_stdout(task_pack_out):
            task_pack_code = main(
                [
                    "smart",
                    "--schema-version",
                    "1",
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
        self.assertIn("- evidence fields: `status`, `evidence`, `failed_checks`, `unresolved_assumptions`, `residual_risks`", markdown)
        self.assertIn("method-only", markdown.lower())

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
        for skill in payload["skills"]:
            self.assertNotIn("schema_version", skill.get("contract", {}))
            self.assertNotIn("approval_classes", skill.get("contract", {}))
            if skill["name"] == "codebase-explore-map":
                self.assertNotIn("contract", skill)
        self.assertEqual(payload_shape_sha256(payload), ROUTER_SCHEMA_V1_SHAPE_SHA256)

    def test_task_pack_mesh_schema_v1_preserves_current_contract_shape(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            exit_code = main(
                [
                    "task-pack",
                    "build a landing page and prepare launch checks",
                    "--registry",
                    "catalog",
                    "--bundles",
                    "bundles/index.json",
                    "--router",
                    "mesh",
                    "--max-skills",
                    "8",
                    "--include-bundles",
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
        self.assertEqual(payload_shape_sha256(payload), ROUTER_SCHEMA_V1_SHAPE_SHA256)

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
                        "--schema-version",
                        "1",
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
            self.assertNotIn("pipeline_plan", task_pack)
            self.assertEqual(task_pack["skills"][0]["name"], "design-dashboard")

    def test_real_catalog_scenario_router_selects_website_bundle(self):
        task_pack_out = io.StringIO()
        with contextlib.redirect_stdout(task_pack_out):
            task_pack_code = main(
                [
                    "task-pack",
                    "--schema-version",
                    "1",
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
        self.assertIn("selection_quality", task_pack)
        self.assertIn(task_pack["selection_quality"]["confidence"], {"high", "medium"})
        self.assertGreater(task_pack["selection_quality"]["coverage_ratio"], 0)
        self.assertIn("acceptance_criteria", task_pack)
        self.assertIn("completion_contract", task_pack)

    def test_real_catalog_scenario_router_keeps_vague_general_fallback_lightweight(self):
        task_pack_out = io.StringIO()
        with contextlib.redirect_stdout(task_pack_out):
            task_pack_code = main(
                [
                    "task-pack",
                    "--schema-version",
                    "1",
                    "可以，按照步骤，继续优化",
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
        names = [skill["name"] for skill in task_pack["skills"]]

        self.assertEqual(task_pack["task_profile"]["task_type"], "general")
        self.assertEqual(task_pack["selected_scenario"]["id"], "")
        self.assertTrue(task_pack["selection_quality"]["low_confidence"])
        self.assertLessEqual(len(names), 3)
        self.assertIn("execution-file-batch", names)
        self.assertIn("execution-rollback-checkpoint-plan", names)
        self.assertNotIn("execution-browser-use-web-task", names)
        self.assertNotIn("execution-playwright-browser-automation", names)
        self.assertNotIn("execution-publish-check", names)

        smart_out = io.StringIO()
        with contextlib.redirect_stdout(smart_out):
            smart_code = main(
                [
                    "smart",
                    "--schema-version",
                    "1",
                    "可以，按照步骤，继续优化",
                    "--max-skills",
                    "8",
                ]
            )

        self.assertEqual(smart_code, 0)
        smart_pack = json.loads(smart_out.getvalue())
        smart_names = [skill["name"] for skill in smart_pack["skills"]]
        self.assertEqual(smart_pack["task_profile"]["task_type"], "general")
        self.assertEqual(smart_pack["selected_scenario"]["id"], "")
        self.assertTrue(smart_pack["selection_quality"]["low_confidence"])
        self.assertEqual(smart_names, ["execution-file-batch", "execution-rollback-checkpoint-plan"])

    def test_task_pack_markdown_renders_low_confidence_explanations(self):
        task_pack_out = io.StringIO()
        with contextlib.redirect_stdout(task_pack_out):
            task_pack_code = main(
                [
                    "task-pack",
                    "--schema-version",
                    "1",
                    "可以，按照步骤，继续优化",
                    "--registry",
                    "catalog",
                    "--include-bundles",
                    "--bundles",
                    "bundles/index.json",
                    "--router",
                    "scenario",
                    "--max-skills",
                    "8",
                    "--format",
                    "markdown",
                ]
            )

        self.assertEqual(task_pack_code, 0)
        markdown = task_pack_out.getvalue()
        self.assertIn("## Selection Quality", markdown)
        self.assertIn("- reason: `no_trusted_scenario_match`", markdown)
        self.assertIn("- explanation: No trusted scenario bundle matched the task.", markdown)
        self.assertIn("- recommended action: Record low-confidence route as a residual risk.", markdown)

    def test_smart_defaults_resolve_repository_assets_from_environment(self):
        original_cwd = Path.cwd()
        original_home = os.environ.get("SAFE_AGENT_SKILLS_HOME")
        with tempfile.TemporaryDirectory() as tmp:
            try:
                os.environ["SAFE_AGENT_SKILLS_HOME"] = str(original_cwd)
                os.chdir(tmp)
                task_pack_out = io.StringIO()
                with contextlib.redirect_stdout(task_pack_out):
                    task_pack_code = main(
                        [
                            "smart",
                            "--schema-version",
                            "1",
                            "审查整个项目，看是否还有需要优化和完善的地方",
                            "--max-skills",
                            "8",
                        ]
                    )
            finally:
                os.chdir(original_cwd)
                if original_home is None:
                    os.environ.pop("SAFE_AGENT_SKILLS_HOME", None)
                else:
                    os.environ["SAFE_AGENT_SKILLS_HOME"] = original_home

        self.assertEqual(task_pack_code, 0)
        task_pack = json.loads(task_pack_out.getvalue())
        self.assertEqual(task_pack["selected_scenario"]["id"], "codebase-change-lifecycle")
        self.assertEqual(task_pack["task_profile"]["task_type"], "codebase_change_lifecycle")

    def test_real_catalog_scenario_router_selects_rag_bundle(self):
        task_pack_out = io.StringIO()
        with contextlib.redirect_stdout(task_pack_out):
            task_pack_code = main(
                [
                    "task-pack",
                    "--schema-version",
                    "1",
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

    def test_real_catalog_scenario_router_selects_industry_application_bundle(self):
        task_pack_out = io.StringIO()
        with contextlib.redirect_stdout(task_pack_out):
            task_pack_code = main(
                [
                    "task-pack",
                    "--schema-version",
                    "1",
                    "为医疗、金融、教育、制造和房地产客户设计一套行业 AI 应用方案，包含合规边界、数据质量和交付计划",
                    "--registry",
                    "catalog",
                    "--include-bundles",
                    "--bundles",
                    "bundles/index.json",
                    "--router",
                    "scenario",
                    "--max-skills",
                    "12",
                ]
            )

        self.assertEqual(task_pack_code, 0)
        task_pack = json.loads(task_pack_out.getvalue())
        names = [skill["name"] for skill in task_pack["skills"]]
        coverage = {item["capability"]: item for item in task_pack["coverage"]}
        self.assertEqual(task_pack["selected_scenario"]["id"], "industry-application-orchestration")
        self.assertEqual(task_pack["bundles"][0]["id"], "industry-application-orchestration")
        self.assertIn("vertical-industry-intake-orchestration", names)
        self.assertIn("compliance-regulated-industry-boundary", names)
        self.assertIn("vertical-industry-solution-packaging", names)
        self.assertEqual(coverage["industry_intake"]["status"], "covered")
        self.assertEqual(coverage["regulated_boundary"]["status"], "covered")
        self.assertEqual(coverage["solution_packaging"]["status"], "covered")


if __name__ == "__main__":
    unittest.main()
