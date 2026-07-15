from __future__ import annotations

import copy
import inspect
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from typing import Callable

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
