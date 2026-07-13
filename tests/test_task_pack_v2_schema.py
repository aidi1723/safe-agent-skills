import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jsonschema import ValidationError
from jsonschema import validators
from jsonschema import Draft202012Validator

from onecode_skill_sanitizer.cli import main
from onecode_skill_sanitizer import task_packs
from onecode_skill_sanitizer.task_packs import load_trusted_skill_pack_items
from onecode_skill_sanitizer.validation import validate_contract
from onecode_skill_sanitizer.validation import validate_policy
from onecode_skill_sanitizer.validation import validate_source

from tests.registry_cli_helpers import validate_task_pack_v2


def _smart_payload(task: str, *extra: str) -> dict:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        exit_code = main(
            ["smart", task, *extra, "--schema-version", "2", "--format", "json"]
        )
    if exit_code != 0:
        raise AssertionError(out.getvalue())
    return json.loads(out.getvalue())


class TaskPackV2SchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._temporary_directory = tempfile.TemporaryDirectory()
        bundles_path = Path(cls._temporary_directory.name) / "blocked-bundles.json"
        bundles = json.loads(Path("bundles/index.json").read_text(encoding="utf-8"))
        website = copy.deepcopy(
            next(bundle for bundle in bundles["bundles"] if bundle["id"] == "website-build-launch")
        )
        website["execution_order"] = []
        bundles_path.write_text(
            json.dumps({"schema_version": 1, "bundle_count": 1, "bundles": [website]}),
            encoding="utf-8",
        )
        cls.payloads = {
            "complete": _smart_payload("build a landing page"),
            "incomplete": _smart_payload("help me with this"),
            "blocked": _smart_payload("build a landing page", "--bundles", str(bundles_path)),
        }
        cls.compound_payload = _smart_payload(
            "构建官网，同时审计 skill 路由器，验证通过后发布更新"
        )
        cls.invariant_ready_payload = _smart_payload(
            "build a landing page", "--invariants", "不能泄露密钥"
        )
        with patch.object(task_packs, "validate_task_pack_v2_semantics", return_value=None):
            cls.invariant_incomplete_payload = _smart_payload(
                "help me with this", "--invariants", "不能泄露密钥"
            )

    @classmethod
    def tearDownClass(cls):
        cls._temporary_directory.cleanup()

    def test_public_complete_incomplete_and_blocked_payloads_validate(self):
        self.assertEqual(
            [payload["routing_status"] for payload in self.payloads.values()],
            ["complete", "incomplete", "blocked"],
        )
        for status, payload in self.payloads.items():
            with self.subTest(status=status):
                validate_task_pack_v2(payload)

    def test_public_vague_incomplete_pack_preserves_invariant_safeguard(self):
        payload = _smart_payload(
            "help me with this", "--invariants", "不能泄露密钥"
        )
        self.assertEqual(payload["routing_status"], "incomplete")
        self.assertEqual(
            [skill["name"] for skill in payload["selected_skills"]],
            ["security-secret-context-redaction"],
        )
        self.assertEqual(
            payload["execution_graph"]["nodes"],
            [
                {
                    "host_action": False,
                    "id": "invariant:secret_redaction:security-secret-context-redaction",
                    "intent_ids": [],
                    "invariant_capability": "secret_redaction",
                    "scenario_ids": [],
                    "skill": "security-secret-context-redaction",
                    "stage": "review",
                }
            ],
        )
        validate_task_pack_v2(payload)

    def test_public_ready_pack_binds_invariant_capability_to_execution_node(self):
        payload = _smart_payload(
            "build a landing page", "--invariants", "不能泄露密钥"
        )
        capability = next(
            item
            for item in payload["capability_resolution"]["capabilities"]
            if item.get("source") == "invariant"
        )
        node = next(
            item
            for item in payload["execution_graph"]["nodes"]
            if "invariant_capability" in item
        )
        self.assertEqual(
            (node["id"], node["invariant_capability"], node["skill"], node["stage"]),
            (
                f"invariant:{capability['capability']}:{capability['skills'][0]}",
                capability["capability"],
                capability["skills"][0],
                capability["stage"],
            ),
        )
        validate_task_pack_v2(payload)

    def test_every_selected_skill_record_produced_from_the_catalog_validates(self):
        payload = copy.deepcopy(self.payloads["complete"])
        payload["selected_skills"] = load_trusted_skill_pack_items(Path("catalog"))

        try:
            validate_task_pack_v2(payload)
        except ValidationError as error:
            self.fail(f"produced selected skill failed schema validation: {error.message}")

    def test_patterned_identifiers_reject_trailing_and_interior_control_characters(self):
        mutations = {
            "route_id": lambda p, value: p.update(route_id=value(p["route_id"])),
            "intent_graph_id": lambda p, value: p["intent_graph"]["intents"][0].update(
                id=value(p["intent_graph"]["intents"][0]["id"])
            ),
            "intent_dependency_id": lambda p, value: p["intent_graph"]["intents"][0].update(
                depends_on=[value("i2")]
            ),
            "candidate_intent_id": lambda p, value: p["scenario_candidates"][0].update(
                intent_id=value(p["scenario_candidates"][0]["intent_id"])
            ),
            "candidate_scenario_id": lambda p, value: p["scenario_candidates"][0].update(
                scenario_id=value(p["scenario_candidates"][0]["scenario_id"])
            ),
            "selected_scenario_id": lambda p, value: p["selected_scenarios"][0].update(
                scenario_id=value(p["selected_scenarios"][0]["scenario_id"])
            ),
            "selected_scenario_intent_id": lambda p, value: p["selected_scenarios"][0].update(
                intent_ids=[value(p["selected_scenarios"][0]["intent_ids"][0])]
            ),
            "uncovered_intent_id": lambda p, value: p.update(uncovered_intents=[value("i1")]),
            "selected_skill_name": lambda p, value: p["selected_skills"][0].update(
                name=value(p["selected_skills"][0]["name"])
            ),
            "selected_skill_registry_path": lambda p, value: p["selected_skills"][0].update(
                registry_path=value(p["selected_skills"][0]["registry_path"])
            ),
            "selected_skill_sha256": lambda p, value: p["selected_skills"][0]["hashes"].update(
                source_sha256=value(p["selected_skills"][0]["hashes"]["source_sha256"])
            ),
            "taxonomy_subcategory": lambda p, value: p["selected_skills"][0]["taxonomy"].update(
                subcategory=value(p["selected_skills"][0]["taxonomy"]["subcategory"])
            ),
            "source_provenance": lambda p, value: p["selected_skills"][0]["source"].update(
                collected_by=value(p["selected_skills"][0]["source"]["collected_by"])
            ),
            "contract_capability": lambda p, value: p["selected_skills"][0]["contract"].update(
                capability_vector=[value(p["selected_skills"][0]["contract"]["capability_vector"][0])]
            ),
            "contract_artifact": lambda p, value: p["selected_skills"][0]["contract"].update(
                requires_context=[value(p["selected_skills"][0]["contract"]["requires_context"][0])]
            ),
            "capability_id": lambda p, value: p["capability_resolution"]["capabilities"][0].update(
                capability=value(p["capability_resolution"]["capabilities"][0]["capability"])
            ),
            "capability_scenario_id": lambda p, value: p["capability_resolution"][
                "capabilities"
            ][0].update(
                scenario_id=value(p["capability_resolution"]["capabilities"][0]["scenario_id"])
            ),
            "capability_skill_name": lambda p, value: p["capability_resolution"][
                "capabilities"
            ][0].update(skills=[value(p["capability_resolution"]["capabilities"][0]["skills"][0])]),
            "node_id": lambda p, value: p["execution_graph"]["nodes"][0].update(
                id=value(p["execution_graph"]["nodes"][0]["id"])
            ),
            "node_intent_id": lambda p, value: p["execution_graph"]["nodes"][0].update(
                intent_ids=[value(p["execution_graph"]["nodes"][0]["intent_ids"][0])]
            ),
            "node_scenario_id": lambda p, value: p["execution_graph"]["nodes"][0].update(
                scenario_ids=[value(p["execution_graph"]["nodes"][0]["scenario_ids"][0])]
            ),
            "node_skill_name": lambda p, value: p["execution_graph"]["nodes"][0].update(
                skill=value(p["execution_graph"]["nodes"][0]["skill"])
            ),
            "node_invariant_capability": lambda p, value: p["execution_graph"]["nodes"][0].update(
                invariant_capability=value("test_capability")
            ),
            "edge_from": lambda p, value: p["execution_graph"]["edges"][0].update(
                **{"from": value(p["execution_graph"]["edges"][0]["from"])}
            ),
            "edge_to": lambda p, value: p["execution_graph"]["edges"][0].update(
                to=value(p["execution_graph"]["edges"][0]["to"])
            ),
            "omitted_skill_name": lambda p, value: p["routing_metrics"].update(
                required_skills_omitted=[value(p["selected_skills"][0]["name"])]
            ),
            "registry_issue_id": lambda p, value: p["registry_verification"].update(
                issues=[
                    {
                        "id": value("unknown-provenance"),
                        "severity": "medium",
                        "skill": p["selected_skills"][0]["name"],
                        "path": "catalog/example/skill.json",
                    }
                ]
            ),
            "compatibility_scenario_id": lambda p, value: p["compatibility"][
                "compatibility_loss"
            ].update(scenarios_dropped=[value(p["selected_scenarios"][0]["scenario_id"])]),
        }
        corruptions = {
            "trailing_newline": lambda value: f"{value}\n",
            "interior_newline": lambda value: f"{value[:1]}\n{value[1:]}",
            "trailing_tab": lambda value: f"{value}\t",
            "interior_control": lambda value: f"{value[:1]}\x00{value[1:]}",
        }
        for field, mutate in mutations.items():
            for corruption, corrupt in corruptions.items():
                with self.subTest(field=field, corruption=corruption):
                    payload = copy.deepcopy(self.payloads["complete"])
                    mutate(payload, corrupt)
                    with self.assertRaises(ValidationError):
                        validate_task_pack_v2(payload)

    def test_selected_skill_contract_matches_authoritative_manifest_and_runtime_contracts(self):
        manifest_schema = json.loads(
            Path("schemas/skill-manifest.schema.json").read_text(encoding="utf-8")
        )
        strict_type_checker = Draft202012Validator.TYPE_CHECKER.redefine(
            "integer", lambda checker, value: isinstance(value, int) and not isinstance(value, bool)
        )
        strict_validator = validators.extend(
            Draft202012Validator, type_checker=strict_type_checker
        )(manifest_schema)
        base_manifest = json.loads(
            Path("catalog/business/business-requirements-brief/skill.json").read_text(
                encoding="utf-8"
            )
        )
        cases = [
            ({}, True),
            ({"schema_version": 1}, True),
            (
                {
                    "schema_version": 1,
                    "requires_context": ["task_brief"],
                    "produces_artifacts": ["result_artifact"],
                    "capability_vector": ["test.capability"],
                    "stage_hint": "planning",
                    "conflicts_with": ["other-skill"],
                    "excludes": [],
                    "requires_after": [],
                    "cost_weight": 1,
                },
                True,
            ),
            (copy.deepcopy(self.payloads["complete"]["selected_skills"][0]["contract"]), True),
            ({"schema_version": True}, False),
            ({"schema_version": 1, "stage_hint": "unknown"}, False),
            ({"schema_version": 1, "unexpected": True}, False),
        ]
        for contract, expected in cases:
            with self.subTest(contract=contract):
                payload = copy.deepcopy(self.payloads["complete"])
                payload["selected_skills"][0]["contract"] = contract
                try:
                    validate_task_pack_v2(payload)
                except ValidationError:
                    selected_valid = False
                else:
                    selected_valid = True

                manifest = copy.deepcopy(base_manifest)
                manifest["contract"] = contract
                manifest_valid = not list(strict_validator.iter_errors(manifest))
                runtime_issues = []
                validate_contract(
                    {"name": manifest["name"], "contract": contract},
                    Path("skill.json"),
                    runtime_issues,
                )
                self.assertEqual(selected_valid, expected)
                self.assertEqual(manifest_valid, expected)
                self.assertEqual(not runtime_issues, expected)

    def test_source_type_usage_pairs_match_manifest_schema_and_runtime(self):
        manifest_schema = json.loads(
            Path("schemas/skill-manifest.schema.json").read_text(encoding="utf-8")
        )
        manifest_validator = Draft202012Validator(manifest_schema)
        base_manifest = json.loads(
            Path("catalog/business/business-requirements-brief/skill.json").read_text(
                encoding="utf-8"
            )
        )
        pairs = [
            ("local_folder", "local_authoring", True),
            ("local_folder", "reference_only", False),
            ("github_reference", "reference_only", True),
            ("github_reference", "local_authoring", False),
            ("web_reference", "reference_only", True),
            ("web_reference", "source_import", False),
        ]
        for source_type, usage, expected in pairs:
            with self.subTest(source_type=source_type, usage=usage):
                source = copy.deepcopy(base_manifest["source"])
                source.update(type=source_type, usage=usage)
                payload = copy.deepcopy(self.payloads["complete"])
                payload["selected_skills"][0]["source"] = source
                try:
                    validate_task_pack_v2(payload)
                except ValidationError:
                    selected_valid = False
                else:
                    selected_valid = True

                manifest = copy.deepcopy(base_manifest)
                manifest["source"] = source
                manifest_valid = not list(manifest_validator.iter_errors(manifest))
                runtime_issues = []
                validate_source({"source": source}, Path("skill.json"), runtime_issues)
                self.assertEqual(selected_valid, expected)
                self.assertEqual(manifest_valid, expected)
                self.assertEqual(not runtime_issues, expected)

    def test_source_import_requires_complete_runtime_capture(self):
        source = copy.deepcopy(self.payloads["complete"]["selected_skills"][0]["source"])
        source.update(
            type="archive",
            usage="source_import",
            capture={
                "upstream_url": "https://example.test/archive.tar.gz",
                "upstream_ref_type": "release",
                "upstream_ref": "v1.0.0",
                "captured_at": "2026-07-12T00:00:00Z",
                "license_snapshot": "Apache-2.0",
                "upstream_sha256": "a" * 64,
                "content_path": "skills/example",
                "capture_method": "archive_download",
            },
        )
        payload = copy.deepcopy(self.payloads["complete"])
        payload["selected_skills"][0]["source"] = source
        try:
            validate_task_pack_v2(payload)
        except ValidationError as error:
            self.fail(f"valid source_import capture failed schema validation: {error.message}")
        runtime_issues = []
        validate_source({"source": source}, Path("skill.json"), runtime_issues)
        self.assertEqual(runtime_issues, [])

        capture_mutations = {
            "missing_sha256": lambda item: item.pop("upstream_sha256"),
            "newline_url": lambda item: item.update(upstream_url=f"{item['upstream_url']}\n"),
            "tab_reference": lambda item: item.update(upstream_ref=f"{item['upstream_ref']}\t"),
            "control_sha256": lambda item: item.update(upstream_sha256=f"{item['upstream_sha256']}\x00"),
        }
        for label, mutate in capture_mutations.items():
            with self.subTest(label=label):
                invalid_source = copy.deepcopy(source)
                mutate(invalid_source["capture"])
                payload["selected_skills"][0]["source"] = invalid_source
                with self.assertRaises(ValidationError):
                    validate_task_pack_v2(payload)

    def test_policy_string_items_match_runtime_for_empty_and_control_values(self):
        cases = [
            ("example.test", True),
            ("publication", True),
            ("", False),
            ("\n", False),
            ("\t", False),
            ("\x00", False),
            ("example\n.test", False),
            (True, False),
            (7, False),
            (None, False),
        ]
        for field in ("approved_hosts", "required_for"):
            for value, expected in cases:
                with self.subTest(field=field, value=value):
                    payload = copy.deepcopy(self.payloads["complete"])
                    policy = payload["selected_skills"][0]["policy"]
                    if field == "approved_hosts":
                        policy["network"][field] = [value]
                    else:
                        policy["approval"][field] = [value]
                    try:
                        validate_task_pack_v2(payload)
                    except ValidationError:
                        schema_valid = False
                    else:
                        schema_valid = True
                    issues = []
                    validate_policy({"policy": policy}, Path("skill.json"), issues)
                    self.assertEqual(schema_valid, expected)
                    self.assertEqual(not issues, expected)

    def test_provenance_strings_match_runtime_for_control_characters(self):
        base_source = copy.deepcopy(self.payloads["complete"]["selected_skills"][0]["source"])
        corruptions = ["", "\n", "\t", "\x00", "value\nwith-control", True, 7, None]
        fields = [
            "path",
            "url",
            "author",
            "license",
            "reference",
            "collected_by",
            "captured_at",
            "commit",
        ]
        for field in fields:
            for value in corruptions:
                with self.subTest(field=field, value=value):
                    source = copy.deepcopy(base_source)
                    source[field] = value
                    payload = copy.deepcopy(self.payloads["complete"])
                    payload["selected_skills"][0]["source"] = source
                    try:
                        validate_task_pack_v2(payload)
                    except ValidationError:
                        schema_valid = False
                    else:
                        schema_valid = True
                    issues = []
                    validate_source({"source": source}, Path("skill.json"), issues)
                    self.assertFalse(schema_valid)
                    self.assertTrue(issues)

    def test_source_import_capture_strings_match_runtime_for_control_characters(self):
        source = copy.deepcopy(self.payloads["complete"]["selected_skills"][0]["source"])
        source.update(
            type="archive",
            usage="source_import",
            capture={
                "upstream_url": "https://example.test/archive.tar.gz",
                "upstream_ref_type": "release",
                "upstream_ref": "v1.0.0",
                "captured_at": "2026-07-12T00:00:00Z",
                "license_snapshot": "Apache-2.0",
                "upstream_sha256": "a" * 64,
                "content_path": "skills/example",
                "capture_method": "archive_download",
            },
        )
        for field in source["capture"]:
            if field == "upstream_sha256":
                invalid_values = ["", "a" * 63, f"{'a' * 64}\n", f"{'a' * 32}\x00{'a' * 32}"]
            elif field == "upstream_ref_type":
                invalid_values = ["", "release\n", "release\t", "release\x00"]
            else:
                invalid_values = ["", "\n", "\t", "\x00", "value\nwith-control"]
            for value in invalid_values:
                with self.subTest(field=field, value=value):
                    invalid_source = copy.deepcopy(source)
                    invalid_source["capture"][field] = value
                    payload = copy.deepcopy(self.payloads["complete"])
                    payload["selected_skills"][0]["source"] = invalid_source
                    try:
                        validate_task_pack_v2(payload)
                    except ValidationError:
                        schema_valid = False
                    else:
                        schema_valid = True
                    issues = []
                    validate_source({"source": invalid_source}, Path("skill.json"), issues)
                    self.assertFalse(schema_valid)
                    self.assertTrue(issues)

    def test_source_import_url_runtime_matches_schema_whitespace_contract(self):
        source = copy.deepcopy(self.payloads["complete"]["selected_skills"][0]["source"])
        source.update(
            type="archive",
            usage="source_import",
            capture={
                "upstream_url": "https://example.test/archive%20name.tar.gz?ref=a%2Fb",
                "upstream_ref_type": "release",
                "upstream_ref": "v1.0.0",
                "captured_at": "2026-07-12T00:00:00Z",
                "license_snapshot": "Apache-2.0",
                "upstream_sha256": "a" * 64,
                "content_path": "skills/example",
                "capture_method": "archive_download",
            },
        )
        cases = [
            ("https://example.test/archive%20name.tar.gz?ref=a%2Fb", True),
            ("http://example.test/a", True),
            ("https://", False),
            ("ftp://example.test/a", False),
            ("https://example.test/a b", False),
            ("https://example.test/a\tb", False),
            ("https://example.test/a\nb", False),
            ("https://example.test/a\u00a0b", False),
            ("https://example.test/a\u2003b", False),
            ("https://example.test/a\u2028b", False),
        ]
        for upstream_url, expected in cases:
            with self.subTest(upstream_url=upstream_url):
                candidate = copy.deepcopy(source)
                candidate["capture"]["upstream_url"] = upstream_url
                payload = copy.deepcopy(self.payloads["complete"])
                payload["selected_skills"][0]["source"] = candidate
                try:
                    validate_task_pack_v2(payload)
                except ValidationError:
                    schema_valid = False
                else:
                    schema_valid = True
                issues = []
                validate_source({"source": candidate}, Path("skill.json"), issues)
                self.assertEqual(schema_valid, expected)
                self.assertEqual(not issues, expected)

    def test_semantic_validator_rejects_identity_and_reference_corruption(self):
        validator = getattr(task_packs, "validate_task_pack_v2_semantics", None)
        self.assertIsNotNone(validator)
        mutations = {
            "duplicate_skill_name": lambda p: p["selected_skills"].append(
                {**copy.deepcopy(p["selected_skills"][0]), "match_score": 1}
            ),
            "duplicate_candidate_identity": lambda p: p["scenario_candidates"].append(
                {**copy.deepcopy(p["scenario_candidates"][0]), "score": 0.5}
            ),
            "duplicate_intent_id": lambda p: p["intent_graph"]["intents"].append(
                {**copy.deepcopy(p["intent_graph"]["intents"][0]), "summary": "duplicate"}
            ),
            "duplicate_scenario_id": lambda p: p["selected_scenarios"].append(
                {**copy.deepcopy(p["selected_scenarios"][0]), "score": 0.5}
            ),
            "duplicate_node_id": lambda p: p["execution_graph"]["nodes"].append(
                {**copy.deepcopy(p["execution_graph"]["nodes"][0]), "stage": "review"}
            ),
            "duplicate_edge": lambda p: p["execution_graph"]["edges"].append(
                copy.deepcopy(p["execution_graph"]["edges"][0])
            ),
            "dangling_edge": lambda p: p["execution_graph"]["edges"].append(
                {
                    "from": "missing:node",
                    "to": p["execution_graph"]["nodes"][0]["id"],
                    "type": "scenario_order",
                }
            ),
            "unknown_candidate_intent": lambda p: p["scenario_candidates"][0].update(
                intent_id="i99"
            ),
            "unknown_selected_intent": lambda p: p["selected_scenarios"][0].update(
                intent_ids=["i99"]
            ),
            "unknown_uncovered_intent": lambda p: p.update(uncovered_intents=["i99"]),
            "unknown_node_intent": lambda p: p["execution_graph"]["nodes"][0].update(
                intent_ids=["i99"]
            ),
            "unknown_node_scenario": lambda p: p["execution_graph"]["nodes"][0].update(
                scenario_ids=["unknown-scenario"]
            ),
            "unknown_node_skill": lambda p: p["execution_graph"]["nodes"][0].update(
                skill="unknown-skill"
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                payload = copy.deepcopy(self.payloads["complete"])
                mutate(payload)
                with self.assertRaises(ValueError):
                    validator(payload)

    def test_semantic_validator_rejects_intent_cycles_and_unresolved_state_forgery(self):
        validator = task_packs.validate_task_pack_v2_semantics

        self_cycle = copy.deepcopy(self.payloads["complete"])
        self_cycle["intent_graph"]["intents"][0]["depends_on"] = ["i1"]

        dependency_cycle = copy.deepcopy(self.compound_payload)
        first_id, second_id = [
            intent["id"] for intent in dependency_cycle["intent_graph"]["intents"][:2]
        ]
        dependency_cycle["intent_graph"]["intents"][0]["depends_on"] = [second_id]
        dependency_cycle["intent_graph"]["intents"][1]["depends_on"] = [first_id]

        unresolved_complete = copy.deepcopy(self.payloads["complete"])
        unresolved_complete["intent_graph"]["unresolved_dependencies"] = ["missing target"]

        unresolved_incomplete = copy.deepcopy(self.payloads["incomplete"])
        unresolved_incomplete["intent_graph"]["unresolved_dependencies"] = ["missing target"]

        unresolved_wrong_block = copy.deepcopy(self.payloads["blocked"])
        unresolved_wrong_block["intent_graph"]["unresolved_dependencies"] = ["missing target"]

        unresolved_valid_block = copy.deepcopy(unresolved_wrong_block)
        unresolved_valid_block["execution_graph"]["reason_codes"] = ["invalid_intent_graph"]

        for label, payload in {
            "self_cycle": self_cycle,
            "dependency_cycle": dependency_cycle,
            "unresolved_complete": unresolved_complete,
            "unresolved_incomplete": unresolved_incomplete,
            "unresolved_wrong_block": unresolved_wrong_block,
        }.items():
            with self.subTest(label=label), self.assertRaises(ValueError):
                validator(payload)
        validator(unresolved_valid_block)

    def test_semantic_validator_derives_graph_topology_and_node_intent_mapping(self):
        validator = task_packs.validate_task_pack_v2_semantics

        complete_cycle = copy.deepcopy(self.payloads["complete"])
        complete_cycle["execution_graph"]["edges"].append(
            {
                "from": complete_cycle["execution_graph"]["nodes"][-1]["id"],
                "to": complete_cycle["execution_graph"]["nodes"][0]["id"],
                "type": "scenario_order",
            }
        )

        complete_self_edge = copy.deepcopy(self.payloads["complete"])
        complete_self_edge["execution_graph"]["edges"].append(
            {
                "from": complete_self_edge["execution_graph"]["nodes"][0]["id"],
                "to": complete_self_edge["execution_graph"]["nodes"][0]["id"],
                "type": "scenario_order",
            }
        )

        empty_node_intents = copy.deepcopy(self.payloads["complete"])
        empty_node_intents["execution_graph"]["nodes"][0]["intent_ids"] = []

        mismatched_mapping = copy.deepcopy(self.compound_payload)
        selected_by_intent = {
            intent_id: selection["scenario_id"]
            for selection in mismatched_mapping["selected_scenarios"]
            for intent_id in selection["intent_ids"]
        }
        node = next(
            item
            for item in mismatched_mapping["execution_graph"]["nodes"]
            if "invariant_capability" not in item
        )
        wrong_intent = next(
            intent_id
            for intent_id, scenario_id in selected_by_intent.items()
            if scenario_id != node["scenario_ids"][0]
        )
        node["intent_ids"] = [wrong_intent]

        incomplete_true_flag = copy.deepcopy(self.payloads["incomplete"])
        incomplete_true_flag["execution_graph"]["acyclic"] = True

        blocked_true_flag = copy.deepcopy(self.payloads["blocked"])
        blocked_true_flag["execution_graph"]["acyclic"] = True

        for label, payload in {
            "complete_cycle": complete_cycle,
            "complete_self_edge": complete_self_edge,
            "empty_node_intents": empty_node_intents,
            "mismatched_mapping": mismatched_mapping,
            "incomplete_true_flag": incomplete_true_flag,
            "blocked_true_flag": blocked_true_flag,
        }.items():
            with self.subTest(label=label), self.assertRaises(ValueError):
                validator(payload)

    def test_semantic_validator_limits_empty_intent_mapping_to_invariant_only_fallback(self):
        validator = task_packs.validate_task_pack_v2_semantics
        valid_fallback = copy.deepcopy(self.invariant_incomplete_payload)
        validator(valid_fallback)

        ready_forgery = copy.deepcopy(self.payloads["complete"])
        ready_node = ready_forgery["execution_graph"]["nodes"][0]
        ready_node.update(
            intent_ids=[], scenario_ids=[], invariant_capability="secret_redaction"
        )

        normal_node_empty = copy.deepcopy(self.payloads["complete"])
        normal_node_empty["execution_graph"]["nodes"][0]["intent_ids"] = []

        incomplete_with_standard_mappings = copy.deepcopy(self.payloads["complete"])
        incomplete_with_standard_mappings["routing_status"] = "incomplete"
        incomplete_with_standard_mappings["routing_metrics"]["decomposition"][
            "reason_codes"
        ] = ["task_scan_limit_exceeded"]
        invariant_node = incomplete_with_standard_mappings["execution_graph"]["nodes"][0]
        invariant_node.update(
            intent_ids=[], scenario_ids=[], invariant_capability="secret_redaction"
        )

        for label, payload in {
            "ready_forgery": ready_forgery,
            "normal_node_empty": normal_node_empty,
            "incomplete_with_standard_mappings": incomplete_with_standard_mappings,
        }.items():
            with self.subTest(label=label), self.assertRaises(ValueError):
                validator(payload)

    def test_semantic_validator_binds_invariant_capabilities_to_exact_nodes(self):
        validator = task_packs.validate_task_pack_v2_semantics

        def invariant_parts(payload):
            capability = next(
                item
                for item in payload["capability_resolution"]["capabilities"]
                if item.get("source") == "invariant"
            )
            node = next(
                item
                for item in payload["execution_graph"]["nodes"]
                if "invariant_capability" in item
            )
            return capability, node

        def remove_expected_record(payload):
            capability, _ = invariant_parts(payload)
            capability.pop("source")

        def drift_capability(payload):
            _, node = invariant_parts(payload)
            node["invariant_capability"] = "forged_capability"

        def drift_stage(payload):
            _, node = invariant_parts(payload)
            node["stage"] = "handoff"

        def drift_identifier(payload):
            _, node = invariant_parts(payload)
            original_id = node["id"]
            node["id"] = f"{original_id}:forged"
            for edge in payload["execution_graph"]["edges"]:
                if edge["from"] == original_id:
                    edge["from"] = node["id"]
                if edge["to"] == original_id:
                    edge["to"] = node["id"]

        def duplicate_node(payload):
            _, node = invariant_parts(payload)
            duplicate = copy.deepcopy(node)
            duplicate["id"] = f"{node['id']}:duplicate"
            payload["execution_graph"]["nodes"].append(duplicate)

        def drift_skill(payload):
            capability, node = invariant_parts(payload)
            forged_name = "security-secret-context-redaction-alt"
            forged_skill = copy.deepcopy(payload["selected_skills"][0])
            forged_skill["name"] = forged_name
            payload["selected_skills"].append(forged_skill)
            capability["skills"] = [forged_name]
            forged_node = copy.deepcopy(node)
            forged_node["id"] = f"invariant:{capability['capability']}:{forged_name}"
            forged_node["skill"] = forged_name
            payload["execution_graph"]["nodes"].append(forged_node)
            payload["routing_metrics"]["required_skill_count"] += 1
            payload["routing_metrics"]["selected_skill_count"] += 1

        mutations = {
            "missing_expected_record": remove_expected_record,
            "capability_drift": drift_capability,
            "stage_drift": drift_stage,
            "identifier_drift": drift_identifier,
            "duplicate_extra": duplicate_node,
            "skill_drift": drift_skill,
        }
        for state, baseline in {
            "ready": self.invariant_ready_payload,
            "fallback": self.invariant_incomplete_payload,
        }.items():
            for label, mutate in mutations.items():
                with self.subTest(state=state, label=label):
                    payload = copy.deepcopy(baseline)
                    mutate(payload)
                    with self.assertRaises(ValueError):
                        validator(payload)

    def test_semantic_validator_binds_node_host_actions_to_selected_skill_contracts(self):
        validator = task_packs.validate_task_pack_v2_semantics
        ready_browser_invariant = _smart_payload(
            "build a landing page", "--invariants", "必须使用浏览器自动化"
        )
        fallback_browser_invariant = _smart_payload(
            "help me with this", "--invariants", "必须使用浏览器自动化"
        )

        def forge_host_action(baseline, *, approval_class, invariant, value):
            payload = copy.deepcopy(baseline)
            skills = {item["name"]: item for item in payload["selected_skills"]}
            node = next(
                item
                for item in payload["execution_graph"]["nodes"]
                if ("invariant_capability" in item) is invariant
                and (
                    approval_class is None
                    and not item["host_action"]
                    or approval_class
                    in skills[item["skill"]].get("contract", {}).get("approval_classes", [])
                )
            )
            node["host_action"] = value
            return payload

        mutations = {
            "ordinary_shell_true_to_false": forge_host_action(
                self.payloads["complete"],
                approval_class="shell_execution",
                invariant=False,
                value=False,
            ),
            "ordinary_browser_true_to_false": forge_host_action(
                self.payloads["complete"],
                approval_class="browser_automation",
                invariant=False,
                value=False,
            ),
            "ordinary_no_approval_false_to_true": forge_host_action(
                self.payloads["complete"],
                approval_class=None,
                invariant=False,
                value=True,
            ),
            "ready_invariant_browser_true_to_false": forge_host_action(
                ready_browser_invariant,
                approval_class="browser_automation",
                invariant=True,
                value=False,
            ),
            "fallback_invariant_browser_true_to_false": forge_host_action(
                fallback_browser_invariant,
                approval_class="browser_automation",
                invariant=True,
                value=False,
            ),
            "ready_invariant_no_approval_false_to_true": forge_host_action(
                self.invariant_ready_payload,
                approval_class=None,
                invariant=True,
                value=True,
            ),
            "fallback_invariant_no_approval_false_to_true": forge_host_action(
                self.invariant_incomplete_payload,
                approval_class=None,
                invariant=True,
                value=True,
            ),
        }
        for label, payload in mutations.items():
            with self.subTest(label=label), self.assertRaises(ValueError):
                validator(payload)

    def test_semantic_validator_requires_each_graph_node_skill_to_be_selected(self):
        payload = copy.deepcopy(self.payloads["complete"])
        omitted_name = "execution-browser-use-web-task"
        self.assertNotIn(
            omitted_name,
            {
                skill_name
                for capability in payload["capability_resolution"]["capabilities"]
                for skill_name in capability["skills"]
            },
        )
        payload["selected_skills"] = [
            skill for skill in payload["selected_skills"] if skill["name"] != omitted_name
        ]
        payload["routing_metrics"]["selected_skill_count"] -= 1
        payload["routing_metrics"]["required_skills_omitted"] = [omitted_name]

        with self.assertRaises(ValueError):
            task_packs.validate_task_pack_v2_semantics(payload)

    def test_semantic_validator_bounds_malformed_host_action_contract_types(self):
        validator = task_packs.validate_task_pack_v2_semantics

        def malformed_contract(value):
            payload = copy.deepcopy(self.payloads["complete"])
            skill = next(item for item in payload["selected_skills"] if "contract" in item)
            skill["contract"] = value
            for node in payload["execution_graph"]["nodes"]:
                if node["skill"] == skill["name"]:
                    node["host_action"] = False
            return payload

        def malformed_approvals(value):
            payload = copy.deepcopy(self.payloads["complete"])
            skill = next(item for item in payload["selected_skills"] if "contract" in item)
            skill["contract"]["approval_classes"] = value
            for node in payload["execution_graph"]["nodes"]:
                if node["skill"] == skill["name"]:
                    node["host_action"] = bool(value)
            return payload

        def malformed_node_host_action(value):
            payload = copy.deepcopy(self.payloads["complete"])
            payload["execution_graph"]["nodes"][0]["host_action"] = value
            return payload

        mutations = {
            "null_contract": malformed_contract(None),
            "list_contract": malformed_contract([]),
            "null_approval_classes": malformed_approvals(None),
            "object_approval_classes": malformed_approvals({}),
            "string_approval_classes": malformed_approvals("shell_execution"),
            "boolean_approval_class": malformed_approvals([True]),
            "null_host_action": malformed_node_host_action(None),
            "string_host_action": malformed_node_host_action("false"),
        }
        for label, payload in mutations.items():
            with self.subTest(label=label), self.assertRaises(ValueError):
                validator(payload)

    def test_semantic_validator_rejects_every_derivable_count_mismatch(self):
        validator = getattr(task_packs, "validate_task_pack_v2_semantics", None)
        self.assertIsNotNone(validator)
        paths = [
            ("routing_metrics.intent_count", ("routing_metrics", "intent_count")),
            ("routing_metrics.candidate_count", ("routing_metrics", "candidate_count")),
            (
                "routing_metrics.selected_scenario_count",
                ("routing_metrics", "selected_scenario_count"),
            ),
            (
                "routing_metrics.required_skill_count",
                ("routing_metrics", "required_skill_count"),
            ),
            (
                "routing_metrics.selected_skill_count",
                ("routing_metrics", "selected_skill_count"),
            ),
            (
                "routing_metrics.optional_skills_selected",
                ("routing_metrics", "optional_skills_selected"),
            ),
            (
                "capability_resolution.missing_required_count",
                ("capability_resolution", "missing_required_count"),
            ),
            (
                "decomposition.emitted_intent_count",
                ("routing_metrics", "decomposition", "emitted_intent_count"),
            ),
            (
                "registry_verification.tampered_count",
                ("registry_verification", "tampered_count"),
            ),
            (
                "registry_verification.unknown_provenance_count",
                ("registry_verification", "unknown_provenance_count"),
            ),
            (
                "compatibility.cross_scenario_edges_dropped",
                ("compatibility", "compatibility_loss", "cross_scenario_edges_dropped"),
            ),
        ]
        for label, path in paths:
            for delta in (-1, 1):
                with self.subTest(label=label, delta=delta):
                    payload = copy.deepcopy(self.payloads["complete"])
                    owner = payload
                    for component in path[:-1]:
                        owner = owner[component]
                    owner[path[-1]] = owner[path[-1]] + delta
                    with self.assertRaises(ValueError):
                        validator(payload)

    def test_semantic_validator_rejects_derived_lists_and_status_mismatches(self):
        validator = getattr(task_packs, "validate_task_pack_v2_semantics", None)
        self.assertIsNotNone(validator)
        mutations = {
            "required_skills_omitted": lambda p: p["routing_metrics"].update(
                required_skills_omitted=[p["selected_skills"][0]["name"]]
            ),
            "compatibility_multi_intent": lambda p: p["compatibility"][
                "compatibility_loss"
            ].update(multi_intent_dropped=True),
            "compatibility_scenarios": lambda p: p["compatibility"][
                "compatibility_loss"
            ].update(scenarios_dropped=[p["selected_scenarios"][0]["scenario_id"]]),
            "capability_status": lambda p: p["capability_resolution"].update(
                status="incomplete"
            ),
            "registry_status": lambda p: p["registry_verification"].update(status="failed"),
            "registry_trusted_above_total": lambda p: p["registry_verification"].update(
                trusted_count=p["registry_verification"]["skill_count"] + 1
            ),
            "routing_status": lambda p: p.update(routing_status="incomplete"),
            "decomposition_flag": lambda p: p["routing_metrics"]["decomposition"].update(
                intent_limit_exceeded=True
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                payload = copy.deepcopy(self.payloads["complete"])
                mutate(payload)
                with self.assertRaises(ValueError):
                    validator(payload)

    def test_semantic_validator_is_total_for_arbitrary_json_like_input(self):
        validator = getattr(task_packs, "validate_task_pack_v2_semantics", None)
        self.assertIsNotNone(validator)
        malformed = [None, [], "payload", 7, True, {}, {"routing_metrics": []}]
        for payload in malformed:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                validator(payload)

    def test_semantic_validator_fails_closed_for_malformed_nested_types(self):
        validator = getattr(task_packs, "validate_task_pack_v2_semantics", None)
        self.assertIsNotNone(validator)
        mutations = {
            "intents": lambda p: p["intent_graph"].update(intents="intents"),
            "dependencies": lambda p: p["intent_graph"]["intents"][0].update(depends_on={}),
            "candidates": lambda p: p.update(scenario_candidates={}),
            "selections": lambda p: p.update(selected_scenarios=None),
            "uncovered": lambda p: p.update(uncovered_intents={}),
            "skills": lambda p: p.update(selected_skills=[True]),
            "capabilities": lambda p: p["capability_resolution"].update(capabilities={}),
            "nodes": lambda p: p["execution_graph"].update(nodes="nodes"),
            "edges": lambda p: p["execution_graph"].update(edges=[True]),
            "reason_codes": lambda p: p["execution_graph"].update(reason_codes={}),
            "metrics": lambda p: p.update(routing_metrics=[]),
            "optional_limit": lambda p: p["routing_metrics"].update(optional_skill_limit=True),
            "decomposition": lambda p: p["routing_metrics"].update(decomposition=[]),
            "observed_count": lambda p: p["routing_metrics"]["decomposition"].update(
                observed_candidate_count=True
            ),
            "registry_issues": lambda p: p["registry_verification"].update(issues=[True]),
            "registry_skill_count": lambda p: p["registry_verification"].update(skill_count=True),
            "compatibility": lambda p: p.update(compatibility=[]),
            "compatibility_loss": lambda p: p["compatibility"].update(compatibility_loss=[]),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                payload = copy.deepcopy(self.payloads["complete"])
                mutate(payload)
                with self.assertRaises(ValueError):
                    validator(payload)

    def test_public_cli_bounds_semantic_validation_failure(self):
        out = io.StringIO()
        with patch.object(
            task_packs,
            "validate_task_pack_v2_semantics",
            side_effect=ValueError("sensitive semantic detail"),
            create=True,
        ):
            with contextlib.redirect_stdout(out):
                exit_code = main(
                    ["smart", "build a landing page", "--schema-version", "2", "--format", "json"]
                )
        result = json.loads(out.getvalue())
        self.assertEqual(exit_code, 2)
        self.assertEqual(result["error"]["code"], "invalid_input")
        self.assertNotIn("sensitive semantic detail", json.dumps(result))

    def test_cross_field_state_contradictions_are_rejected(self):
        complete_mutations = {
            "complete_capability_positive_count": lambda p: p["capability_resolution"].update(
                missing_required_count=1
            ),
            "complete_capability_missing_entry": lambda p: p["capability_resolution"][
                "capabilities"
            ][0].update(status="missing", skills=[]),
            "covered_capability_without_skill": lambda p: p["capability_resolution"][
                "capabilities"
            ][0].update(skills=[]),
            "missing_capability_with_skill": lambda p: p["capability_resolution"][
                "capabilities"
            ][0].update(status="missing"),
            "ready_graph_not_acyclic": lambda p: p["execution_graph"].update(acyclic=False),
            "ready_graph_with_reason": lambda p: p["execution_graph"].update(
                reason_codes=["dependency_cycle"]
            ),
            "ready_graph_without_nodes": lambda p: p["execution_graph"].update(nodes=[], edges=[]),
            "complete_route_uncovered": lambda p: p.update(uncovered_intents=["i1"]),
            "complete_route_incomplete_capabilities": lambda p: p["capability_resolution"].update(
                status="incomplete", missing_required_count=1
            ),
            "complete_route_blocked_graph": lambda p: p["execution_graph"].update(
                status="blocked", acyclic=False, reason_codes=["dependency_cycle"]
            ),
            "complete_route_incomplete_decomposition": lambda p: p["routing_metrics"][
                "decomposition"
            ].update(intent_limit_exceeded=True, reason_codes=["intent_limit_exceeded"]),
            "incomplete_without_incomplete_cause": lambda p: p.update(routing_status="incomplete"),
            "blocked_route_ready_graph": lambda p: p.update(routing_status="blocked"),
        }
        for label, mutate in complete_mutations.items():
            with self.subTest(label=label):
                payload = copy.deepcopy(self.payloads["complete"])
                mutate(payload)
                with self.assertRaises(ValidationError):
                    validate_task_pack_v2(payload)

        blocked_mutations = {
            "incomplete_capability_zero_count": lambda p: p["capability_resolution"].update(
                missing_required_count=0
            ),
            "incomplete_capability_without_missing": lambda p: p["capability_resolution"].update(
                capabilities=[]
            ),
            "blocked_graph_acyclic": lambda p: p["execution_graph"].update(acyclic=True),
            "blocked_graph_without_reason": lambda p: p["execution_graph"].update(reason_codes=[]),
        }
        for label, mutate in blocked_mutations.items():
            with self.subTest(label=label):
                payload = copy.deepcopy(self.payloads["blocked"])
                mutate(payload)
                with self.assertRaises(ValidationError):
                    validate_task_pack_v2(payload)

    def test_repeated_records_and_counts_above_hard_producer_limits_are_rejected(self):
        duplicate_mutations = {
            "scenario_candidates": lambda p: p["scenario_candidates"].append(
                copy.deepcopy(p["scenario_candidates"][0])
            ),
            "selected_scenarios": lambda p: p["selected_scenarios"].append(
                copy.deepcopy(p["selected_scenarios"][0])
            ),
            "selected_skills": lambda p: p["selected_skills"].append(
                copy.deepcopy(p["selected_skills"][0])
            ),
            "capabilities": lambda p: p["capability_resolution"]["capabilities"].append(
                copy.deepcopy(p["capability_resolution"]["capabilities"][0])
            ),
            "nodes": lambda p: p["execution_graph"]["nodes"].append(
                copy.deepcopy(p["execution_graph"]["nodes"][0])
            ),
            "edges": lambda p: p["execution_graph"]["edges"].append(
                copy.deepcopy(p["execution_graph"]["edges"][0])
            ),
        }
        for label, mutate in duplicate_mutations.items():
            with self.subTest(label=label):
                payload = copy.deepcopy(self.payloads["complete"])
                mutate(payload)
                with self.assertRaises(ValidationError):
                    validate_task_pack_v2(payload)

        count_mutations = {
            "intent_count": lambda p: p["routing_metrics"].update(intent_count=999),
            "candidate_count": lambda p: p["routing_metrics"].update(candidate_count=999),
            "selected_scenario_count": lambda p: p["routing_metrics"].update(
                selected_scenario_count=999
            ),
            "observed_candidate_count": lambda p: p["routing_metrics"]["decomposition"].update(
                observed_candidate_count=999
            ),
            "emitted_intent_count": lambda p: p["routing_metrics"]["decomposition"].update(
                emitted_intent_count=999
            ),
        }
        for label, mutate in count_mutations.items():
            with self.subTest(label=label):
                payload = copy.deepcopy(self.payloads["complete"])
                mutate(payload)
                with self.assertRaises(ValidationError):
                    validate_task_pack_v2(payload)

    def test_user_controlled_optional_skill_limit_is_not_given_a_false_schema_bound(self):
        payload = _smart_payload("build a landing page", "--max-skills", "999")

        self.assertEqual(payload["routing_metrics"]["optional_skill_limit"], 999)
        validate_task_pack_v2(payload)

    def test_unknown_fields_are_rejected_throughout_nested_records(self):
        mutations = {
            "scenario_candidate": lambda p: p["scenario_candidates"][0].update(extra=True),
            "selected_scenario": lambda p: p["selected_scenarios"][0].update(extra=True),
            "score_breakdown": lambda p: p["selected_scenarios"][0]["score_breakdown"].update(extra=True),
            "selected_skill": lambda p: p["selected_skills"][0].update(extra=True),
            "selected_skill_hashes": lambda p: p["selected_skills"][0]["hashes"].update(extra=True),
            "selected_skill_taxonomy": lambda p: p["selected_skills"][0]["taxonomy"].update(extra=True),
            "selected_skill_source": lambda p: p["selected_skills"][0]["source"].update(extra=True),
            "selected_skill_policy": lambda p: p["selected_skills"][0]["policy"].update(extra=True),
            "selected_skill_contract": lambda p: p["selected_skills"][0]["contract"].update(extra=True),
            "capability_resolution": lambda p: p["capability_resolution"].update(extra=True),
            "capability": lambda p: p["capability_resolution"]["capabilities"][0].update(extra=True),
            "execution_graph": lambda p: p["execution_graph"].update(extra=True),
            "execution_node": lambda p: p["execution_graph"]["nodes"][0].update(extra=True),
            "execution_edge": lambda p: p["execution_graph"]["edges"][0].update(extra=True),
            "routing_metrics": lambda p: p["routing_metrics"].update(extra=True),
            "decomposition": lambda p: p["routing_metrics"]["decomposition"].update(extra=True),
            "registry_verification": lambda p: p["registry_verification"].update(extra=True),
            "compatibility": lambda p: p["compatibility"].update(extra=True),
            "compatibility_loss": lambda p: p["compatibility"]["compatibility_loss"].update(extra=True),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                payload = copy.deepcopy(self.payloads["complete"])
                mutate(payload)
                with self.assertRaises(ValidationError):
                    validate_task_pack_v2(payload)

    def test_missing_nested_required_fields_are_rejected(self):
        mutations = {
            "candidate_intent_id": lambda p: p["scenario_candidates"][0].pop("intent_id"),
            "score_breakdown": lambda p: p["selected_scenarios"][0].pop("score_breakdown"),
            "skill_description": lambda p: p["selected_skills"][0].pop("description"),
            "capabilities": lambda p: p["capability_resolution"].pop("capabilities"),
            "capability_status": lambda p: p["capability_resolution"]["capabilities"][0].pop("status"),
            "graph_edges": lambda p: p["execution_graph"].pop("edges"),
            "node_host_action": lambda p: p["execution_graph"]["nodes"][0].pop("host_action"),
            "edge_type": lambda p: p["execution_graph"]["edges"][0].pop("type"),
            "decomposition_mode": lambda p: p["routing_metrics"]["decomposition"].pop("mode"),
            "verification_status": lambda p: p["registry_verification"].pop("status"),
            "compatibility_loss": lambda p: p["compatibility"].pop("compatibility_loss"),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                payload = copy.deepcopy(self.payloads["complete"])
                mutate(payload)
                with self.assertRaises(ValidationError):
                    validate_task_pack_v2(payload)

    def test_invalid_enums_and_ids_are_rejected(self):
        mutations = {
            "candidate_intent_id": lambda p: p["scenario_candidates"][0].update(intent_id="intent-1"),
            "candidate_scenario_id": lambda p: p["scenario_candidates"][0].update(scenario_id="Bad ID"),
            "skill_name": lambda p: p["selected_skills"][0].update(name="Bad Skill"),
            "skill_risk": lambda p: p["selected_skills"][0].update(risk_level="unknown"),
            "capability_status": lambda p: p["capability_resolution"]["capabilities"][0].update(status="unknown"),
            "graph_status": lambda p: p["execution_graph"].update(status="complete"),
            "node_id": lambda p: p["execution_graph"]["nodes"][0].update(id="node 1"),
            "node_stage": lambda p: p["execution_graph"]["nodes"][0].update(stage="deploy"),
            "edge_type": lambda p: p["execution_graph"]["edges"][0].update(type="unknown"),
            "decomposition_mode": lambda p: p["routing_metrics"]["decomposition"].update(mode="unknown"),
            "decomposition_reason": lambda p: p["routing_metrics"]["decomposition"].update(reason_codes=["unknown"]),
            "overlap_policy": lambda p: p["routing_metrics"].update(overlap_policy="ignored"),
            "verification_status": lambda p: p["registry_verification"].update(status="trusted"),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                payload = copy.deepcopy(self.payloads["complete"])
                mutate(payload)
                with self.assertRaises(ValidationError):
                    validate_task_pack_v2(payload)

    def test_boolean_values_do_not_satisfy_integer_fields(self):
        mutations = {
            "candidate_score": lambda p: p["scenario_candidates"][0].update(deterministic_score=True),
            "selected_score": lambda p: p["selected_scenarios"][0]["score_breakdown"].update(deterministic_score=True),
            "skill_match_score": lambda p: p["selected_skills"][0].update(match_score=True),
            "contract_schema_version": lambda p: p["selected_skills"][0]["contract"].update(schema_version=True),
            "missing_required_count": lambda p: p["capability_resolution"].update(missing_required_count=True),
            "graph_schema_version": lambda p: p["execution_graph"].update(schema_version=True),
            "metric_count": lambda p: p["routing_metrics"].update(intent_count=True),
            "decomposition_count": lambda p: p["routing_metrics"]["decomposition"].update(emitted_intent_count=True),
            "verification_count": lambda p: p["registry_verification"].update(skill_count=True),
            "legacy_version": lambda p: p["compatibility"].update(legacy_schema_version=True),
            "dropped_edge_count": lambda p: p["compatibility"]["compatibility_loss"].update(cross_scenario_edges_dropped=True),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                payload = copy.deepcopy(self.payloads["complete"])
                mutate(payload)
                with self.assertRaises(ValidationError):
                    validate_task_pack_v2(payload)

    def test_malformed_nested_arrays_and_objects_are_rejected(self):
        mutations = {
            "scenario_candidates": lambda p: p.update(scenario_candidates={}),
            "selected_skills": lambda p: p.update(selected_skills={}),
            "capability_resolution": lambda p: p.update(capability_resolution=[]),
            "capabilities": lambda p: p["capability_resolution"].update(capabilities={}),
            "capability_skills": lambda p: p["capability_resolution"]["capabilities"][0].update(skills={}),
            "execution_graph": lambda p: p.update(execution_graph=[]),
            "graph_nodes": lambda p: p["execution_graph"].update(nodes={}),
            "node_intent_ids": lambda p: p["execution_graph"]["nodes"][0].update(intent_ids={}),
            "graph_edges": lambda p: p["execution_graph"].update(edges={}),
            "reason_codes": lambda p: p["execution_graph"].update(reason_codes={}),
            "routing_metrics": lambda p: p.update(routing_metrics=[]),
            "decomposition": lambda p: p["routing_metrics"].update(decomposition=[]),
            "required_skills_omitted": lambda p: p["routing_metrics"].update(required_skills_omitted={}),
            "registry_verification": lambda p: p.update(registry_verification=[]),
            "verification_issues": lambda p: p["registry_verification"].update(issues={}),
            "compatibility": lambda p: p.update(compatibility=[]),
            "scenarios_dropped": lambda p: p["compatibility"]["compatibility_loss"].update(scenarios_dropped={}),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                payload = copy.deepcopy(self.payloads["complete"])
                mutate(payload)
                with self.assertRaises(ValidationError):
                    validate_task_pack_v2(payload)


if __name__ == "__main__":
    unittest.main()
