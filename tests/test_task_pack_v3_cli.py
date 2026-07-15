from __future__ import annotations

import contextlib
import io
import json
import unittest

from onecode_skill_sanitizer.cli import build_parser, main


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


if __name__ == "__main__":
    unittest.main()
