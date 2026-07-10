import json
import shutil
import tempfile
import unittest
from pathlib import Path

from onecode_skill_sanitizer import cli
from onecode_skill_sanitizer import registry
from onecode_skill_sanitizer.validation import manifest_sha256, text_sha256


ROOT = Path(__file__).resolve().parents[1]


class RegistryBoundaryTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
