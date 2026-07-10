import unittest

from onecode_skill_sanitizer import bulk
from onecode_skill_sanitizer import cli


class BulkBoundaryTest(unittest.TestCase):
    def test_cli_reexports_bulk_builders(self):
        self.assertIs(cli.build_claude_skills_bulk_plan, bulk.build_claude_skills_bulk_plan)
        self.assertIs(cli.build_claude_skills_bulk_assessment, bulk.build_claude_skills_bulk_assessment)

    def test_cli_keeps_draft_builder_compatibility_wrapper(self):
        self.assertIsNot(cli.build_claude_skills_bulk_drafts, bulk.build_claude_skills_bulk_drafts)


if __name__ == "__main__":
    unittest.main()
