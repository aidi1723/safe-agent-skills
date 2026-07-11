from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVAL_PATH = ROOT / "evals" / "multi-intent-gold.json"
EXPECTED_CATEGORIES = {
    "compound": 40,
    "sequential": 20,
    "vague_context": 15,
    "negative": 10,
    "multilingual_typo_paraphrase": 10,
    "safety_sensitive": 5,
}
EXPECTED_LABELING = {
    "method": "manual_review",
    "reviewer_role": "independent_dataset_review",
    "generated_from_router": False,
    "reviewed_at": "2026-07-10",
}
VALID_STATUS_GRAPH_PAIRS = [
    ("complete", "ready", True),
    ("incomplete", "blocked", True),
    ("blocked", "blocked", True),
]


def bundle_scenario_ids() -> set[str]:
    bundles = json.loads((ROOT / "bundles" / "index.json").read_text(encoding="utf-8"))["bundles"]
    return {bundle["id"] for bundle in bundles}


def gold_payload() -> dict:
    return json.loads(EVAL_PATH.read_text(encoding="utf-8"))


def write_payload(temp_dir: str, payload: dict) -> Path:
    path = Path(temp_dir) / "dataset.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def synthetic_route(
    intent_types: list[str],
    scenarios: list[str],
    dependency_pairs: list[tuple[str, str]] | None = None,
    *,
    graph_status: str = "ready",
    acyclic: bool = True,
    routing_status: str = "complete",
    reason_codes: list[str] | None = None,
    intent_dependencies: list[list[str]] | None = None,
    intent_confidences: list[float] | None = None,
    selected_skills: list[str] | None = None,
    capability_resolution: list[dict] | None = None,
) -> dict:
    intents = [
        {
            "id": f"i{index}",
            "task_type": task_type,
            "depends_on": (intent_dependencies or [[] for _ in intent_types])[index - 1],
            "confidence": (intent_confidences or [0.5 for _ in intent_types])[index - 1],
        }
        for index, task_type in enumerate(intent_types, start=1)
    ]
    nodes = [
        {
            "id": f"node-{index}",
            "intent_ids": [intent["id"]],
            "skill": f"skill-{index}",
        }
        for index, intent in enumerate(intents, start=1)
    ]
    node_by_type = {intent["task_type"]: nodes[index] for index, intent in enumerate(intents)}
    edges = []
    for source_type, target_type in dependency_pairs or []:
        edges.append(
            {
                "from": node_by_type[source_type]["id"],
                "to": node_by_type[target_type]["id"],
                "type": "intent_completion_dependency",
            }
        )
    return {
        "routing_status": routing_status,
        "intent_graph": {"intents": intents},
        "selected_scenarios": [{"scenario_id": scenario_id, "intent_ids": []} for scenario_id in scenarios],
        "selected_skills": [{"name": name} for name in selected_skills or []],
        "capability_resolution": {
            "status": "complete",
            "capabilities": capability_resolution or [],
            "missing_required_count": 0,
        },
        "execution_graph": {
            "status": graph_status,
            "acyclic": acyclic,
            "nodes": nodes,
            "edges": edges,
            "reason_codes": reason_codes or [],
        },
    }


def evaluate_fixture(cases: list[dict], *, route_builder, **kwargs) -> dict:
    from onecode_skill_sanitizer.router_eval_v2 import evaluate_router_v2

    kwargs.setdefault(
        "bundle_required_capabilities",
        {
            scenario_id: ()
            for case in cases
            for scenario_id in case["expected_scenarios"]
        },
    )
    kwargs.setdefault("core_bundle_contract_counts", (0, 0))
    return evaluate_router_v2(cases, route_builder=route_builder, **kwargs)


class RouterEvalV2Tests(unittest.TestCase):
    def test_gold_dataset_has_exact_count_distribution_and_contract(self):
        from onecode_skill_sanitizer.router_eval_v2 import load_eval_dataset_v2

        dataset = load_eval_dataset_v2(EVAL_PATH)
        cases = dataset["cases"]

        self.assertEqual(dataset["labeling"], EXPECTED_LABELING)
        self.assertEqual(len(cases), 100)
        self.assertEqual(Counter(case["category"] for case in cases), EXPECTED_CATEGORIES)
        self.assertEqual(len({case["id"] for case in cases}), 100)
        self.assertTrue(all(case["forbidden_skills"] == [] for case in cases))

    def test_gold_dataset_has_independent_manual_labeling_metadata(self):
        payload = gold_payload()

        self.assertEqual(payload["labeling"], EXPECTED_LABELING)
        actual_fields = {key for case in payload["cases"] for key in case if key.startswith("actual_")}
        self.assertEqual(actual_fields, set())
        for case in payload["cases"]:
            for expected_field in (
                "expected_intents",
                "expected_scenarios",
                "required_dependency_edges",
            ):
                copied_field = expected_field.replace("expected_", "actual_").replace("required_", "actual_")
                self.assertNotIn(copied_field, case)

    def test_gold_dataset_covers_all_bundle_scenarios(self):
        from onecode_skill_sanitizer.router_eval_v2 import load_eval_dataset_v2

        cases = load_eval_dataset_v2(EVAL_PATH)["cases"]
        scenario_counts = Counter(scenario for case in cases for scenario in case["expected_scenarios"])

        self.assertEqual(set(scenario_counts), bundle_scenario_ids())
        self.assertGreaterEqual(min(scenario_counts.values()), 5)

    def test_dataset_identity_is_bound_to_canonical_validated_payload(self):
        from onecode_skill_sanitizer.router_eval_v2 import dataset_identity_v2
        from onecode_skill_sanitizer.router_eval_v2 import load_eval_dataset_v2

        dataset = load_eval_dataset_v2(EVAL_PATH)
        canonical = json.dumps(
            dataset,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")

        identity = dataset_identity_v2(dataset)

        self.assertEqual(
            identity,
            {
                "case_count": 100,
                "dataset_sha256": f"sha256:{hashlib.sha256(canonical).hexdigest()}",
                "labeling_generated_from_router": False,
                "labeling_method": "manual_review",
                "labeling_reviewed_at": "2026-07-10",
                "labeling_reviewer_role": "independent_dataset_review",
            },
        )

    def test_dataset_identity_ignores_object_key_order_but_preserves_content_and_list_order(self):
        from onecode_skill_sanitizer.router_eval_v2 import dataset_identity_v2
        from onecode_skill_sanitizer.router_eval_v2 import load_eval_dataset_v2

        dataset = load_eval_dataset_v2(EVAL_PATH)
        reordered = {
            "cases": [dict(reversed(list(case.items()))) for case in dataset["cases"]],
            "labeling": dict(reversed(list(dataset["labeling"].items()))),
        }
        changed_content = json.loads(json.dumps(dataset))
        changed_content["cases"][0]["task"] += " changed"
        changed_order = json.loads(json.dumps(dataset))
        changed_order["cases"][0], changed_order["cases"][1] = (
            changed_order["cases"][1],
            changed_order["cases"][0],
        )

        original_identity = dataset_identity_v2(dataset)

        self.assertEqual(dataset_identity_v2(reordered), original_identity)
        self.assertNotEqual(dataset_identity_v2(changed_content), original_identity)
        self.assertNotEqual(dataset_identity_v2(changed_order), original_identity)

    def test_gold_sequential_cases_have_dependency_target_and_phrase_diversity(self):
        cases = [case for case in gold_payload()["cases"] if case["category"] == "sequential"]
        edges = [edge for case in cases for edge in case["required_dependency_edges"]]
        targets = Counter(target for _, target in edges)
        chain_cases = [case for case in cases if len(case["expected_intents"]) >= 3]
        normalized_tasks = [" ".join(case["task"].lower().split()) for case in cases]

        self.assertEqual(len(cases), 20)
        self.assertLessEqual(targets["open_source_release"], 6)
        self.assertGreaterEqual(len(targets), 10)
        self.assertGreaterEqual(len(chain_cases), 5)
        self.assertEqual(len(set(normalized_tasks)), 20)

    def test_gold_sequential_cases_cover_required_semantic_patterns(self):
        cases = [case for case in gold_payload()["cases"] if case["category"] == "sequential"]
        edges = {tuple(edge) for case in cases for edge in case["required_dependency_edges"]}
        required_patterns = {
            ("multi_platform_research_discovery", "investment_research_diligence"),
            ("document_knowledge_base", "rag_agent"),
            ("agent_planning_orchestration", "website_build"),
            ("agent_security", "open_source_release"),
            ("data_analysis", "content_seo"),
            ("content_video_production", "agentic_media_production"),
            ("code_review", "website_build"),
            ("multi_platform_research_discovery", "content_seo"),
            ("agent_role_library_governance", "agent_planning_orchestration"),
            ("agent_long_term_memory_governance", "rag_agent"),
        }

        self.assertTrue(required_patterns.issubset(edges))

    def test_loader_rejects_incorrect_labeling_metadata(self):
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError
        from onecode_skill_sanitizer.router_eval_v2 import load_eval_dataset_v2

        payload = gold_payload()
        payload["labeling"]["generated_from_router"] = True
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(DatasetValidationError):
                load_eval_dataset_v2(write_payload(temp_dir, payload), bundle_scenario_ids())

    def test_loader_identifies_legacy_router_eval_schema_v2_payload(self):
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError
        from onecode_skill_sanitizer.router_eval_v2 import load_eval_dataset_v2

        valid_legacy_payload = {
            "schema_version": 2,
            "dataset": "router-quality-v2-baseline",
            "split": "regression",
            "case_count": 0,
            "cases": [],
            "notes": "optional legacy metadata",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(
                DatasetValidationError,
                "router-eval dataset.*use router-eval.*multi-intent gold/suite contract",
            ):
                load_eval_dataset_v2(write_payload(temp_dir, valid_legacy_payload))

        malformed_payloads = {
            "null dataset": {**valid_legacy_payload, "dataset": None},
            "empty dataset": {**valid_legacy_payload, "dataset": ""},
            "wrong split": {**valid_legacy_payload, "split": "training"},
            "boolean case count": {**valid_legacy_payload, "case_count": True},
            "string case count": {**valid_legacy_payload, "case_count": "0"},
            "mismatched case count": {**valid_legacy_payload, "case_count": 1},
            "non-list cases": {**valid_legacy_payload, "cases": {}},
            "invalid case id": {
                **valid_legacy_payload,
                "case_count": 1,
                "cases": [{}],
            },
            "duplicate case ids": {
                **valid_legacy_payload,
                "case_count": 2,
                "cases": [{"id": "same"}, {"id": "same"}],
            },
            "hybrid labeling": {
                **valid_legacy_payload,
                "labeling": EXPECTED_LABELING,
            },
        }
        for label, payload in malformed_payloads.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp_dir:
                with self.assertRaises(DatasetValidationError) as captured:
                    load_eval_dataset_v2(write_payload(temp_dir, payload))
                self.assertEqual(
                    str(captured.exception),
                    "evaluation dataset must be an object containing only labeling and cases",
                )

    def test_loader_rejects_strict_case_contract_violations(self):
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError
        from onecode_skill_sanitizer.router_eval_v2 import load_eval_dataset_v2

        mutations = {
            "duplicate intents": lambda case: case.update(expected_intents=["x", "x"]),
            "empty scenario": lambda case: case.update(expected_scenarios=[""]),
            "unknown scenario": lambda case: case.update(expected_scenarios=["not-known"]),
            "unknown forbidden scenario": lambda case: case.update(forbidden_scenarios=["website-build-launc"]),
            "duplicate forbidden": lambda case: case.update(forbidden_scenarios=["x", "x"]),
            "overlap": lambda case: case.update(forbidden_scenarios=[case["expected_scenarios"][0]]),
            "duplicate edge": lambda case: case.update(
                expected_intents=["a", "b"],
                required_dependency_edges=[["a", "b"], ["a", "b"]],
            ),
            "self edge": lambda case: case.update(expected_intents=["a"], required_dependency_edges=[["a", "a"]]),
            "unknown edge endpoint": lambda case: case.update(
                expected_intents=["a"], required_dependency_edges=[["a", "b"]]
            ),
            "bad status": lambda case: case.update(expected_status="ready"),
            "bad category": lambda case: case.update(category="other"),
            "extra field": lambda case: case.update(actual_intents=[]),
            "non-list forbidden skills": lambda case: case.update(forbidden_skills="skill"),
            "blank forbidden skill": lambda case: case.update(forbidden_skills=[""]),
            "duplicate forbidden skill": lambda case: case.update(forbidden_skills=["skill", "skill"]),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp_dir:
                payload = gold_payload()
                mutate(payload["cases"][0])
                with self.assertRaises(DatasetValidationError):
                    load_eval_dataset_v2(write_payload(temp_dir, payload))

    def test_malformed_dataset_fails_closed(self):
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError
        from onecode_skill_sanitizer.router_eval_v2 import load_eval_dataset_v2

        malformed = {
            "cases": [
                {
                    "id": "bad",
                    "category": "compound",
                    "task": "task",
                    "expected_intents": "not-a-list",
                    "expected_scenarios": [],
                    "required_dependency_edges": [],
                    "forbidden_scenarios": [],
                }
            ]
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.json"
            path.write_text(json.dumps(malformed), encoding="utf-8")
            with self.assertRaises(DatasetValidationError):
                load_eval_dataset_v2(path)

    def test_metric_math_uses_micro_counts_and_explicit_zero_denominators(self):

        cases = [
            {
                "id": "one",
                "category": "compound",
                "task": "one",
                "expected_intents": ["alpha", "beta"],
                "expected_scenarios": ["s1", "s2"],
                "required_dependency_edges": [["alpha", "beta"]],
                "forbidden_scenarios": ["bad"],
                "expected_status": "complete",
            },
            {
                "id": "two",
                "category": "negative",
                "task": "two",
                "expected_intents": ["general"],
                "expected_scenarios": [],
                "required_dependency_edges": [],
                "forbidden_scenarios": ["bad", "worse"],
                "expected_status": "complete",
            },
        ]
        routes = {
            "one": synthetic_route(
                ["alpha", "beta"],
                ["s1", "extra", "bad"],
                [("alpha", "beta")],
            ),
            "two": synthetic_route(["wrong"], ["bad"]),
        }

        report = evaluate_fixture(cases, route_builder=lambda case: routes[case["id"]])

        self.assertEqual(report["metrics"]["multi_intent_exact_match"], 0.5)
        self.assertEqual(report["metrics"]["scenario_precision"], 0.25)
        self.assertEqual(report["metrics"]["scenario_recall"], 0.5)
        self.assertEqual(report["metrics"]["scenario_f1"], 1 / 3)
        self.assertEqual(
            report["metrics"]["forbidden_scenario_false_positive_rate"],
            2 / 3,
        )
        self.assertEqual(report["metrics"]["dependency_edge_recall"], 1.0)
        self.assertEqual(report["metrics"]["dag_validity"], 1.0)
        self.assertEqual([result["id"] for result in report["cases"]], ["one", "two"])

    def test_zero_denominators_are_finite(self):

        cases = [
            {
                "id": "zero",
                "category": "negative",
                "task": "zero",
                "expected_intents": ["general"],
                "expected_scenarios": [],
                "required_dependency_edges": [],
                "forbidden_scenarios": [],
            }
        ]
        report = evaluate_fixture(
            cases,
            route_builder=lambda case: synthetic_route(["general"], []),
        )

        self.assertEqual(report["metrics"]["scenario_precision"], 1.0)
        self.assertEqual(report["metrics"]["scenario_recall"], 1.0)
        self.assertEqual(report["metrics"]["scenario_f1"], 1.0)
        self.assertEqual(report["metrics"]["dependency_edge_recall"], 1.0)
        self.assertEqual(report["metrics"]["forbidden_scenario_false_positive_rate"], 0.0)
        json.dumps(report, allow_nan=False)

    def test_new_task_type_metrics_match_hand_calculation_without_changing_old_metrics(self):

        cases = [
            {
                "id": case_id,
                "category": "compound",
                "task": case_id,
                "expected_intents": expected,
                "expected_scenarios": [],
                "required_dependency_edges": [],
                "forbidden_scenarios": [],
                "forbidden_skills": [],
            }
            for case_id, expected in (("one", ["a"]), ("two", ["a"]), ("three", ["b"]))
        ]
        routes = {
            "one": synthetic_route(["a"], []),
            "two": synthetic_route(["b"], []),
            "three": synthetic_route(["b"], []),
        }

        report = evaluate_fixture(cases, route_builder=lambda case: routes[case["id"]])

        self.assertEqual(report["metrics"]["task_type_macro_precision"], 0.75)
        self.assertEqual(report["metrics"]["task_type_macro_recall"], 0.75)
        self.assertAlmostEqual(report["metrics"]["task_type_macro_f1"], 2 / 3)
        self.assertEqual(report["metrics"]["multi_intent_exact_match"], 2 / 3)
        self.assertEqual(report["counts"]["task_type_label_count"], 2)
        self.assertEqual(
            report["counts"]["task_type_by_label"],
            [
                {
                    "task_type": "a",
                    "true_positive": 1,
                    "false_positive": 0,
                    "false_negative": 1,
                },
                {
                    "task_type": "b",
                    "true_positive": 1,
                    "false_positive": 1,
                    "false_negative": 0,
                },
            ],
        )

    def test_required_capability_recall_counts_only_covered_expected_capabilities(self):

        case = {
            "id": "capabilities",
            "category": "compound",
            "task": "capabilities",
            "expected_intents": ["a"],
            "expected_scenarios": ["s1", "s2"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "forbidden_skills": [],
        }
        route = synthetic_route(
            ["a"],
            ["s1", "s2"],
            capability_resolution=[
                {"scenario_id": "s1", "capability": "c1", "required": True, "status": "covered", "skills": ["x"]},
                {"scenario_id": "s1", "capability": "c2", "required": True, "status": "covered", "skills": ["x"]},
                {"scenario_id": "s2", "capability": "c3", "required": True, "status": "covered", "skills": ["x"]},
                {"scenario_id": "s2", "capability": "c4", "required": True, "status": "missing", "skills": []},
            ],
        )

        report = evaluate_fixture(
            [case],
            route_builder=lambda current: route,
            bundle_required_capabilities={"s1": ("c1", "c2"), "s2": ("c3", "c4")},
        )

        self.assertEqual(report["metrics"]["required_capability_recall"], 0.75)
        self.assertEqual(report["counts"]["required_capability_hits"], 3)
        self.assertEqual(report["counts"]["required_capability_total"], 4)

    def test_core_bundle_contract_coverage_is_finite_and_has_support_counts(self):

        case = {
            "id": "contracts",
            "category": "compound",
            "task": "contracts",
            "expected_intents": ["a"],
            "expected_scenarios": [],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "forbidden_skills": [],
        }

        report = evaluate_fixture(
            [case],
            route_builder=lambda current: synthetic_route(["a"], []),
            core_bundle_contract_counts=(4, 5),
        )

        self.assertEqual(report["metrics"]["core_bundle_contract_coverage"], 0.8)
        self.assertEqual(report["counts"]["core_bundle_contract_covered"], 4)
        self.assertEqual(report["counts"]["core_bundle_contract_total"], 5)
        self.assertTrue(report["counts"]["core_bundle_contract_available"])

    def test_evaluator_requires_explicit_capability_and_contract_support_context(self):
        from onecode_skill_sanitizer.router_eval_v2 import EvaluatorError
        from onecode_skill_sanitizer.router_eval_v2 import evaluate_router_v2 as evaluate_without_support

        case = {
            "id": "support-required",
            "category": "compound",
            "task": "support",
            "expected_intents": ["a"],
            "expected_scenarios": [],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "forbidden_skills": [],
        }
        def route_builder(current):
            return synthetic_route(["a"], [])
        malformed_calls = [
            {},
            {"bundle_required_capabilities": None, "core_bundle_contract_counts": (0, 0)},
            {"bundle_required_capabilities": {}, "core_bundle_contract_counts": None},
            {"bundle_required_capabilities": {}, "core_bundle_contract_counts": [0, 0]},
            {"bundle_required_capabilities": {}, "core_bundle_contract_counts": (True, 1)},
            {"bundle_required_capabilities": {"s": True}, "core_bundle_contract_counts": (0, 0)},
        ]
        for kwargs in malformed_calls:
            with self.subTest(kwargs=kwargs), self.assertRaises(EvaluatorError):
                evaluate_without_support([case], route_builder=route_builder, **kwargs)

    def test_evaluator_requires_capability_context_for_every_expected_scenario(self):
        from onecode_skill_sanitizer.router_eval_v2 import EvaluatorError

        case = {
            "id": "missing-scenario-context",
            "category": "compound",
            "task": "support",
            "expected_intents": ["a"],
            "expected_scenarios": ["missing"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "forbidden_skills": [],
        }

        with self.assertRaisesRegex(EvaluatorError, "missing required capability context.*missing"):
            evaluate_fixture(
                [case],
                route_builder=lambda current: synthetic_route(["a"], ["missing"]),
                bundle_required_capabilities={},
                core_bundle_contract_counts=(0, 0),
            )

    def test_explicit_empty_context_is_available_but_zero_contract_support_fails_closed(self):

        case = {
            "id": "explicit-empty",
            "category": "negative",
            "task": "empty",
            "expected_intents": ["a"],
            "expected_scenarios": [],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "forbidden_skills": [],
        }

        report = evaluate_fixture(
            [case],
            route_builder=lambda current: synthetic_route(["a"], []),
            bundle_required_capabilities={},
            core_bundle_contract_counts=(0, 0),
        )

        self.assertEqual(report["metrics"]["required_capability_recall"], 1.0)
        self.assertTrue(report["counts"]["required_capability_context_available"])
        self.assertEqual(report["metrics"]["core_bundle_contract_coverage"], 0.0)
        self.assertFalse(report["counts"]["core_bundle_contract_available"])

        no_required_case = {
            **case,
            "id": "explicit-no-required-capabilities",
            "expected_scenarios": ["no-required-capabilities"],
        }
        no_required_report = evaluate_fixture(
            [no_required_case],
            route_builder=lambda current: synthetic_route(["a"], ["no-required-capabilities"]),
            bundle_required_capabilities={"no-required-capabilities": []},
        )
        self.assertEqual(no_required_report["metrics"]["required_capability_recall"], 1.0)
        self.assertTrue(no_required_report["counts"]["required_capability_context_available"])

    def test_dependency_precision_and_recall_use_deduplicated_logical_pairs(self):

        case = {
            "id": "dependencies",
            "category": "sequential",
            "task": "dependencies",
            "expected_intents": ["a", "b", "c"],
            "expected_scenarios": [],
            "required_dependency_edges": [["a", "b"], ["b", "c"]],
            "forbidden_scenarios": [],
            "forbidden_skills": [],
        }
        route = synthetic_route(
            ["a", "b", "c"],
            [],
            dependency_pairs=[("a", "b"), ("a", "c")],
        )
        route["execution_graph"]["edges"].append(
            {**route["execution_graph"]["edges"][0], "type": "intent_verification_dependency"}
        )

        report = evaluate_fixture([case], route_builder=lambda current: route)

        self.assertEqual(report["metrics"]["dependency_edge_precision"], 0.5)
        self.assertEqual(report["metrics"]["dependency_edge_recall"], 0.5)
        self.assertEqual(report["counts"]["dependency_hits"], 1)
        self.assertEqual(report["counts"]["dependency_predicted"], 2)
        self.assertEqual(report["counts"]["dependency_total"], 2)

    def test_forbidden_skill_false_positive_rate_has_explicit_four_label_support(self):

        case = {
            "id": "skills",
            "category": "negative",
            "task": "skills",
            "expected_intents": ["a"],
            "expected_scenarios": [],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "forbidden_skills": ["bad-1", "bad-2", "bad-3", "bad-4"],
        }
        route = synthetic_route(["a"], [], selected_skills=["good", "bad-2"])

        report = evaluate_fixture([case], route_builder=lambda current: route)

        self.assertEqual(report["metrics"]["forbidden_skill_false_positive_rate"], 0.25)
        self.assertEqual(report["counts"]["forbidden_skill_hits"], 1)
        self.assertEqual(report["counts"]["forbidden_skill_total"], 4)

    def test_high_confidence_error_rate_counts_cases_and_uses_set_errors(self):

        cases = [
            {
                "id": case_id,
                "category": "compound",
                "task": case_id,
                "expected_intents": expected,
                "expected_scenarios": [],
                "required_dependency_edges": [],
                "forbidden_scenarios": [],
                "forbidden_skills": [],
            }
            for case_id, expected in (("correct", ["a", "b"]), ("wrong", ["a", "b"]), ("low", ["a"]))
        ]
        routes = {
            "correct": synthetic_route(["b", "a"], [], intent_confidences=[0.8, 0.7]),
            "wrong": synthetic_route(["a", "c"], [], intent_confidences=[0.7, 0.9]),
            "low": synthetic_route(["wrong"], [], intent_confidences=[0.79]),
        }

        report = evaluate_fixture(cases, route_builder=lambda case: routes[case["id"]])

        self.assertEqual(report["metrics"]["high_confidence_error_rate"], 0.5)
        self.assertEqual(report["counts"]["high_confidence_error_cases"], 1)
        self.assertEqual(report["counts"]["high_confidence_cases"], 2)

    def test_new_metric_zero_denominators_are_finite_and_malformed_routes_fail_closed(self):
        from onecode_skill_sanitizer.router_eval_v2 import EvaluatorError

        case = {
            "id": "empty",
            "category": "negative",
            "task": "empty",
            "expected_intents": ["a"],
            "expected_scenarios": [],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "forbidden_skills": [],
        }
        report = evaluate_fixture([case], route_builder=lambda current: synthetic_route(["a"], []))
        for value in report["metrics"].values():
            self.assertTrue(math.isfinite(value))

        malformed_routes = []
        for field, value in (("confidence", float("nan")), ("confidence", True)):
            route = synthetic_route(["a"], [])
            route["intent_graph"]["intents"][0][field] = value
            malformed_routes.append(route)
        missing_skill_name = synthetic_route(["a"], [])
        missing_skill_name["selected_skills"] = [{}]
        malformed_routes.append(missing_skill_name)
        bad_resolution = synthetic_route(["a"], [])
        bad_resolution["capability_resolution"]["capabilities"] = [
            {"scenario_id": "", "capability": "c", "required": True, "status": "covered", "skills": []}
        ]
        malformed_routes.append(bad_resolution)

        for route in malformed_routes:
            with self.subTest(route=route), self.assertRaises(EvaluatorError):
                evaluate_fixture([case], route_builder=lambda current: route)

    def test_unexpected_cycle_is_an_evaluator_error(self):
        from onecode_skill_sanitizer.router_eval_v2 import EvaluatorError

        case = {
            "id": "cycle",
            "category": "compound",
            "task": "cycle",
            "expected_intents": ["alpha", "beta"],
            "expected_scenarios": ["s1", "s2"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "complete",
        }
        route = synthetic_route(["alpha"], ["s1"], graph_status="blocked", acyclic=False)
        route["execution_graph"]["edges"] = [{"from": "node-1", "to": "node-1", "type": "skill_order"}]

        with self.assertRaises(EvaluatorError):
            evaluate_fixture([case], route_builder=lambda item: route)

    def test_unexpected_blocked_graph_is_an_evaluator_error_for_nonblocked_case(self):
        from onecode_skill_sanitizer.router_eval_v2 import EvaluatorError

        for expected_status in ("complete", "incomplete"):
            case = {
                "id": expected_status,
                "category": "compound",
                "task": "task",
                "expected_intents": ["alpha"],
                "expected_scenarios": ["s1"],
                "required_dependency_edges": [],
                "forbidden_scenarios": [],
                "expected_status": expected_status,
            }
            with self.subTest(expected_status=expected_status), self.assertRaises(EvaluatorError):
                evaluate_fixture(
                    [case],
                    route_builder=lambda current: synthetic_route(
                        current["expected_intents"],
                        current["expected_scenarios"],
                        graph_status="blocked",
                        routing_status="blocked",
                    ),
                )

    def test_coherent_status_graph_pairs_are_valid(self):

        for routing_status, graph_status, expected_valid in VALID_STATUS_GRAPH_PAIRS:
            case = {
                "id": routing_status,
                "category": "compound",
                "task": "task",
                "expected_intents": ["alpha"],
                "expected_scenarios": ["s1"],
                "required_dependency_edges": [],
                "forbidden_scenarios": [],
                "expected_status": routing_status,
            }
            route = synthetic_route(
                ["alpha"],
                ["s1"],
                graph_status=graph_status,
                acyclic=graph_status == "ready",
                routing_status=routing_status,
                reason_codes=[] if graph_status == "ready" else ["incomplete_composition"],
            )
            if graph_status == "blocked":
                route["execution_graph"]["nodes"] = []
                route["execution_graph"]["edges"] = []

            with self.subTest(routing_status=routing_status, graph_status=graph_status):
                report = evaluate_fixture([case], route_builder=lambda current: route)
                self.assertEqual(report["cases"][0]["dag_valid"], expected_valid)

    def test_fail_closed_empty_graph_accepts_only_incomplete_reasons(self):

        case = {
            "id": "fail-closed",
            "category": "compound",
            "task": "task",
            "expected_intents": ["alpha"],
            "expected_scenarios": ["s1"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        for reason in ("incomplete_composition", "missing_required_capability"):
            route = synthetic_route(
                ["alpha"],
                ["s1"],
                graph_status="blocked",
                acyclic=False,
                routing_status="blocked",
                reason_codes=[reason],
            )
            route["execution_graph"]["nodes"] = []
            route["execution_graph"]["edges"] = []
            with self.subTest(reason=reason):
                report = evaluate_fixture([case], route_builder=lambda current: route)
                self.assertTrue(report["cases"][0]["dag_valid"])

        for reason in ("dependency_cycle", "missing_scenario_bundle", "invented_reason"):
            route = synthetic_route(
                ["alpha"],
                ["s1"],
                graph_status="blocked",
                acyclic=False,
                routing_status="blocked",
                reason_codes=[reason],
            )
            route["execution_graph"]["nodes"] = []
            route["execution_graph"]["edges"] = []
            with self.subTest(reason=reason):
                report = evaluate_fixture([case], route_builder=lambda current: route)
                self.assertFalse(report["cases"][0]["dag_valid"])

    def test_fail_closed_incomplete_graph_rejects_nodes_edges_and_acyclic_flag(self):

        case = {
            "id": "incomplete",
            "category": "compound",
            "task": "task",
            "expected_intents": ["alpha"],
            "expected_scenarios": ["s1"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        nonempty = synthetic_route(
            ["alpha"],
            ["s1"],
            graph_status="blocked",
            acyclic=False,
            routing_status="incomplete",
            reason_codes=["incomplete_composition"],
        )
        wrong_flag = synthetic_route(
            ["alpha"],
            ["s1"],
            graph_status="blocked",
            acyclic=True,
            routing_status="incomplete",
            reason_codes=["incomplete_composition"],
        )
        wrong_flag["execution_graph"]["nodes"] = []
        wrong_flag["execution_graph"]["edges"] = []

        for route in (nonempty, wrong_flag):
            with self.subTest(route=route):
                report = evaluate_fixture([case], route_builder=lambda current: route)
                self.assertFalse(report["cases"][0]["dag_valid"])

    def test_dependency_edge_types_collapse_to_one_logical_intent_pair(self):

        case = {
            "id": "logical-edge",
            "category": "sequential",
            "task": "task",
            "expected_intents": ["alpha", "beta"],
            "expected_scenarios": ["s1", "s2"],
            "required_dependency_edges": [["alpha", "beta"]],
            "forbidden_scenarios": [],
            "expected_status": "complete",
        }
        route = synthetic_route(
            ["alpha", "beta"],
            ["s1", "s2"],
            dependency_pairs=[("alpha", "beta")],
        )
        route["execution_graph"]["edges"].append(
            {
                **route["execution_graph"]["edges"][0],
                "type": "intent_verification_dependency",
            }
        )

        report = evaluate_fixture([case], route_builder=lambda current: route)

        self.assertEqual(report["cases"][0]["actual_dependency_edges"], [["alpha", "beta"]])
        self.assertEqual(report["counts"]["dependency_hits"], 1)
        self.assertEqual(report["counts"]["dependency_total"], 1)

    def test_complete_ready_route_rejects_source_intent_cycle_despite_status_mismatch(self):

        case = {
            "id": "source-cycle",
            "category": "sequential",
            "task": "task",
            "expected_intents": ["alpha", "beta"],
            "expected_scenarios": ["s1", "s2"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        route = synthetic_route(
            ["alpha", "beta"],
            ["s1", "s2"],
            routing_status="complete",
            graph_status="ready",
            intent_dependencies=[["i2"], ["i1"]],
        )

        report = evaluate_fixture([case], route_builder=lambda current: route)
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}

        self.assertFalse(report["cases"][0]["dag_valid"])
        self.assertIn("source_intent_graph_cycle", issue_ids)
        self.assertIn("status_mismatch", issue_ids)

    def test_complete_ready_route_rejects_unknown_and_malformed_source_dependencies(self):

        case = {
            "id": "source-dependencies",
            "category": "sequential",
            "task": "task",
            "expected_intents": ["alpha"],
            "expected_scenarios": ["s1"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        routes = {
            "unknown": synthetic_route(["alpha"], ["s1"], intent_dependencies=[["missing"]]),
            "not-list": synthetic_route(["alpha"], ["s1"]),
            "empty": synthetic_route(["alpha"], ["s1"], intent_dependencies=[[""]]),
        }
        routes["not-list"]["intent_graph"]["intents"][0]["depends_on"] = "i1"

        for label, route in routes.items():
            with self.subTest(label=label):
                report = evaluate_fixture([case], route_builder=lambda current: route)
                issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}
                self.assertFalse(report["cases"][0]["dag_valid"])
                self.assertIn("source_intent_graph_invalid", issue_ids)

    def test_source_intent_and_matching_node_identities_reject_blank_or_padded_values(self):
        from onecode_skill_sanitizer.router_eval_v2 import EvaluatorError

        case = {
            "id": "source-identity",
            "category": "compound",
            "task": "task",
            "expected_intents": ["alpha"],
            "expected_scenarios": ["s1"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        for intent_id in (" ", " i1 "):
            route = synthetic_route(["alpha"], ["s1"])
            route["intent_graph"]["intents"][0]["id"] = intent_id
            route["execution_graph"]["nodes"][0]["intent_ids"] = [intent_id]
            with self.subTest(intent_id=intent_id), self.assertRaises(EvaluatorError):
                evaluate_fixture([case], route_builder=lambda current: route)

        for task_type in (" ", " code_review "):
            route = synthetic_route(["alpha"], ["s1"])
            route["intent_graph"]["intents"][0]["task_type"] = task_type
            with self.subTest(task_type=task_type), self.assertRaises(EvaluatorError):
                evaluate_fixture([case], route_builder=lambda current: route)

    def test_source_depends_on_rejects_blank_or_padded_values_as_malformed(self):

        case = {
            "id": "dependency-identity",
            "category": "sequential",
            "task": "task",
            "expected_intents": ["alpha"],
            "expected_scenarios": ["s1"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        for dependency_id in (" ", " i1 "):
            route = synthetic_route(["alpha"], ["s1"], intent_dependencies=[[dependency_id]])
            with self.subTest(dependency_id=dependency_id):
                report = evaluate_fixture([case], route_builder=lambda current: route)
                source_issue = next(
                    issue for issue in report["cases"][0]["issues"] if issue["id"] == "source_intent_graph_invalid"
                )
                self.assertFalse(report["cases"][0]["dag_valid"])
                self.assertEqual(source_issue["reason"], "malformed_dependencies")

    def test_source_identity_accepts_canonical_intent_id_and_task_type(self):

        case = {
            "id": "canonical-identity",
            "category": "compound",
            "task": "task",
            "expected_intents": ["code_review"],
            "expected_scenarios": ["s1"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "complete",
        }
        route = synthetic_route(["code_review"], ["s1"])

        report = evaluate_fixture([case], route_builder=lambda current: route)

        self.assertEqual(route["intent_graph"]["intents"][0]["id"], "i1")
        self.assertTrue(report["cases"][0]["dag_valid"])

    def test_complete_ready_graph_requires_exactly_empty_reason_codes(self):

        case = {
            "id": "complete-reasons",
            "category": "compound",
            "task": "task",
            "expected_intents": ["alpha"],
            "expected_scenarios": ["s1"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        invalid_reason_codes = (
            ["incomplete_composition"],
            ["dependency_cycle"],
            ["invented_reason"],
            ["incomplete_composition", "dependency_cycle"],
            ["invented_reason", "invented_reason"],
        )

        for reason_codes in invalid_reason_codes:
            route = synthetic_route(["alpha"], ["s1"], reason_codes=reason_codes)
            with self.subTest(reason_codes=reason_codes):
                report = evaluate_fixture([case], route_builder=lambda current: route)
                issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}
                self.assertFalse(report["cases"][0]["dag_valid"])
                self.assertIn("unexpected_ready_graph_reason", issue_ids)

    def test_reason_codes_malformed_types_fail_closed(self):
        from onecode_skill_sanitizer.router_eval_v2 import EvaluatorError

        case = {
            "id": "malformed-reasons",
            "category": "compound",
            "task": "task",
            "expected_intents": ["alpha"],
            "expected_scenarios": ["s1"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        for reason_codes in ("incomplete_composition", [""], [1], [True]):
            route = synthetic_route(["alpha"], ["s1"])
            route["execution_graph"]["reason_codes"] = reason_codes
            with self.subTest(reason_codes=reason_codes), self.assertRaises(EvaluatorError):
                evaluate_fixture([case], route_builder=lambda current: route)

    def test_dependency_edge_endpoint_nodes_require_strict_intent_ids(self):
        from onecode_skill_sanitizer.router_eval_v2 import EvaluatorError

        case = {
            "id": "dependency-node",
            "category": "sequential",
            "task": "task",
            "expected_intents": ["alpha", "beta"],
            "expected_scenarios": ["s1", "s2"],
            "required_dependency_edges": [["alpha", "beta"]],
            "forbidden_scenarios": [],
            "expected_status": "complete",
        }
        mutations = {
            "empty intent ids": [],
            "unknown intent id": ["missing"],
            "duplicate intent id": ["i1", "i1"],
            "empty intent id": [""],
            "malformed intent ids": ("i1",),
        }
        for label, intent_ids in mutations.items():
            route = synthetic_route(
                ["alpha", "beta"],
                ["s1", "s2"],
                dependency_pairs=[("alpha", "beta")],
            )
            route["execution_graph"]["nodes"][0]["intent_ids"] = intent_ids
            with self.subTest(label=label), self.assertRaises(EvaluatorError):
                evaluate_fixture([case], route_builder=lambda current: route)

        for label, endpoint in (("empty endpoint", ""), ("unknown endpoint", "missing"), ("malformed endpoint", 1)):
            route = synthetic_route(
                ["alpha", "beta"],
                ["s1", "s2"],
                dependency_pairs=[("alpha", "beta")],
            )
            route["execution_graph"]["edges"][0]["from"] = endpoint
            with self.subTest(label=label), self.assertRaises(EvaluatorError):
                evaluate_fixture([case], route_builder=lambda current: route)

    def test_non_dependency_nodes_require_strict_intent_ids(self):
        from onecode_skill_sanitizer.router_eval_v2 import EvaluatorError

        case = {
            "id": "ordinary-node",
            "category": "compound",
            "task": "task",
            "expected_intents": ["alpha"],
            "expected_scenarios": ["s1"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "complete",
        }
        for label, intent_ids in {
            "empty": [],
            "unknown": ["missing"],
            "duplicate": ["i1", "i1"],
        }.items():
            route = synthetic_route(["alpha"], ["s1"])
            route["execution_graph"]["nodes"][0]["intent_ids"] = intent_ids
            with self.subTest(label=label), self.assertRaises(EvaluatorError):
                evaluate_fixture([case], route_builder=lambda current: route)

    def test_complete_ready_graph_requires_nodes_and_full_source_intent_coverage(self):

        case = {
            "id": "execution-coverage",
            "category": "compound",
            "task": "task",
            "expected_intents": ["alpha", "beta"],
            "expected_scenarios": ["s1", "s2"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        empty = synthetic_route(["alpha", "beta"], ["s1", "s2"])
        empty["execution_graph"]["nodes"] = []
        missing = synthetic_route(["alpha", "beta"], ["s1", "s2"])
        missing["execution_graph"]["nodes"] = missing["execution_graph"]["nodes"][:1]

        for label, route, expected_issue in (
            ("empty", empty, "empty_ready_graph"),
            ("missing", missing, "missing_source_intent_coverage"),
        ):
            with self.subTest(label=label):
                report = evaluate_fixture([case], route_builder=lambda current: route)
                issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}
                self.assertFalse(report["cases"][0]["dag_valid"])
                self.assertIn(expected_issue, issue_ids)

    def test_complete_ready_graph_allows_multi_intent_node_mapping(self):

        case = {
            "id": "multi-intent-node",
            "category": "compound",
            "task": "task",
            "expected_intents": ["alpha", "beta"],
            "expected_scenarios": ["s1", "s2"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "complete",
        }
        route = synthetic_route(["alpha", "beta"], ["s1", "s2"])
        route["execution_graph"]["nodes"] = [
            {
                **route["execution_graph"]["nodes"][0],
                "intent_ids": ["i1", "i2"],
            }
        ]

        report = evaluate_fixture([case], route_builder=lambda current: route)

        self.assertTrue(report["cases"][0]["dag_valid"])

    def test_blocked_empty_graph_rejects_empty_source_intent_graph(self):

        case = {
            "id": "empty-source",
            "category": "compound",
            "task": "task",
            "expected_intents": [],
            "expected_scenarios": [],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        route = synthetic_route(
            [],
            [],
            graph_status="blocked",
            acyclic=False,
            routing_status="blocked",
            reason_codes=["incomplete_composition"],
        )

        report = evaluate_fixture([case], route_builder=lambda current: route)
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}

        self.assertFalse(report["cases"][0]["dag_valid"])
        self.assertIn("source_intent_graph_invalid", issue_ids)

    def test_execution_node_ids_must_be_exact_nonblank_strings(self):
        from onecode_skill_sanitizer.router_eval_v2 import EvaluatorError

        case = {
            "id": "node-id",
            "category": "compound",
            "task": "task",
            "expected_intents": ["alpha"],
            "expected_scenarios": ["s1"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "complete",
        }
        for node_id in ("", "   "):
            route = synthetic_route(["alpha"], ["s1"])
            route["execution_graph"]["nodes"][0]["id"] = node_id
            with self.subTest(node_id=node_id), self.assertRaises(EvaluatorError):
                evaluate_fixture([case], route_builder=lambda current: route)

    def test_dependency_edge_cannot_reference_matching_blank_node_id(self):
        from onecode_skill_sanitizer.router_eval_v2 import EvaluatorError

        case = {
            "id": "blank-dependency-node",
            "category": "sequential",
            "task": "task",
            "expected_intents": ["alpha", "beta"],
            "expected_scenarios": ["s1", "s2"],
            "required_dependency_edges": [["alpha", "beta"]],
            "forbidden_scenarios": [],
            "expected_status": "complete",
        }
        route = synthetic_route(
            ["alpha", "beta"],
            ["s1", "s2"],
            dependency_pairs=[("alpha", "beta")],
        )
        route["execution_graph"]["nodes"][0]["id"] = "   "
        route["execution_graph"]["edges"][0]["from"] = "   "

        with self.assertRaises(EvaluatorError):
            evaluate_fixture([case], route_builder=lambda current: route)

    def test_expected_blocked_case_accepts_allowed_empty_graph_and_scores_ready_as_mismatch(self):

        case = {
            "id": "blocked",
            "category": "sequential",
            "task": "impossible dependency",
            "expected_intents": ["alpha", "beta"],
            "expected_scenarios": ["s1", "s2"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        blocked = evaluate_fixture(
            [case],
            route_builder=lambda current: {
                **synthetic_route(
                    current["expected_intents"],
                    current["expected_scenarios"],
                    graph_status="blocked",
                    acyclic=False,
                    routing_status="blocked",
                    reason_codes=["incomplete_composition"],
                ),
                "execution_graph": {
                    "status": "blocked",
                    "acyclic": False,
                    "nodes": [],
                    "edges": [],
                    "reason_codes": ["incomplete_composition"],
                },
            },
        )
        ready = evaluate_fixture(
            [case],
            route_builder=lambda current: synthetic_route(
                current["expected_intents"],
                current["expected_scenarios"],
                graph_status="ready",
                routing_status="complete",
            ),
        )

        self.assertTrue(blocked["cases"][0]["dag_valid"])
        self.assertTrue(ready["cases"][0]["dag_valid"])
        self.assertIn("status_mismatch", {issue["id"] for issue in ready["cases"][0]["issues"]})

    def test_blocked_source_cycle_is_invalid_even_with_empty_execution_graph(self):

        case = {
            "id": "blocked-cycle",
            "category": "sequential",
            "task": "cyclic dependency",
            "expected_intents": ["alpha", "beta"],
            "expected_scenarios": ["s1", "s2"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        route = synthetic_route(
            ["alpha", "beta"],
            ["s1", "s2"],
            graph_status="blocked",
            acyclic=False,
            routing_status="blocked",
            reason_codes=["dependency_cycle"],
            intent_dependencies=[["i2"], ["i1"]],
        )
        route["execution_graph"]["nodes"] = []
        route["execution_graph"]["edges"] = []

        report = evaluate_fixture([case], route_builder=lambda current: route)

        self.assertFalse(report["cases"][0]["dag_valid"])
        self.assertTrue(report["cases"][0]["topology_acyclic"])
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}
        self.assertIn("source_intent_graph_cycle", issue_ids)
        self.assertIn("invalid_incomplete_graph_reason", issue_ids)

    def test_incoherent_blocked_self_cycle_is_invalid_with_flag_issue(self):

        case = {
            "id": "blocked-cycle",
            "category": "sequential",
            "task": "cyclic dependency",
            "expected_intents": ["alpha"],
            "expected_scenarios": ["s1"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        route = synthetic_route(
            ["alpha", "beta"],
            ["s1", "s2"],
            graph_status="blocked",
            acyclic=True,
            routing_status="blocked",
            reason_codes=["dependency_cycle"],
            intent_dependencies=[["i2"], ["i1"]],
        )
        route["execution_graph"]["nodes"] = []
        route["execution_graph"]["edges"] = []

        report = evaluate_fixture([case], route_builder=lambda current: route)
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}

        self.assertFalse(report["cases"][0]["dag_valid"])
        self.assertIn("acyclic_flag_mismatch", issue_ids)

    def test_dependency_cycle_reason_with_acyclic_source_intents_is_invalid(self):

        case = {
            "id": "blocked-cycle",
            "category": "sequential",
            "task": "cyclic dependency",
            "expected_intents": ["alpha", "beta"],
            "expected_scenarios": ["s1", "s2"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        route = synthetic_route(
            ["alpha", "beta"],
            ["s1", "s2"],
            graph_status="blocked",
            acyclic=False,
            routing_status="blocked",
            reason_codes=["dependency_cycle"],
            intent_dependencies=[[], ["i1"]],
        )
        route["execution_graph"]["nodes"] = []
        route["execution_graph"]["edges"] = []

        report = evaluate_fixture([case], route_builder=lambda current: route)
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}

        self.assertFalse(report["cases"][0]["dag_valid"])
        self.assertIn("invalid_incomplete_graph_reason", issue_ids)

    def test_cyclic_source_with_noncycle_blocking_reason_is_invalid(self):

        case = {
            "id": "blocked-cycle",
            "category": "sequential",
            "task": "cyclic dependency",
            "expected_intents": ["alpha", "beta"],
            "expected_scenarios": ["s1", "s2"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        route = synthetic_route(
            ["alpha", "beta"],
            ["s1", "s2"],
            graph_status="blocked",
            acyclic=False,
            routing_status="blocked",
            reason_codes=["invalid_intent_graph"],
            intent_dependencies=[["i2"], ["i1"]],
        )
        route["execution_graph"]["nodes"] = []
        route["execution_graph"]["edges"] = []

        report = evaluate_fixture([case], route_builder=lambda current: route)
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}

        self.assertFalse(report["cases"][0]["dag_valid"])
        self.assertIn("source_intent_graph_cycle", issue_ids)
        self.assertIn("invalid_incomplete_graph_reason", issue_ids)

    def test_real_compiler_cyclic_intent_graph_is_invalid_blocked(self):
        from onecode_skill_sanitizer.compiler import compile_execution_graph
        from onecode_skill_sanitizer.composer import ScenarioComposition, ScenarioSelection
        from onecode_skill_sanitizer.intent import Intent, IntentGraph

        def intent(intent_id: str, depends_on: tuple[str, ...]) -> Intent:
            return Intent(
                id=intent_id,
                summary=intent_id,
                task_type=intent_id,
                required_artifacts=(),
                risk_flags=(),
                depends_on=depends_on,
                source="deterministic",
                confidence=1.0,
            )

        graph = IntentGraph(
            intents=(intent("i1", ("i2",)), intent("i2", ("i1",))),
            unresolved_dependencies=(),
        )
        composition = ScenarioComposition(
            selections=(
                ScenarioSelection("first", ("i1",), 1.0, 1),
                ScenarioSelection("second", ("i2",), 1.0, 1),
            ),
            uncovered_intents=(),
            status="complete",
        )
        compiled = compile_execution_graph(
            graph,
            composition,
            {"bundles": []},
            set(),
        )
        route = {
            "routing_status": "blocked",
            "intent_graph": {
                "intents": [
                    {
                        "id": intent.id,
                        "task_type": intent.task_type,
                        "depends_on": list(intent.depends_on),
                        "confidence": intent.confidence,
                    }
                    for intent in graph.intents
                ]
            },
            "selected_scenarios": [],
            "selected_skills": [],
            "capability_resolution": {"status": "complete", "capabilities": [], "missing_required_count": 0},
            "execution_graph": compiled,
        }
        case = {
            "id": "real-cycle",
            "category": "sequential",
            "task": "cycle",
            "expected_intents": ["i1", "i2"],
            "expected_scenarios": [],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }

        report = evaluate_fixture([case], route_builder=lambda current: route)

        self.assertIn("dependency_cycle", compiled["reason_codes"])
        self.assertEqual(compiled["nodes"], [])
        self.assertEqual(compiled["edges"], [])
        self.assertFalse(report["cases"][0]["dag_valid"])
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}
        self.assertIn("source_intent_graph_cycle", issue_ids)
        self.assertIn("invalid_incomplete_graph_reason", issue_ids)

    def test_noncycle_blocked_boundary_rejects_disallowed_reason(self):

        case = {
            "id": "blocked-boundary",
            "category": "sequential",
            "task": "missing scenario",
            "expected_intents": ["alpha"],
            "expected_scenarios": ["s1"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        route = synthetic_route(
            ["alpha"],
            ["s1"],
            graph_status="blocked",
            acyclic=False,
            routing_status="blocked",
            reason_codes=["missing_scenario_bundle"],
        )
        route["execution_graph"]["nodes"] = []
        route["execution_graph"]["edges"] = []

        report = evaluate_fixture([case], route_builder=lambda current: route)

        self.assertFalse(report["cases"][0]["dag_valid"])
        self.assertTrue(report["cases"][0]["topology_acyclic"])
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}
        self.assertIn("invalid_incomplete_graph_reason", issue_ids)

    def test_noncycle_blocked_payload_with_emitted_graph_is_invalid(self):

        case = {
            "id": "blocked-boundary",
            "category": "sequential",
            "task": "missing scenario",
            "expected_intents": ["alpha"],
            "expected_scenarios": ["s1"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        route = synthetic_route(
            ["alpha"],
            ["s1"],
            graph_status="blocked",
            acyclic=False,
            routing_status="blocked",
            reason_codes=["missing_scenario_bundle"],
        )

        report = evaluate_fixture([case], route_builder=lambda current: route)
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}

        self.assertFalse(report["cases"][0]["dag_valid"])
        self.assertIn("blocked_graph_not_empty", issue_ids)

    def test_cycle_blocked_payload_with_emitted_graph_is_invalid(self):

        case = {
            "id": "blocked-cycle",
            "category": "sequential",
            "task": "cyclic dependency",
            "expected_intents": ["alpha", "beta"],
            "expected_scenarios": ["s1", "s2"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        route = synthetic_route(
            ["alpha", "beta"],
            ["s1", "s2"],
            graph_status="blocked",
            acyclic=False,
            routing_status="blocked",
            reason_codes=["dependency_cycle", "invalid_intent_graph"],
            intent_dependencies=[["i2"], ["i1"]],
        )

        report = evaluate_fixture([case], route_builder=lambda current: route)
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}

        self.assertFalse(report["cases"][0]["dag_valid"])
        self.assertIn("blocked_graph_not_empty", issue_ids)

    def test_real_compiler_missing_scenario_payload_is_invalid_blocked_boundary(self):
        from onecode_skill_sanitizer.compiler import compile_execution_graph
        from onecode_skill_sanitizer.composer import ScenarioComposition, ScenarioSelection
        from onecode_skill_sanitizer.intent import Intent, IntentGraph

        graph = IntentGraph(
            intents=(
                Intent(
                    id="i1",
                    summary="missing scenario",
                    task_type="alpha",
                    required_artifacts=(),
                    risk_flags=(),
                    depends_on=(),
                    source="deterministic",
                    confidence=1.0,
                ),
            ),
            unresolved_dependencies=(),
        )
        composition = ScenarioComposition(
            selections=(ScenarioSelection("missing", ("i1",), 1.0, 1),),
            uncovered_intents=(),
            status="complete",
        )
        compiled = compile_execution_graph(graph, composition, {"bundles": []}, set())
        route = {
            "routing_status": "blocked",
            "intent_graph": {
                "intents": [
                    {"id": "i1", "task_type": "alpha", "depends_on": [], "confidence": 1.0},
                ]
            },
            "selected_scenarios": [{"scenario_id": "missing", "intent_ids": ["i1"]}],
            "selected_skills": [],
            "capability_resolution": {"status": "complete", "capabilities": [], "missing_required_count": 0},
            "execution_graph": compiled,
        }
        case = {
            "id": "real-blocked-boundary",
            "category": "sequential",
            "task": "missing scenario",
            "expected_intents": ["alpha"],
            "expected_scenarios": ["missing"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }

        report = evaluate_fixture([case], route_builder=lambda current: route)

        self.assertEqual(compiled["reason_codes"], ["missing_scenario_bundle"])
        self.assertEqual(compiled["nodes"], [])
        self.assertEqual(compiled["edges"], [])
        self.assertFalse(report["cases"][0]["dag_valid"])
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}
        self.assertIn("invalid_incomplete_graph_reason", issue_ids)

    def test_real_compiler_missing_verification_diagnostic_graph_is_invalid_blocked(self):
        from onecode_skill_sanitizer.compiler import compile_execution_graph
        from onecode_skill_sanitizer.composer import ScenarioComposition, ScenarioSelection
        from onecode_skill_sanitizer.intent import Intent, IntentGraph

        def intent(intent_id: str, depends_on: tuple[str, ...] = ()) -> Intent:
            return Intent(
                id=intent_id,
                summary=intent_id,
                task_type=intent_id,
                required_artifacts=(),
                risk_flags=(),
                depends_on=depends_on,
                source="deterministic",
                confidence=1.0,
            )

        graph = IntentGraph(
            intents=(intent("i1"), intent("i2", ("i1",))),
            unresolved_dependencies=(),
        )
        composition = ScenarioComposition(
            selections=(
                ScenarioSelection("first", ("i1",), 1.0, 1),
                ScenarioSelection("second", ("i2",), 1.0, 1),
            ),
            uncovered_intents=(),
            status="complete",
        )
        bundles = {
            "bundles": [
                {
                    "id": "first",
                    "name": "first",
                    "scenario": "first",
                    "status": "trusted",
                    "task_signals": [],
                    "required_capabilities": [],
                    "execution_order": ["skill-a", "skill-b"],
                    "skills": ["skill-a", "skill-b"],
                    "expected_output": [],
                    "safety_boundary": "method only",
                },
                {
                    "id": "second",
                    "name": "second",
                    "scenario": "second",
                    "status": "trusted",
                    "task_signals": [],
                    "required_capabilities": [],
                    "execution_order": ["execution-publish-check"],
                    "skills": ["execution-publish-check"],
                    "expected_output": [],
                    "safety_boundary": "method only",
                },
            ]
        }
        compiled = compile_execution_graph(
            graph,
            composition,
            bundles,
            {"skill-a", "skill-b", "execution-publish-check"},
        )
        route = {
            "routing_status": "blocked",
            "intent_graph": {
                "intents": [
                    {
                        "id": intent.id,
                        "task_type": intent.task_type,
                        "depends_on": list(intent.depends_on),
                        "confidence": intent.confidence,
                    }
                    for intent in graph.intents
                ]
            },
            "selected_scenarios": [
                {"scenario_id": "first", "intent_ids": ["i1"]},
                {"scenario_id": "second", "intent_ids": ["i2"]},
            ],
            "selected_skills": [],
            "capability_resolution": {"status": "complete", "capabilities": [], "missing_required_count": 0},
            "execution_graph": compiled,
        }
        case = {
            "id": "missing-verification",
            "category": "sequential",
            "task": "missing verification",
            "expected_intents": ["i1", "i2"],
            "expected_scenarios": ["first", "second"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }

        report = evaluate_fixture([case], route_builder=lambda current: route)

        self.assertEqual(compiled["reason_codes"], ["missing_intent_verification"])
        self.assertTrue(compiled["nodes"])
        self.assertTrue(compiled["edges"])
        self.assertEqual({edge["type"] for edge in compiled["edges"]}, {"scenario_order"})
        self.assertFalse(report["cases"][0]["dag_valid"])
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}
        self.assertIn("invalid_incomplete_graph_reason", issue_ids)
        self.assertIn("blocked_graph_not_empty", issue_ids)

    def test_missing_verification_rejects_dependent_intent_edges(self):

        case = {
            "id": "missing-verification",
            "category": "sequential",
            "task": "missing verification",
            "expected_intents": ["alpha", "beta"],
            "expected_scenarios": ["s1", "s2"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        route = synthetic_route(
            ["alpha", "beta"],
            ["s1", "s2"],
            dependency_pairs=[("alpha", "beta")],
            graph_status="blocked",
            acyclic=False,
            routing_status="blocked",
            reason_codes=["missing_intent_verification"],
            intent_dependencies=[[], ["i1"]],
        )

        report = evaluate_fixture([case], route_builder=lambda current: route)
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}

        self.assertFalse(report["cases"][0]["dag_valid"])
        self.assertIn("invalid_incomplete_graph_reason", issue_ids)
        self.assertIn("blocked_graph_not_empty", issue_ids)

    def test_ready_graph_requires_true_flag_and_acyclic_topology(self):
        from onecode_skill_sanitizer.router_eval_v2 import EvaluatorError

        case = {
            "id": "ready",
            "category": "compound",
            "task": "ready",
            "expected_intents": ["alpha"],
            "expected_scenarios": ["s1"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "complete",
        }
        coherent = synthetic_route(["alpha"], ["s1"])
        contradictory = synthetic_route(["alpha"], ["s1"], acyclic=False)

        report = evaluate_fixture([case], route_builder=lambda current: coherent)
        self.assertTrue(report["cases"][0]["dag_valid"])
        with self.assertRaises(EvaluatorError):
            evaluate_fixture([case], route_builder=lambda current: contradictory)

    def test_blocked_graph_requires_blocked_route_and_recognized_reason(self):

        case = {
            "id": "blocked",
            "category": "sequential",
            "task": "blocked",
            "expected_intents": ["alpha"],
            "expected_scenarios": ["s1"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        routes = [
            synthetic_route(
                ["alpha"],
                ["s1"],
                graph_status="blocked",
                routing_status="complete",
                reason_codes=["missing_intent_verification"],
            ),
            synthetic_route(
                ["alpha"],
                ["s1"],
                graph_status="blocked",
                routing_status="blocked",
                reason_codes=[],
            ),
            synthetic_route(
                ["alpha"],
                ["s1"],
                graph_status="blocked",
                routing_status="blocked",
                reason_codes=["invented_reason"],
            ),
        ]

        for route in routes:
            with self.subTest(route=route):
                report = evaluate_fixture([case], route_builder=lambda current: route)
                self.assertFalse(report["cases"][0]["dag_valid"])

    def test_real_command_prints_json_without_failing_on_low_metrics(self):
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "onecode_skill_sanitizer",
                "router-eval-v2",
                "--eval",
                str(EVAL_PATH),
                "--registry",
                str(ROOT / "catalog"),
                "--bundles",
                str(ROOT / "bundles" / "index.json"),
            ],
            cwd=ROOT,
            env={"PYTHONPATH": str(ROOT / "src")},
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["case_count"], 100)
        self.assertFalse(report["quality_gate"]["production_ready"])
        self.assertEqual(
            report["quality_gate"]["failed_gates"],
            ["forbidden_scenario_false_positive_rate", "high_confidence_error_rate"],
        )
        self.assertEqual(
            report["quality_gate"]["missing_gates"],
            ["forbidden_skill_false_positive_rate", "independent_label_review"],
        )
        self.assertEqual(
            report["quality_gate"]["dataset_identity"],
            {
                "case_count": 100,
                "dataset_sha256": report["quality_gate"]["dataset_identity"]["dataset_sha256"],
                "labeling_generated_from_router": False,
                "labeling_method": "manual_review",
                "labeling_reviewed_at": "2026-07-10",
                "labeling_reviewer_role": "independent_dataset_review",
            },
        )
        self.assertRegex(
            report["quality_gate"]["dataset_identity"]["dataset_sha256"],
            r"^sha256:[0-9a-f]{64}$",
        )
        self.assertIsNone(report["quality_gate"]["review_identity"])
        self.assertEqual(report["metrics"]["dag_validity"], 1.0)
        self.assertGreaterEqual(report["metrics"]["dependency_edge_recall"], 0.90)
        self.assertEqual(
            set(report["metrics"]),
            {
                "multi_intent_exact_match",
                "scenario_precision",
                "scenario_recall",
                "scenario_f1",
                "forbidden_scenario_false_positive_rate",
                "dependency_edge_recall",
                "dag_validity",
                "task_type_macro_precision",
                "task_type_macro_recall",
                "task_type_macro_f1",
                "required_capability_recall",
                "forbidden_skill_false_positive_rate",
                "dependency_edge_precision",
                "high_confidence_error_rate",
                "core_bundle_contract_coverage",
            },
        )
        task_type_support = report["counts"]["task_type_by_label"]
        self.assertEqual(
            [item["task_type"] for item in task_type_support],
            sorted(item["task_type"] for item in task_type_support),
        )
        for item in task_type_support:
            for field in ("true_positive", "false_positive", "false_negative"):
                self.assertIs(type(item[field]), int)
                self.assertGreaterEqual(item[field], 0)
        per_label = []
        for item in task_type_support:
            true_positive = item["true_positive"]
            precision_denominator = true_positive + item["false_positive"]
            recall_denominator = true_positive + item["false_negative"]
            precision = true_positive / precision_denominator if precision_denominator else 0.0
            recall = true_positive / recall_denominator if recall_denominator else 0.0
            f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
            per_label.append((precision, recall, f1))
        self.assertTrue(per_label)
        self.assertAlmostEqual(
            report["metrics"]["task_type_macro_precision"],
            sum(item[0] for item in per_label) / len(per_label),
        )
        self.assertAlmostEqual(
            report["metrics"]["task_type_macro_recall"],
            sum(item[1] for item in per_label) / len(per_label),
        )
        self.assertAlmostEqual(
            report["metrics"]["task_type_macro_f1"],
            sum(item[2] for item in per_label) / len(per_label),
        )

    def test_real_command_requires_production_ready_only_when_requested(self):
        base_command = [
            sys.executable,
            "-m",
            "onecode_skill_sanitizer",
            "router-eval-v2",
            "--eval",
            str(EVAL_PATH),
            "--registry",
            str(ROOT / "catalog"),
            "--bundles",
            str(ROOT / "bundles" / "index.json"),
        ]
        normal = subprocess.run(
            base_command,
            cwd=ROOT,
            env={"PYTHONPATH": str(ROOT / "src")},
            capture_output=True,
            text=True,
            check=False,
        )
        completed = subprocess.run(
            [*base_command, "--require-production-ready"],
            cwd=ROOT,
            env={"PYTHONPATH": str(ROOT / "src")},
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(normal.returncode, 0, normal.stderr)
        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertEqual(completed.stdout, normal.stdout)
        report = json.loads(completed.stdout)
        self.assertFalse(report["quality_gate"]["production_ready"])
        self.assertEqual(
            report["quality_gate"]["failed_gates"],
            ["forbidden_scenario_false_positive_rate", "high_confidence_error_rate"],
        )
        self.assertEqual(
            report["quality_gate"]["missing_gates"],
            ["forbidden_skill_false_positive_rate", "independent_label_review"],
        )

    def test_bundle_capability_context_is_deterministic_and_required_only(self):
        from onecode_skill_sanitizer.commands import _bundle_required_capability_context

        bundles = {
            "bundles": [
                {
                    "id": "zeta",
                    "required_capabilities": [
                        {"id": "optional", "required": False, "preferred_skills": ["x"]},
                        {"id": "required-b", "required": True, "preferred_skills": ["x"]},
                    ],
                },
                {
                    "id": "alpha",
                    "required_capabilities": [
                        {"id": "required-a", "required": True, "preferred_skills": ["x"]},
                    ],
                },
            ]
        }

        self.assertEqual(
            _bundle_required_capability_context(bundles),
            {"alpha": ("required-a",), "zeta": ("required-b",)},
        )

    def test_bundle_capability_context_rejects_malformed_or_duplicate_required_capabilities(self):
        from onecode_skill_sanitizer.commands import _bundle_required_capability_context

        malformed = [
            {"bundles": [{"id": "s", "required_capabilities": "bad"}]},
            {"bundles": [{"id": "s", "required_capabilities": [{"id": "c", "required": 1}]}]},
            {
                "bundles": [
                    {
                        "id": "s",
                        "required_capabilities": [
                            {"id": "c", "required": True},
                            {"id": "c", "required": True},
                        ],
                    }
                ]
            },
        ]
        for bundles in malformed:
            with self.subTest(bundles=bundles), self.assertRaises(ValueError):
                _bundle_required_capability_context(bundles)

    def test_command_returns_two_for_schema_errors(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.json"
            path.write_text('{"cases": []}', encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "onecode_skill_sanitizer",
                    "router-eval-v2",
                    "--eval",
                    str(path),
                    "--registry",
                    str(ROOT / "catalog"),
                    "--bundles",
                    str(ROOT / "bundles" / "index.json"),
                ],
                cwd=ROOT,
                env={"PYTHONPATH": str(ROOT / "src")},
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 2)
        json.loads(completed.stdout)

    def test_command_returns_two_for_missing_bundle_catalog(self):
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "onecode_skill_sanitizer",
                "router-eval-v2",
                "--eval",
                str(EVAL_PATH),
                "--registry",
                str(ROOT / "catalog"),
                "--bundles",
                str(ROOT / "bundles" / "missing.json"),
            ],
            cwd=ROOT,
            env={"PYTHONPATH": str(ROOT / "src")},
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 2)
        json.loads(completed.stdout)

    def test_command_uses_catalog_and_bundle_defaults(self):
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "onecode_skill_sanitizer",
                "router-eval-v2",
                "--eval",
                str(EVAL_PATH),
            ],
            cwd=ROOT,
            env={"PYTHONPATH": str(ROOT / "src")},
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertNotEqual(completed.returncode, 2, completed.stdout + completed.stderr)

    def test_evaluator_has_no_label_generation_helper(self):
        import onecode_skill_sanitizer.router_eval_v2 as evaluator

        prohibited = {
            "generate_labels",
            "generate_expected_labels",
            "label_cases_from_router",
        }
        self.assertTrue(prohibited.isdisjoint(dir(evaluator)))


if __name__ == "__main__":
    unittest.main()
