import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from onecode_skill_sanitizer.registry import reseal_skill_content, verify_registry
from onecode_skill_sanitizer.cli import main
from onecode_skill_sanitizer.skill_depth import analyze_skill, audit_catalog_depth
from onecode_skill_sanitizer.validation import auxiliary_content_sha256


ROOT = Path(__file__).resolve().parents[1]


class SkillDepthTest(unittest.TestCase):
    def assert_real_specialist(self, name: str):
        report = audit_catalog_depth(ROOT / "catalog", ROOT / "catalog/depth-policy.json")
        skill_report = next(item for item in report["skills"] if item["name"] == name)
        skill_dir = next((ROOT / "catalog").glob(f"*/{name}"))
        manifest = json.loads((skill_dir / "skill.json").read_text(encoding="utf-8"))

        self.assertEqual(skill_report["depth_class"], "specialist")
        self.assertEqual(skill_report["reference_count"], 1)
        self.assertIn("Decision Guidance", skill_report["sections"])
        self.assertIn("Evidence Minimum", skill_report["sections"])
        self.assertIn("References", skill_report["sections"])
        self.assertEqual(skill_report["warnings"], [])
        self.assertEqual(
            manifest["hashes"]["auxiliary_sha256"],
            auxiliary_content_sha256(skill_dir),
        )

    def test_real_ui_review_is_specialist_with_protected_reference(self):
        self.assert_real_specialist("design-ui-review")

    def test_real_code_review_is_specialist_with_protected_reference(self):
        self.assert_real_specialist("code-review-risk")

    def test_real_regression_testing_is_specialist_with_protected_reference(self):
        self.assert_real_specialist("code-test-regression")

    def test_real_source_check_is_specialist_with_protected_reference(self):
        self.assert_real_specialist("research-source-check")

    def test_real_codebase_explore_is_specialist_with_protected_reference(self):
        self.assert_real_specialist("codebase-explore-map")

    def test_real_browser_check_is_specialist_with_protected_reference(self):
        self.assert_real_specialist("execution-browser-check")

    def test_real_ci_troubleshoot_is_specialist_with_protected_reference(self):
        self.assert_real_specialist("engineering-ci-troubleshoot")

    def test_real_pdf_report_is_specialist_with_protected_reference(self):
        self.assert_real_specialist("office-pdf-report")

    def test_real_docx_brief_is_specialist_with_protected_reference(self):
        self.assert_real_specialist("office-docx-brief")

    def test_real_table_analysis_is_specialist_with_protected_reference(self):
        self.assert_real_specialist("data-table-analysis")

    def test_depth_check_command_returns_warnings_without_failure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill_dir = root / "catalog/code/specialist"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                """# Specialist

## When To Use
Use for review.

## Safe Workflow
1. Review.

## Expected Output
- findings

## Verifier Expectations
- evidence check
""",
                encoding="utf-8",
            )
            policy_path = root / "depth-policy.json"
            policy_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "default_depth_class": "routing_card",
                        "skills": {"specialist": "specialist"},
                    }
                ),
                encoding="utf-8",
            )
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                exit_code = main(
                    [
                        "depth-check",
                        "--catalog",
                        str(root / "catalog"),
                        "--policy",
                        str(policy_path),
                    ]
                )

        payload = json.loads(out.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["status"], "ok")
        self.assertGreater(payload["warning_count"], 0)

    def test_specialist_without_reference_is_warning(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "specialist"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                """# Specialist

## When To Use

Use this for a specialist review.

## Safe Workflow

1. Review the evidence.

## Expected Output

- findings

## Verifier Expectations

- evidence check

## Failure Handling

Stop when evidence is missing.
""",
                encoding="utf-8",
            )

            report = analyze_skill(skill_dir, {"depth_class": "specialist"})

        self.assertIn("specialist-missing-reference", [item["id"] for item in report["warnings"]])

    def test_auxiliary_hash_changes_with_reference_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "skill"
            reference = skill_dir / "references/guide.md"
            reference.parent.mkdir(parents=True)
            reference.write_text("first\n", encoding="utf-8")
            first = auxiliary_content_sha256(skill_dir)
            reference.write_text("changed\n", encoding="utf-8")

            second = auxiliary_content_sha256(skill_dir)

        self.assertNotEqual(first, second)

    def test_verify_registry_reports_auxiliary_tampering(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            registry_dir = Path(temp_dir) / "catalog"
            skill_dir = registry_dir / "commerce/commerce-product-keyword-plan"
            shutil.copytree(ROOT / "catalog/commerce/commerce-product-keyword-plan", skill_dir)
            reference = skill_dir / "references/guide.md"
            reference.parent.mkdir()
            reference.write_text("reviewed\n", encoding="utf-8")
            reseal_skill_content(skill_dir)
            reference.write_text("tampered\n", encoding="utf-8")

            report = verify_registry(registry_dir)

        self.assertIn("auxiliary-content-mismatch", [item["id"] for item in report["issues"]])


if __name__ == "__main__":
    unittest.main()
