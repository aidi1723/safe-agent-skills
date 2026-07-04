import json
import tempfile
import unittest
from pathlib import Path

from onecode_skill_sanitizer.references import validate_external_references


class ReferencesTest(unittest.TestCase):
    def test_validate_external_references_rejects_non_metadata_only_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            references = Path(tmp) / "index.json"
            references.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "reference_count": 1,
                        "references": [
                            {
                                "name": "ExampleTool",
                                "source_url": "https://github.com/example/tool",
                                "source_type": "github_reference",
                                "author": "example",
                                "license": "MIT",
                                "captured_at": "2026-07-04",
                                "project_category": "tool_router",
                                "claimed_capabilities": ["tool_selection"],
                                "taxonomy_categories": ["ai.routing"],
                                "runtime_permission_notes": "Reference only.",
                                "adoption_status": "reference_only",
                                "review_notes": "Metadata-only reference.",
                                "metadata_only": False,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = validate_external_references(references)

        self.assertEqual(result["status"], "failed")
        self.assertIn("reference-not-metadata-only", {issue["id"] for issue in result["issues"]})


if __name__ == "__main__":
    unittest.main()
