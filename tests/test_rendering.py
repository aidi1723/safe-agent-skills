import unittest

from onecode_skill_sanitizer import cli
from onecode_skill_sanitizer import rendering


class RenderingBoundaryTest(unittest.TestCase):
    def test_cli_reexports_rendering_functions(self):
        self.assertIs(cli.render_task_pack_markdown, rendering.render_task_pack_markdown)
        self.assertIs(cli.render_task_pack_v2_markdown, rendering.render_task_pack_v2_markdown)
        self.assertIs(cli.markdown_safe_line, rendering.markdown_safe_line)
        self.assertIs(cli.project_legacy_contracts, rendering.project_legacy_contracts)


if __name__ == "__main__":
    unittest.main()
