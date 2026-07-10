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
) -> dict:
    intents = [
        {"id": f"i{index}", "task_type": task_type, "depends_on": []}
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

    def test_loader_rejects_incorrect_labeling_metadata(self):
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError
        from onecode_skill_sanitizer.router_eval_v2 import load_eval_dataset_v2

        payload = gold_payload()
        payload["labeling"]["generated_from_router"] = True
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(DatasetValidationError):
                load_eval_dataset_v2(write_payload(temp_dir, payload), bundle_scenario_ids())

    def test_loader_rejects_strict_case_contract_violations(self):
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError
        from onecode_skill_sanitizer.router_eval_v2 import load_eval_dataset_v2

        mutations = {
            "duplicate intents": lambda case: case.update(expected_intents=["x", "x"]),
            "empty scenario": lambda case: case.update(expected_scenarios=[""]),
            "unknown scenario": lambda case: case.update(expected_scenarios=["not-known"]),
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
            "expected_intents": ["alpha"],
            "expected_scenarios": ["s1"],
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
            "expected_intents": ["alpha"],
            "expected_scenarios": ["s1"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        blocked = evaluate_router_v2(
            [case],
            route_builder=lambda current: synthetic_route(
                current["expected_intents"],
                current["expected_scenarios"],
                graph_status="blocked",
                routing_status="blocked",
            ),
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
