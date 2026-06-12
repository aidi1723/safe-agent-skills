import unittest
from pathlib import Path


class VerifyScriptTest(unittest.TestCase):
    def test_verify_script_requires_ripgrep_before_scans(self):
        script = Path("scripts/verify.sh").read_text(encoding="utf-8")

        self.assertIn("require_command rg", script)
        self.assertNotIn("if command -v rg", script)


if __name__ == "__main__":
    unittest.main()
