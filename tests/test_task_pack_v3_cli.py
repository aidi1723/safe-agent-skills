from __future__ import annotations

import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

try:
    from jsonschema import Draft202012Validator
except ImportError:
    Draft202012Validator = None

from onecode_skill_sanitizer.cli import build_parser, main
from onecode_skill_sanitizer.task_pack_v3 import build_task_pack_v3


ROOT = Path(__file__).resolve().parents[1]


class FixtureSemanticProvider:
    name = "fixture-provider"

    def __init__(self, model_or_adapter: str):
        self.model_or_adapter = model_or_adapter
        self.requests = []

    def rerank(self, request):
        self.requests.append(copy.deepcopy(request))
        candidates = request["candidates"]
        return {
            "status": "ok",
            "scores": [
                {
                    "skill": item["skill"],
                    "score": round((index + 1) / len(candidates), 6),
                    "confidence": 0.9,
                }
                for index, item in enumerate(candidates)
            ],
        }


class TaskPackV3CliTest(unittest.TestCase):
    def run_cli(self, argv: list[str]) -> tuple[int, str, str]:
        out = io.StringIO()
        err = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            exit_code = main(argv)
        return exit_code, out.getvalue(), err.getvalue()

    def assert_v3_json_success(self, argv: list[str]) -> dict:
        exit_code, output, error_output = self.run_cli(argv)
        payload = json.loads(output)
        schema = json.loads(
            (ROOT / "schemas/task-pack-v3.schema.json").read_text(encoding="utf-8")
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(error_output, "")
        self.assertNotIn("Traceback", output)
        self.assertNotRegex(output, r"\b(?:NaN|Infinity|-Infinity)\b")
        self.assertEqual(payload["schema_version"], 3)
        self.assertEqual(set(payload), set(schema["required"]))
        if Draft202012Validator is not None:
            self.assertEqual(list(Draft202012Validator(schema).iter_errors(payload)), [])
        return payload

    def assert_uniform_v3_json_error(self, argv: list[str]) -> None:
        exit_code, output, error_output = self.run_cli(argv)
        payload = json.loads(output)

        self.assertEqual(exit_code, 2)
        self.assertEqual(error_output, "")
        self.assertNotIn("Traceback", output)
        self.assertEqual(
            payload,
            {
                "schema_version": 3,
                "status": "error",
                "error": {
                    "code": "invalid_input",
                    "message": "Routing input or assets are invalid.",
                },
            },
        )

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

    def test_smart_and_task_pack_v3_emit_strict_json(self):
        commands = (
            ["smart", "review this patch", "--schema-version", "3", "--format", "json"],
            [
                "task-pack",
                "review this patch",
                "--registry",
                "catalog",
                "--schema-version",
                "3",
                "--format",
                "json",
            ],
        )
        for argv in commands:
            with self.subTest(command=argv[0]):
                payload = self.assert_v3_json_success(argv)
                self.assertEqual(payload["normalized_task"]["current"], "review this patch")

    def test_v3_markdown_escapes_dynamic_heading_fence_and_html_injection(self):
        attack = "review this patch\n## Injected\n```html\n<span>unsafe</span>"
        expected_headings = [
            "# OneCode Agent Task Pack v3",
            "## Task",
            "## Need Decision",
            "## Selected Skills",
            "## Confidence",
            "## Provider",
            "## Execution Graph",
            "## Routing Diagnostics",
            "## Safety Boundary",
        ]
        for command in ("smart", "task-pack"):
            with self.subTest(command=command):
                argv = [command, attack, "--schema-version", "3", "--format", "markdown"]
                if command == "task-pack":
                    argv.extend(["--registry", "catalog"])
                exit_code, output, error_output = self.run_cli(argv)
                headings = [line for line in output.splitlines() if line.startswith("#")]

                self.assertEqual(exit_code, 0)
                self.assertEqual(error_output, "")
                self.assertNotIn("Traceback", output)
                self.assertEqual(headings, expected_headings)
                self.assertNotIn("## Injected", output)
                self.assertNotIn("```", output)
                self.assertNotIn("<span>", output)

    def test_v3_markdown_escapes_tilde_fences_without_hiding_sections(self):
        attack = "~~~html\n<span>unsafe</span>\n~~~\nafter fence"
        exit_code, output, error_output = self.run_cli(
            ["smart", attack, "--schema-version", "3", "--format", "markdown"]
        )
        headings = [line for line in output.splitlines() if line.startswith("#")]

        self.assertEqual(exit_code, 0)
        self.assertEqual(error_output, "")
        self.assertNotIn("~~~", output)
        self.assertEqual(
            headings,
            [
                "# OneCode Agent Task Pack v3",
                "## Task",
                "## Need Decision",
                "## Selected Skills",
                "## Confidence",
                "## Provider",
                "## Execution Graph",
                "## Routing Diagnostics",
                "## Safety Boundary",
            ],
        )

    def test_empty_v3_task_returns_bounded_json_error(self):
        commands = (
            ["smart", "", "--schema-version", "3", "--format", "json"],
            [
                "task-pack",
                "",
                "--registry",
                "catalog",
                "--schema-version",
                "3",
                "--format",
                "json",
            ],
        )
        for argv in commands:
            with self.subTest(command=argv[0]):
                self.assert_uniform_v3_json_error(argv)

    def test_v3_caught_exception_types_return_one_uniform_json_error(self):
        exceptions = (
            json.JSONDecodeError("sensitive JSON detail", "private document", 0),
            OSError("sensitive filesystem detail"),
            ValueError("sensitive value detail"),
            SystemExit("sensitive exit detail"),
        )
        for exc in exceptions:
            with self.subTest(exception=type(exc).__name__):
                with mock.patch(
                    "onecode_skill_sanitizer.commands.build_task_pack_v3",
                    side_effect=exc,
                ):
                    self.assert_uniform_v3_json_error(
                        [
                            "smart",
                            "review this patch",
                            "--schema-version",
                            "3",
                            "--format",
                            "json",
                        ]
                    )

    def test_v3_missing_routing_examples_returns_uniform_json_error(self):
        self.assert_uniform_v3_json_error(
            [
                "smart",
                "review this patch",
                "--schema-version",
                "3",
                "--routing-examples",
                "catalog/does-not-exist.json",
                "--format",
                "json",
            ]
        )

    def test_v3_markdown_error_is_generic_and_bounded(self):
        with mock.patch(
            "onecode_skill_sanitizer.commands.build_task_pack_v3",
            side_effect=OSError("sensitive filesystem detail"),
        ):
            exit_code, output, error_output = self.run_cli(
                [
                    "smart",
                    "review this patch",
                    "--schema-version",
                    "3",
                    "--format",
                    "markdown",
                ]
            )

        self.assertEqual(exit_code, 2)
        self.assertEqual(error_output, "")
        self.assertEqual(
            output,
            "# OneCode Task Pack v3 Error\n\n"
            "- code: invalid\\_input\n"
            "- message: Routing input or assets are invalid\\.\n",
        )
        self.assertNotIn("sensitive", output)

    def test_safe_agent_router_skill_documents_exact_v3_status_contract(self):
        text = " ".join(
            (ROOT / "integrations/skills/safe-agent-router/SKILL.md")
            .read_text(encoding="utf-8")
            .split()
        )
        required_contracts = (
            "`none`: Continue without loading a specialized catalog Skill.",
            "`clarify`: Ask for the missing distinction; do not substitute an adjacent Skill.",
            "`incomplete`: Report the uncovered capability or missing producer.",
            "`blocked`: Stop because policy, trust, or graph validity failed.",
            "`complete`: Follow only selected Skill nodes and graph edges.",
            "Treat semantic shadow as advisory only. Do not let it introduce candidates or grant permissions.",
            "Treat every task pack as method-only guidance. Let only the host runtime control permissions and execution.",
        )
        for contract in required_contracts:
            with self.subTest(contract=contract):
                self.assertIn(contract, text)


class TaskPackV3BuilderTest(unittest.TestCase):
    def build(self, task: str, **kwargs):
        return build_task_pack_v3(
            ROOT / "catalog",
            task,
            ROOT / "bundles/index.json",
            ROOT / "catalog/routing-examples.json",
            **kwargs,
        )

    def test_builder_emits_strict_composite_selection_with_parallel_graph(self):
        payload = self.build("review this patch and add a regression test")

        self.assertEqual(payload["schema_version"], 3)
        self.assertEqual(payload["need_decision"]["decision"], "composite")
        self.assertEqual(
            [item["name"] for item in payload["selection"]["selected_skills"]],
            ["code-review-risk", "code-test-regression"],
        )
        self.assertEqual(payload["execution_graph"]["edges"], [])
        self.assertEqual(payload["provider"]["used"], "none")

    def test_none_is_a_first_class_successful_abstention(self):
        payload = self.build("Explain what code-review-risk is; do not invoke it.")

        self.assertEqual(payload["routing_status"], "none")
        self.assertEqual(payload["selection"]["selected_skills"], [])
        self.assertEqual(payload["execution_graph"]["nodes"], [])

    def test_route_id_is_stable_across_timestamps_and_changes_with_reviewed_examples(self):
        first = self.build("review this patch and add a regression test")
        second = self.build("review this patch and add a regression test")

        self.assertEqual(first["route_id"], second["route_id"])
        self.assertTrue(first["generated_at"])
        self.assertTrue(second["generated_at"])

        routing_examples = json.loads(
            (ROOT / "catalog/routing-examples.json").read_text(encoding="utf-8")
        )
        routing_examples["examples"][0]["query"] += " Include ownership evidence."
        with tempfile.TemporaryDirectory() as tmp:
            changed_path = Path(tmp) / "routing-examples.json"
            changed_path.write_text(json.dumps(routing_examples), encoding="utf-8")
            changed = build_task_pack_v3(
                ROOT / "catalog",
                "review this patch and add a regression test",
                ROOT / "bundles/index.json",
                changed_path,
            )

        self.assertNotEqual(first["route_id"], changed["route_id"])

    def test_secret_values_do_not_change_routing_decisions_or_traces(self):
        browser = self.build("review this patch api_key=browser")
        banana = self.build("review this patch api_key=banana")

        self.assertEqual(browser["route_id"], banana["route_id"])
        for field in (
            "routing_mode",
            "routing_status",
            "need_decision",
            "intent_graph",
            "candidates",
            "selection",
            "capability_resolution",
            "execution_graph",
            "confidence",
            "provider",
            "routing_metrics",
        ):
            with self.subTest(field=field):
                self.assertEqual(browser[field], banana[field])
        self.assertIn("api_key=browser", browser["normalized_task"]["raw"])
        self.assertIn("api_key=browser", browser["normalized_task"]["current"])
        self.assertIn("api_key=banana", banana["normalized_task"]["raw"])
        self.assertIn("api_key=banana", banana["normalized_task"]["current"])

    def assert_authorization_credentials_are_route_inert(
        self,
        first_task: str,
        second_task: str,
        forbidden_values: tuple[str, ...],
    ):
        first_provider = FixtureSemanticProvider("adapter-a")
        second_provider = FixtureSemanticProvider("adapter-a")
        first = self.build(first_task, semantic_provider=first_provider)
        second = self.build(second_task, semantic_provider=second_provider)

        for field in (
            "route_id",
            "routing_mode",
            "routing_status",
            "need_decision",
            "intent_graph",
            "candidates",
            "selection",
            "capability_resolution",
            "execution_graph",
            "confidence",
            "provider",
            "routing_metrics",
        ):
            with self.subTest(field=field):
                self.assertEqual(first[field], second[field])

        for provider in (first_provider, second_provider):
            self.assertEqual(len(provider.requests), 1)
            current_intent = provider.requests[0]["current_intent"]
            self.assertIn("[REDACTED]", current_intent)
            self.assertIn("add a regression test", current_intent)
            for forbidden in forbidden_values:
                with self.subTest(forbidden=forbidden):
                    self.assertNotIn(forbidden, current_intent)

    def test_basic_authorization_credentials_are_fully_route_inert(self):
        self.assert_authorization_credentials_are_route_inert(
            "review this patch authorization: Basic dXNlcjpwYXNzd29yZA==, "
            "and add a regression test",
            "review this patch authorization: Basic YWxpY2U6c2VjcmV0, "
            "and add a regression test",
            ("Basic", "dXNlcjpwYXNzd29yZA==", "YWxpY2U6c2VjcmV0"),
        )

    def test_digest_authorization_credentials_are_fully_route_inert(self):
        self.assert_authorization_credentials_are_route_inert(
            'review this patch authorization: Digest username="Mufasa", '
            'realm="testrealm@host.com", nonce="nonce-a", uri="/dir/index.html", '
            'response="response-a", qop=auth, and add a regression test',
            'review this patch authorization: Digest username="Circle Of Life", '
            'realm="second.example", nonce="nonce-b", uri="/other", '
            'response="response-b", qop=auth, and add a regression test',
            (
                "Digest",
                "Mufasa",
                "Circle Of Life",
                "nonce-a",
                "nonce-b",
                "response-a",
                "response-b",
            ),
        )

    def test_digest_extended_parameter_credentials_are_fully_route_inert(self):
        self.assert_authorization_credentials_are_route_inert(
            "review this patch authorization: Digest "
            "username*=UTF-8''M%C3%BCller, realm=first.example, "
            "nonce=nonce-a, response=response-a, and add a regression test",
            "review this patch authorization: Digest "
            "username*=UTF-8''Alice, realm=second.example, "
            "nonce=nonce-b, response=response-b, and add a regression test",
            (
                "Digest",
                "username*",
                "M%C3%BCller",
                "Alice",
                "first.example",
                "second.example",
                "nonce-a",
                "nonce-b",
                "response-a",
                "response-b",
            ),
        )

    def test_route_id_binds_max_candidates(self):
        one = self.build("review this patch", max_candidates=1)
        three = self.build("review this patch", max_candidates=3)

        self.assertNotEqual(one["candidates"], three["candidates"])
        self.assertNotEqual(one["route_id"], three["route_id"])

    def test_route_id_binds_semantic_mode(self):
        task = "review this patch and add a regression test"
        shadow = self.build(
            task,
            semantic_provider=FixtureSemanticProvider("adapter-a"),
            semantic_mode="shadow",
        )
        influence = self.build(
            task,
            semantic_provider=FixtureSemanticProvider("adapter-a"),
            semantic_mode="influence",
        )

        self.assertNotEqual(shadow["provider"], influence["provider"])
        self.assertNotEqual(shadow["route_id"], influence["route_id"])

    def test_route_id_binds_provider_adapter(self):
        task = "review this patch and add a regression test"
        adapter_a = self.build(
            task,
            semantic_provider=FixtureSemanticProvider("adapter-a"),
        )
        adapter_b = self.build(
            task,
            semantic_provider=FixtureSemanticProvider("adapter-b"),
        )

        self.assertEqual(adapter_a["provider"]["requested"], "fixture-provider")
        self.assertEqual(adapter_b["provider"]["requested"], "fixture-provider")
        self.assertNotEqual(
            adapter_a["provider"]["model_or_adapter"],
            adapter_b["provider"]["model_or_adapter"],
        )
        self.assertNotEqual(adapter_a["route_id"], adapter_b["route_id"])

    def assert_explicit_order_edge(self, task: str, source: str, target: str):
        payload = self.build(task)

        self.assertEqual(
            payload["selection"]["selected_skill_names"],
            ["code-review-risk", "code-test-regression"],
        )
        self.assertEqual(
            payload["execution_graph"]["edges"],
            [
                {
                    "from": f"skill:{source}",
                    "to": f"skill:{target}",
                    "type": "explicit_user_order",
                    "evidence": "current_request",
                }
            ],
        )

    def test_canonical_skill_names_preserve_explicit_user_order(self):
        cases = (
            (
                "Use code-review-risk, then use code-test-regression.",
                "code-review-risk",
                "code-test-regression",
            ),
            (
                "Use code-review-risk before code-test-regression.",
                "code-review-risk",
                "code-test-regression",
            ),
            (
                "Use code-review-risk, then code-test-regression.",
                "code-review-risk",
                "code-test-regression",
            ),
            (
                "Use code-review-risk after code-test-regression.",
                "code-test-regression",
                "code-review-risk",
            ),
            (
                "使用 code-review-risk，然后 code-test-regression。",
                "code-review-risk",
                "code-test-regression",
            ),
            (
                "Use code-review-risk before code-test-regression, then use "
                "code-test-regression after code-review-risk.",
                "code-review-risk",
                "code-test-regression",
            ),
            (
                "Use, as planned, code-review-risk before code-test-regression.",
                "code-review-risk",
                "code-test-regression",
            ),
            (
                "As discussed, use code-review-risk before code-test-regression.",
                "code-review-risk",
                "code-test-regression",
            ),
            (
                "The documentation mentions old routing. Now use "
                "code-review-risk before code-test-regression.",
                "code-review-risk",
                "code-test-regression",
            ),
            (
                "Explain code-review-risk, then use code-review-risk before "
                "code-test-regression.",
                "code-review-risk",
                "code-test-regression",
            ),
            (
                "Be sure to use code-review-risk before code-test-regression.",
                "code-review-risk",
                "code-test-regression",
            ),
            (
                "Use code-review-risk, not the generic reviewer, before "
                "code-test-regression.",
                "code-review-risk",
                "code-test-regression",
            ),
        )
        for task, source, target in cases:
            with self.subTest(task=task):
                payload = self.build(task)

                self.assertEqual(
                    set(payload["selection"]["selected_skill_names"]),
                    {"code-review-risk", "code-test-regression"},
                )
                self.assertEqual(
                    payload["need_decision"]["explicit_skills"],
                    ["code-review-risk", "code-test-regression"],
                )
                self.assertEqual(
                    payload["execution_graph"]["edges"],
                    [
                        {
                            "from": f"skill:{source}",
                            "to": f"skill:{target}",
                            "type": "explicit_user_order",
                            "evidence": "current_request",
                        }
                    ],
                )

    def test_canonical_skill_mentions_do_not_manufacture_order_edges(self):
        cases = (
            (
                "Use code-review-risk, code-test-regression.",
                {"code-review-risk", "code-test-regression"},
            ),
            (
                "Use code-review-risk, then explain code-test-regression.",
                {"code-review-risk"},
            ),
            (
                "Use code-review-risk, then do not use code-test-regression.",
                {"code-review-risk"},
            ),
            (
                "The documentation mentions code-review-risk before "
                "code-test-regression.",
                set(),
            ),
            (
                "History: use code-review-risk before code-test-regression. "
                "Current request: review this patch.",
                {"code-review-risk"},
            ),
            (
                "Use code-review-risk. Independently, use code-test-regression.",
                {"code-review-risk", "code-test-regression"},
            ),
            (
                "Use code-review-risk and code-test-regression. "
                "The documentation mentions code-review-risk before "
                "code-test-regression.",
                {"code-review-risk", "code-test-regression"},
            ),
            (
                "Use code-review-risk and code-test-regression. "
                "Earlier we discussed code-review-risk before "
                "code-test-regression.",
                {"code-review-risk", "code-test-regression"},
            ),
            (
                "Use code-review-risk and code-test-regression, but the "
                "documentation mentions code-review-risk before "
                "code-test-regression.",
                {"code-review-risk", "code-test-regression"},
            ),
            (
                "Use code-review-risk and code-test-regression, but explain "
                "code-review-risk before code-test-regression.",
                {"code-review-risk", "code-test-regression"},
            ),
            (
                "Use code-review-risk and code-test-regression, but earlier we "
                "discussed code-review-risk before code-test-regression.",
                {"code-review-risk", "code-test-regression"},
            ),
            (
                "Use code-review-risk and code-test-regression, but list the "
                "Skills as code-review-risk before code-test-regression.",
                {"code-review-risk", "code-test-regression"},
            ),
            (
                "Earlier we discussed code-review-risk before "
                "code-test-regression.",
                set(),
            ),
            (
                "Previously, we discussed code-review-risk before "
                "code-test-regression.",
                set(),
            ),
            (
                "Use code-review-risk and code-test-regression, but the "
                "documentation mentioned code-review-risk before "
                "code-test-regression.",
                {"code-review-risk", "code-test-regression"},
            ),
            (
                "Use code-review-risk and code-test-regression, but previously, "
                "we discussed code-review-risk before code-test-regression.",
                {"code-review-risk", "code-test-regression"},
            ),
            (
                "Explain how best to use code-review-risk before "
                "code-test-regression.",
                set(),
            ),
            (
                "解释如何正确使用 code-review-risk before "
                "code-test-regression.",
                set(),
            ),
            (
                "Use code-review-risk, not code-test-regression.",
                {"code-review-risk"},
            ),
            (
                "Use code-review-risk, not use code-test-regression.",
                {"code-review-risk"},
            ),
            (
                "Explain the use of code-review-risk before "
                "code-test-regression.",
                set(),
            ),
            (
                "Use code-review-risk, while code-test-regression was "
                "mentioned in the documentation before "
                "execution-browser-check.",
                {"code-review-risk"},
            ),
            (
                "code-test-regression appears in the inventory.",
                set(),
            ),
            (
                "code-test-regression appeared in docs.",
                set(),
            ),
            (
                "code-test-regression appeared in docs with review this patch.",
                set(),
            ),
            (
                "code-test-regression appeared in docs, but use "
                "code-review-risk.",
                {"code-review-risk"},
            ),
            (
                "code-test-regression appeared in docs, but review this patch.",
                {"code-review-risk"},
            ),
        )
        for task, selected in cases:
            with self.subTest(task=task):
                payload = self.build(task)

                self.assertEqual(
                    set(payload["selection"]["selected_skill_names"]), selected
                )
                self.assertEqual(payload["execution_graph"]["edges"], [])

    def test_builder_reverses_textual_order_for_after_connector(self):
        self.assert_explicit_order_edge(
            "review this patch after adding a regression test",
            "code-test-regression",
            "code-review-risk",
        )

    def test_builder_preserves_compound_gerund_after_complement(self):
        self.assert_explicit_order_edge(
            "review this patch after writing and running a regression test",
            "code-test-regression",
            "code-review-risk",
        )

    def test_builder_preserves_adverb_modified_compound_gerund_after_complement(self):
        self.assert_explicit_order_edge(
            "review this patch after writing and successfully running a regression test",
            "code-test-regression",
            "code-review-risk",
        )

    def test_builder_treats_then_as_internal_to_compound_gerund_after_complement(self):
        self.assert_explicit_order_edge(
            "review this patch after writing and then running a regression test",
            "code-test-regression",
            "code-review-risk",
        )

    def test_builder_preserves_textual_order_for_before_connector(self):
        self.assert_explicit_order_edge(
            "review this patch before adding a regression test",
            "code-review-risk",
            "code-test-regression",
        )

    def test_builder_reverses_textual_order_for_chinese_before_phrase(self):
        self.assert_explicit_order_edge(
            "审查这个补丁之前先补回归测试",
            "code-test-regression",
            "code-review-risk",
        )

    def test_builder_preserves_chinese_postfix_after_semantics(self):
        self.assert_explicit_order_edge(
            "审查这个补丁之后补回归测试",
            "code-review-risk",
            "code-test-regression",
        )

    def test_binary_connector_does_not_serialize_an_unrelated_third_skill(self):
        payload = self.build(
            "review this patch after adding a regression test and verify these claims "
            "against primary sources"
        )

        self.assertEqual(
            payload["execution_graph"]["edges"],
            [
                {
                    "from": "skill:code-test-regression",
                    "to": "skill:code-review-risk",
                    "type": "explicit_user_order",
                    "evidence": "current_request",
                }
            ],
        )

    def test_then_connectors_order_only_adjacent_explicit_items(self):
        payload = self.build(
            "review this patch, then add a regression test, then verify these claims "
            "against primary sources"
        )

        self.assertEqual(
            payload["execution_graph"]["edges"],
            [
                {
                    "from": "skill:code-review-risk",
                    "to": "skill:code-test-regression",
                    "type": "explicit_user_order",
                    "evidence": "current_request",
                },
                {
                    "from": "skill:code-test-regression",
                    "to": "skill:research-source-check",
                    "type": "explicit_user_order",
                    "evidence": "current_request",
                },
            ],
        )

    def test_then_does_not_skip_an_unmapped_independent_action(self):
        payload = self.build(
            "review this patch, then deploy it, and separately verify these claims "
            "against primary sources"
        )

        self.assertEqual(
            set(payload["selection"]["selected_skill_names"]),
            {"code-review-risk", "research-source-check"},
        )
        self.assertEqual(payload["execution_graph"]["edges"], [])

    def test_contradictory_connectors_are_blocked_by_the_selection_dag(self):
        payload = self.build(
            "review this patch before adding a regression test, then review this patch "
            "after adding a regression test"
        )

        self.assertEqual(payload["routing_status"], "blocked")
        self.assertEqual(payload["execution_graph"]["status"], "blocked")
        self.assertEqual(payload["execution_graph"]["reason_codes"], ["dependency_cycle"])

    def test_xian_orders_two_actions_in_its_local_clause(self):
        payload = self.build("先审查这个补丁，补一个回归测试")

        self.assertEqual(
            set(payload["selection"]["selected_skill_names"]),
            {"code-review-risk", "code-test-regression"},
        )
        self.assertEqual(
            payload["execution_graph"]["edges"],
            [
                {
                    "from": "skill:code-review-risk",
                    "to": "skill:code-test-regression",
                    "type": "explicit_user_order",
                    "evidence": "current_request",
                }
            ],
        )

    def test_xian_scope_keeps_then_inside_a_compound_gerund(self):
        self.assert_explicit_order_edge(
            "先 writing and then running a regression test, review this patch",
            "code-test-regression",
            "code-review-risk",
        )

    def test_xian_orders_adjacent_actions_in_one_sequence_clause(self):
        payload = self.build(
            "先 review this patch, add a regression test, verify these claims against primary sources"
        )

        self.assertEqual(
            payload["execution_graph"]["edges"],
            [
                {
                    "from": "skill:code-review-risk",
                    "to": "skill:code-test-regression",
                    "type": "explicit_user_order",
                    "evidence": "current_request",
                },
                {
                    "from": "skill:code-test-regression",
                    "to": "skill:research-source-check",
                    "type": "explicit_user_order",
                    "evidence": "current_request",
                },
            ],
        )

    def test_xian_sequence_does_not_cross_a_strong_clause_boundary(self):
        payload = self.build(
            "先 review this patch, add a regression test. "
            "Verify these claims against primary sources."
        )

        self.assertEqual(
            payload["execution_graph"]["edges"],
            [
                {
                    "from": "skill:code-review-risk",
                    "to": "skill:code-test-regression",
                    "type": "explicit_user_order",
                    "evidence": "current_request",
                }
            ],
        )

    def test_xian_scope_stops_at_independent_adversative_coordination(self):
        payload = self.build(
            "先 review this patch, add a regression test, but independently verify "
            "these claims against primary sources"
        )

        self.assertEqual(
            payload["execution_graph"]["edges"],
            [
                {
                    "from": "skill:code-review-risk",
                    "to": "skill:code-test-regression",
                    "type": "explicit_user_order",
                    "evidence": "current_request",
                }
            ],
        )

    def test_xian_scope_stops_at_explicit_parallel_coordination(self):
        payload = self.build(
            "先 review this patch, add a regression test，同时 verify these claims "
            "against primary sources"
        )

        self.assertEqual(
            payload["execution_graph"]["edges"],
            [
                {
                    "from": "skill:code-review-risk",
                    "to": "skill:code-test-regression",
                    "type": "explicit_user_order",
                    "evidence": "current_request",
                }
            ],
        )

    def assert_grouped_review_order(self, task: str):
        payload = self.build(task)

        self.assertEqual(
            payload["execution_graph"]["edges"],
            [
                {
                    "from": "skill:code-review-risk",
                    "to": "skill:research-source-check",
                    "type": "explicit_user_order",
                    "evidence": "current_request",
                },
                {
                    "from": "skill:code-test-regression",
                    "to": "skill:code-review-risk",
                    "type": "explicit_user_order",
                    "evidence": "current_request",
                },
            ],
        )

    def test_but_before_reuses_the_grouped_main_action(self):
        self.assert_grouped_review_order(
            "review this patch after adding a regression test but before verifying "
            "these claims against primary sources"
        )

    def test_but_before_follows_a_compound_gerund_after_complement(self):
        self.assert_grouped_review_order(
            "review this patch after writing and running a regression test but before "
            "verifying these claims against primary sources"
        )

    def test_and_before_reuses_the_grouped_main_action(self):
        self.assert_grouped_review_order(
            "review this patch after adding a regression test and before verifying "
            "these claims against primary sources"
        )

    def test_comma_elided_binary_complements_reuse_the_main_action(self):
        self.assert_grouped_review_order(
            "review this patch after adding a regression test, before verifying "
            "these claims against primary sources"
        )

    def test_new_left_action_starts_a_new_connector_relation(self):
        payload = self.build(
            "review this patch after adding a regression test, and verify these claims "
            "before running a browser check"
        )

        self.assertEqual(
            payload["execution_graph"]["edges"],
            [
                {
                    "from": "skill:code-test-regression",
                    "to": "skill:code-review-risk",
                    "type": "explicit_user_order",
                    "evidence": "current_request",
                },
                {
                    "from": "skill:research-source-check",
                    "to": "skill:execution-browser-check",
                    "type": "explicit_user_order",
                    "evidence": "current_request",
                },
            ],
        )

    def assert_binary_precedes_overlapping_xian_sequence(self, task: str):
        payload = self.build(task)

        self.assertNotEqual(payload["routing_status"], "blocked")
        self.assertEqual(
            payload["execution_graph"]["edges"],
            [
                {
                    "from": "skill:code-test-regression",
                    "to": "skill:code-review-risk",
                    "type": "explicit_user_order",
                    "evidence": "current_request",
                }
            ],
        )

    def test_binary_temporal_relation_precedes_xian_text_order(self):
        self.assert_binary_precedes_overlapping_xian_sequence(
            "先在审查这个补丁之前，补一个回归测试"
        )

    def test_binary_temporal_relation_precedes_mixed_xian_text_order(self):
        self.assert_binary_precedes_overlapping_xian_sequence(
            "先 review this patch after adding a regression test"
        )

    def test_repeated_complement_skill_mentions_preserve_the_grouped_anchor(self):
        self.assert_grouped_review_order(
            "review this patch after adding a regression test and checking test coverage, "
            "but before verifying these claims against primary sources"
        )

    def test_xian_scope_stops_at_the_first_explicit_connector(self):
        payload = self.build(
            "先 review this patch, add a regression test, then verify these claims "
            "against primary sources before running a browser check"
        )

        self.assertEqual(
            payload["execution_graph"]["edges"],
            [
                {
                    "from": "skill:code-review-risk",
                    "to": "skill:code-test-regression",
                    "type": "explicit_user_order",
                    "evidence": "current_request",
                },
                {
                    "from": "skill:code-test-regression",
                    "to": "skill:research-source-check",
                    "type": "explicit_user_order",
                    "evidence": "current_request",
                },
                {
                    "from": "skill:research-source-check",
                    "to": "skill:execution-browser-check",
                    "type": "explicit_user_order",
                    "evidence": "current_request",
                },
            ],
        )

    def assert_unmapped_binary_complement_is_skipped(self, task: str):
        payload = self.build(task)

        self.assertNotEqual(payload["routing_status"], "blocked")
        self.assertEqual(payload["execution_graph"]["edges"], [])

    def test_binary_complement_stops_at_comma_coordination_boundary(self):
        self.assert_unmapped_binary_complement_is_skipped(
            "review this patch after deployment, and verify these claims against primary sources"
        )

    def test_binary_complement_stops_at_coordination_boundary(self):
        self.assert_unmapped_binary_complement_is_skipped(
            "review this patch after deployment and verify these claims against primary sources"
        )

    def test_schema_has_strict_v3_structure_and_current_conflict_reasons(self):
        schema = json.loads(
            (ROOT / "schemas/task-pack-v3.schema.json").read_text(encoding="utf-8")
        )

        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["$id"], "https://onecode.local/schemas/task-pack-v3.schema.json")
        self.assertEqual(schema["title"], "OneCode Task Pack v3")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            set(schema["required"]),
            {
                "schema_version",
                "generated_at",
                "route_id",
                "routing_mode",
                "routing_status",
                "provider",
                "normalized_task",
                "need_decision",
                "intent_graph",
                "candidates",
                "selection",
                "capability_resolution",
                "execution_graph",
                "confidence",
                "host_execution_protocol",
                "routing_metrics",
                "registry_verification",
                "compatibility",
            },
        )
        self.assertEqual(
            schema["$defs"]["selection"]["properties"]["conflict_resolutions"]
            ["items"]["properties"]["reason"]["enum"],
            ["insufficient_margin", "higher_final_score"],
        )
        self.assertTrue(
            {
                "provider",
                "normalizedTask",
                "needDecision",
                "candidate",
                "scoreEvidence",
                "selection",
                "capabilityResolution",
                "executionGraph",
                "confidence",
                "hostProtocol",
            }
            <= set(schema["$defs"])
        )
        for definition in ("candidate", "scoreEvidence", "selection", "selectedSkill"):
            with self.subTest(definition=definition):
                self.assertFalse(schema["$defs"][definition]["additionalProperties"])
        self.assertTrue(
            {"name", "status", "registry_path"}
            <= set(schema["$defs"]["selectedSkill"]["required"])
        )
        evidence_properties = schema["$defs"]["scoreEvidence"]["properties"]
        self.assertTrue(
            {"type", "value", "weight", "similarity", "token_overlap", "token_union", "contribution"}
            <= set(evidence_properties)
        )

    @unittest.skipUnless(Draft202012Validator is not None, "jsonschema is not installed")
    def test_builder_payload_validates_and_rejects_unknown_fields(self):
        schema = json.loads(
            (ROOT / "schemas/task-pack-v3.schema.json").read_text(encoding="utf-8")
        )
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        payload = self.build("review this patch and add a regression test")

        self.assertEqual(list(validator.iter_errors(payload)), [])
        for location in ((), ("selection",), ("candidates", 0)):
            with self.subTest(location=location):
                mutated = copy.deepcopy(payload)
                target = mutated
                for part in location:
                    target = target[part]
                target["unknown_field"] = True
                self.assertTrue(list(validator.iter_errors(mutated)))


if __name__ == "__main__":
    unittest.main()
