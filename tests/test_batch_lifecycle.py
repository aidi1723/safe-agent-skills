import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from onecode_skill_sanitizer.batch_lifecycle import build_batch_index
from onecode_skill_sanitizer.batch_lifecycle import compact_promoted_bodies
from onecode_skill_sanitizer.batch_lifecycle import validate_batch_index
from onecode_skill_sanitizer.cli import main


def write_skill(root: Path, batch: str, name: str, body: str, status: str | None = None) -> Path:
    skill_dir = root / batch / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")
    payload = {"name": name}
    if status is not None:
        payload["status"] = status
    (skill_dir / "skill.json").write_text(json.dumps(payload), encoding="utf-8")
    return skill_dir


def write_catalog_skill(root: Path, category: str, name: str, body: str) -> Path:
    skill_dir = root / category / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")
    return skill_dir


class BatchLifecycleTest(unittest.TestCase):
    def test_batch_check_command_reports_clean_and_tampered_indexes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            batches = root / "batches"
            catalog = root / "catalog"
            write_skill(batches, "batch-a", "same-skill", "same\n")
            canonical = write_catalog_skill(catalog, "code", "same-skill", "same\n")
            index = build_batch_index(batches, catalog, source_commit="abc123")
            index_path = batches / "index.json"
            index_path.write_text(json.dumps(index), encoding="utf-8")

            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                clean_code = main(
                    [
                        "batch-check",
                        "--batches",
                        str(batches),
                        "--catalog",
                        str(catalog),
                        "--index",
                        str(index_path),
                    ]
                )
            (canonical / "SKILL.md").write_text("tampered\n", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                tampered_code = main(
                    [
                        "batch-check",
                        "--batches",
                        str(batches),
                        "--catalog",
                        str(catalog),
                        "--index",
                        str(index_path),
                    ]
                )

        self.assertEqual(clean_code, 0)
        self.assertEqual(json.loads(out.getvalue())["status"], "ok")
        self.assertEqual(tampered_code, 2)

    def test_inventory_classifies_draft_promoted_and_mismatch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            batches = root / "batches"
            catalog = root / "catalog"
            write_skill(batches, "batch-a", "draft-skill", "draft\n", "draft")
            write_skill(batches, "batch-a", "same-skill", "same\n")
            write_skill(batches, "batch-b", "changed-skill", "old\n")
            write_catalog_skill(catalog, "code", "same-skill", "same\n")
            write_catalog_skill(catalog, "code", "changed-skill", "new\n")

            inventory = build_batch_index(batches, catalog, source_commit="abc123")

        items = {item["name"]: item for item in inventory["items"]}
        self.assertEqual(items["draft-skill"]["lifecycle"], "active_draft")
        self.assertEqual(items["same-skill"]["lifecycle"], "promoted")
        self.assertTrue(items["same-skill"]["content_match"])
        self.assertEqual(items["changed-skill"]["lifecycle"], "promoted")
        self.assertFalse(items["changed-skill"]["content_match"])

    def test_compaction_only_replaces_byte_identical_promoted_body(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            batches = root / "batches"
            catalog = root / "catalog"
            same_dir = write_skill(batches, "batch-a", "same-skill", "same\n")
            changed_dir = write_skill(batches, "batch-a", "changed-skill", "old\n")
            write_catalog_skill(catalog, "code", "same-skill", "same\n")
            write_catalog_skill(catalog, "code", "changed-skill", "new\n")
            inventory = build_batch_index(batches, catalog, source_commit="abc123")

            result = compact_promoted_bodies(inventory, batches, catalog)
            issues = validate_batch_index(inventory, batches, catalog)

            self.assertEqual(result["compacted"], ["same-skill"])
            self.assertTrue((same_dir / "PROMOTED.md").is_file())
            self.assertFalse((same_dir / "SKILL.md").exists())
            self.assertTrue((changed_dir / "SKILL.md").is_file())
            self.assertEqual(issues, [])

    def test_rebuild_preserves_compacted_promotion_records(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            batches = root / "batches"
            catalog = root / "catalog"
            write_skill(batches, "batch-a", "same-skill", "same\n")
            write_catalog_skill(catalog, "code", "same-skill", "same\n")
            inventory = build_batch_index(batches, catalog, source_commit="abc123")
            compact_promoted_bodies(inventory, batches, catalog)

            rebuilt = build_batch_index(
                batches,
                catalog,
                source_commit="def456",
                previous_index=inventory,
            )

        self.assertEqual(rebuilt["item_count"], 1)
        self.assertTrue(rebuilt["items"][0]["compacted"])
        self.assertEqual(rebuilt["items"][0]["source_commit"], "abc123")

    def test_rebuild_preserves_compacted_record_after_catalog_evolves(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            batches = root / "batches"
            catalog = root / "catalog"
            write_skill(batches, "batch-a", "same-skill", "same\n")
            canonical = write_catalog_skill(catalog, "code", "same-skill", "same\n")
            inventory = build_batch_index(batches, catalog, source_commit="abc123")
            compact_promoted_bodies(inventory, batches, catalog)
            (canonical / "SKILL.md").write_text("expanded\n", encoding="utf-8")

            rebuilt = build_batch_index(
                batches,
                catalog,
                source_commit="def456",
                previous_index=inventory,
            )
            issues = validate_batch_index(rebuilt, batches, catalog)

        self.assertEqual(rebuilt["item_count"], 1)
        self.assertTrue(rebuilt["items"][0]["compacted"])
        self.assertFalse(rebuilt["items"][0]["content_match"])
        self.assertNotEqual(rebuilt["items"][0]["source_sha256"], rebuilt["items"][0]["catalog_sha256"])
        self.assertEqual(rebuilt["items"][0]["source_commit"], "abc123")
        self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()
