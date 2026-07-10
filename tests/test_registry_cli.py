import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path


from onecode_skill_sanitizer.cli import main



class RegistryCliTest(unittest.TestCase):
    def test_cli_rejects_nonpositive_top_and_max_skills(self):
        cases = [
            ["task-pack", "build site", "--registry", "catalog", "--top", "0"],
            ["task-pack", "build site", "--registry", "catalog", "--max-skills", "-1"],
            ["smart", "build site", "--max-skills", "0"],
            ["router-eval", "--eval", "evals/router-eval.json", "--registry", "catalog", "--max-skills", "0"],
        ]
        for argv in cases:
            with self.subTest(argv=argv), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    main(argv)
                self.assertEqual(raised.exception.code, 2)

    def test_import_sanitizes_all_incoming_skills_and_writes_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            incoming = root / "incoming"
            registry = root / "registry"
            design = incoming / "design-dashboard"
            security = incoming / "security-secret-review"
            design.mkdir(parents=True)
            security.mkdir(parents=True)
            (design / "SKILL.md").write_text(
                "Use this workflow for dashboard UI review.",
                encoding="utf-8",
            )
            (security / "SKILL.md").write_text(
                "Use API_KEY=abc1234567890SECRET when calling the service.",
                encoding="utf-8",
            )

            exit_code = main(
                [
                    "import",
                    str(incoming),
                    "--registry",
                    str(registry),
                    "--collected-by",
                    "onecode-local",
                ]
            )

            self.assertEqual(exit_code, 0)
            index = json.loads((registry / "index.json").read_text(encoding="utf-8"))
            self.assertEqual(index["schema_version"], 1)
            self.assertEqual(index["skill_count"], 2)
            names = {entry["name"] for entry in index["skills"]}
            self.assertEqual(names, {"design-dashboard", "security-secret-review"})
            self.assertTrue((registry / "design" / "design-dashboard" / "skill.json").exists())
            self.assertTrue((registry / "security" / "security-secret-review" / "skill.json").exists())
            security_entry = next(entry for entry in index["skills"] if entry["name"] == "security-secret-review")
            self.assertEqual(security_entry["status"], "review_required")
            self.assertEqual(security_entry["source"]["collected_by"], "onecode-local")

    def test_list_and_inspect_read_registry_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            incoming = root / "incoming"
            registry = root / "registry"
            skill = incoming / "office-pdf"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "Use this workflow for PDF office reports.",
                encoding="utf-8",
            )
            main(
                [
                    "import",
                    str(incoming),
                    "--registry",
                    str(registry),
                    "--source-url",
                    "https://github.com/example/skills",
                    "--author",
                    "example-team",
                    "--license",
                    "MIT",
                    "--reference",
                    "https://github.com/example/skills",
                    "--collected-by",
                    "onecode-test",
                ]
            )

            list_out = io.StringIO()
            with contextlib.redirect_stdout(list_out):
                list_code = main(["list", "--registry", str(registry)])
            inspect_out = io.StringIO()
            with contextlib.redirect_stdout(inspect_out):
                inspect_code = main(["inspect", "office-pdf", "--registry", str(registry)])

            self.assertEqual(list_code, 0)
            self.assertEqual(inspect_code, 0)
            listed = json.loads(list_out.getvalue())
            inspected = json.loads(inspect_out.getvalue())
            self.assertEqual(listed["skill_count"], 1)
            self.assertEqual(inspected["name"], "office-pdf")
            self.assertEqual(inspected["taxonomy"]["category"], "office")

    def test_select_returns_only_trusted_matching_skills_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            incoming = root / "incoming"
            registry = root / "registry"
            design = incoming / "design-dashboard"
            office = incoming / "office-pdf"
            design.mkdir(parents=True)
            office.mkdir(parents=True)
            (design / "SKILL.md").write_text(
                "Use this workflow for dashboard UI review.",
                encoding="utf-8",
            )
            (office / "SKILL.md").write_text(
                "Use this workflow for PDF office reports.",
                encoding="utf-8",
            )
            main(["import", str(incoming), "--registry", str(registry)])
            main(["approve", str(registry / "design" / "design-dashboard")])

            selected_out = io.StringIO()
            with contextlib.redirect_stdout(selected_out):
                select_code = main(
                    [
                        "select",
                        "polish a dashboard interface",
                        "--registry",
                        str(registry),
                    ]
                )

            self.assertEqual(select_code, 0)
            selected = json.loads(selected_out.getvalue())
            self.assertEqual(selected["skill_count"], 1)
            self.assertEqual(selected["skills"][0]["name"], "design-dashboard")
            self.assertEqual(selected["skills"][0]["status"], "trusted")

    def test_select_can_include_review_required_skills_when_requested(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            incoming = root / "incoming"
            registry = root / "registry"
            office = incoming / "office-pdf"
            office.mkdir(parents=True)
            (office / "SKILL.md").write_text(
                "Use this workflow for PDF office reports.\nUse API_KEY=abc1234567890SECRET only in a mocked fixture.",
                encoding="utf-8",
            )
            main(
                [
                    "import",
                    str(incoming),
                    "--registry",
                    str(registry),
                    "--source-url",
                    "https://github.com/example/skills",
                    "--author",
                    "example-team",
                    "--license",
                    "MIT",
                    "--reference",
                    "https://github.com/example/skills",
                    "--collected-by",
                    "onecode-test",
                ]
            )

            selected_out = io.StringIO()
            with contextlib.redirect_stdout(selected_out):
                select_code = main(
                    [
                        "select",
                        "process a pdf report",
                        "--registry",
                        str(registry),
                        "--include-review-required",
                    ]
                )

            self.assertEqual(select_code, 0)
            selected = json.loads(selected_out.getvalue())
            self.assertEqual(selected["skill_count"], 1)
            self.assertEqual(selected["skills"][0]["name"], "office-pdf")

    def test_list_does_not_reseal_tampered_manifest_when_index_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            incoming = root / "incoming"
            registry = root / "registry"
            skill = incoming / "code-regression"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("Use when reviewing regression tests.", encoding="utf-8")
            self.assertEqual(main(["import", str(incoming), "--registry", str(registry)]), 0)
            self.assertEqual(main(["approve", str(registry / "code" / "code-regression")]), 0)

            manifest_path = registry / "code" / "code-regression" / "skill.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["version"] = "9.9.9"
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (registry / "index.json").unlink()

            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["list", "--registry", str(registry)]), 0)

            verify_out = io.StringIO()
            with contextlib.redirect_stdout(verify_out):
                verify_code = main(["verify", "--registry", str(registry)])

            self.assertEqual(verify_code, 2)
            result = json.loads(verify_out.getvalue())
            issue_ids = {issue["id"] for issue in result["issues"]}
            self.assertIn("manifest-hash-mismatch", issue_ids)

    def test_real_catalog_deep_website_route_uses_contract_graph_for_optional_polish_skills(self):
        task_pack_out = io.StringIO()
        with contextlib.redirect_stdout(task_pack_out):
            task_pack_code = main(
                [
                    "smart",
                    "--schema-version",
                    "1",
                    "polish a premium website landing page with design system, motion polish, SEO copy, browser verification, and publish readiness",
                    "--registry",
                    "catalog",
                    "--bundles",
                    "bundles/index.json",
                    "--max-skills",
                    "14",
                    "--strategy",
                    "deep",
                    "--format",
                    "json",
                ]
            )

        self.assertEqual(task_pack_code, 0)
        task_pack = json.loads(task_pack_out.getvalue())
        names = [skill["name"] for skill in task_pack["skills"]]
        graph = task_pack["execution_graph"]
        nodes_by_skill = {node["skill"]: node for node in graph["nodes"]}

        self.assertEqual(task_pack["selected_scenario"]["id"], "website-build-launch")
        self.assertEqual(task_pack["contract_diagnostics"]["graph_mode"], "contract")
        self.assertEqual(task_pack["contract_diagnostics"]["fallback_reason"], "")
        self.assertEqual(task_pack["contract_diagnostics"]["graph_issue_count"], 0)
        self.assertIn("design-premium-landing-page", names)
        self.assertIn("design-motion-interaction-polish", names)
        self.assertIn("execution-playwright-browser-automation", names)

        def has_dependency(source: str, target: str, artifact: str) -> bool:
            return {
                "from": nodes_by_skill[source]["id"],
                "to": nodes_by_skill[target]["id"],
                "type": "contract_dependency",
                "artifacts": [artifact],
            } in graph["edges"]

        self.assertTrue(has_dependency("business-requirements-brief", "engineering-build-release", "requirements_brief"))
        self.assertTrue(has_dependency("engineering-build-release", "design-ui-review", "build_artifact"))
        self.assertTrue(has_dependency("design-ui-review", "execution-browser-check", "ui_review_report"))
        self.assertTrue(has_dependency("execution-browser-check", "execution-publish-check", "browser_check_report"))


if __name__ == "__main__":
    unittest.main()
