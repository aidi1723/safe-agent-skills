import unittest

from onecode_skill_sanitizer.intent import (
    DecompositionDiagnostics,
    TaskDecomposition,
    decompose_task_detailed,
)
from onecode_skill_sanitizer import intent_spans, routing_profiles
from onecode_skill_sanitizer.intent_spans import ProfileSignalSpan


GOOD_CASES = [
    (
        "UI design, code review, PDF documents, spreadsheet analysis, SEO article",
        [
            "website_build",
            "code_review",
            "document_knowledge_base",
            "data_analysis",
            "content_seo",
        ],
    ),
    (
        "UI 设计、代码审查、PDF/DOCX 文档、表格分析和 SEO 文章",
        [
            "website_build",
            "code_review",
            "document_knowledge_base",
            "data_analysis",
            "content_seo",
        ],
    ),
    (
        "design system and component states, then review the pull request",
        ["design_md_system_governance", "code_review"],
    ),
]

NEGATIVE_CASES = [
    "Supported files: PDF, DOCX, XLSX, and CSV",
    "The report contains website, SEO, code, and release terminology",
    "Do not build a website, review code, or publish anything",
    "Compare GitHub, YouTube, Reddit, and Bilibili source names",
]


class IntentSpansTest(unittest.TestCase):
    def test_profile_enumeration_matrix_preserves_source_order(self):
        for task, expected_task_types in GOOD_CASES:
            with self.subTest(task=task):
                result = decompose_task_detailed(task)
                self.assertEqual(
                    [intent.task_type for intent in result.intent_graph.intents],
                    expected_task_types,
                )

    def test_non_action_lists_remain_one_intent(self):
        for task in NEGATIVE_CASES:
            with self.subTest(task=task):
                self.assertEqual(len(decompose_task_detailed(task).intent_graph.intents), 1)

    def test_motivating_request_coalesces_capabilities_by_scenario(self):
        result = decompose_task_detailed(
            "优化高频场景：UI 设计、代码审查、浏览器验证、CI 排障、PDF/DOCX 文档、表格分析、SEO，验证后推送 GitHub"
        )

        self.assertEqual(
            [intent.task_type for intent in result.intent_graph.intents],
            [
                "website_build",
                "code_review",
                "document_knowledge_base",
                "data_analysis",
                "content_seo",
                "open_source_release",
            ],
        )
        self.assertEqual(result.diagnostics.mode, "profile_spans")

    def test_same_profile_phrases_merge_and_keep_readable_summary(self):
        result = decompose_task_detailed(
            "UI design and browser verification, code review and CI troubleshooting"
        )

        self.assertEqual(
            [intent.task_type for intent in result.intent_graph.intents],
            ["website_build", "code_review"],
        )
        self.assertEqual(
            [intent.summary for intent in result.intent_graph.intents],
            [
                "UI design and browser verification",
                "code review and CI troubleshooting",
            ],
        )

    def test_merge_same_profile_spans_combines_adjacent_or_overlapping_spans(self):
        spans = (
            ProfileSignalSpan(0, 9, "website_build", "ui design", 4),
            ProfileSignalSpan(5, 29, "website_build", "browser verification", 4),
            ProfileSignalSpan(31, 42, "code_review", "code review", 4),
        )

        self.assertEqual(
            intent_spans.merge_same_profile_spans(spans),
            (
                ProfileSignalSpan(0, 29, "website_build", "ui design / browser verification", 8),
                ProfileSignalSpan(31, 42, "code_review", "code review", 4),
            ),
        )

    def test_signal_matches_preserve_offsets_order_and_short_token_boundaries(self):
        text = "approve PR, then SEO"
        matches = routing_profiles.iter_profile_signal_matches(text)

        self.assertNotIn(
            "pr",
            [item["signal"] for item in routing_profiles.iter_profile_signal_matches("approve")],
        )
        self.assertEqual(
            [(item["start"], item["end"], item["task_type"], item["signal"]) for item in matches],
            [
                (8, 10, "code_review", "pr"),
                (17, 20, "content_seo", "seo"),
            ],
        )

    def test_generic_signals_and_tied_task_types_do_not_create_spans(self):
        report_spans, _, _ = intent_spans.find_profile_signal_spans("report, SEO")
        github_spans, _, _ = intent_spans.find_profile_signal_spans("GitHub, SEO")

        self.assertNotIn("report", [span.signal for span in report_spans])
        self.assertNotIn("open_source_release", [span.task_type for span in github_spans])
        self.assertNotIn("multi_platform_research_discovery", [span.task_type for span in github_spans])

    def test_negated_profile_enumeration_does_not_split(self):
        result = decompose_task_detailed(
            "Do not build a website, perform code review, or write an SEO article"
        )

        self.assertEqual(len(result.intent_graph.intents), 1)

    def test_candidate_signal_limit_is_explicit_and_incomplete(self):
        task = ", ".join(["SEO"] * 129)
        result = decompose_task_detailed(task)

        self.assertTrue(result.diagnostics.candidate_signal_limit_exceeded)
        self.assertEqual(result.diagnostics.observed_candidate_count, 129)
        self.assertEqual(result.diagnostics.reason_codes, ("candidate_signal_limit_exceeded",))
        self.assertEqual(result.diagnostics.status, "incomplete")

    def test_intent_limit_keeps_at_most_twelve_and_is_explicit(self):
        task = ", ".join(
            [
                "landing page",
                "code lifecycle",
                "call graph",
                "copywriting",
                "agentic video",
                "deep interview",
                "multi-platform search",
                "value investing",
                "role library",
                "design tokens",
                "simplex",
                "pull request",
                "prompt injection",
            ]
        )
        result = decompose_task_detailed(task)

        self.assertEqual(len(result.intent_graph.intents), 12)
        self.assertTrue(result.diagnostics.intent_limit_exceeded)
        self.assertEqual(result.diagnostics.reason_codes, ("intent_limit_exceeded",))
        self.assertEqual(result.diagnostics.status, "incomplete")

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
