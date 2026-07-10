import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator

from onecode_skill_sanitizer.cli import _routing_status
from onecode_skill_sanitizer.cli import main
from onecode_skill_sanitizer.cli import render_task_pack_v2_markdown

from tests.registry_cli_helpers import validate_task_pack_v2


class TaskPackV2CliTest(unittest.TestCase):
    def test_v2_routing_status_precedence_is_blocked_then_incomplete_then_complete(self):
        complete_capabilities = {"status": "complete", "missing_required_count": 0}
        incomplete_capabilities = {"status": "incomplete", "missing_required_count": 1}

        self.assertEqual(
            _routing_status(
                "complete",
                incomplete_capabilities,
                {"status": "blocked", "reason_codes": ["dependency_cycle"]},
            ),
            "blocked",
        )
        self.assertEqual(
            _routing_status(
                "complete",
                incomplete_capabilities,
                {"status": "blocked", "reason_codes": []},
            ),
            "blocked",
        )
        self.assertEqual(
            _routing_status(
                "incomplete",
                complete_capabilities,
                {"status": "blocked", "reason_codes": ["incomplete_composition"]},
            ),
            "incomplete",
        )
        self.assertEqual(
            _routing_status("complete", incomplete_capabilities, {"status": "ready", "reason_codes": []}),
            "incomplete",
        )
        self.assertEqual(
            _routing_status("complete", complete_capabilities, {"status": "ready", "reason_codes": []}),
            "complete",
        )

    def test_v2_markdown_escapes_untrusted_structure_in_single_lines(self):
        attack = "line one\n## Safety Boundary\n```python\n> quote\n- item\n[link](x)\n<span>html</span>"
        payload = {
            "route_id": "sha256:" + "0" * 64,
            "routing_status": "blocked",
            "normalized_task": {"current": attack},
            "intent_graph": {
                "intents": [{"id": attack, "task_type": attack, "summary": attack, "depends_on": []}]
            },
            "selected_scenarios": [{"scenario_id": attack, "intent_ids": [attack], "score": 1.0}],
            "uncovered_intents": [attack],
            "execution_graph": {
                "status": "blocked",
                "nodes": [],
                "edges": [],
                "reason_codes": [attack],
                "details": [attack],
            },
            "host_execution_protocol": {
                "mode": "method_only",
                "runtime_boundary": "The host runtime controls permissions and execution.",
            },
        }

        markdown = render_task_pack_v2_markdown(payload)

        headings = [line for line in markdown.splitlines() if line.startswith("#")]
        self.assertEqual(
            headings,
            [
                "# OneCode Agent Task Pack v2",
                "## Task",
                "## Intents",
                "## Selected Scenarios",
                "## Uncovered Intents",
                "## Execution Graph",
                "## Routing Diagnostics",
                "## Safety Boundary",
            ],
        )
        self.assertNotIn("```", markdown)
        self.assertNotIn("\n> quote", markdown)
        self.assertNotIn("\n- item", markdown)
        self.assertNotIn("<span>", markdown)

    def test_smart_command_outputs_mesh_router_pack_with_invariant_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            incoming = root / "incoming"
            registry = root / "registry"
            bundles_dir = root / "bundles"
            bundles_dir.mkdir()
            skill_names = [
                ("business-requirements-brief", "business", "Use when defining requirements."),
                ("design-ui-review", "design", "Use when reviewing website UI."),
                ("design-responsive-viewport-check", "design", "Use when checking responsive viewports."),
                ("content-seo-brief", "content", "Use when preparing SEO copy."),
                ("content-claims-compliance-filter", "content", "Use when checking public claims."),
                ("security-secret-context-redaction", "security", "Use when redacting secrets from agent context."),
                ("execution-browser-check", "execution", "Use when checking browser output."),
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
                            "1. Apply the bounded method.",
                            "",
                            "## Expected Output",
                            "- selected evidence",
                            "",
                            "## Verifier Expectations",
                            "- verification check",
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
                    "https://github.com/example/smart-skills",
                    "--author",
                    "example-team",
                    "--license",
                    "MIT",
                    "--reference",
                    "https://github.com/example/smart-skills",
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
                                "scenario": "Build or polish a website, landing page, dashboard, or product page.",
                                "status": "trusted",
                                "task_signals": ["website", "landing page", "launch"],
                                "skills": [
                                    "business-requirements-brief",
                                    "design-ui-review",
                                    "content-seo-brief",
                                    "execution-browser-check",
                                ],
                                "required_capabilities": [
                                    {
                                        "id": "requirements",
                                        "required": True,
                                        "preferred_skills": ["business-requirements-brief"],
                                    },
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
                                ],
                                "execution_order": [
                                    "business-requirements-brief",
                                    "design-ui-review",
                                    "content-seo-brief",
                                    "execution-browser-check",
                                ],
                                "expected_output": ["launch checklist"],
                                "safety_boundary": "Skills provide method only.",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (registry / "overlap-groups.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "group_count": 1,
                        "groups": [
                            {
                                "id": "ui-quality-review",
                                "name": "UI Quality Review",
                                "status": "trusted",
                                "intent": "Prefer primary UI review unless responsive checks are required.",
                                "primary_skill": "design-ui-review",
                                "adjacent_skills": ["design-responsive-viewport-check"],
                                "use_before": [],
                                "use_after": [],
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
                        "smart",
                        "--schema-version",
                        "1",
                        "build a landing page and prepare launch checks",
                        "--registry",
                        str(registry),
                        "--bundles",
                        str(bundles_dir / "index.json"),
                        "--invariants",
                        "不能泄露密钥；公开文案必须合规；必须响应式验证",
                    ]
                )

            self.assertEqual(task_pack_code, 0)
            task_pack = json.loads(task_pack_out.getvalue())
            names = [skill["name"] for skill in task_pack["skills"]]
            self.assertEqual(task_pack["router"]["mode"], "deterministic_mesh_router")
            self.assertIn("security-secret-context-redaction", names)
            self.assertIn("content-claims-compliance-filter", names)
            self.assertIn("design-responsive-viewport-check", names)
            self.assertTrue(task_pack["execution_graph"]["edges"])

    def test_smart_schema_v2_routes_compound_task(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            exit_code = main(
                [
                    "smart",
                    "构建官网，同时审计 skill 路由器，验证通过后发布更新",
                    "--registry",
                    "catalog",
                    "--bundles",
                    "bundles/index.json",
                    "--schema-version",
                    "2",
                    "--format",
                    "json",
                ]
            )
        payload = json.loads(out.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["schema_version"], 2)
        self.assertEqual(
            [scenario["scenario_id"] for scenario in payload["selected_scenarios"]],
            ["website-build-launch", "skill-router-quality-review", "open-source-release"],
        )
        self.assertEqual(payload["execution_graph"]["status"], "ready")
        self.assertEqual(payload["routing_status"], "complete")
        self.assertEqual(payload["provider"]["used"], "none")
        self.assertEqual(payload["host_execution_protocol"]["mode"], "method_only")
        graph_skills = {node["skill"] for node in payload["execution_graph"]["nodes"]}
        selected_skills = {skill["name"] for skill in payload["selected_skills"]}
        self.assertLessEqual(payload["routing_metrics"]["optional_skill_limit"], 8)
        self.assertTrue(graph_skills.issubset(selected_skills))

    def test_smart_schema_v2_marks_contract_approval_nodes_as_host_actions(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(
                main(
                    [
                        "smart",
                        "构建官网，同时验证通过后发布更新",
                        "--schema-version",
                        "2",
                        "--format",
                        "json",
                    ]
                ),
                0,
            )
        payload = json.loads(out.getvalue())
        nodes = {node["skill"]: node for node in payload["execution_graph"]["nodes"]}

        self.assertTrue(nodes["engineering-build-release"]["host_action"])
        self.assertTrue(nodes["research-source-check"]["host_action"])

    def test_smart_schema_v2_preserves_selected_skill_contracts(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(
                main(
                    [
                        "smart",
                        "构建官网，同时验证通过后发布更新",
                        "--schema-version",
                        "2",
                        "--format",
                        "json",
                    ]
                ),
                0,
            )
        payload = json.loads(out.getvalue())
        selected = {skill["name"]: skill for skill in payload["selected_skills"]}

        self.assertEqual(selected["engineering-build-release"]["contract"]["stage_hint"], "execution")
        self.assertNotIn("contract", selected["compliance-terms-review"])
        self.assertNotIn("contract", selected["content-editorial-review"])

        contract_schema = json.loads(Path("schemas/contract-v2.schema.json").read_text(encoding="utf-8"))
        validator = Draft202012Validator(contract_schema)
        for skill in selected.values():
            if "contract" in skill:
                self.assertEqual(list(validator.iter_errors(skill["contract"])), [])

    def test_v2_empty_task_returns_bounded_error(self):
        for command in ("smart", "task-pack"):
            for output_format in ("json", "markdown"):
                with self.subTest(command=command, output_format=output_format):
                    out = io.StringIO()
                    err = io.StringIO()
                    argv = [command, "", "--schema-version", "2", "--format", output_format]
                    if command == "task-pack":
                        argv.extend(["--registry", "catalog", "--bundles", "bundles/index.json"])
                    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                        exit_code = main(argv)
                    output = out.getvalue()
                    self.assertEqual(exit_code, 2)
                    self.assertEqual(err.getvalue(), "")
                    self.assertNotIn("Traceback", output)
                    if output_format == "json":
                        payload = json.loads(output)
                        self.assertEqual(payload["status"], "error")
                        self.assertEqual(payload["error"]["code"], "invalid_input")
                    else:
                        self.assertIn("# OneCode Task Pack v2 Error", output)

    def test_smart_schema_v2_marks_vague_task_incomplete(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            exit_code = main(["smart", "help me with this", "--schema-version", "2", "--format", "json"])
        payload = json.loads(out.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["routing_status"], "incomplete")
        self.assertEqual(payload["selected_scenarios"], [])
        self.assertEqual(payload["uncovered_intents"], ["i1"])

    def test_task_pack_schema_v2_returns_v2_contract(self):
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
                    "scenario",
                    "--schema-version",
                    "2",
                    "--format",
                    "json",
                ]
            )
        payload = json.loads(out.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["schema_version"], 2)
        self.assertEqual(payload["routing_mode"], "hybrid")
        self.assertIn("selected_scenarios", payload)

    def test_smart_schema_v2_default_and_low_max_skills_keep_graph_consistent(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            exit_code = main(
                [
                    "smart",
                    "构建官网，同时审计 skill 路由器，验证通过后发布更新",
                    "--registry",
                    "catalog",
                    "--bundles",
                    "bundles/index.json",
                    "--max-skills",
                    "1",
                    "--format",
                    "json",
                ]
            )
        payload = json.loads(out.getvalue())
        graph_skills = {node["skill"] for node in payload["execution_graph"]["nodes"]}
        selected_skills = {skill["name"] for skill in payload["selected_skills"]}
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["schema_version"], 2)
        self.assertTrue(graph_skills.issubset(selected_skills))
        self.assertGreater(len(selected_skills), 1)

    def test_smart_schema_v2_route_id_is_stable_and_changes_with_task(self):
        route_ids = []
        for task in ["build a landing page", "build a landing page", "audit the skill router"]:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(main(["smart", task, "--schema-version", "2", "--format", "json"]), 0)
            route_ids.append(json.loads(out.getvalue())["route_id"])
        self.assertEqual(route_ids[0], route_ids[1])
        self.assertNotEqual(route_ids[0], route_ids[2])

    def test_smart_schema_v2_route_id_redacts_embedded_secret_values_end_to_end(self):
        tasks = [
            "build a landing page api_key=alpha Bearer aaa.bbb password: first",
            "build a landing page api_key=beta Bearer ccc.ddd password: second",
            "audit the skill router api_key=alpha Bearer aaa.bbb password: first",
        ]
        route_ids = []
        for task in tasks:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(main(["smart", task, "--schema-version", "2", "--format", "json"]), 0)
            route_ids.append(json.loads(out.getvalue())["route_id"])

        self.assertEqual(route_ids[0], route_ids[1])
        self.assertNotEqual(route_ids[0], route_ids[2])

    def test_smart_schema_v2_route_id_redacts_full_width_chinese_secret_assignments(self):
        pairs = [
            ("密码：甲，构建官网", "密码：乙，构建官网"),
            ("访问令牌：令牌甲，构建官网", "访问令牌：令牌乙，构建官网"),
            ("授权：授权甲，构建官网", "授权：授权乙，构建官网"),
            ("会话：会话甲，构建官网", "会话：会话乙，构建官网"),
            ("私钥：私钥甲，构建官网", "私钥：私钥乙，构建官网"),
            ("密钥＝密钥甲，构建官网", "密钥＝密钥乙，构建官网"),
            (
                "历史：密码：历史甲，保留审计上下文\n当前任务：构建官网",
                "历史：密码：历史乙，保留审计上下文\n当前任务：构建官网",
            ),
        ]
        for first_task, second_task in pairs:
            with self.subTest(first_task=first_task):
                route_ids = []
                for task in [first_task, second_task]:
                    out = io.StringIO()
                    with contextlib.redirect_stdout(out):
                        self.assertEqual(main(["smart", task, "--schema-version", "2", "--format", "json"]), 0)
                    route_ids.append(json.loads(out.getvalue())["route_id"])
                self.assertEqual(route_ids[0], route_ids[1])

        intent_route_ids = []
        for task in ["密码：甲，构建官网", "密码：乙，审计 skill 路由器"]:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(main(["smart", task, "--schema-version", "2", "--format", "json"]), 0)
            intent_route_ids.append(json.loads(out.getvalue())["route_id"])
        self.assertNotEqual(intent_route_ids[0], intent_route_ids[1])

    def test_smart_schema_v2_route_id_uses_canonical_overlap_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            overlap_a = root / "first" / "overlap.json"
            overlap_b = root / "second" / "renamed.json"
            overlap_c = root / "changed.json"
            overlap_a.parent.mkdir()
            overlap_b.parent.mkdir()
            shared = {
                "schema_version": 1,
                "group_count": 1,
                "generated_at": "2026-07-10T00:00:00Z",
                "api_key": "secret-one",
                "groups": [{"id": "shared", "status": "trusted", "primary_skill": "design-ui-review"}],
            }
            same_material = copy.deepcopy(shared)
            same_material["generated_at"] = "2027-01-01T00:00:00Z"
            same_material["api_key"] = "secret-two"
            changed = copy.deepcopy(shared)
            changed["groups"][0]["primary_skill"] = "design-system-consistency"
            for path, content in [(overlap_a, shared), (overlap_b, same_material), (overlap_c, changed)]:
                path.write_text(json.dumps(content), encoding="utf-8")

            route_ids = []
            for overlap_path in [overlap_a, overlap_b, overlap_c]:
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    self.assertEqual(
                        main(
                            [
                                "smart",
                                "build a landing page",
                                "--overlap-groups",
                                str(overlap_path),
                                "--schema-version",
                                "2",
                                "--format",
                                "json",
                            ]
                        ),
                        0,
                    )
                route_ids.append(json.loads(out.getvalue())["route_id"])

        self.assertEqual(route_ids[0], route_ids[1])
        self.assertNotEqual(route_ids[0], route_ids[2])

    def test_v2_validates_overlap_groups_and_records_not_applied_policy(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(
                main(["smart", "build a landing page", "--schema-version", "2", "--format", "json"]),
                0,
            )
        payload = json.loads(out.getvalue())
        self.assertEqual(payload["routing_metrics"]["overlap_policy"], "validated_not_applied")

    def test_v2_overlap_structure_and_trust_failures_are_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            invalid_payloads = [
                [],
                {},
                {"schema_version": 1, "groups": ["not-an-object"]},
                {
                    "schema_version": 1,
                    "group_count": 1,
                    "groups": [
                        {
                            "id": "untrusted",
                            "status": "review_required",
                            "primary_skill": "design-ui-review",
                        }
                    ],
                },
                {
                    "schema_version": 1,
                    "group_count": 1,
                    "groups": [
                        {
                            "id": "unknown-reference",
                            "status": "trusted",
                            "primary_skill": "missing-skill",
                        }
                    ],
                },
            ]
            cases = []
            for index, payload in enumerate(invalid_payloads):
                overlap_path = root / f"overlap-{index}.json"
                overlap_path.write_text(json.dumps(payload), encoding="utf-8")
                cases.extend(
                    [
                        ["smart", "build site", "--schema-version", "2", "--overlap-groups", str(overlap_path)],
                        [
                            "task-pack",
                            "build site",
                            "--registry",
                            "catalog",
                            "--schema-version",
                            "2",
                            "--overlap-groups",
                            str(overlap_path),
                        ],
                    ]
                )

            for argv in cases:
                for output_format in ("json", "markdown"):
                    with self.subTest(argv=argv, output_format=output_format):
                        out = io.StringIO()
                        err = io.StringIO()
                        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                            exit_code = main([*argv, "--format", output_format])
                        output = out.getvalue()
                        self.assertEqual(exit_code, 2)
                        self.assertEqual(err.getvalue(), "")
                        self.assertNotIn("Traceback", output)
                        self.assertNotIn(str(root), output)
                        if output_format == "json":
                            payload = json.loads(output)
                            self.assertEqual(payload["schema_version"], 2)
                            self.assertEqual(payload["status"], "error")
                        else:
                            self.assertIn("# OneCode Task Pack v2 Error", output)

    def test_v2_overlap_group_id_type_failures_are_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for index, group_id in enumerate(({}, 123)):
                overlap_path = root / f"invalid-id-{index}.json"
                overlap_path.write_text(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "group_count": 1,
                            "groups": [
                                {
                                    "id": group_id,
                                    "status": "trusted",
                                    "primary_skill": "design-ui-review",
                                }
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                commands = [
                    ["smart", "build site", "--schema-version", "2", "--overlap-groups", str(overlap_path)],
                    [
                        "task-pack",
                        "build site",
                        "--registry",
                        "catalog",
                        "--schema-version",
                        "2",
                        "--overlap-groups",
                        str(overlap_path),
                    ],
                ]
                for argv in commands:
                    for output_format in ("json", "markdown"):
                        with self.subTest(group_id=group_id, argv=argv, output_format=output_format):
                            out = io.StringIO()
                            err = io.StringIO()
                            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                                exit_code = main([*argv, "--format", output_format])
                            output = out.getvalue()
                            self.assertEqual(exit_code, 2)
                            self.assertEqual(err.getvalue(), "")
                            self.assertNotIn("Traceback", output)
                            self.assertNotIn(str(root), output)
                            if output_format == "json":
                                payload = json.loads(output)
                                self.assertEqual(payload["schema_version"], 2)
                                self.assertEqual(payload["status"], "error")
                            else:
                                self.assertIn("# OneCode Task Pack v2 Error", output)

    def test_smart_schema_v2_marks_missing_required_capability_incomplete(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundles_path = Path(tmp) / "bundles.json"
            bundles = json.loads(Path("bundles/index.json").read_text(encoding="utf-8"))
            website = copy.deepcopy(next(bundle for bundle in bundles["bundles"] if bundle["id"] == "website-build-launch"))
            website["required_capabilities"].append(
                {"id": "missing_required", "required": True, "preferred_skills": []}
            )
            bundles_path.write_text(
                json.dumps({"schema_version": 1, "bundle_count": 1, "bundles": [website]}),
                encoding="utf-8",
            )
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(
                    main(
                        [
                            "smart",
                            "build a landing page",
                            "--bundles",
                            str(bundles_path),
                            "--schema-version",
                            "2",
                            "--format",
                            "json",
                        ]
                    ),
                    0,
                )
            payload = json.loads(out.getvalue())

        self.assertEqual(payload["execution_graph"]["status"], "ready")
        self.assertEqual(payload["capability_resolution"]["status"], "incomplete")
        self.assertEqual(payload["capability_resolution"]["missing_required_count"], 1)
        self.assertEqual(payload["routing_status"], "incomplete")

    def test_task_pack_v2_schema_validates_complete_incomplete_and_blocked_payloads(self):
        payloads = []
        for task in ["build a landing page", "help me with this"]:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(main(["smart", task, "--schema-version", "2", "--format", "json"]), 0)
            payloads.append(json.loads(out.getvalue()))

        with tempfile.TemporaryDirectory() as tmp:
            bundles_path = Path(tmp) / "blocked-bundles.json"
            bundles = json.loads(Path("bundles/index.json").read_text(encoding="utf-8"))
            website = copy.deepcopy(next(bundle for bundle in bundles["bundles"] if bundle["id"] == "website-build-launch"))
            website["execution_order"] = []
            bundles_path.write_text(
                json.dumps({"schema_version": 1, "bundle_count": 1, "bundles": [website]}),
                encoding="utf-8",
            )
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(
                    main(
                        [
                            "smart",
                            "build a landing page",
                            "--bundles",
                            str(bundles_path),
                            "--schema-version",
                            "2",
                            "--format",
                            "json",
                        ]
                    ),
                    0,
                )
            payloads.append(json.loads(out.getvalue()))

        self.assertEqual([payload["routing_status"] for payload in payloads], ["complete", "incomplete", "blocked"])
        for payload in payloads:
            with self.subTest(status=payload["routing_status"]):
                validate_task_pack_v2(payload)

    def test_smart_schema_v2_matches_strict_top_level_schema_and_markdown(self):
        json_out = io.StringIO()
        with contextlib.redirect_stdout(json_out):
            self.assertEqual(
                main(["smart", "build a landing page", "--schema-version", "2", "--format", "json"]),
                0,
            )
        payload = json.loads(json_out.getvalue())
        schema = json.loads(Path("schemas/task-pack-v2.schema.json").read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(payload), set(schema["required"]))

        markdown_out = io.StringIO()
        with contextlib.redirect_stdout(markdown_out):
            self.assertEqual(
                main(["smart", "help me with this", "--schema-version", "2", "--format", "markdown"]),
                0,
            )
        markdown = markdown_out.getvalue()
        self.assertIn("## Intents", markdown)
        self.assertIn("## Selected Scenarios", markdown)
        self.assertIn("## Uncovered Intents", markdown)
        self.assertIn("## Execution Graph", markdown)
        self.assertIn("## Safety Boundary", markdown)

    def test_real_catalog_smart_router_covers_task_and_invariant_skills(self):
        task_pack_out = io.StringIO()
        with contextlib.redirect_stdout(task_pack_out):
            task_pack_code = main(
                [
                    "smart",
                    "--schema-version",
                    "1",
                    "build a landing page and prepare launch checks",
                    "--invariants",
                    "不能泄露密钥；公开文案必须合规；必须响应式验证",
                ]
            )

        self.assertEqual(task_pack_code, 0)
        task_pack = json.loads(task_pack_out.getvalue())
        names = [skill["name"] for skill in task_pack["skills"]]
        coverage = {item["capability"]: item for item in task_pack["coverage"]}
        self.assertEqual(task_pack["router"]["mode"], "deterministic_mesh_router")
        self.assertEqual(task_pack["selected_scenario"]["id"], "website-build-launch")
        self.assertEqual(task_pack["bundles"][0]["id"], "website-build-launch")
        self.assertIn("business-requirements-brief", names)
        self.assertIn("design-ui-review", names)
        self.assertIn("content-seo-brief", names)
        self.assertIn("execution-browser-check", names)
        self.assertIn("execution-publish-check", names)
        self.assertIn("security-secret-context-redaction", names)
        self.assertIn("content-claims-compliance-filter", names)
        self.assertIn("design-responsive-viewport-check", names)
        self.assertEqual(coverage["secret_redaction"]["status"], "covered")
        self.assertEqual(coverage["claims_compliance"]["status"], "covered")
        self.assertEqual(coverage["responsive_check"]["status"], "covered")
        self.assertTrue(task_pack["execution_graph"]["acyclic"])

    def test_v2_enforces_invariant_safeguards_in_selected_skills_and_graph(self):
        invariant_text = "不能泄露密钥；公开文案必须合规；必须响应式验证"
        payloads = {}
        for schema_version in (1, 2):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(
                    main(
                        [
                            "smart",
                            "build a landing page and prepare launch checks",
                            "--schema-version",
                            str(schema_version),
                            "--invariants",
                            invariant_text,
                            "--format",
                            "json",
                        ]
                    ),
                    0,
                )
            payloads[schema_version] = json.loads(out.getvalue())

        expected = {
            "secret_redaction": "security-secret-context-redaction",
            "claims_compliance": "content-claims-compliance-filter",
            "responsive_check": "design-responsive-viewport-check",
        }
        v1_names = {skill["name"] for skill in payloads[1]["skills"]}
        v2_names = {skill["name"] for skill in payloads[2]["selected_skills"]}
        graph_names = {node["skill"] for node in payloads[2]["execution_graph"]["nodes"]}
        invariant_records = {
            item["capability"]: item
            for item in payloads[2]["capability_resolution"]["capabilities"]
            if item.get("source") == "invariant"
        }

        self.assertTrue(set(expected.values()).issubset(v1_names))
        self.assertTrue(set(expected.values()).issubset(v2_names))
        self.assertTrue(set(expected.values()).issubset(graph_names))
        self.assertEqual(set(invariant_records), set(expected))
        self.assertTrue(all(item["status"] == "covered" for item in invariant_records.values()))
        self.assertEqual(payloads[2]["routing_status"], "complete")

    def test_v2_missing_invariant_safeguard_is_reported_incomplete(self):
        import onecode_skill_sanitizer.cli as cli_module

        trusted = cli_module.trusted_skill_names(Path("catalog"))
        trusted -= {
            "security-secret-context-redaction",
            "security-llm-guard-io-scanning",
        }
        out = io.StringIO()
        with patch("onecode_skill_sanitizer.task_packs.trusted_skill_names", return_value=trusted):
            with contextlib.redirect_stdout(out):
                self.assertEqual(
                    main(
                        [
                            "smart",
                            "build a landing page",
                            "--schema-version",
                            "2",
                            "--invariants",
                            "不能泄露密钥",
                            "--format",
                            "json",
                        ]
                    ),
                    0,
                )
        payload = json.loads(out.getvalue())
        record = next(
            item
            for item in payload["capability_resolution"]["capabilities"]
            if item.get("source") == "invariant" and item["capability"] == "secret_redaction"
        )
        self.assertEqual(record["status"], "missing")
        self.assertEqual(record["skills"], [])
        self.assertEqual(payload["capability_resolution"]["status"], "incomplete")
        self.assertEqual(payload["routing_status"], "incomplete")

    def test_v2_cli_returns_safe_bounded_errors_for_invalid_assets(self):
        cases = []
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            malformed_bundles = root / "malformed-bundles.json"
            malformed_bundles.write_text("{not-json", encoding="utf-8")
            malformed_catalog = root / "catalog"
            malformed_catalog.mkdir()
            (malformed_catalog / "index.json").write_text("{not-json", encoding="utf-8")
            cases.extend(
                [
                    ["smart", "build site", "--schema-version", "2", "--bundles", str(malformed_bundles)],
                    [
                        "task-pack",
                        "build site",
                        "--registry",
                        "catalog",
                        "--schema-version",
                        "2",
                        "--bundles",
                        str(root / "missing-bundles.json"),
                    ],
                    ["smart", "build site", "--schema-version", "2", "--overlap-groups", str(root / "missing-overlap.json")],
                    ["smart", "build site", "--schema-version", "2", "--registry", str(malformed_catalog)],
                ]
            )
            for argv in cases:
                for output_format in ("json", "markdown"):
                    with self.subTest(argv=argv, output_format=output_format):
                        out = io.StringIO()
                        err = io.StringIO()
                        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                            exit_code = main([*argv, "--format", output_format])
                        output = out.getvalue()
                        self.assertEqual(exit_code, 2)
                        self.assertEqual(err.getvalue(), "")
                        self.assertNotIn("Traceback", output)
                        self.assertNotIn(str(root), output)
                        if output_format == "json":
                            payload = json.loads(output)
                            self.assertEqual(payload["schema_version"], 2)
                            self.assertEqual(payload["status"], "error")
                            self.assertIn("code", payload["error"])
                            self.assertIn("message", payload["error"])
                        else:
                            self.assertIn("# OneCode Task Pack v2 Error", output)

    def test_v2_cli_bounds_valid_json_with_malformed_structures(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            malformed_assets = []
            for index, payload in enumerate(([], {}, {"bundles": ["not-an-object"]})):
                path = root / f"bundles-{index}.json"
                path.write_text(json.dumps(payload), encoding="utf-8")
                malformed_assets.extend(
                    [
                        ["smart", "build site", "--schema-version", "2", "--bundles", str(path)],
                        [
                            "task-pack",
                            "build site",
                            "--registry",
                            "catalog",
                            "--schema-version",
                            "2",
                            "--bundles",
                            str(path),
                        ],
                    ]
                )
            for index, payload in enumerate(({}, {"skills": "not-a-list"})):
                registry = root / f"catalog-{index}"
                registry.mkdir()
                (registry / "index.json").write_text(json.dumps(payload), encoding="utf-8")
                malformed_assets.extend(
                    [
                        ["smart", "build site", "--schema-version", "2", "--registry", str(registry)],
                        [
                            "task-pack",
                            "build site",
                            "--registry",
                            str(registry),
                            "--schema-version",
                            "2",
                        ],
                    ]
                )

            for argv in malformed_assets:
                for output_format in ("json", "markdown"):
                    with self.subTest(argv=argv, output_format=output_format):
                        out = io.StringIO()
                        err = io.StringIO()
                        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                            exit_code = main([*argv, "--format", output_format])
                        output = out.getvalue()
                        self.assertEqual(exit_code, 2)
                        self.assertEqual(err.getvalue(), "")
                        self.assertNotIn("Traceback", output)
                        self.assertNotIn(str(root), output)
                        if output_format == "json":
                            payload = json.loads(output)
                            self.assertEqual(payload["schema_version"], 2)
                            self.assertEqual(payload["status"], "error")
                            self.assertIn(payload["error"]["code"], {"invalid_asset", "invalid_input"})
                        else:
                            self.assertIn("# OneCode Task Pack v2 Error", output)

    def test_v2_all_invariant_nodes_follow_contract_stages_and_forward_edges(self):
        from onecode_skill_sanitizer.router import PIPELINE_STAGE_ORDER
        from onecode_skill_sanitizer.router import pipeline_stage_for_skill

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(
                main(
                    [
                        "smart",
                        "build a landing page and prepare launch checks",
                        "--schema-version",
                        "2",
                        "--invariants",
                        "不能泄露密钥；公开文案必须合规；必须响应式验证；必须核查来源证据；必须使用浏览器截图验证",
                        "--format",
                        "json",
                    ]
                ),
                0,
            )
        payload = json.loads(out.getvalue())
        selected = {skill["name"]: skill for skill in payload["selected_skills"]}
        nodes = {node["id"]: node for node in payload["execution_graph"]["nodes"]}
        invariant_nodes = [node for node in nodes.values() if node["id"].startswith("invariant:")]
        stage_rank = {stage: rank for rank, stage in enumerate(PIPELINE_STAGE_ORDER)}
        records = {
            item["capability"]: item
            for item in payload["capability_resolution"]["capabilities"]
            if item.get("source") == "invariant"
        }

        self.assertEqual(payload["execution_graph"]["status"], "ready")
        self.assertTrue(payload["execution_graph"]["acyclic"])
        self.assertEqual(len(invariant_nodes), 5)
        self.assertEqual(set(records), {"secret_redaction", "claims_compliance", "responsive_check", "source_check", "browser_verification"})
        self.assertEqual(
            {node["skill"] for node in invariant_nodes},
            set(selected) & {node["skill"] for node in invariant_nodes},
        )
        for node in invariant_nodes:
            contract = selected[node["skill"]].get("contract")
            expected_stage = (
                contract["stage_hint"]
                if isinstance(contract, dict) and contract.get("stage_hint") in PIPELINE_STAGE_ORDER
                else pipeline_stage_for_skill(node["skill"])
            )
            self.assertEqual(node["stage"], expected_stage)
            self.assertEqual(records[node["invariant_capability"]]["stage"], node["stage"])
        for edge in payload["execution_graph"]["edges"]:
            source_stage = nodes[edge["from"]]["stage"]
            target_stage = nodes[edge["to"]]["stage"]
            self.assertLessEqual(stage_rank[source_stage], stage_rank[target_stage])


if __name__ == "__main__":
    unittest.main()
