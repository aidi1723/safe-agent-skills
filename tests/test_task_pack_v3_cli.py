from __future__ import annotations

import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError:
    Draft202012Validator = None

from onecode_skill_sanitizer.cli import build_parser, main
from onecode_skill_sanitizer.task_pack_v3 import build_task_pack_v3


ROOT = Path(__file__).resolve().parents[1]


class TaskPackV3CliTest(unittest.TestCase):
    def assert_v3_json_fails_closed(self, argv: list[str]) -> None:
        out = io.StringIO()
        err = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            exit_code = main(argv)
        output = out.getvalue()
        payload = json.loads(output)

        self.assertEqual(exit_code, 2)
        self.assertEqual(err.getvalue(), "")
        self.assertNotIn("Traceback", output)
        self.assertEqual(payload["schema_version"], 3)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error"]["code"], "feature_not_ready")
        self.assertEqual(payload["error"]["message"], "Task-pack v3 is not implemented yet.")

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

    def test_smart_v3_json_fails_closed(self):
        self.assert_v3_json_fails_closed(
            ["smart", "review this patch", "--schema-version", "3", "--format", "json"]
        )

    def test_task_pack_v3_json_fails_closed(self):
        self.assert_v3_json_fails_closed(
            [
                "task-pack",
                "review this patch",
                "--registry",
                "catalog",
                "--schema-version",
                "3",
                "--format",
                "json",
            ]
        )

    def test_v3_markdown_fails_closed(self):
        for command in ("smart", "task-pack"):
            with self.subTest(command=command):
                argv = [command, "review this patch", "--schema-version", "3", "--format", "markdown"]
                if command == "task-pack":
                    argv.extend(["--registry", "catalog"])
                out = io.StringIO()
                err = io.StringIO()
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    exit_code = main(argv)
                output = out.getvalue()

                self.assertEqual(exit_code, 2)
                self.assertEqual(err.getvalue(), "")
                self.assertNotIn("Traceback", output)
                self.assertIn("# OneCode Task Pack v3 Error", output)
                self.assertIn("- code: `feature_not_ready`", output)
                self.assertIn("- message: Task-pack v3 is not implemented yet.", output)


class TaskPackV3BuilderTest(unittest.TestCase):
    def build(self, task: str):
        return build_task_pack_v3(
            ROOT / "catalog",
            task,
            ROOT / "bundles/index.json",
            ROOT / "catalog/routing-examples.json",
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
