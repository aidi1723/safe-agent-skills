import json
import shutil
import tempfile
import unittest
from pathlib import Path

from onecode_skill_sanitizer import cli
from onecode_skill_sanitizer import registry
from onecode_skill_sanitizer.validation import (
    UnsafeAuxiliaryContentError,
    manifest_sha256,
    seal_manifest,
    text_sha256,
)


ROOT = Path(__file__).resolve().parents[1]


class RegistryBoundaryTest(unittest.TestCase):
    def test_verify_registry_reports_unsafe_auxiliary_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = ROOT / "catalog/commerce/commerce-product-keyword-plan"
            registry_dir = root / "catalog"
            skill_dir = registry_dir / "commerce" / source.name
            shutil.copytree(source, skill_dir)
            outside = root / "secret.txt"
            outside.write_text("secret\n", encoding="utf-8")
            link = skill_dir / "references/secret-link.txt"
            link.parent.mkdir(exist_ok=True)
            link.symlink_to(outside)
            manifest_path = skill_dir / "skill.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["hashes"]["auxiliary_sha256"] = "0" * 64
            seal_manifest(manifest)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            report = registry.verify_registry(registry_dir)

        self.assertEqual(report["status"], "failed")
        self.assertIn("unsafe-auxiliary-content", [item["id"] for item in report["issues"]])

    def test_reseal_rejects_unsafe_auxiliary_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = ROOT / "catalog/commerce/commerce-product-keyword-plan"
            skill_dir = root / "skill"
            shutil.copytree(source, skill_dir)
            outside = root / "secret.txt"
            outside.write_text("secret\n", encoding="utf-8")
            link = skill_dir / "scripts/secret-link.txt"
            link.parent.mkdir(exist_ok=True)
            link.symlink_to(outside)

            with self.assertRaises(UnsafeAuxiliaryContentError):
                registry.reseal_skill_content(skill_dir)

    def test_cli_reexports_registry_operations(self):
        self.assertIs(cli.load_manifest, registry.load_manifest)
        self.assertIs(cli.build_registry_index, registry.build_registry_index)
        self.assertIs(cli.verify_registry, registry.verify_registry)

    def test_reseal_content_updates_body_manifest_and_report_hashes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = ROOT / "catalog/commerce/commerce-product-keyword-plan"
            skill_dir = Path(temp_dir) / "skill"
            shutil.copytree(source, skill_dir)
            changed_body = "# Changed Skill\n"
            (skill_dir / "SKILL.md").write_text(changed_body, encoding="utf-8")

            manifest = registry.reseal_skill_content(skill_dir)
            report = json.loads((skill_dir / "SANITIZATION_REPORT.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["hashes"]["sanitized_sha256"], text_sha256(changed_body))
        self.assertEqual(manifest["hashes"]["manifest_sha256"], manifest_sha256(manifest))
        self.assertEqual(report["hashes"]["sanitized_sha256"], manifest["hashes"]["sanitized_sha256"])
        self.assertEqual(report["hashes"]["manifest_sha256"], manifest["hashes"]["manifest_sha256"])

    def test_seal_registry_manifests_leaves_valid_entries_unchanged(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = ROOT / "catalog/commerce/commerce-product-keyword-plan"
            skill_dir = Path(temp_dir) / "catalog" / "commerce" / source.name
            shutil.copytree(source, skill_dir)
            report_path = skill_dir / "SANITIZATION_REPORT.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["hashes"]["manifest_sha256"] = "report-sentinel"
            report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            manifest_path = skill_dir / "skill.json"
            manifest_before = manifest_path.read_bytes()
            report_before = report_path.read_bytes()

            registry.seal_registry_manifests(Path(temp_dir) / "catalog")

            self.assertEqual(manifest_path.read_bytes(), manifest_before)
            self.assertEqual(report_path.read_bytes(), report_before)


if __name__ == "__main__":
    unittest.main()
