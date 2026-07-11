from __future__ import annotations

import json
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


def bundle_scenario_ids() -> set[str]:
    bundles = json.loads(
        (ROOT / "bundles" / "index.json").read_text(encoding="utf-8")
    )["bundles"]
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
) -> dict:
    intents = [
        {
            "id": f"i{index}",
            "task_type": task_type,
            "depends_on": (intent_dependencies or [[] for _ in intent_types])[index - 1],
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
    node_by_type = {
        intent["task_type"]: nodes[index]
        for index, intent in enumerate(intents)
    }
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
        "selected_scenarios": [
            {"scenario_id": scenario_id, "intent_ids": []}
            for scenario_id in scenarios
        ],
        "execution_graph": {
            "status": graph_status,
            "acyclic": acyclic,
            "nodes": nodes,
            "edges": edges,
            "reason_codes": reason_codes or [],
        },
    }


class RouterEvalV2Tests(unittest.TestCase):
    def test_gold_dataset_has_exact_count_distribution_and_contract(self):
        from onecode_skill_sanitizer.router_eval_v2 import load_eval_dataset_v2

        cases = load_eval_dataset_v2(EVAL_PATH)

        self.assertEqual(len(cases), 100)
        self.assertEqual(Counter(case["category"] for case in cases), EXPECTED_CATEGORIES)
        self.assertEqual(len({case["id"] for case in cases}), 100)

    def test_gold_dataset_has_independent_manual_labeling_metadata(self):
        payload = gold_payload()

        self.assertEqual(payload["labeling"], EXPECTED_LABELING)
        actual_fields = {
            key
            for case in payload["cases"]
            for key in case
            if key.startswith("actual_")
        }
        self.assertEqual(actual_fields, set())
        for case in payload["cases"]:
            for expected_field in (
                "expected_intents",
                "expected_scenarios",
                "required_dependency_edges",
            ):
                copied_field = expected_field.replace("expected_", "actual_").replace(
                    "required_", "actual_"
                )
                self.assertNotIn(copied_field, case)

    def test_gold_dataset_covers_all_bundle_scenarios(self):
        from onecode_skill_sanitizer.router_eval_v2 import load_eval_dataset_v2

        cases = load_eval_dataset_v2(EVAL_PATH)
        scenario_counts = Counter(
            scenario for case in cases for scenario in case["expected_scenarios"]
        )

        self.assertEqual(set(scenario_counts), bundle_scenario_ids())
        self.assertGreaterEqual(min(scenario_counts.values()), 5)

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

        legacy_payload = {
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
                load_eval_dataset_v2(write_payload(temp_dir, legacy_payload))

    def test_loader_rejects_strict_case_contract_violations(self):
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError
        from onecode_skill_sanitizer.router_eval_v2 import load_eval_dataset_v2

        mutations = {
            "duplicate intents": lambda case: case.update(expected_intents=["x", "x"]),
            "empty scenario": lambda case: case.update(expected_scenarios=[""]),
            "unknown scenario": lambda case: case.update(expected_scenarios=["not-known"]),
            "unknown forbidden scenario": lambda case: case.update(
                forbidden_scenarios=["website-build-launc"]
            ),
            "duplicate forbidden": lambda case: case.update(forbidden_scenarios=["x", "x"]),
            "overlap": lambda case: case.update(
                forbidden_scenarios=[case["expected_scenarios"][0]]
            ),
            "duplicate edge": lambda case: case.update(
                expected_intents=["a", "b"],
                required_dependency_edges=[["a", "b"], ["a", "b"]],
            ),
            "self edge": lambda case: case.update(
                expected_intents=["a"], required_dependency_edges=[["a", "a"]]
            ),
            "unknown edge endpoint": lambda case: case.update(
                expected_intents=["a"], required_dependency_edges=[["a", "b"]]
            ),
            "bad status": lambda case: case.update(expected_status="ready"),
            "bad category": lambda case: case.update(category="other"),
            "extra field": lambda case: case.update(actual_intents=[]),
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
        from onecode_skill_sanitizer.router_eval_v2 import evaluate_router_v2

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

        report = evaluate_router_v2(cases, route_builder=lambda case: routes[case["id"]])

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
        from onecode_skill_sanitizer.router_eval_v2 import evaluate_router_v2

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
        report = evaluate_router_v2(
            cases,
            route_builder=lambda case: synthetic_route(["general"], []),
        )

        self.assertEqual(report["metrics"]["scenario_precision"], 1.0)
        self.assertEqual(report["metrics"]["scenario_recall"], 1.0)
        self.assertEqual(report["metrics"]["scenario_f1"], 1.0)
        self.assertEqual(report["metrics"]["dependency_edge_recall"], 1.0)
        self.assertEqual(
            report["metrics"]["forbidden_scenario_false_positive_rate"], 0.0
        )
        json.dumps(report, allow_nan=False)

    def test_unexpected_cycle_is_an_evaluator_error(self):
        from onecode_skill_sanitizer.router_eval_v2 import EvaluatorError
        from onecode_skill_sanitizer.router_eval_v2 import evaluate_router_v2

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
        route["execution_graph"]["edges"] = [
            {"from": "node-1", "to": "node-1", "type": "skill_order"}
        ]

        with self.assertRaises(EvaluatorError):
            evaluate_router_v2([case], route_builder=lambda item: route)

    def test_unexpected_blocked_graph_is_an_evaluator_error_for_nonblocked_case(self):
        from onecode_skill_sanitizer.router_eval_v2 import EvaluatorError
        from onecode_skill_sanitizer.router_eval_v2 import evaluate_router_v2

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
                evaluate_router_v2(
                    [case],
                    route_builder=lambda current: synthetic_route(
                        current["expected_intents"],
                        current["expected_scenarios"],
                        graph_status="blocked",
                        routing_status="blocked",
                    ),
                )

    def test_expected_blocked_case_accepts_blocked_graph_and_scores_ready_as_mismatch(self):
        from onecode_skill_sanitizer.router_eval_v2 import evaluate_router_v2

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
        blocked = evaluate_router_v2(
            [case],
            route_builder=lambda current: {
                **synthetic_route(
                    current["expected_intents"],
                    current["expected_scenarios"],
                    graph_status="blocked",
                    acyclic=False,
                    routing_status="blocked",
                    reason_codes=["missing_intent_verification"],
                ),
                "execution_graph": {
                    "status": "blocked",
                    "acyclic": False,
                    "nodes": [],
                    "edges": [],
                    "reason_codes": ["missing_intent_verification"],
                },
            },
        )
        ready = evaluate_router_v2(
            [case],
            route_builder=lambda current: synthetic_route(
                current["expected_intents"],
                current["expected_scenarios"],
                graph_status="ready",
                routing_status="complete",
            ),
        )

        self.assertTrue(blocked["cases"][0]["dag_valid"])
        self.assertFalse(ready["cases"][0]["dag_valid"])
        self.assertIn(
            "status_mismatch", {issue["id"] for issue in ready["cases"][0]["issues"]}
        )

    def test_coherent_blocked_self_cycle_is_valid_and_records_cyclic_topology(self):
        from onecode_skill_sanitizer.router_eval_v2 import evaluate_router_v2

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

        report = evaluate_router_v2([case], route_builder=lambda current: route)

        self.assertTrue(report["cases"][0]["dag_valid"])
        self.assertTrue(report["cases"][0]["topology_acyclic"])
        self.assertEqual(report["cases"][0]["issues"], [])

    def test_incoherent_blocked_self_cycle_is_invalid_with_flag_issue(self):
        from onecode_skill_sanitizer.router_eval_v2 import evaluate_router_v2

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

        report = evaluate_router_v2([case], route_builder=lambda current: route)
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}

        self.assertFalse(report["cases"][0]["dag_valid"])
        self.assertIn("acyclic_flag_mismatch", issue_ids)

    def test_dependency_cycle_reason_with_acyclic_source_intents_is_invalid(self):
        from onecode_skill_sanitizer.router_eval_v2 import evaluate_router_v2

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

        report = evaluate_router_v2([case], route_builder=lambda current: route)
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}

        self.assertFalse(report["cases"][0]["dag_valid"])
        self.assertIn("dependency_cycle_source_mismatch", issue_ids)

    def test_cyclic_source_with_noncycle_blocking_reason_is_invalid(self):
        from onecode_skill_sanitizer.router_eval_v2 import evaluate_router_v2

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

        report = evaluate_router_v2([case], route_builder=lambda current: route)
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}

        self.assertFalse(report["cases"][0]["dag_valid"])
        self.assertIn("missing_dependency_cycle_reason", issue_ids)

    def test_real_compiler_cyclic_intent_graph_is_valid_blocked(self):
        from onecode_skill_sanitizer.compiler import compile_execution_graph
        from onecode_skill_sanitizer.composer import ScenarioComposition, ScenarioSelection
        from onecode_skill_sanitizer.intent import Intent, IntentGraph
        from onecode_skill_sanitizer.router_eval_v2 import evaluate_router_v2

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
                    {"id": intent.id, "task_type": intent.task_type, "depends_on": list(intent.depends_on)}
                    for intent in graph.intents
                ]
            },
            "selected_scenarios": [],
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

        report = evaluate_router_v2([case], route_builder=lambda current: route)

        self.assertIn("dependency_cycle", compiled["reason_codes"])
        self.assertEqual(compiled["nodes"], [])
        self.assertEqual(compiled["edges"], [])
        self.assertTrue(report["cases"][0]["dag_valid"])

    def test_noncycle_blocked_boundary_allows_empty_acyclic_topology(self):
        from onecode_skill_sanitizer.router_eval_v2 import evaluate_router_v2

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

        report = evaluate_router_v2([case], route_builder=lambda current: route)

        self.assertTrue(report["cases"][0]["dag_valid"])
        self.assertTrue(report["cases"][0]["topology_acyclic"])
        self.assertEqual(report["cases"][0]["issues"], [])

    def test_noncycle_blocked_payload_with_emitted_graph_is_invalid(self):
        from onecode_skill_sanitizer.router_eval_v2 import evaluate_router_v2

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

        report = evaluate_router_v2([case], route_builder=lambda current: route)
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}

        self.assertFalse(report["cases"][0]["dag_valid"])
        self.assertIn("blocked_graph_not_empty", issue_ids)

    def test_cycle_blocked_payload_with_emitted_graph_is_invalid(self):
        from onecode_skill_sanitizer.router_eval_v2 import evaluate_router_v2

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

        report = evaluate_router_v2([case], route_builder=lambda current: route)
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}

        self.assertFalse(report["cases"][0]["dag_valid"])
        self.assertIn("blocked_graph_not_empty", issue_ids)

    def test_real_compiler_missing_scenario_payload_is_valid_blocked_boundary(self):
        from onecode_skill_sanitizer.compiler import compile_execution_graph
        from onecode_skill_sanitizer.composer import ScenarioComposition, ScenarioSelection
        from onecode_skill_sanitizer.intent import Intent, IntentGraph
        from onecode_skill_sanitizer.router_eval_v2 import evaluate_router_v2

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
                    {"id": "i1", "task_type": "alpha", "depends_on": []},
                ]
            },
            "selected_scenarios": [{"scenario_id": "missing", "intent_ids": ["i1"]}],
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

        report = evaluate_router_v2([case], route_builder=lambda current: route)

        self.assertEqual(compiled["reason_codes"], ["missing_scenario_bundle"])
        self.assertEqual(compiled["nodes"], [])
        self.assertEqual(compiled["edges"], [])
        self.assertTrue(report["cases"][0]["dag_valid"])

    def test_real_compiler_missing_verification_diagnostic_graph_is_valid_blocked(self):
        from onecode_skill_sanitizer.compiler import compile_execution_graph
        from onecode_skill_sanitizer.composer import ScenarioComposition, ScenarioSelection
        from onecode_skill_sanitizer.intent import Intent, IntentGraph
        from onecode_skill_sanitizer.router_eval_v2 import evaluate_router_v2

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
                    {"id": intent.id, "task_type": intent.task_type, "depends_on": list(intent.depends_on)}
                    for intent in graph.intents
                ]
            },
            "selected_scenarios": [
                {"scenario_id": "first", "intent_ids": ["i1"]},
                {"scenario_id": "second", "intent_ids": ["i2"]},
            ],
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

        report = evaluate_router_v2([case], route_builder=lambda current: route)

        self.assertEqual(compiled["reason_codes"], ["missing_intent_verification"])
        self.assertTrue(compiled["nodes"])
        self.assertTrue(compiled["edges"])
        self.assertEqual({edge["type"] for edge in compiled["edges"]}, {"scenario_order"})
        self.assertTrue(report["cases"][0]["dag_valid"])

    def test_missing_verification_rejects_dependent_intent_edges(self):
        from onecode_skill_sanitizer.router_eval_v2 import evaluate_router_v2

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

        report = evaluate_router_v2([case], route_builder=lambda current: route)
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}

        self.assertFalse(report["cases"][0]["dag_valid"])
        self.assertIn("blocked_dependent_intent_edges", issue_ids)

    def test_ready_graph_requires_true_flag_and_acyclic_topology(self):
        from onecode_skill_sanitizer.router_eval_v2 import EvaluatorError
        from onecode_skill_sanitizer.router_eval_v2 import evaluate_router_v2

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

        report = evaluate_router_v2([case], route_builder=lambda current: coherent)
        self.assertTrue(report["cases"][0]["dag_valid"])
        with self.assertRaises(EvaluatorError):
            evaluate_router_v2([case], route_builder=lambda current: contradictory)

    def test_blocked_graph_requires_blocked_route_and_recognized_reason(self):
        from onecode_skill_sanitizer.router_eval_v2 import evaluate_router_v2

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
                ["alpha"], ["s1"], graph_status="blocked", routing_status="complete",
                reason_codes=["missing_intent_verification"],
            ),
            synthetic_route(
                ["alpha"], ["s1"], graph_status="blocked", routing_status="blocked",
                reason_codes=[],
            ),
            synthetic_route(
                ["alpha"], ["s1"], graph_status="blocked", routing_status="blocked",
                reason_codes=["invented_reason"],
            ),
        ]

        for route in routes:
            with self.subTest(route=route):
                report = evaluate_router_v2([case], route_builder=lambda current: route)
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
        self.assertEqual(set(report["metrics"]), {
            "multi_intent_exact_match",
            "scenario_precision",
            "scenario_recall",
            "scenario_f1",
            "forbidden_scenario_false_positive_rate",
            "dependency_edge_recall",
            "dag_validity",
        })

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
