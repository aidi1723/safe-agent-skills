from __future__ import annotations

import copy
import io
import inspect
import json
import math
import tempfile
import unittest
from collections import Counter
from contextlib import redirect_stdout
from pathlib import Path
from typing import Callable
from unittest import mock

from onecode_skill_sanitizer.need_gate import CAPABILITY_SKILL
from onecode_skill_sanitizer.skill_candidates import HIGH_FREQUENCY_ENTRY_NAMES
from onecode_skill_sanitizer.skill_candidates import HIGH_FREQUENCY_SKILL_NAMES


ROOT = Path(__file__).resolve().parents[1]
EVAL_PATH = ROOT / "evals" / "high-frequency-skill-selection.json"
SRC_PACKAGE = ROOT / "src" / "onecode_skill_sanitizer"

CANDIDATE_NAMES = list(HIGH_FREQUENCY_SKILL_NAMES)
EXPECTED_COHORT = {
    "entry_names": list(HIGH_FREQUENCY_ENTRY_NAMES),
    "candidate_names": list(HIGH_FREQUENCY_SKILL_NAMES),
}
SKILL_CAPABILITIES = {
    skill: capability
    for capability, skill in CAPABILITY_SKILL.items()
    if skill in HIGH_FREQUENCY_SKILL_NAMES
}
EXPECTED_LABELING = {
    "method": "manual_review",
    "reviewer_role": "independent_dataset_review",
    "generated_from_router": False,
    "reviewed_at": "2026-07-15",
    "runtime_examples_visible_during_labeling": False,
}
EXPECTED_CATEGORY_COUNTS = {
    "single_positive": 48,
    "near_miss": 24,
    "no_skill": 16,
    "multi_skill": 16,
    "dependency_conflict": 16,
}
EXPECTED_CASE_KEYS = {
    "id",
    "split",
    "category",
    "query",
    "expected_need",
    "expected_intents",
    "required_skills",
    "allowed_skills",
    "forbidden_skills",
    "expected_dependency_edges",
    "expected_status",
    "expected_reason",
}


def gold_payload() -> dict:
    return json.loads(EVAL_PATH.read_text(encoding="utf-8"))


def case_by_id(payload: dict, case_id: str) -> dict:
    return next(case for case in payload["cases"] if case["id"] == case_id)


def changed(mutator: Callable[[dict], None]) -> dict:
    payload = copy.deepcopy(gold_payload())
    mutator(payload)
    return payload


def write_payload(temp_dir: str, payload: object) -> Path:
    path = Path(temp_dir) / "dataset.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def synthetic_case(
    *,
    case_id: str = "case",
    split: str = "validation",
    category: str = "single_positive",
    expected_need: str = "single",
    expected_intents: list[str] | None = None,
    required_skills: list[str] | None = None,
    allowed_skills: list[str] | None = None,
    forbidden_skills: list[str] | None = None,
    expected_edges: list[list[str]] | None = None,
    expected_status: str = "complete",
    expected_reason: str = "",
) -> dict:
    return {
        "id": case_id,
        "split": split,
        "category": category,
        "query": case_id,
        "expected_need": expected_need,
        "expected_intents": (
            ["code.review"] if expected_intents is None else expected_intents
        ),
        "required_skills": (
            ["code-review-risk"] if required_skills is None else required_skills
        ),
        "allowed_skills": [] if allowed_skills is None else allowed_skills,
        "forbidden_skills": (
            [] if forbidden_skills is None else forbidden_skills
        ),
        "expected_dependency_edges": [] if expected_edges is None else expected_edges,
        "expected_status": expected_status,
        "expected_reason": expected_reason,
    }


def synthetic_route(
    *,
    need: str = "single",
    intents: list[str] | None = None,
    candidates: list[tuple[str, float]] | None = None,
    selected: list[str] | None = None,
    edges: list[tuple[str, str]] | None = None,
    routing_status: str = "complete",
    graph_status: str = "ready",
    acyclic: bool = True,
    clarification_reason: str = "",
    abstention_reason: str = "",
    failure_reason: str = "",
) -> dict:
    candidate_items = (
        [("code-review-risk", 0.9)] if candidates is None else candidates
    )
    selected_names = selected if selected is not None else ["code-review-risk"]
    nodes = [
        {"id": f"skill:{name}", "skill": name}
        for name in selected_names
    ]
    return {
        "routing_status": routing_status,
        "need_decision": {
            "decision": need,
            "required_capabilities": (
                ["code.review"] if intents is None else intents
            ),
        },
        "candidates": [
            {"skill": name, "final_score": score}
            for name, score in candidate_items
        ],
        "selection": {
            "selected_skills": [{"name": name} for name in selected_names],
            "clarification_reason": clarification_reason,
            "abstention_reason": abstention_reason,
            "failure_reason": failure_reason,
        },
        "execution_graph": {
            "status": graph_status,
            "acyclic": acyclic,
            "nodes": nodes,
            "edges": [
                {
                    "from": f"skill:{source}",
                    "to": f"skill:{target}",
                    "type": "explicit_user_order",
                    "evidence": "current_request",
                }
                for source, target in (edges or [])
            ],
            "reason_codes": [],
        },
    }


class RouterEvalV3DatasetTests(unittest.TestCase):
    def assert_payload_rejected(self, payload: object) -> None:
        from onecode_skill_sanitizer.router_eval_v3 import DatasetValidationError
        from onecode_skill_sanitizer.router_eval_v3 import load_eval_dataset_v3

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(DatasetValidationError):
                load_eval_dataset_v3(write_payload(temp_dir, payload))

    def test_evaluator_reuses_canonical_high_frequency_cohort_constants(self):
        from onecode_skill_sanitizer import router_eval_v3

        self.assertIs(
            getattr(router_eval_v3, "HIGH_FREQUENCY_ENTRY_NAMES", None),
            HIGH_FREQUENCY_ENTRY_NAMES,
        )
        self.assertIs(
            getattr(router_eval_v3, "HIGH_FREQUENCY_SKILL_NAMES", None),
            HIGH_FREQUENCY_SKILL_NAMES,
        )
        self.assertNotIn("_CANDIDATE_NAMES", vars(router_eval_v3))

    def test_loader_has_no_implicit_default_dataset_path(self):
        from onecode_skill_sanitizer import router_eval_v3

        self.assertNotIn("HIGH_FREQUENCY_DATASET_PATH", vars(router_eval_v3))
        path_parameter = inspect.signature(router_eval_v3.load_eval_dataset_v3).parameters[
            "path"
        ]
        self.assertIs(path_parameter.default, inspect.Parameter.empty)

    def test_gold_dataset_has_exact_count_distribution_and_balanced_splits(self):
        from onecode_skill_sanitizer.router_eval_v3 import load_eval_dataset_v3

        cases = load_eval_dataset_v3(EVAL_PATH)

        self.assertEqual(len(cases), 120)
        self.assertEqual(
            Counter(case["category"] for case in cases),
            Counter(EXPECTED_CATEGORY_COUNTS),
        )
        self.assertEqual(
            Counter(case["split"] for case in cases),
            Counter({"validation": 60, "final_test": 60}),
        )
        for category, count in EXPECTED_CATEGORY_COUNTS.items():
            with self.subTest(category=category):
                self.assertEqual(
                    Counter(
                        case["split"]
                        for case in cases
                        if case["category"] == category
                    ),
                    Counter({"validation": count // 2, "final_test": count // 2}),
                )

    def test_gold_dataset_has_exact_manual_metadata_and_case_schema(self):
        payload = gold_payload()

        self.assertEqual(
            set(payload), {"schema_version", "cohort", "labeling", "cases"}
        )
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["cohort"], EXPECTED_COHORT)
        self.assertEqual(payload["labeling"], EXPECTED_LABELING)
        self.assertTrue(
            all(set(case) == EXPECTED_CASE_KEYS for case in payload["cases"])
        )

    def test_gold_expected_intents_follow_canonical_required_skill_capabilities(self):
        self.assertEqual(set(SKILL_CAPABILITIES), set(HIGH_FREQUENCY_SKILL_NAMES))
        mismatched_ids = []
        for case in gold_payload()["cases"]:
            expected = [SKILL_CAPABILITIES[skill] for skill in case["required_skills"]]
            if case["expected_intents"] != expected:
                mismatched_ids.append(case["id"])

        self.assertEqual(
            len(mismatched_ids),
            0,
            f"{len(mismatched_ids)} cases use noncanonical expected_intents",
        )

    def test_gold_dataset_has_exact_ids_split_parity_and_unique_queries(self):
        from onecode_skill_sanitizer.router_eval_v3 import load_eval_dataset_v3

        cases = load_eval_dataset_v3(EVAL_PATH)
        expected_ids = {
            *(f"hf-single-{number:03d}" for number in range(1, 49)),
            *(f"hf-near-{number:03d}" for number in range(1, 25)),
            *(f"hf-none-{number:03d}" for number in range(1, 17)),
            *(f"hf-multi-{number:03d}" for number in range(1, 17)),
            *(f"hf-dependency-{number:03d}" for number in range(1, 17)),
        }
        normalized_queries = [
            " ".join(case["query"].casefold().split()) for case in cases
        ]

        self.assertEqual({case["id"] for case in cases}, expected_ids)
        self.assertEqual(len(normalized_queries), len(set(normalized_queries)))
        for case in cases:
            number = int(case["id"].rsplit("-", 1)[1])
            expected_split = "validation" if number % 2 else "final_test"
            self.assertEqual(case["split"], expected_split)

    def test_dataset_filename_is_isolated_from_runtime_modules(self):
        offending = []
        for path in SRC_PACKAGE.glob("*.py"):
            if path.name == "router_eval_v3.py":
                continue
            if "high-frequency-skill-selection.json" in path.read_text(
                encoding="utf-8"
            ):
                offending.append(path.name)

        self.assertEqual(offending, [])

    def test_loader_wraps_missing_and_invalid_json(self):
        from onecode_skill_sanitizer.router_eval_v3 import DatasetValidationError
        from onecode_skill_sanitizer.router_eval_v3 import load_eval_dataset_v3

        with tempfile.TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing.json"
            with self.assertRaises(DatasetValidationError):
                load_eval_dataset_v3(missing)
            invalid = Path(temp_dir) / "invalid.json"
            invalid.write_text("{", encoding="utf-8")
            with self.assertRaises(DatasetValidationError):
                load_eval_dataset_v3(invalid)

    def test_loader_rejects_top_level_schema_cohort_and_labeling_mutations(self):
        self.assert_payload_rejected([])
        mutations = {
            "missing top field": lambda payload: payload.pop("cohort"),
            "unknown top field": lambda payload: payload.__setitem__("extra", True),
            "schema version": lambda payload: payload.__setitem__(
                "schema_version", 2
            ),
            "schema bool": lambda payload: payload.__setitem__("schema_version", True),
            "cohort field": lambda payload: payload["cohort"].__setitem__(
                "candidate_names", list(reversed(CANDIDATE_NAMES))
            ),
            "cohort shape": lambda payload: payload["cohort"].__setitem__(
                "extra", []
            ),
            "labeling value": lambda payload: payload["labeling"].__setitem__(
                "generated_from_router", True
            ),
            "labeling bool as integer": lambda payload: payload["labeling"].__setitem__(
                "generated_from_router", 0
            ),
            "labeling shape": lambda payload: payload["labeling"].pop(
                "runtime_examples_visible_during_labeling"
            ),
        }

        for name, mutator in mutations.items():
            with self.subTest(name=name):
                payload = gold_payload()
                mutator(payload)
                self.assert_payload_rejected(payload)

    def test_loader_rejects_case_field_and_scalar_mutations(self):
        mutations = {
            "missing case field": lambda payload: payload["cases"][0].pop(
                "expected_reason"
            ),
            "unknown case field": lambda payload: payload["cases"][0].__setitem__(
                "actual_skills", []
            ),
            "case is not object": lambda payload: payload["cases"].__setitem__(0, []),
            "empty id": lambda payload: payload["cases"][0].__setitem__("id", " "),
            "noncanonical id": lambda payload: payload["cases"][0].__setitem__(
                "id", "hf-single-999"
            ),
            "empty query": lambda payload: payload["cases"][0].__setitem__(
                "query", "\t"
            ),
            "invalid split": lambda payload: payload["cases"][0].__setitem__(
                "split", "train"
            ),
            "invalid category": lambda payload: payload["cases"][0].__setitem__(
                "category", "other"
            ),
            "invalid need": lambda payload: payload["cases"][0].__setitem__(
                "expected_need", "many"
            ),
            "invalid status": lambda payload: payload["cases"][0].__setitem__(
                "expected_status", "ready"
            ),
            "reason not string": lambda payload: payload["cases"][0].__setitem__(
                "expected_reason", None
            ),
        }

        for name, mutator in mutations.items():
            with self.subTest(name=name):
                self.assert_payload_rejected(changed(mutator))


    def test_metric_math_uses_micro_counts_and_finite_empty_denominators(self):
        from onecode_skill_sanitizer.router_eval_v3 import evaluate_router_v3

        cases = [
            synthetic_case(
                case_id="multi",
                category="multi_skill",
                expected_need="composite",
                expected_intents=["code.review", "code.test"],
                required_skills=["code-review-risk", "code-test-regression"],
                forbidden_skills=["execution-browser-check"],
                expected_edges=[["code-review-risk", "code-test-regression"]],
            ),
            synthetic_case(
                case_id="none",
                category="no_skill",
                expected_need="none",
                expected_intents=[],
                required_skills=[],
                forbidden_skills=["design-ui-review"],
                expected_status="none",
                expected_reason="no_specialized_need",
            ),
        ]
        routes = {
            "multi": synthetic_route(
                need="composite",
                intents=["code.review", "code.test"],
                candidates=[
                    ("code-review-risk", 0.9),
                    ("execution-browser-check", 0.8),
                    ("code-test-regression", 0.7),
                ],
                selected=["code-review-risk", "execution-browser-check"],
            ),
            "none": synthetic_route(
                need="none",
                intents=[],
                candidates=[],
                selected=[],
                routing_status="none",
                abstention_reason="no_specialized_need",
            ),
        }

        report = evaluate_router_v3(
            cases,
            route_builder=lambda case: routes[case["id"]],
        )

        expected = {
            "skill_precision": 0.5,
            "skill_recall": 0.5,
            "skill_f1": 0.5,
            "scenario_f1": 1.0,
            "recall_at_3": 1.0,
            "top_1_accuracy": 1.0,
            "no_skill_accuracy": 1.0,
            "exact_selected_set_accuracy": 0.5,
            "multi_intent_exact_match": 1.0,
            "forbidden_skill_false_positive_rate": 0.5,
            "forbidden_scenario_false_positive_rate": 0.5,
            "dependency_edge_recall": 0.0,
            "dag_validity": 1.0,
        }
        for metric, value in expected.items():
            with self.subTest(metric=metric):
                self.assertEqual(report["metrics"][metric], value)
        json.dumps(report, allow_nan=False)

    def test_acceptance_gate_uses_exact_thresholds_and_rejects_invalid_values(self):
        from onecode_skill_sanitizer.router_eval_v3 import ACCEPTANCE_THRESHOLDS
        from onecode_skill_sanitizer.router_eval_v3 import acceptance_gate

        passing = {
            "forbidden_skill_false_positive_rate": 0.019,
            "forbidden_scenario_false_positive_rate": 0.019,
            "dag_validity": 0.98,
            "dependency_edge_recall": 0.70,
            "multi_intent_exact_match": 0.92,
            "scenario_f1": 0.96,
            "skill_f1": 0.96,
            "recall_at_3": 0.95,
            "top_1_accuracy": 0.90,
            "no_skill_accuracy": 0.90,
            "exact_selected_set_accuracy": 0.85,
        }
        self.assertEqual(
            ACCEPTANCE_THRESHOLDS,
            {
                "forbidden_skill_false_positive_rate": ("lt", 0.02),
                "forbidden_scenario_false_positive_rate": ("lt", 0.02),
                "dag_validity": ("ge", 0.98),
                "dependency_edge_recall": ("ge", 0.70),
                "multi_intent_exact_match": ("ge", 0.92),
                "scenario_f1": ("ge", 0.96),
                "skill_f1": ("ge", 0.96),
                "recall_at_3": ("ge", 0.95),
                "top_1_accuracy": ("ge", 0.90),
                "no_skill_accuracy": ("ge", 0.90),
                "exact_selected_set_accuracy": ("ge", 0.85),
            },
        )
        self.assertEqual(acceptance_gate(passing)["status"], "passed")
        boundary = dict(passing, forbidden_skill_false_positive_rate=0.02)
        self.assertEqual(acceptance_gate(boundary)["status"], "failed")
        for name, value in {
            "missing": None,
            "boolean": True,
            "infinity": math.inf,
            "not-a-number": math.nan,
        }.items():
            with self.subTest(name=name):
                invalid = dict(passing)
                if name == "missing":
                    invalid.pop("skill_f1")
                else:
                    invalid["skill_f1"] = value
                gate = acceptance_gate(invalid)
                self.assertEqual(gate["status"], "failed")
                json.dumps(gate, allow_nan=False)

    def test_evaluator_rejects_malformed_route_records_and_cohort_names(self):
        from onecode_skill_sanitizer.router_eval_v3 import EvaluatorError
        from onecode_skill_sanitizer.router_eval_v3 import evaluate_router_v3

        case = synthetic_case()
        mutations = {
            "route nonobject": lambda route: [],
            "missing need record": lambda route: route.pop("need_decision") or route,
            "missing selection record": lambda route: route.pop("selection") or route,
            "missing graph record": lambda route: route.pop("execution_graph") or route,
            "missing candidates record": lambda route: route.pop("candidates") or route,
            "candidate item nonobject": lambda route: route["candidates"].__setitem__(0, []),
            "candidate name missing": lambda route: route["candidates"][0].pop("skill"),
            "candidate name empty": lambda route: route["candidates"][0].__setitem__("skill", ""),
            "candidate duplicate": lambda route: route["candidates"].append(
                copy.deepcopy(route["candidates"][0])
            ),
            "candidate outside cohort": lambda route: route["candidates"][0].__setitem__(
                "skill", "unknown-skill"
            ),
            "candidate score missing": lambda route: route["candidates"][0].pop("final_score"),
            "candidate score boolean": lambda route: route["candidates"][0].__setitem__(
                "final_score", True
            ),
            "candidate score nonfinite": lambda route: route["candidates"][0].__setitem__(
                "final_score", math.inf
            ),
            "selected list malformed": lambda route: route["selection"].__setitem__(
                "selected_skills", None
            ),
            "selected item nonobject": lambda route: route["selection"][
                "selected_skills"
            ].__setitem__(0, []),
            "selected name missing": lambda route: route["selection"][
                "selected_skills"
            ][0].pop("name"),
            "selected name empty": lambda route: route["selection"][
                "selected_skills"
            ][0].__setitem__("name", ""),
            "selected duplicate": lambda route: route["selection"][
                "selected_skills"
            ].append(copy.deepcopy(route["selection"]["selected_skills"][0])),
            "selected outside cohort": lambda route: route["selection"][
                "selected_skills"
            ][0].__setitem__("name", "unknown-skill"),
            "selected not a candidate": lambda route: route["candidates"].clear(),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                route: object = synthetic_route()
                replacement = mutate(route)
                if name == "route nonobject":
                    route = replacement
                with self.assertRaises(EvaluatorError):
                    evaluate_router_v3([case], route_builder=lambda current, route=route: route)

    def test_evaluator_rejects_malformed_need_status_and_reason_records(self):
        from onecode_skill_sanitizer.router_eval_v3 import EvaluatorError
        from onecode_skill_sanitizer.router_eval_v3 import evaluate_router_v3

        case = synthetic_case()
        mutations = {
            "decision missing": lambda route: route["need_decision"].pop("decision"),
            "decision invalid": lambda route: route["need_decision"].__setitem__(
                "decision", "many"
            ),
            "capabilities malformed": lambda route: route["need_decision"].__setitem__(
                "required_capabilities", None
            ),
            "capability item malformed": lambda route: route["need_decision"].__setitem__(
                "required_capabilities", [False]
            ),
            "capability duplicate": lambda route: route["need_decision"].__setitem__(
                "required_capabilities", ["code.review", "code.review"]
            ),
            "capability unknown": lambda route: route["need_decision"].__setitem__(
                "required_capabilities", ["unknown.capability"]
            ),
            "routing status invalid": lambda route: route.__setitem__(
                "routing_status", "ready"
            ),
            "reason nonstring": lambda route: route["selection"].__setitem__(
                "clarification_reason", []
            ),
            "multiple active reasons": lambda route: route["selection"].update(
                {"clarification_reason": "ambiguous", "failure_reason": "failed"}
            ),
            "none status incoherent": lambda route: route.__setitem__(
                "routing_status", "none"
            ),
            "clarify status incoherent": lambda route: route.__setitem__(
                "routing_status", "clarify"
            ),
            "blocked status incoherent": lambda route: route.__setitem__(
                "routing_status", "blocked"
            ),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                route = synthetic_route()
                mutate(route)
                with self.assertRaises(EvaluatorError):
                    evaluate_router_v3([case], route_builder=lambda current, route=route: route)

    def test_evaluator_rejects_malformed_or_incoherent_execution_graphs(self):
        from onecode_skill_sanitizer.router_eval_v3 import EvaluatorError
        from onecode_skill_sanitizer.router_eval_v3 import evaluate_router_v3

        case = synthetic_case()

        def add_second_skill(route: dict) -> None:
            route["candidates"].append(
                {"skill": "code-test-regression", "final_score": 0.8}
            )
            route["selection"]["selected_skills"].append(
                {"name": "code-test-regression"}
            )
            route["execution_graph"]["nodes"].append(
                {
                    "id": "skill:code-test-regression",
                    "skill": "code-test-regression",
                }
            )

        def add_edge(route: dict, source: str, target: str) -> None:
            route["execution_graph"]["edges"].append(
                {
                    "from": source,
                    "to": target,
                    "type": "explicit_user_order",
                    "evidence": "current_request",
                }
            )

        mutations = {
            "nodes malformed": lambda route: route["execution_graph"].__setitem__(
                "nodes", None
            ),
            "edges malformed": lambda route: route["execution_graph"].__setitem__(
                "edges", None
            ),
            "node nonobject": lambda route: route["execution_graph"]["nodes"].__setitem__(
                0, []
            ),
            "node id malformed": lambda route: route["execution_graph"]["nodes"][
                0
            ].__setitem__("id", ""),
            "node skill malformed": lambda route: route["execution_graph"]["nodes"][
                0
            ].__setitem__("skill", False),
            "node id duplicate": lambda route: route["execution_graph"]["nodes"].append(
                copy.deepcopy(route["execution_graph"]["nodes"][0])
            ),
            "node skill duplicate": lambda route: route["execution_graph"]["nodes"].append(
                {"id": "other-id", "skill": "code-review-risk"}
            ),
            "node skill outside cohort": lambda route: route["execution_graph"]["nodes"][
                0
            ].__setitem__("skill", "unknown-skill"),
            "node skill not selected": lambda route: route["execution_graph"]["nodes"][
                0
            ].__setitem__("skill", "code-test-regression"),
            "edge nonobject": lambda route: route["execution_graph"]["edges"].append([]),
            "edge missing endpoint": lambda route: route["execution_graph"]["edges"].append(
                {"from": "skill:code-review-risk"}
            ),
            "edge unknown endpoint": lambda route: route["execution_graph"]["edges"].append(
                {
                    "from": "skill:code-review-risk",
                    "to": "skill:code-test-regression",
                }
            ),
            "edge self reference": lambda route: add_edge(
                route, "skill:code-review-risk", "skill:code-review-risk"
            ),
            "edge duplicate": lambda route: (
                add_second_skill(route),
                add_edge(
                    route,
                    "skill:code-review-risk",
                    "skill:code-test-regression",
                ),
                add_edge(
                    route,
                    "skill:code-review-risk",
                    "skill:code-test-regression",
                ),
            ),
            "acyclic nonboolean": lambda route: route["execution_graph"].__setitem__(
                "acyclic", 1
            ),
            "acyclic declaration mismatch": lambda route: route["execution_graph"].__setitem__(
                "acyclic", False
            ),
            "graph status invalid": lambda route: route["execution_graph"].__setitem__(
                "status", "complete"
            ),
            "reason codes malformed": lambda route: route["execution_graph"].__setitem__(
                "reason_codes", None
            ),
            "ready graph has reasons": lambda route: route["execution_graph"].__setitem__(
                "reason_codes", ["dependency_cycle"]
            ),
            "unexpected cycle": lambda route: (
                add_second_skill(route),
                add_edge(route, "skill:code-review-risk", "skill:code-test-regression"),
                add_edge(route, "skill:code-test-regression", "skill:code-review-risk"),
                route["execution_graph"].__setitem__("acyclic", False),
            ),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                route = synthetic_route()
                mutate(route)
                with self.assertRaises(EvaluatorError):
                    evaluate_router_v3([case], route_builder=lambda current, route=route: route)

    def test_blocked_route_reason_must_match_the_graph_reason(self):
        from onecode_skill_sanitizer.router_eval_v3 import EvaluatorError
        from onecode_skill_sanitizer.router_eval_v3 import evaluate_router_v3

        route = synthetic_route(
            routing_status="blocked",
            graph_status="blocked",
            acyclic=False,
            failure_reason="explicit_skill_excluded",
        )
        route["execution_graph"].update(
            {
                "nodes": [],
                "edges": [],
                "reason_codes": ["dependency_cycle"],
            }
        )

        with self.assertRaises(EvaluatorError):
            evaluate_router_v3(
                [synthetic_case(expected_status="blocked")],
                route_builder=lambda current: route,
            )

    def test_empty_aggregate_and_grouped_metrics_are_finite(self):
        from onecode_skill_sanitizer.router_eval_v3 import evaluate_router_v3

        empty = evaluate_router_v3([], route_builder=lambda case: synthetic_route())
        success_metrics = {
            "skill_precision",
            "skill_recall",
            "skill_f1",
            "scenario_f1",
            "recall_at_3",
            "top_1_accuracy",
            "mean_reciprocal_rank",
            "no_skill_accuracy",
            "exact_selected_set_accuracy",
            "multi_intent_exact_match",
            "dependency_edge_recall",
            "dag_validity",
            "status_accuracy",
        }
        self.assertTrue(all(empty["metrics"][name] == 1.0 for name in success_metrics))
        self.assertEqual(empty["metrics"]["forbidden_skill_false_positive_rate"], 0.0)
        self.assertEqual(empty["metrics"]["forbidden_scenario_false_positive_rate"], 0.0)
        self.assertEqual(empty["metrics_by_category"], {})
        self.assertEqual(empty["metrics_by_split"], {})
        json.dumps(empty, allow_nan=False)

        cases = [
            synthetic_case(case_id="one", category="single_positive"),
            synthetic_case(case_id="two", category="near_miss"),
        ]
        grouped = evaluate_router_v3(
            cases,
            route_builder=lambda case: synthetic_route(),
        )
        self.assertEqual(
            set(grouped["metrics_by_category"]), {"single_positive", "near_miss"}
        )
        self.assertEqual(set(grouped["metrics_by_split"]), {"validation"})
        json.dumps(grouped, allow_nan=False)

    def test_case_pass_contract_and_redaction_expose_no_labels_or_queries(self):
        from onecode_skill_sanitizer.router_eval_v3 import evaluate_router_v3

        case = synthetic_case(
            case_id="redacted",
            split="final_test",
            expected_reason="",
        )
        case["query"] = "secret held-out request"
        route = synthetic_route(
            need="none",
            intents=[],
            candidates=[],
            selected=[],
            routing_status="none",
            abstention_reason="no_specialized_need",
        )

        report = evaluate_router_v3(
            [case],
            route_builder=lambda current: route,
            redact_expected_labels=True,
        )

        self.assertEqual(
            set(report["cases"][0]),
            {"id", "category", "passed", "failure_dimensions"},
        )
        self.assertFalse(report["cases"][0]["passed"])
        self.assertIn("need_decision", report["cases"][0]["failure_dimensions"])
        self.assertIn("required_skill_recall", report["cases"][0]["failure_dimensions"])
        serialized = json.dumps(report, allow_nan=False)
        for prohibited in ("expected_", "actual_", case["query"]):
            self.assertNotIn(prohibited, serialized)

    def test_cli_registers_required_v3_split_without_changing_v2_defaults(self):
        from onecode_skill_sanitizer.cli import build_parser

        parser = build_parser()
        validation = parser.parse_args(
            [
                "router-eval-v3",
                "--eval",
                "dataset.json",
                "--split",
                "validation",
            ]
        )
        final_test = parser.parse_args(
            [
                "router-eval-v3",
                "--eval",
                "dataset.json",
                "--split",
                "final_test",
            ]
        )
        self.assertEqual(validation.registry, "catalog")
        self.assertEqual(validation.bundles, "bundles/index.json")
        self.assertEqual(validation.routing_examples, "catalog/routing-examples.json")
        self.assertEqual(final_test.split, "final_test")
        with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
            parser.parse_args(["router-eval-v3", "--eval", "dataset.json"])
        with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
            parser.parse_args(
                [
                    "router-eval-v3",
                    "--eval",
                    "dataset.json",
                    "--split",
                    "train",
                ]
            )

        v2 = parser.parse_args(["router-eval-v2", "--eval", "dataset.json"])
        self.assertEqual(v2.registry, "catalog")
        self.assertEqual(v2.bundles, "bundles/index.json")
        self.assertFalse(hasattr(v2, "split"))
        self.assertFalse(hasattr(v2, "routing_examples"))

    def test_v3_command_exit_codes_filter_split_and_redact_final(self):
        from onecode_skill_sanitizer import commands

        cases = [
            synthetic_case(case_id="validation", split="validation"),
            synthetic_case(case_id="held-out", split="final_test"),
        ]

        def run(split: str, acceptance_status: str) -> tuple[int, dict, mock.Mock]:
            args = mock.Mock(
                eval="dataset.json",
                registry="catalog",
                bundles="bundles/index.json",
                routing_examples="catalog/routing-examples.json",
                split=split,
            )
            evaluator = mock.Mock(
                return_value={
                    "status": "ok",
                    "acceptance": {"status": acceptance_status, "checks": []},
                    "cases": [],
                    "metrics": {},
                }
            )
            with (
                mock.patch.object(commands, "load_eval_dataset_v3", return_value=cases),
                mock.patch.object(commands, "evaluate_router_v3", evaluator),
                redirect_stdout(io.StringIO()) as output,
            ):
                return_code = commands.router_eval_v3_command(args)
            return return_code, json.loads(output.getvalue()), evaluator

        passed_code, passed_report, validation_evaluator = run("validation", "passed")
        failed_code, failed_report, final_evaluator = run("final_test", "failed")
        self.assertEqual(passed_code, 0)
        self.assertEqual(failed_code, 1)
        self.assertEqual(passed_report["acceptance"]["status"], "passed")
        self.assertEqual(failed_report["acceptance"]["status"], "failed")
        validation_call = validation_evaluator.call_args
        final_call = final_evaluator.call_args
        self.assertEqual([case["id"] for case in validation_call.args[0]], ["validation"])
        self.assertEqual([case["id"] for case in final_call.args[0]], ["held-out"])
        self.assertFalse(validation_call.kwargs["redact_expected_labels"])
        self.assertTrue(final_call.kwargs["redact_expected_labels"])

        error_args = mock.Mock(
            eval="missing.json",
            registry="catalog",
            bundles="bundles/index.json",
            routing_examples="catalog/routing-examples.json",
            split="validation",
        )
        error_types = (
            commands.RouterEvalV3DatasetValidationError("invalid dataset"),
            commands.RouterEvalV3EvaluatorError("invalid route"),
            OSError("missing asset"),
            ValueError("invalid asset"),
            SystemExit("invalid registry"),
        )
        for error in error_types:
            with self.subTest(error=type(error).__name__), mock.patch.object(
                commands,
                "load_eval_dataset_v3",
                side_effect=error,
            ), redirect_stdout(io.StringIO()) as output:
                self.assertEqual(commands.router_eval_v3_command(error_args), 2)
                payload = json.loads(output.getvalue())
                self.assertEqual(payload["status"], "error")
                json.dumps(payload, allow_nan=False)

    def test_loader_rejects_invalid_string_lists_and_duplicates(self):
        list_fields = (
            "expected_intents",
            "required_skills",
            "allowed_skills",
            "forbidden_skills",
        )
        for field in list_fields:
            with self.subTest(field=field, mutation="not a list"):
                self.assert_payload_rejected(
                    changed(
                        lambda payload, field=field: payload["cases"][0].__setitem__(
                            field, None
                        )
                    )
                )
            with self.subTest(field=field, mutation="empty string item"):
                self.assert_payload_rejected(
                    changed(
                        lambda payload, field=field: payload["cases"][0].__setitem__(
                            field, [""]
                        )
                    )
                )

        duplicate_mutations = {
            "duplicate id": lambda payload: payload["cases"][1].__setitem__(
                "id", payload["cases"][0]["id"]
            ),
            "normalized duplicate query": lambda payload: payload["cases"][1].__setitem__(
                "query", f"  {payload['cases'][0]['query'].upper()}  "
            ),
            "duplicate intent": lambda payload: payload["cases"][0].__setitem__(
                "expected_intents",
                payload["cases"][0]["expected_intents"] * 2,
            ),
            "duplicate required skill": lambda payload: payload["cases"][0].__setitem__(
                "required_skills", payload["cases"][0]["required_skills"] * 2
            ),
            "duplicate allowed skill": lambda payload: case_by_id(
                payload, "hf-dependency-009"
            ).__setitem__("allowed_skills", ["design-ui-review"] * 2),
            "duplicate forbidden skill": lambda payload: case_by_id(
                payload, "hf-near-001"
            ).__setitem__("forbidden_skills", ["codebase-explore-map"] * 2),
        }
        for name, mutator in duplicate_mutations.items():
            with self.subTest(name=name):
                self.assert_payload_rejected(changed(mutator))

    def test_loader_rejects_out_of_cohort_skills_and_forbidden_overlaps(self):
        mutations = {
            "unknown required": lambda payload: payload["cases"][0].__setitem__(
                "required_skills", ["unknown-skill"]
            ),
            "unknown allowed": lambda payload: case_by_id(
                payload, "hf-dependency-009"
            ).__setitem__("allowed_skills", ["unknown-skill"]),
            "unknown forbidden": lambda payload: payload["cases"][0].__setitem__(
                "forbidden_skills", ["unknown-skill"]
            ),
            "required forbidden overlap": lambda payload: payload["cases"][0].__setitem__(
                "forbidden_skills", payload["cases"][0]["required_skills"][:]
            ),
            "allowed forbidden overlap": lambda payload: case_by_id(
                payload, "hf-dependency-009"
            ).__setitem__("forbidden_skills", ["design-ui-review"]),
        }
        for name, mutator in mutations.items():
            with self.subTest(name=name):
                self.assert_payload_rejected(changed(mutator))

    def test_loader_rejects_invalid_dependency_edges(self):
        dependency_id = "hf-dependency-001"
        mutations = {
            "edges not list": lambda payload: case_by_id(
                payload, dependency_id
            ).__setitem__("expected_dependency_edges", None),
            "edge not pair": lambda payload: case_by_id(
                payload, dependency_id
            ).__setitem__("expected_dependency_edges", [["codebase-explore-map"]]),
            "empty endpoint": lambda payload: case_by_id(
                payload, dependency_id
            ).__setitem__("expected_dependency_edges", [["", "code-review-risk"]]),
            "self edge": lambda payload: case_by_id(
                payload, dependency_id
            ).__setitem__(
                "expected_dependency_edges",
                [["codebase-explore-map", "codebase-explore-map"]],
            ),
            "endpoint not required": lambda payload: case_by_id(
                payload, dependency_id
            ).__setitem__(
                "expected_dependency_edges",
                [["codebase-explore-map", "design-ui-review"]],
            ),
            "duplicate edge": lambda payload: case_by_id(
                payload, dependency_id
            ).__setitem__(
                "expected_dependency_edges",
                [["codebase-explore-map", "code-review-risk"]] * 2,
            ),
        }
        for name, mutator in mutations.items():
            with self.subTest(name=name):
                self.assert_payload_rejected(changed(mutator))

    def test_loader_rejects_incoherent_need_status_intents_and_reasons(self):
        mutations = {
            "none status needs none": lambda payload: case_by_id(
                payload, "hf-none-001"
            ).__setitem__("expected_need", "single"),
            "clarify status needs clarify": lambda payload: case_by_id(
                payload, "hf-dependency-009"
            ).__setitem__("expected_need", "none"),
            "complete status needs selection": lambda payload: payload["cases"][0].__setitem__(
                "expected_need", "none"
            ),
            "incomplete status needs selection": lambda payload: case_by_id(
                payload, "hf-dependency-013"
            ).__setitem__("expected_need", "clarify"),
            "single need has one required": lambda payload: payload["cases"][0].__setitem__(
                "required_skills", []
            ),
            "composite need has multiple required": lambda payload: case_by_id(
                payload, "hf-multi-001"
            ).__setitem__("required_skills", ["codebase-explore-map"]),
            "intents match required skills": lambda payload: payload["cases"][0].__setitem__(
                "expected_intents", ["code.review"]
            ),
            "legacy browser capability alias": lambda payload: case_by_id(
                payload, "hf-single-022"
            ).__setitem__("expected_intents", ["execution.browser"]),
            "legacy research capability alias": lambda payload: case_by_id(
                payload, "hf-single-029"
            ).__setitem__("expected_intents", ["research.verify"]),
            "legacy design capability alias": lambda payload: case_by_id(
                payload, "hf-single-036"
            ).__setitem__("expected_intents", ["design.review"]),
            "clarify requires reason": lambda payload: case_by_id(
                payload, "hf-dependency-009"
            ).__setitem__("expected_reason", ""),
            "incomplete requires reason": lambda payload: case_by_id(
                payload, "hf-dependency-013"
            ).__setitem__("expected_reason", ""),
            "blocked requires reason": lambda payload: payload["cases"][0].update(
                {"expected_status": "blocked", "expected_reason": ""}
            ),
        }
        for name, mutator in mutations.items():
            with self.subTest(name=name):
                self.assert_payload_rejected(changed(mutator))

    def test_loader_rejects_case_count_category_count_and_split_balance_mutations(self):
        mutations = {
            "case count": lambda payload: payload["cases"].pop(),
            "category count": lambda payload: payload["cases"][0].__setitem__(
                "category", "near_miss"
            ),
            "overall split balance": lambda payload: payload["cases"][0].__setitem__(
                "split", "final_test"
            ),
            "per category split balance": lambda payload: (
                payload["cases"][0].__setitem__("split", "final_test"),
                case_by_id(payload, "hf-near-002").__setitem__(
                    "split", "validation"
                ),
            ),
        }
        for name, mutator in mutations.items():
            with self.subTest(name=name):
                self.assert_payload_rejected(changed(mutator))


if __name__ == "__main__":
    unittest.main()
