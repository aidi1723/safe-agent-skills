import unittest
from pathlib import Path


class VerifyScriptTest(unittest.TestCase):
    def test_verify_script_falls_back_to_grep_when_ripgrep_is_missing(self):
        script = Path("scripts/verify.sh").read_text(encoding="utf-8")

        self.assertNotIn("require_command rg", script)
        self.assertIn("if command -v rg", script)
        self.assertIn("grep -RInE", script)


if __name__ == "__main__":
    unittest.main()
