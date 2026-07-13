import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, validators

from onecode_skill_sanitizer.contracts import contract_coverage
from onecode_skill_sanitizer.registry import VerifiedRegistrySkill
from onecode_skill_sanitizer.registry import VerifiedRegistrySnapshot


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

REVIEWED_CORE_CONTRACTS = {
    "ai-langchain-agent-orchestration": (["agent_task", "available_tools", "data_sources", "allowed_actions"], []),
    "ai-llamaindex-rag-knowledge-workflow": (["knowledge_sources", "grounding_requirements"], []),
    "ai-opensquilla-metaskill-workflow": (["repeated_task", "expected_artifact", "verification_requirements"], []),
    "ai-opensquilla-token-routing-pattern": (["agent_task", "trusted_skill_catalog", "context_budget"], []),
    "ai-output-schema-eval": (["output_under_review", "expected_schema_or_checklist"], []),
    "ai-rule-failure-log-synthesis": (["sanitized_failure_logs", "failed_rules_or_verifiers"], []),
    "ai-tool-schema-protocol-check": (["tool_or_protocol_schema", "arguments_or_payload"], []),
    "business-requirements-brief": (["business_goal", "stakeholders", "constraints"], []),
    "code-ast-refactor-safety": (["codebase_context", "refactor_target", "behavior_constraints"], []),
    "code-dead-path-cleanup-review": (["codebase_context", "cleanup_candidates"], []),
    "code-python-debug": (["python_failure", "expected_behavior", "reproduction_context"], ["shell_execution"]),
    "code-review-risk": (["change_set", "review_scope"], []),
    "code-simplify-refactor-plan": (["codebase_context", "simplification_target", "behavior_invariants"], []),
    "code-test-regression": (["behavior_or_change_under_test", "regression_scope"], ["shell_execution"]),
    "codebase-explore-map": (["repository", "change_goal"], []),
    "content-seo-brief": (["topic", "audience", "search_goal"], []),
    "content-social-post": (["topic", "audience", "facts", "channel_constraints"], []),
    "data-haystack-rag-pipeline": (["application_goal", "knowledge_sources", "retrieval_requirements"], []),
    "data-marker-pdf-markdown-review": (["source_pdf", "conversion_output", "quality_criteria"], []),
    "data-markitdown-file-to-markdown": (["source_files", "conversion_requirements"], []),
    "data-qdrant-vector-retrieval": (["retrieval_corpus", "query_requirements", "metadata_filters"], []),
    "data-unstructured-document-partition": (["source_documents", "partition_requirements"], []),
    "design-motion-interaction-polish": (["interface_under_review", "interaction_goals"], []),
    "design-premium-landing-page": (["landing_page_goal", "audience", "brand_constraints"], []),
    "design-system-consistency": (["interface_scope", "design_tokens_or_components"], []),
    "design-tailwind-radix-system": (["react_project", "component_system_requirements"], []),
    "design-ui-review": (["interface_under_review", "user_goals", "viewport_targets"], []),
    "design-visual-quality-review": (["interface_under_review", "product_domain", "viewport_targets"], []),
    "engineering-build-release": (["project_context", "build_command", "release_target"], ["shell_execution"]),
    "engineering-ci-troubleshoot": (["pipeline_failure", "ci_logs", "pipeline_configuration"], ["shell_execution"]),
    "execution-browser-check": (["target_page_or_flow", "browser_check_criteria"], ["browser_automation"]),
    "execution-browser-use-web-task": (["web_task", "target_sites", "allowed_actions"], ["browser_automation", "network_access"]),
    "execution-playwright-browser-automation": (["target_url", "browser_assertions", "allowed_actions"], ["browser_automation"]),
    "execution-publish-check": (["release_candidate", "release_criteria", "verification_evidence"], []),
    "research-source-check": (["claims_to_verify", "source_requirements"], ["network_access"]),
    "security-guardrails-output-validation": (["output_under_review", "validation_rules", "failure_policy"], []),
    "security-llm-guard-io-scanning": (["agent_io_boundaries", "scan_policy"], []),
    "security-prompt-injection-review": (["prompt_or_agent_instructions", "authority_boundary"], []),
    "security-supply-chain-review": (["source_or_package_metadata", "provenance_record", "intended_use"], []),
}


STRICT_TYPE_CHECKER = Draft202012Validator.TYPE_CHECKER.redefine(
    "integer", lambda checker, value: isinstance(value, int) and not isinstance(value, bool)
)
StrictDraft202012Validator = validators.extend(Draft202012Validator, type_checker=STRICT_TYPE_CHECKER)


def contract_validator():
    schema = json.loads(Path("schemas/contract-v2.schema.json").read_text(encoding="utf-8"))
    return StrictDraft202012Validator(schema)


def manifest_validator():
    schema = json.loads(Path("schemas/skill-manifest.schema.json").read_text(encoding="utf-8"))
    return StrictDraft202012Validator(schema)


class ContractCoverageTest(unittest.TestCase):
    def test_contract_coverage_uses_verified_snapshot_without_manifest_reread(self):
        registry = {
            "skills": [
                {
                    "name": "alpha",
                    "status": "trusted",
                    "registry_path": "code/alpha",
                }
            ]
        }
        manifest = {
            "name": "alpha",
            "contract": {
                "schema_version": 2,
                "stage_hint": "review",
                "capability_vector": ["code.review"],
            },
        }
        snapshot = VerifiedRegistrySnapshot(
            index_json=json.dumps(registry),
            skills=(
                VerifiedRegistrySkill(
                    registry_path="code/alpha",
                    entry_json=json.dumps(registry["skills"][0]),
                    manifest_json=json.dumps(manifest),
                    skill_text="---\nname: alpha\n---\n",
                ),
            ),
            verification_json=json.dumps({"status": "ok"}),
        )

        result = contract_coverage(
            registry,
            {"bundles": [{"id": "core", "skills": ["alpha"]}]},
            registry_root=Path("does-not-exist"),
            snapshot=snapshot,
        )

        self.assertEqual(result["coverage_ratio"], 1.0)
        self.assertEqual(result["covered_skill_names"], ["alpha"])

    def test_contract_v2_schema_is_strict(self):
        validator = contract_validator()
        valid_contract = {
            "schema_version": 2,
            "stage_hint": "review",
            "capability_vector": ["code.review"],
        }

        self.assertEqual(list(validator.iter_errors(valid_contract)), [])
        self.assertTrue(list(validator.iter_errors({**valid_contract, "unknown": True})))
        self.assertTrue(list(validator.iter_errors({**valid_contract, "schema_version": True})))
        self.assertTrue(list(validator.iter_errors({**valid_contract, "schema_version": 2.0})))
        self.assertTrue(list(validator.iter_errors({**valid_contract, "cost_weight": True})))
        self.assertTrue(
            list(
                validator.iter_errors(
                    {**valid_contract, "estimated_cost": {"time": True, "tokens": 1, "runtime": 0}}
                )
            )
        )
        self.assertTrue(
            list(
                validator.iter_errors(
                    {**valid_contract, "estimated_cost": {"time": 2.0, "tokens": 1, "runtime": 0}}
                )
            )
        )

    def test_authoritative_manifest_schema_accepts_legacy_contract(self):
        validator = manifest_validator()
        manifest_path = next(Path("catalog").glob("*/business-requirements-brief/skill.json"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["contract"] = {
            "schema_version": 1,
            "stage_hint": "planning",
            "capability_vector": ["business.requirements"],
            "requires_context": ["business_goal"],
            "produces_artifacts": ["requirements_brief"],
            "cost_weight": 1,
        }

        self.assertEqual(list(validator.iter_errors(manifest)), [])

    def test_embedded_contract_v2_schema_matches_standalone_core(self):
        manifest_schema = json.loads(Path("schemas/skill-manifest.schema.json").read_text(encoding="utf-8"))
        standalone = json.loads(Path("schemas/contract-v2.schema.json").read_text(encoding="utf-8"))
        embedded = manifest_schema["$defs"]["contractV2"]

        for field in ["type", "additionalProperties", "required", "properties", "$defs"]:
            self.assertEqual(embedded[field], standalone[field], field)

    def test_contract_coverage_rejects_malformed_registry_and_bundle_inputs(self):
        valid_registry = {
            "skills": [{"name": "alpha", "status": "trusted", "registry_path": "code/alpha"}]
        }
        valid_bundles = {"bundles": [{"id": "core", "skills": ["alpha"]}]}
        cases = [
            ([], valid_bundles, None, "registry index must be an object"),
            ({"skills": "abc"}, valid_bundles, None, "registry index skills must be an array"),
            ({"skills": ["alpha"]}, valid_bundles, None, "registry skill entry 0 must be an object"),
            (
                {"skills": [{"name": "alpha", "status": "unknown", "registry_path": "code/alpha"}]},
                valid_bundles,
                None,
                "registry skill alpha status is not supported: unknown",
            ),
            (
                {"skills": [{"name": "alpha", "status": "trusted", "registry_path": "../alpha"}]},
                valid_bundles,
                None,
                "registry skill alpha registry_path must be a safe relative path",
            ),
            (
                {"skills": [{"name": "alpha", "status": "trusted", "registry_path": "code/alpha"}, {"name": "alpha", "status": "trusted", "registry_path": "code/beta"}]},
                valid_bundles,
                None,
                "registry skill names must be unique: alpha",
            ),
            (valid_registry, [], None, "bundles index must be an object"),
            (valid_registry, {"bundles": "abc"}, None, "bundles index bundles must be an array"),
            (valid_registry, {"bundles": ["core"]}, None, "bundle entry 0 must be an object"),
            (valid_registry, {"bundles": [{"id": "core", "skills": "abc"}]}, None, "bundle core skills must be a nonempty string array"),
            (valid_registry, {"bundles": [{"id": "core", "skills": []}]}, None, "bundle core skills must be a nonempty string array"),
            (
                valid_registry,
                {"bundles": [{"id": "core", "skills": ["alpha", "alpha"]}]},
                None,
                "bundle core skills must be unique",
            ),
            (
                valid_registry,
                {"bundles": [{"id": "core", "skills": ["alpha"]}, {"id": "core", "skills": ["alpha"]}]},
                None,
                "bundle ids must be unique: core",
            ),
            (valid_registry, {"bundles": []}, None, "no scenarios are available for contract coverage"),
            (valid_registry, valid_bundles, [], "no scenarios were selected for contract coverage"),
        ]

        for registry, bundles, scenario_ids, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, f"^{message}$"):
                contract_coverage(registry, bundles, scenario_ids)

    def test_authoritative_manifest_schema_validates_all_migrated_manifests(self):
        validator = manifest_validator()
        validated = []
        for name in REVIEWED_CORE_CONTRACTS:
            manifest_path = next(Path("catalog").glob(f"*/{name}/skill.json"))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            errors = sorted(validator.iter_errors(manifest), key=lambda error: list(error.path))
            self.assertEqual(errors, [], f"{name}: {[error.message for error in errors]}")
            validated.append(name)
        self.assertEqual(len(validated), 39)

    def test_all_migrated_standalone_contracts_validate(self):
        validator = contract_validator()
        for name in REVIEWED_CORE_CONTRACTS:
            manifest_path = next(Path("catalog").glob(f"*/{name}/skill.json"))
            contract = json.loads(manifest_path.read_text(encoding="utf-8"))["contract"]
            errors = sorted(validator.iter_errors(contract), key=lambda error: list(error.path))
            self.assertEqual(errors, [], f"{name}: {[error.message for error in errors]}")

    def test_reviewed_core_contract_inputs_and_approvals_match_skill_workflows(self):
        self.assertEqual(len(REVIEWED_CORE_CONTRACTS), 39)
        for name, (required_context, approval_classes) in REVIEWED_CORE_CONTRACTS.items():
            manifest_path = next(Path("catalog").glob(f"*/{name}/skill.json"))
            contract = json.loads(manifest_path.read_text(encoding="utf-8"))["contract"]
            self.assertEqual(contract["requires_context"], required_context, name)
            self.assertEqual(contract["approval_classes"], approval_classes, name)

        publish_contract = json.loads(
            next(Path("catalog").glob("*/execution-publish-check/skill.json")).read_text(encoding="utf-8")
        )["contract"]
        self.assertEqual(publish_contract["approval_classes"], [])
        self.assertEqual(
            publish_contract["requires_context"],
            ["release_candidate", "release_criteria", "verification_evidence"],
        )

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
