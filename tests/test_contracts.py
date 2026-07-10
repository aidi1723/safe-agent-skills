import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from onecode_skill_sanitizer.contracts import contract_coverage


CORE_SCENARIOS = [
    "website-build-launch",
    "code-review-hardening",
    "codebase-change-lifecycle",
    "skill-router-quality-review",
    "open-source-release",
    "rag-agent-knowledge-app",
    "document-to-knowledge-base",
    "security-agent-guardrails",
]


class ContractCoverageTest(unittest.TestCase):
    def test_contract_v2_schema_is_strict(self):
        schema = json.loads(Path("schemas/contract-v2.schema.json").read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema)
        valid_contract = {
            "schema_version": 2,
            "stage_hint": "review",
            "capability_vector": ["code.review"],
        }

        self.assertEqual(list(validator.iter_errors(valid_contract)), [])
        self.assertTrue(list(validator.iter_errors({**valid_contract, "unknown": True})))

    def test_contract_coverage_counts_only_usable_contracts(self):
        registry = {
            "skills": [
                {"name": "alpha", "status": "trusted", "registry_path": "code/alpha"},
                {"name": "beta", "status": "trusted", "registry_path": "code/beta"},
            ]
        }
        bundles = {"bundles": [{"id": "core", "skills": ["beta", "alpha"]}]}

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for name, contract in [
                (
                    "alpha",
                    {
                        "schema_version": 2,
                        "stage_hint": "review",
                        "capability_vector": ["code.review"],
                    },
                ),
                ("beta", {"schema_version": 2, "stage_hint": "review", "capability_vector": []}),
            ]:
                skill_dir = root / "code" / name
                skill_dir.mkdir(parents=True)
                (skill_dir / "skill.json").write_text(
                    json.dumps({"name": name, "contract": contract}), encoding="utf-8"
                )

            result = contract_coverage(registry, bundles, registry_root=root)

        self.assertEqual(result["covered_skill_count"], 1)
        self.assertEqual(result["total_skill_count"], 2)
        self.assertEqual(result["coverage_ratio"], 0.5)
        self.assertEqual(result["missing_skill_names"], ["beta"])

    def test_contract_coverage_rejects_invalid_v2_contract_fields(self):
        registry = {"skills": [{"name": "alpha", "status": "trusted", "registry_path": "code/alpha"}]}
        bundles = {"bundles": [{"id": "core", "skills": ["alpha"]}]}

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill_dir = root / "code" / "alpha"
            skill_dir.mkdir(parents=True)
            (skill_dir / "skill.json").write_text(
                json.dumps(
                    {
                        "name": "alpha",
                        "contract": {
                            "schema_version": 2,
                            "stage_hint": "review",
                            "capability_vector": ["code.review"],
                            "retry_policy": "execute_automatically",
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = contract_coverage(registry, bundles, registry_root=root)

        self.assertEqual(result["covered_skill_count"], 0)
        self.assertEqual(result["missing_skill_names"], ["alpha"])

    def test_contract_coverage_filters_scenarios_and_sorts_missing_names(self):
        registry = {
            "skills": [
                {"name": "alpha", "status": "trusted", "registry_path": "code/alpha"},
                {"name": "beta", "status": "trusted", "registry_path": "code/beta"},
                {"name": "zeta", "status": "trusted", "registry_path": "code/zeta"},
            ]
        }
        bundles = {
            "bundles": [
                {"id": "first", "skills": ["zeta", "alpha"]},
                {"id": "second", "skills": ["beta"]},
            ]
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for name in ["alpha", "beta", "zeta"]:
                skill_dir = root / "code" / name
                skill_dir.mkdir(parents=True)
                (skill_dir / "skill.json").write_text(json.dumps({"name": name}), encoding="utf-8")

            result = contract_coverage(registry, bundles, ["first"], registry_root=root)

        self.assertEqual(result["scenario_ids"], ["first"])
        self.assertEqual(result["total_skill_count"], 2)
        self.assertEqual(result["missing_skill_names"], ["alpha", "zeta"])

    def test_real_catalog_core_scenarios_meet_contract_gate(self):
        registry = json.loads(Path("catalog/index.json").read_text(encoding="utf-8"))
        bundles = json.loads(Path("bundles/index.json").read_text(encoding="utf-8"))

        result = contract_coverage(registry, bundles, CORE_SCENARIOS, registry_root=Path("catalog"))

        self.assertGreaterEqual(result["coverage_ratio"], 0.80)


if __name__ == "__main__":
    unittest.main()
