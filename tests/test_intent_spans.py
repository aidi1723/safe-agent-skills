import unittest

from onecode_skill_sanitizer.intent import (
    DecompositionDiagnostics,
    TaskDecomposition,
    decompose_task_detailed,
)


class IntentSpansTest(unittest.TestCase):
    def test_detailed_decomposition_wraps_existing_strong_clause_behavior(self):
        result = decompose_task_detailed("构建官网，同时审计 skill router")

        self.assertIsInstance(result, TaskDecomposition)
        self.assertIsInstance(result.diagnostics, DecompositionDiagnostics)
        self.assertEqual(
            [intent.task_type for intent in result.intent_graph.intents],
            ["website_build", "skill_router_review"],
        )
        self.assertEqual(result.diagnostics.mode, "strong_clauses")
        self.assertFalse(result.diagnostics.candidate_signal_limit_exceeded)
        self.assertFalse(result.diagnostics.intent_limit_exceeded)

    def test_diagnostics_json_uses_arrays_and_bounded_counts(self):
        result = decompose_task_detailed("审计 skill router")

        self.assertEqual(result.diagnostics.emitted_intent_count, 1)
        self.assertEqual(result.diagnostics.reason_codes, ())
        self.assertIsInstance(result.diagnostics.to_json()["reason_codes"], list)


if __name__ == "__main__":
    unittest.main()
