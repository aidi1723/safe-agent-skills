import unittest
from pathlib import Path

from onecode_skill_sanitizer.validation import validate_source


class ValidationTest(unittest.TestCase):
    def test_validate_source_rejects_usage_that_conflicts_with_source_type(self):
        issues: list[dict] = []
        payload = {
            "source": {
                "type": "github_reference",
                "usage": "source_import",
                "path": "catalog/code/example",
                "url": "https://github.com/example/skills",
                "author": "example",
                "license": "MIT",
                "reference": "https://github.com/example/skills",
                "collected_by": "onecode-test",
                "captured_at": "2026-07-04T00:00:00Z",
            }
        }

        validate_source(payload, Path("skill.json"), issues)

        self.assertIn(
            "schema-invalid-source-usage-for-type",
            {issue["id"] for issue in issues},
        )


if __name__ == "__main__":
    unittest.main()
