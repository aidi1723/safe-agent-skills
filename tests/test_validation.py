import copy
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from onecode_skill_sanitizer.validation import (
    UnsafeAuxiliaryContentError,
    auxiliary_content_sha256,
    validate_contract,
    validate_manifest_schema,
    validate_registry_index_schema,
    validate_sanitization_report_schema,
    validate_source,
    validate_verify_report_schema,
)


class ValidationTest(unittest.TestCase):
    def test_auxiliary_hash_preserves_regular_file_contract(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "skill"
            files = {
                "references/nested/guide.md": b"guide\n",
                "scripts/check.sh": b"#!/bin/sh\n",
            }
            for relative, content in files.items():
                path = skill_dir / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            expected = hashlib.sha256()
            for relative, content in sorted(files.items()):
                expected.update(relative.encode("utf-8"))
                expected.update(b"\0")
                expected.update(content)
                expected.update(b"\0")

            self.assertEqual(auxiliary_content_sha256(skill_dir), expected.hexdigest())
            self.assertIsNone(auxiliary_content_sha256(Path(temp_dir) / "empty"))

    def test_auxiliary_hash_rejects_symlinks_without_reading_targets(self):
        variants = [
            ("references/file-link", "file"),
            ("references/dir-link", "directory"),
            ("references/nested/file-link", "file"),
            ("scripts/file-link", "file"),
            ("scripts/dir-link", "directory"),
            ("assets/file-link", "file"),
            ("assets/dir-link", "directory"),
        ]
        original_read_bytes = Path.read_bytes
        for relative, target_kind in variants:
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                skill_dir = root / "skill"
                link = skill_dir / relative
                link.parent.mkdir(parents=True)
                outside = root / "outside"
                if target_kind == "directory":
                    outside.mkdir()
                    (outside / "secret.txt").write_text("secret\n", encoding="utf-8")
                else:
                    outside.write_text("secret\n", encoding="utf-8")

                link.symlink_to(outside, target_is_directory=target_kind == "directory")

                def guarded_read_bytes(path: Path) -> bytes:
                    if path == link or path == outside or outside in path.parents:
                        raise AssertionError("outside auxiliary target was read")
                    return original_read_bytes(path)

                with patch.object(Path, "read_bytes", guarded_read_bytes):
                    with self.assertRaises(UnsafeAuxiliaryContentError):
                        auxiliary_content_sha256(skill_dir)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO is not supported")
    def test_auxiliary_hash_rejects_special_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "skill"
            fifo = skill_dir / "references/events.fifo"
            fifo.parent.mkdir(parents=True)
            os.mkfifo(fifo)

            with self.assertRaises(UnsafeAuxiliaryContentError):
                auxiliary_content_sha256(skill_dir)

    def test_validate_contract_accepts_complete_v2_contract(self):
        issues: list[dict] = []
        payload = {
            "name": "example-skill",
            "contract": {
                "schema_version": 2,
                "stage_hint": "review",
                "capability_vector": ["code.review"],
                "requires_context": ["change_set"],
                "optional_context": ["test_evidence"],
                "produces_artifacts": ["review_report"],
                "produces_evidence": ["review_evidence"],
                "requires_after": ["codebase-explore-map"],
                "conflicts_with": [],
                "excludes": [],
                "approval_classes": [],
                "estimated_cost": {"time": 2, "tokens": 1, "runtime": 0},
                "idempotent": True,
                "retry_policy": "host_decides",
            },
        }

        validate_contract(payload, Path("skill.json"), issues)

        self.assertEqual(issues, [])

    def test_validate_contract_rejects_automatic_execution_retry_policy(self):
        issues: list[dict] = []
        payload = {
            "name": "example-skill",
            "contract": {
                "schema_version": 2,
                "stage_hint": "review",
                "capability_vector": ["code.review"],
                "retry_policy": "execute_automatically",
            },
        }

        validate_contract(payload, Path("skill.json"), issues)

        self.assertIn("schema-invalid-contract-retry-policy", {issue["id"] for issue in issues})

    def test_validate_contract_rejects_incomplete_v2_contract(self):
        issues: list[dict] = []
        payload = {"name": "example-skill", "contract": {"schema_version": 2}}

        validate_contract(payload, Path("skill.json"), issues)

        issue_ids = {issue["id"] for issue in issues}
        self.assertIn("schema-invalid-contract-stage", issue_ids)
        self.assertIn("schema-invalid-contract-capability", issue_ids)

    def test_validate_contract_rejects_boolean_and_float_integer_fields(self):
        invalid_contracts = [
            {"schema_version": True, "stage_hint": "review", "capability_vector": ["code.review"]},
            {"schema_version": 2.0, "stage_hint": "review", "capability_vector": ["code.review"]},
            {"schema_version": 2, "stage_hint": "review", "capability_vector": ["code.review"], "cost_weight": True},
            {
                "schema_version": 2,
                "stage_hint": "review",
                "capability_vector": ["code.review"],
                "estimated_cost": {"time": True, "tokens": 1, "runtime": 0},
            },
            {
                "schema_version": 2,
                "stage_hint": "review",
                "capability_vector": ["code.review"],
                "estimated_cost": {"time": 2.0, "tokens": 1, "runtime": 0},
            },
        ]

        for contract in invalid_contracts:
            with self.subTest(contract=contract):
                issues: list[dict] = []
                validate_contract({"name": "example-skill", "contract": contract}, Path("skill.json"), issues)
                self.assertTrue(issues)

    def test_validate_contract_is_total_for_unhashable_enum_values(self):
        cases = [
            {"schema_version": []},
            {"schema_version": {}},
            {"stage_hint": []},
            {"stage_hint": {}},
            {"retry_policy": []},
            {"retry_policy": {}},
        ]

        for contract in cases:
            with self.subTest(contract=contract):
                first: list[dict] = []
                second: list[dict] = []
                validate_contract(
                    {"name": "example-skill", "contract": contract},
                    Path("skill.json"),
                    first,
                )
                validate_contract(
                    {"name": "example-skill", "contract": contract},
                    Path("skill.json"),
                    second,
                )
                self.assertTrue(first)
                self.assertEqual(first, second)

    def test_manifest_validation_is_total_for_json_field_mutations(self):
        base = json.loads(
            Path("catalog/research/research-source-check/skill.json").read_text(
                encoding="utf-8"
            )
        )
        mutations = [
            (("status",), []),
            (("status",), {}),
            (("status",), None),
            (("status",), True),
            (("risk_level",), []),
            (("risk_level",), {}),
            (("risk_level",), None),
            (("risk_level",), False),
            (("policy", "filesystem", "scope"), []),
            (("policy", "filesystem", "scope"), {}),
            (("policy", "filesystem", "scope"), None),
            (("policy", "filesystem", "scope"), True),
            (("policy", "network", "scope"), []),
            (("policy", "network", "scope"), {}),
            (("policy", "network", "scope"), None),
            (("policy", "network", "scope"), False),
            (("source",), []),
            (("source", "type"), []),
            (("source", "usage"), {}),
            (("taxonomy",), False),
            (("taxonomy", "category"), []),
            (("allowed_tools",), {}),
            (("required_verifiers",), True),
            (("hashes",), []),
            (("contract", "schema_version"), []),
            (("contract", "stage_hint"), {}),
            (("contract", "retry_policy"), []),
            (("contract", "cost_weight"), {}),
            (("contract", "estimated_cost"), []),
            (("contract", "approval_classes"), {}),
        ]

        for keys, value in mutations:
            with self.subTest(keys=keys, value=value):
                payload = copy.deepcopy(base)
                target = payload
                for key in keys[:-1]:
                    target = target[key]
                target[keys[-1]] = value
                first: list[dict] = []
                second: list[dict] = []
                validate_manifest_schema(payload, Path("skill.json"), first)
                validate_manifest_schema(payload, Path("skill.json"), second)
                self.assertTrue(first)
                self.assertEqual(first, second)

    def test_index_and_verify_report_validation_are_total_for_json_values(self):
        index_cases = [
            {
                "schema_version": 1,
                "generated_at": "now",
                "skill_count": 1,
                "skills": [[]],
            },
            {
                "schema_version": 1,
                "generated_at": "now",
                "skill_count": 1,
                "skills": [{"status": [], "risk_level": {}}],
            },
        ]
        for payload in index_cases:
            with self.subTest(payload=payload):
                first: list[dict] = []
                second: list[dict] = []
                validate_registry_index_schema(payload, Path("index.json"), first)
                validate_registry_index_schema(payload, Path("index.json"), second)
                self.assertTrue(first)
                self.assertEqual(first, second)

        for status in ([], {}, None, True):
            with self.subTest(status=status):
                issues: list[dict] = []
                validate_verify_report_schema(
                    {
                        "schema_version": 1,
                        "generated_at": "now",
                        "status": status,
                        "skill_count": 0,
                        "trusted_count": 0,
                        "tampered_count": 0,
                        "unknown_provenance_count": 0,
                        "issues": [],
                    },
                    Path("verify.json"),
                    issues,
                )
                self.assertTrue(issues)

    def test_sanitization_report_allows_metadata_only_manifest_reseal(self):
        issues: list[dict] = []
        shared = {
            "schema_version": 1,
            "name": "example-skill",
            "status": "trusted",
            "risk_level": "low",
            "taxonomy": {"category": "code", "subcategory": "code.review", "collection_priority": "P0"},
            "source": {
                "type": "local_folder",
                "usage": "local_authoring",
                "path": "example",
                "url": "unknown",
                "author": "unknown",
                "license": "unknown",
                "reference": "unknown",
                "collected_by": "test",
                "captured_at": "2026-07-10T00:00:00Z",
            },
            "required_verifiers": [],
        }
        manifest = {
            **shared,
            "hashes": {"source_sha256": "a" * 64, "sanitized_sha256": "b" * 64, "manifest_sha256": "c" * 64},
        }
        report = {
            "schema_version": 1,
            "skill_name": "example-skill",
            "taxonomy": shared["taxonomy"],
            "source": shared["source"],
            "files": ["SKILL.md"],
            "hashes": {"source_sha256": "a" * 64, "sanitized_sha256": "b" * 64, "manifest_sha256": "d" * 64},
            "summary": {
                "status": "trusted",
                "risk_level": "low",
                "removed_fragment_count": 0,
                "rewritten_fragment_count": 0,
                "unresolved_finding_count": 0,
            },
            "findings": [],
            "required_verifiers": [],
            "recommendation": "trusted",
        }

        validate_sanitization_report_schema(report, Path("SANITIZATION_REPORT.json"), manifest, issues)

        self.assertNotIn("schema-report-hashes-mismatch", {issue["id"] for issue in issues})

    def test_validate_source_rejects_usage_that_conflicts_with_source_type(self):
        issues: list[dict] = []
        payload = {
            "source": {
                "type": "github_reference",
                "usage": "source_import",
                "path": "catalog/code/example",
                "url": "https://github.com/example/skills",
                "author": "example",
                "license": "MIT",
                "reference": "https://github.com/example/skills",
                "collected_by": "onecode-test",
                "captured_at": "2026-07-04T00:00:00Z",
            }
        }

        validate_source(payload, Path("skill.json"), issues)

        self.assertIn(
            "schema-invalid-source-usage-for-type",
            {issue["id"] for issue in issues},
        )


if __name__ == "__main__":
    unittest.main()
