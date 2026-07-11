import math
import json
import unittest


PRODUCTION_THRESHOLDS = {
    "task_type_macro_f1": ("minimum", 0.90),
    "scenario_f1": ("minimum", 0.88),
    "required_capability_recall": ("minimum", 0.97),
    "forbidden_scenario_false_positive_rate": ("maximum", 0.005),
    "forbidden_skill_false_positive_rate": ("maximum", 0.005),
    "multi_intent_exact_match": ("minimum", 0.80),
    "dag_validity": ("minimum", 1.0),
    "high_confidence_error_rate": ("maximum", 0.02),
    "core_bundle_contract_coverage": ("minimum", 0.80),
    "dependency_edge_recall": ("minimum", 0.90),
}
_DEFAULT = object()


def valid_dataset_identity():
    return {
        "dataset_sha256": f"sha256:{'a' * 64}",
        "case_count": 100,
        "labeling_method": "manual_review",
        "labeling_reviewer_role": "independent_dataset_review",
        "labeling_generated_from_router": False,
        "labeling_reviewed_at": "2026-07-10",
        "suite_id": "router-production-v1",
        "suite_sha256": f"sha256:{'b' * 64}",
    }


def valid_review_identity():
    return {
        "suite_id": "router-production-v1",
        "suite_sha256": f"sha256:{'b' * 64}",
        "reviewed_commit": "c" * 40,
        "rule_author_id": "routing-author",
        "reviewer_id": "independent-reviewer",
        "reviewer_role": "independent_dataset_review",
        "reviewed_at": "2026-07-11T00:00:00Z",
        "decision": "accepted",
        "independence_attestation": True,
        "reviewed_case_count": 100,
        "exceptions_count": 0,
    }


def passing_metrics():
    return {
        name: threshold if direction == "minimum" else 0.0
        for name, (direction, threshold) in PRODUCTION_THRESHOLDS.items()
    }


def supported_counts():
    return {
        "case_count": 100,
        "task_type_label_count": 12,
        "scenario_expected": 120,
        "required_capability_context_available": True,
        "required_capability_total": 130,
        "forbidden_total": 100,
        "forbidden_skill_total": 40,
        "high_confidence_cases": 50,
        "core_bundle_contract_available": True,
        "core_bundle_contract_total": 20,
        "dependency_total": 30,
    }


class RouterQualityGateTests(unittest.TestCase):
    def build(
        self,
        metrics=None,
        support_counts=None,
        dataset_identity=_DEFAULT,
        review_identity=_DEFAULT,
    ):
        from onecode_skill_sanitizer.router_quality_gate import build_quality_gate

        return build_quality_gate(
            passing_metrics() if metrics is None else metrics,
            support_counts=supported_counts() if support_counts is None else support_counts,
            dataset_identity=valid_dataset_identity()
            if dataset_identity is _DEFAULT
            else dataset_identity,
            review_identity=valid_review_identity()
            if review_identity is _DEFAULT
            else review_identity,
        )

    def test_exact_boundaries_pass_without_rounding(self):
        report = self.build()

        self.assertTrue(report["production_ready"])
        self.assertEqual(report["failed_gates"], [])
        self.assertEqual(report["missing_gates"], [])
        self.assertEqual(list(report["metric_gates"]), sorted(PRODUCTION_THRESHOLDS))
        for name, (direction, threshold) in PRODUCTION_THRESHOLDS.items():
            self.assertEqual(
                report["metric_gates"][name],
                {
                    "status": "pass",
                    "value": passing_metrics()[name],
                    "threshold": threshold,
                    "direction": direction,
                },
            )

    def test_below_and_above_boundaries_fail_at_exact_values(self):
        metrics = passing_metrics()
        metrics["task_type_macro_f1"] = math.nextafter(0.90, 0.0)
        metrics["forbidden_skill_false_positive_rate"] = math.nextafter(0.005, 1.0)

        report = self.build(metrics=metrics)

        self.assertFalse(report["production_ready"])
        self.assertEqual(
            report["failed_gates"],
            ["forbidden_skill_false_positive_rate", "task_type_macro_f1"],
        )
        self.assertEqual(report["metric_gates"]["task_type_macro_f1"]["status"], "fail")
        self.assertEqual(
            report["metric_gates"]["forbidden_skill_false_positive_rate"]["status"],
            "fail",
        )

    def test_missing_boolean_nonfinite_and_out_of_range_metrics_are_missing(self):
        invalid_values = [True, False, math.nan, math.inf, -math.inf, -0.01, 1.01, "0.9", None]
        for value in invalid_values:
            with self.subTest(value=value):
                metrics = passing_metrics()
                metrics["scenario_f1"] = value
                report = self.build(metrics=metrics)
                self.assertIn("scenario_f1", report["missing_gates"])
                self.assertEqual(report["metric_gates"]["scenario_f1"]["status"], "missing")
                self.assertIsNone(report["metric_gates"]["scenario_f1"]["value"])
        metrics = passing_metrics()
        del metrics["dag_validity"]
        self.assertIn("dag_validity", self.build(metrics=metrics)["missing_gates"])

    def test_support_counts_fail_closed_for_missing_malformed_and_zero_evidence(self):
        requirements = {
            "case_count": {"multi_intent_exact_match", "dag_validity"},
            "task_type_label_count": {"task_type_macro_f1"},
            "scenario_expected": {"scenario_f1"},
            "required_capability_total": {"required_capability_recall"},
            "forbidden_total": {"forbidden_scenario_false_positive_rate"},
            "forbidden_skill_total": {"forbidden_skill_false_positive_rate"},
            "high_confidence_cases": {"high_confidence_error_rate"},
            "core_bundle_contract_total": {"core_bundle_contract_coverage"},
            "dependency_total": {"dependency_edge_recall"},
        }
        for field, gates in requirements.items():
            for value in (None, True, -1, 0, 1.5, "1"):
                with self.subTest(field=field, value=value):
                    counts = supported_counts()
                    if value is None:
                        del counts[field]
                    else:
                        counts[field] = value
                    report = self.build(support_counts=counts)
                    self.assertTrue(gates.issubset(report["missing_gates"]))
                    for gate in gates:
                        self.assertEqual(report["support_evidence"][gate]["status"], "missing")
                        self.assertEqual(report["metric_gates"][gate]["status"], "missing")

    def test_required_context_flags_must_be_exact_true(self):
        for field, gate in (
            ("required_capability_context_available", "required_capability_recall"),
            ("core_bundle_contract_available", "core_bundle_contract_coverage"),
        ):
            for value in (None, False, 1, "true"):
                with self.subTest(field=field, value=value):
                    counts = supported_counts()
                    if value is None:
                        del counts[field]
                    else:
                        counts[field] = value
                    report = self.build(support_counts=counts)
                    self.assertIn(gate, report["missing_gates"])
                    self.assertEqual(report["support_evidence"][gate]["status"], "missing")

    def test_support_counts_default_to_missing_for_api_compatibility(self):
        from onecode_skill_sanitizer.router_quality_gate import build_quality_gate

        report = build_quality_gate(
            passing_metrics(),
            dataset_identity=valid_dataset_identity(),
            review_identity=valid_review_identity(),
        )

        self.assertFalse(report["production_ready"])
        self.assertEqual(report["missing_gates"], sorted(PRODUCTION_THRESHOLDS))

    def test_malformed_support_values_are_bounded_strict_json(self):
        for value in (object(), math.nan, math.inf, {}, []):
            with self.subTest(value=value):
                counts = supported_counts()
                counts["dependency_total"] = value
                report = self.build(support_counts=counts)
                rendered = json.dumps(report, allow_nan=False)
                self.assertIsInstance(rendered, str)
                self.assertIsNone(
                    report["support_evidence"]["dependency_edge_recall"]["requirements"][
                        "dependency_total"
                    ]
                )

    def test_empty_review_and_invalid_identities_fail_closed_without_nested_objects(self):
        report = self.build(review_identity={})
        self.assertFalse(report["production_ready"])
        self.assertIn("independent_label_review", report["missing_gates"])
        self.assertIsNone(report["review_identity"])

        invalid_identities = [
            None,
            [],
            {"nested": {}},
            {"nested": []},
            {"blank": " "},
            {"null": None},
            {"boolean": True},
            {"nan": math.nan},
            {"infinity": math.inf},
            {1: "bad"},
        ]
        for identity in invalid_identities:
            with self.subTest(identity=identity):
                report = self.build(dataset_identity=identity)
                self.assertIn("dataset_identity", report["missing_gates"])
                self.assertEqual(report["dataset_identity"], {})

    def test_review_identity_requires_strict_independent_acceptance_projection(self):
        invalid_mutations = {
            "arbitrary flat mapping": {"x": "y"},
            "missing field": {key: value for key, value in valid_review_identity().items() if key != "suite_id"},
            "blank suite": {**valid_review_identity(), "suite_id": " "},
            "uppercase suite digest": {**valid_review_identity(), "suite_sha256": f"sha256:{'A' * 64}"},
            "bare suite digest": {**valid_review_identity(), "suite_sha256": "b" * 64},
            "non-string suite digest": {**valid_review_identity(), "suite_sha256": 1},
            "short commit": {**valid_review_identity(), "reviewed_commit": "c" * 39},
            "uppercase commit": {**valid_review_identity(), "reviewed_commit": "C" * 40},
            "non-string commit": {**valid_review_identity(), "reviewed_commit": []},
            "blank author": {**valid_review_identity(), "rule_author_id": ""},
            "same reviewer and author": {
                **valid_review_identity(),
                "reviewer_id": valid_review_identity()["rule_author_id"],
            },
            "wrong reviewer role": {**valid_review_identity(), "reviewer_role": "dataset_review"},
            "junk timestamp": {**valid_review_identity(), "reviewed_at": "yesterday"},
            "non-string timestamp": {**valid_review_identity(), "reviewed_at": None},
            "date without time": {**valid_review_identity(), "reviewed_at": "2026-07-11"},
            "non-UTC timestamp": {**valid_review_identity(), "reviewed_at": "2026-07-11T00:00:00+08:00"},
            "impossible timestamp": {**valid_review_identity(), "reviewed_at": "2026-02-30T00:00:00Z"},
            "rejected decision": {**valid_review_identity(), "decision": "rejected"},
            "false attestation": {**valid_review_identity(), "independence_attestation": False},
            "integer attestation": {**valid_review_identity(), "independence_attestation": 1},
            "zero reviewed cases": {**valid_review_identity(), "reviewed_case_count": 0},
            "boolean reviewed cases": {**valid_review_identity(), "reviewed_case_count": True},
            "negative exceptions": {**valid_review_identity(), "exceptions_count": -1},
            "boolean exceptions": {**valid_review_identity(), "exceptions_count": False},
            "raw review lists": {
                **valid_review_identity(),
                "reviewed_case_ids": ["normal-001"],
                "exceptions": [],
            },
        }

        for label, identity in invalid_mutations.items():
            with self.subTest(label=label):
                report = self.build(review_identity=identity)
                self.assertFalse(report["production_ready"])
                self.assertIn("independent_label_review", report["missing_gates"])
                self.assertIsNone(report["review_identity"])
                self.assertIsInstance(json.dumps(report, allow_nan=False), str)

    def test_dataset_identity_with_non_string_digest_fails_closed(self):
        report = self.build(dataset_identity={**valid_dataset_identity(), "dataset_sha256": 1})

        self.assertFalse(report["production_ready"])
        self.assertIn("dataset_identity", report["missing_gates"])
        self.assertEqual(report["dataset_identity"], {})

    def test_dataset_suite_identity_requires_exact_null_or_bound_pair(self):
        invalid_pairs = [
            (None, f"sha256:{'b' * 64}"),
            ("router-production-v1", None),
            ("", f"sha256:{'b' * 64}"),
            ("router-production-v1", f"sha256:{'B' * 64}"),
        ]

        for suite_id, suite_sha256 in invalid_pairs:
            with self.subTest(suite_id=suite_id, suite_sha256=suite_sha256):
                dataset = {
                    **valid_dataset_identity(),
                    "suite_id": suite_id,
                    "suite_sha256": suite_sha256,
                }
                report = self.build(dataset_identity=dataset)
                self.assertFalse(report["production_ready"])
                self.assertIn("dataset_identity", report["missing_gates"])
                self.assertEqual(report["dataset_identity"], {})

    def test_review_identity_must_bind_to_suite_and_full_dataset_case_count(self):
        legacy_dataset = {
            **valid_dataset_identity(),
            "suite_id": None,
            "suite_sha256": None,
        }
        mismatches = {
            "different suite id": (
                valid_dataset_identity(),
                {**valid_review_identity(), "suite_id": "other-suite"},
            ),
            "different suite hash": (
                valid_dataset_identity(),
                {**valid_review_identity(), "suite_sha256": f"sha256:{'d' * 64}"},
            ),
            "partial reviewed count": (
                valid_dataset_identity(),
                {**valid_review_identity(), "reviewed_case_count": 99},
            ),
            "legacy single file": (legacy_dataset, valid_review_identity()),
        }

        for label, (dataset, review) in mismatches.items():
            with self.subTest(label=label):
                report = self.build(dataset_identity=dataset, review_identity=review)
                self.assertFalse(report["production_ready"])
                self.assertNotIn("dataset_identity", report["missing_gates"])
                self.assertIn("independent_label_review", report["missing_gates"])
                self.assertIsNone(report["review_identity"])

    def test_review_identity_output_is_normalized_copy_of_validated_projection(self):
        review = dict(reversed(list(valid_review_identity().items())))

        report = self.build(review_identity=review)
        review["reviewer_id"] = "changed"

        self.assertTrue(report["production_ready"])
        self.assertEqual(list(report["review_identity"]), sorted(valid_review_identity()))
        self.assertEqual(report["review_identity"]["reviewer_id"], "independent-reviewer")

    def test_all_null_and_partial_null_identities_never_count_as_evidence(self):
        for field, identity, missing_gate in (
            ("dataset_identity", {"dataset": None}, "dataset_identity"),
            (
                "dataset_identity",
                {"dataset": "gold", "reviewed_at": None},
                "dataset_identity",
            ),
            ("review_identity", {"review_id": None}, "independent_label_review"),
            (
                "review_identity",
                {"review_id": "r1", "reviewed_at": None},
                "independent_label_review",
            ),
        ):
            with self.subTest(field=field, identity=identity):
                kwargs = {field: identity}
                report = self.build(**kwargs)
                self.assertFalse(report["production_ready"])
                self.assertIn(missing_gate, report["missing_gates"])
                expected = None if field == "review_identity" else {}
                self.assertEqual(report[field], expected)

    def test_output_identities_are_copies_and_gate_lists_are_sorted(self):
        dataset = valid_dataset_identity()
        review = valid_review_identity()
        report = self.build(dataset_identity=dataset, review_identity=review)
        dataset["dataset_sha256"] = f"sha256:{'d' * 64}"
        review["reviewer_id"] = "changed"
        self.assertEqual(report["dataset_identity"]["dataset_sha256"], f"sha256:{'a' * 64}")
        self.assertEqual(report["review_identity"]["reviewer_id"], "independent-reviewer")
        self.assertEqual(report["failed_gates"], sorted(report["failed_gates"]))
        self.assertEqual(report["missing_gates"], sorted(report["missing_gates"]))


if __name__ == "__main__":
    unittest.main()
