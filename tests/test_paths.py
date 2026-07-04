import os
import tempfile
import unittest
from pathlib import Path

from onecode_skill_sanitizer.paths import PROJECT_HOME_ENV, resolve_project_asset_path


class PathsTest(unittest.TestCase):
    def test_resolve_project_asset_path_uses_safe_agent_skills_home(self):
        original_home = os.environ.get(PROJECT_HOME_ENV)
        original_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as project_tmp, tempfile.TemporaryDirectory() as cwd_tmp:
            root = Path(project_tmp)
            (root / "catalog").mkdir()
            try:
                os.environ[PROJECT_HOME_ENV] = str(root)
                os.chdir(cwd_tmp)

                resolved = resolve_project_asset_path("catalog")
            finally:
                os.chdir(original_cwd)
                if original_home is None:
                    os.environ.pop(PROJECT_HOME_ENV, None)
                else:
                    os.environ[PROJECT_HOME_ENV] = original_home

        self.assertEqual(resolved, (root / "catalog").resolve())


if __name__ == "__main__":
    unittest.main()
