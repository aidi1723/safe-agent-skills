import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


class VerifyScriptTest(unittest.TestCase):
    def _search_repo_runner(self, repository: Path) -> Path:
        script = Path("scripts/verify.sh").read_text(encoding="utf-8")
        function_start = script.index("search_repo() {")
        function_end = script.index("\n}\n", function_start) + 3
        runner = repository / "run-search-repo.sh"
        runner.write_text(
            "#!/usr/bin/env bash\nset -u\n"
            + script[function_start:function_end]
            + '\nsearch_repo "$@"\n',
            encoding="utf-8",
        )
        runner.chmod(0o755)
        return runner

    def _tracked_search_fixture(self, repository: Path) -> Path:
        subprocess.run(
            ["git", "init", "--quiet", str(repository)],
            check=True,
            capture_output=True,
            text=True,
        )
        (repository / "tracked-clean.txt").write_text("release ready\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "tracked-clean.txt"],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        )
        for relative_path in (
            ".venv/lib/private.py",
            "venv/lib/private.py",
            ".worktrees/topic/private.txt",
            ".pytest_cache/private.txt",
            ".ruff_cache/private.txt",
            "unrelated-local-draft.txt",
        ):
            path = repository / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "/" + "Users/local/private TO" + "DO PLACE" + "HOLDER\n",
                encoding="utf-8",
            )
        return self._search_repo_runner(repository)

    def _run_search(
        self,
        runner: Path,
        pattern: str,
        exclude_path: str | None = None,
        *,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = [str(runner), pattern]
        if exclude_path is not None:
            command.append(exclude_path)
        return subprocess.run(
            command,
            cwd=runner.parent,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

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

    def test_repo_search_ignores_untracked_local_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = Path(temp_dir)
            runner = self._tracked_search_fixture(repository)
            marker_pattern = "TO" + "DO|FIX" + "ME|PLACE" + "HOLDER|T" + "BD|待" + "定"

            for pattern in ("/[U]sers/", marker_pattern):
                with self.subTest(pattern=pattern):
                    result = self._run_search(runner, pattern)
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    self.assertEqual(result.stdout, "")

    def test_repo_search_ignores_untracked_local_files_without_ripgrep(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = Path(temp_dir)
            runner = self._tracked_search_fixture(repository)
            env = {**os.environ, "PATH": "/usr/bin:/bin"}
            self.assertIsNone(shutil.which("rg", path=env["PATH"]))
            marker_pattern = "TO" + "DO|FIX" + "ME|PLACE" + "HOLDER|T" + "BD|待" + "定"

            for pattern in ("/[U]sers/", marker_pattern):
                with self.subTest(pattern=pattern):
                    result = self._run_search(runner, pattern, env=env)
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    self.assertEqual(result.stdout, "")

    def test_repo_search_reports_tracked_matches_and_preserves_exit_codes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = Path(temp_dir)
            runner = self._tracked_search_fixture(repository)
            tracked_match = repository / "tracked-private.txt"
            tracked_match.write_text("/" + "Users/tracked/private\n", encoding="utf-8")
            subprocess.run(
                ["git", "add", tracked_match.name],
                cwd=repository,
                check=True,
                capture_output=True,
                text=True,
            )

            match = self._run_search(runner, "/[U]sers/")
            no_match = self._run_search(runner, "pattern-that-does-not-exist")

            self.assertEqual(match.returncode, 0, match.stderr)
            self.assertIn("tracked-private.txt:1:/" + "Users/tracked/private", match.stdout)
            self.assertEqual(no_match.returncode, 1, no_match.stderr)
            self.assertEqual(no_match.stdout, "")

    def test_repo_search_excludes_the_requested_tracked_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = Path(temp_dir)
            runner = self._tracked_search_fixture(repository)
            excluded = repository / "verify-source.sh"
            excluded.write_text("TO" + "DO\n", encoding="utf-8")
            subprocess.run(
                ["git", "add", excluded.name],
                cwd=repository,
                check=True,
                capture_output=True,
                text=True,
            )

            marker_pattern = "TO" + "DO|FIX" + "ME|PLACE" + "HOLDER|T" + "BD|待" + "定"
            included = self._run_search(runner, marker_pattern)
            excluded_result = self._run_search(
                runner,
                marker_pattern,
                excluded.name,
            )

            self.assertEqual(included.returncode, 0, included.stderr)
            self.assertIn("verify-source.sh:1:TO" + "DO", included.stdout)
            self.assertEqual(
                excluded_result.returncode,
                1,
                excluded_result.stdout + excluded_result.stderr,
            )
            self.assertEqual(excluded_result.stdout, "")

    def test_verify_script_searches_only_git_tracked_files(self):
        script = Path("scripts/verify.sh").read_text(encoding="utf-8")

        self.assertIn("git grep -n -E", script)
        self.assertNotIn("rg -n", script)
        self.assertNotIn("grep -R", script)


if __name__ == "__main__":
    unittest.main()
