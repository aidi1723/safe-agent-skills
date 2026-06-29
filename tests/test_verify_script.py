import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class VerifyScriptTest(unittest.TestCase):
    def test_verify_script_preflights_jsonschema_with_install_instruction(self):
        script = Path("scripts/verify.sh").read_text(encoding="utf-8")

        self.assertIn("python3 -c 'import jsonschema'", script)
        self.assertIn('Install development checks with: python3 -m pip install -e ".[dev]"', script)
        self.assertIn("exit 2", script)

    def test_verify_script_exits_two_when_jsonschema_is_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_python = Path(temp_dir) / "python3"
            fake_python.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
            fake_python.chmod(0o755)
            result = subprocess.run(
                ["bash", "scripts/verify.sh"],
                cwd=Path.cwd(),
                env={**os.environ, "PATH": f"{temp_dir}:/bin:/usr/bin"},
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 2)
        self.assertEqual(
            result.stderr.strip(),
            'Install development checks with: python3 -m pip install -e ".[dev]"',
        )

    def test_verify_script_falls_back_to_grep_when_ripgrep_is_missing(self):
        script = Path("scripts/verify.sh").read_text(encoding="utf-8")

        self.assertNotIn("require_command rg", script)
        self.assertIn("if command -v rg", script)
        self.assertIn("grep -RInE", script)

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

    def test_ci_runs_routine_verification_without_one_shot_authorization(self):
        workflow = Path(".github/workflows/verify.yml").read_text(encoding="utf-8")

        self.assertIn("run: bash scripts/verify.sh", workflow)
        self.assertNotIn("ONECODE_RUN_ROUTER_V3_FINAL_TEST", workflow)

    def test_v3_final_test_is_default_off_guarded_and_after_all_routine_gates(self):
        script = Path("scripts/verify.sh").read_text(encoding="utf-8")
        router_command = (
            "PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval-v3"
        )

        self.assertIn(
            'ONECODE_RUN_ROUTER_V3_FINAL_TEST="${ONECODE_RUN_ROUTER_V3_FINAL_TEST:-0}"',
            script,
        )
        case_start = script.index('case "$ONECODE_RUN_ROUTER_V3_FINAL_TEST" in')
        invalid_start = script.index("  *)", case_start)
        case_end = script.index("esac", invalid_start)
        invalid_branch = script[invalid_start:case_end]
        self.assertIn("ONECODE_RUN_ROUTER_V3_FINAL_TEST must be 0 or 1", invalid_branch)
        self.assertIn("exit 2", invalid_branch)

        self.assertEqual(script.count(router_command), 2)
        self.assertEqual(script.count("--split validation"), 1)
        self.assertEqual(script.count("--split final_test"), 1)
        validation_call = script.index(router_command)
        final_call = script.rindex(router_command)
        final_split = script.index("--split final_test")
        self.assertLess(validation_call, final_call)
        self.assertGreater(final_split, final_call)

        guard_start = script.index(
            'if [[ "$ONECODE_RUN_ROUTER_V3_FINAL_TEST" == "1" ]]; then'
        )
        guard_end = script.index("\nfi", guard_start)
        self.assertLess(guard_start, final_call)
        self.assertLess(final_split, guard_end)
        self.assertEqual(script[guard_end + len("\nfi"):].strip(), "")

        routine_markers = [
            "if rg -n 'high-frequency-skill-selection[.]json'",
            "if grep -RInE --exclude='router_eval_v3.py'",
        ]
        for marker in routine_markers:
            self.assertLess(script.index(marker), final_call)

        unresolved_marker = "TO" + "DO|FIX" + "ME|PLACE" + "HOLDER|TB" + "D|"
        last_routine_gate = script.index(f'if search_repo "{unresolved_marker}')
        last_routine_gate_end = script.index("\nfi", last_routine_gate) + len("\nfi")
        self.assertLess(last_routine_gate_end, guard_start)


if __name__ == "__main__":
    unittest.main()
