import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import ValidationError

from onecode_skill_sanitizer.cli import main
from onecode_skill_sanitizer.task_packs import load_trusted_skill_pack_items

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

    def test_every_selected_skill_record_produced_from_the_catalog_validates(self):
        payload = copy.deepcopy(self.payloads["complete"])
        payload["selected_skills"] = load_trusted_skill_pack_items(Path("catalog"))

        try:
            validate_task_pack_v2(payload)
        except ValidationError as error:
            self.fail(f"produced selected skill failed schema validation: {error.message}")

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
