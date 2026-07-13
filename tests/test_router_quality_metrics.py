from __future__ import annotations

import math
import unittest


class RouterQualityMetricsTests(unittest.TestCase):
    def test_macro_classification_metrics_match_hand_calculation(self):
        from onecode_skill_sanitizer.router_quality_metrics import macro_classification_metrics

        result = macro_classification_metrics(
            [{"a"}, {"a"}, {"b"}],
            [{"a"}, {"b"}, {"b"}],
        )

        self.assertEqual(result["precision"], 0.75)
        self.assertEqual(result["recall"], 0.75)
        self.assertAlmostEqual(result["f1"], 2 / 3)
        self.assertEqual(
            result["per_label"],
            {
                "a": {
                    "counts": {"true_positive": 1, "false_positive": 0, "false_negative": 1},
                    "precision": 1.0,
                    "recall": 0.5,
                    "f1": 2 / 3,
                },
                "b": {
                    "counts": {"true_positive": 1, "false_positive": 1, "false_negative": 0},
                    "precision": 0.5,
                    "recall": 1.0,
                    "f1": 2 / 3,
                },
            },
        )

    def test_macro_classification_metrics_use_union_and_finite_empty_values(self):
        from onecode_skill_sanitizer.router_quality_metrics import macro_classification_metrics

        empty = macro_classification_metrics([], [])
        actual_only = macro_classification_metrics([set()], [{"actual"}])
        expected_only = macro_classification_metrics([{"expected"}], [set()])

        self.assertEqual(empty, {"precision": 1.0, "recall": 1.0, "f1": 1.0, "per_label": {}})
        self.assertEqual(actual_only["precision"], 0.0)
        self.assertEqual(actual_only["recall"], 0.0)
        self.assertEqual(actual_only["f1"], 0.0)
        self.assertEqual(expected_only["precision"], 0.0)
        self.assertEqual(expected_only["recall"], 0.0)
        self.assertEqual(expected_only["f1"], 0.0)
        self.assertTrue(all(math.isfinite(empty[key]) for key in ("precision", "recall", "f1")))

    def test_macro_classification_metrics_reject_malformed_inputs(self):
        from onecode_skill_sanitizer.router_quality_metrics import macro_classification_metrics

        malformed = [
            ([{"a"}], []),
            ([{"a"}], [["a"]]),
            ([{"a"}], [{""}]),
            ([{"a"}], [{True}]),
        ]
        for expected, actual in malformed:
            with self.subTest(expected=expected, actual=actual), self.assertRaises(ValueError):
                macro_classification_metrics(expected, actual)

    def test_classification_counts_are_frozen_and_exact_nonnegative_integers(self):
        from dataclasses import FrozenInstanceError

        from onecode_skill_sanitizer.router_quality_metrics import ClassificationCounts

        counts = ClassificationCounts(true_positive=1, false_positive=2, false_negative=3)
        self.assertEqual(counts.true_positive, 1)
        with self.assertRaises(FrozenInstanceError):
            counts.true_positive = 2
        for value in (True, 1.0, -1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                ClassificationCounts(true_positive=value)

    def test_finite_ratio_uses_explicit_empty_and_rejects_invalid_numbers(self):
        from onecode_skill_sanitizer.router_quality_metrics import finite_ratio

        self.assertEqual(finite_ratio(3, 4, empty=0.0), 0.75)
        self.assertEqual(finite_ratio(0, 0, empty=1.0), 1.0)
        for numerator, denominator, empty in (
            (True, 1, 0.0),
            (1, True, 0.0),
            (-1, 1, 0.0),
            (2, 1, 0.0),
            (0, 0, float("nan")),
            (0, 0, float("inf")),
            (0, 0, -0.1),
            (0, 0, 1.1),
        ):
            with self.subTest(
                numerator=numerator,
                denominator=denominator,
                empty=empty,
            ), self.assertRaises(ValueError):
                finite_ratio(numerator, denominator, empty=empty)


if __name__ == "__main__":
    unittest.main()
