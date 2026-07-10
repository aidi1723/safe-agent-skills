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


if __name__ == "__main__":
    unittest.main()
