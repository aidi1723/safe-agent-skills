import unittest
from itertools import islice
from unittest.mock import patch

from onecode_skill_sanitizer.intent import (
    DecompositionDiagnostics,
    TaskDecomposition,
    decompose_task_detailed,
)
from onecode_skill_sanitizer import intent_spans, routing_profiles
from onecode_skill_sanitizer.intent_evidence import (
    IntentEvidence,
    bind_intent_evidence,
    source_supports_release_action,
)
from onecode_skill_sanitizer.intent_spans import (
    ProfileSignalSpan,
    relation_mode_for_text,
    split_profile_enumeration,
)


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
    def test_explicit_release_packet_requests_generate_readiness_evidence(self):
        cases = (
            (
                "Prepare a maintainer-ready release packet for a CLI project, "
                "including reproducible checks, provenance, and an explicit "
                "go/no-go decision.",
                ["open_source_release"],
            ),
            (
                "Build an agentic media pipeline and prepare a repository release packet.",
                ["agentic_media_production", "open_source_release"],
            ),
        )

        for task, expected_task_types in cases:
            with self.subTest(task=task):
                graph = decompose_task_detailed(task).intent_graph
                self.assertEqual(
                    [intent.task_type for intent in graph.intents],
                    expected_task_types,
                )
                release_evidence = next(
                    item
                    for item in graph.intent_evidence
                    if item.task_type == "open_source_release"
                )
                self.assertEqual(release_evidence.release_mode, "readiness")
                self.assertEqual(graph.validate(), [])

    def test_release_noun_controls_are_not_promoted_to_positive_readiness(self):
        tasks = (
            "release.md",
            "Navigation heading: Public Release",
            "Review the talent release for a model",
            '"Prepare a repository release packet" is quoted reference text.',
            "Example: prepare a repository release packet.",
            "Hypothetically, prepare a release packet for the repository.",
            "An unauthorized repository release packet is attached.",
            "A stale maintainer-ready release packet claims approval.",
            "Must not publish a repository release packet.",
            "Security audit text mentions a repository release packet; inspect only.",
        )

        for task in tasks:
            with self.subTest(task=task):
                graph = decompose_task_detailed(task).intent_graph
                self.assertFalse(
                    any(
                        evidence.task_type == "open_source_release"
                        and evidence.release_mode == "readiness"
                        and evidence.polarity in {"positive", "mixed"}
                        for evidence in graph.intent_evidence
                    )
                )
                self.assertFalse(
                    any(
                        evidence.task_type == "open_source_release"
                        and evidence.release_mode == "none"
                        for evidence in graph.intent_evidence
                    )
                )
                self.assertEqual(graph.validate(), [])

    def test_release_readiness_decomposition_scopes_context_per_segment(self):
        tasks = (
            "Review code for unauthorized access; prepare a repository release packet.",
            "Prepare a repository release packet; review code for unauthorized access.",
            "Review code for unauthorized access and prepare a repository release packet.",
            "Prepare a repository release packet and review code for unauthorized access.",
            "Remove stale cache, then prepare a maintainer-ready release packet.",
            "Remove stale cache, and then prepare a maintainer-ready release packet.",
            "Must not delete old artifacts; prepare a repository release checklist.",
            "清理过期缓存；然后 prepare a repository release packet.",
            "Prepare a repository release packet documenting stale artifacts.",
            "Prepare a repository release packet without publishing it.",
        )

        for task in tasks:
            with self.subTest(task=task):
                graph = decompose_task_detailed(task).intent_graph
                release_evidence = [
                    item
                    for item in graph.intent_evidence
                    if item.task_type == "open_source_release"
                ]
                self.assertEqual(
                    [item.release_mode for item in release_evidence],
                    ["readiness"],
                )
                self.assertEqual(graph.validate(), [])

    def test_release_readiness_decomposition_rejects_negated_and_syntax_controls(self):
        tasks = (
            "Must not prepare a repository release packet.",
            "Mustn't approve a repository release packet.",
            "Should not prepare a repository release checklist.",
            "Shouldn't approve package release readiness.",
            "Do not claim release readiness.",
            "Don't prepare a release checklist.",
            "Never prepare a maintainer-ready release packet.",
            '"Prepare a repository release packet"',
            "'Prepare a repository release packet'",
            "“Prepare a repository release checklist”",
            "# Release readiness",
            "> Release readiness",
            "- [ ] Prepare a repository release checklist",
            "<h2>Release checklist</h2>",
            "Navigation: Release readiness",
            "Title: Release readiness",
            "Release readiness.md",
            "release_packet.yaml",
            "release-checklist.json",
            "Example: prepare a repository release checklist",
            "- Release checklist",
            "Prepare a talent release packet for a photo shoot",
            "Prepare a model release packet for the photographer",
            "Prepare a content release packet for the campaign",
        )

        for task in tasks:
            with self.subTest(task=task):
                graph = decompose_task_detailed(task).intent_graph
                self.assertFalse(
                    any(
                        item.task_type == "open_source_release"
                        and item.release_mode == "readiness"
                        for item in graph.intent_evidence
                    )
                )
                self.assertFalse(
                    any(
                        item.task_type == "open_source_release"
                        and item.release_mode == "none"
                        for item in graph.intent_evidence
                    )
                )
                self.assertEqual(graph.validate(), [])

    def test_direct_text_helpers_share_exact_scan_boundary(self):
        evidence = IntentEvidence(
            "general", "action", "positive", "none", "single", (), 0
        )
        variants = ((" then", "explicit_sequence"), (" 然后", "explicit_sequence"))
        release_variants = (" publish update", " 发布更新")

        for suffix, expected_mode in variants:
            with self.subTest(suffix=suffix):
                base = "x" * routing_profiles.MAX_SCAN_CHARACTERS
                outside = base + suffix
                exact = "x" * (len(base) - len(suffix)) + suffix
                self.assertEqual(relation_mode_for_text(outside), "single")
                self.assertEqual(relation_mode_for_text(exact), expected_mode)
                self.assertEqual(
                    split_profile_enumeration(outside),
                    split_profile_enumeration(base),
                )
                self.assertEqual(
                    bind_intent_evidence((evidence,), outside),
                    bind_intent_evidence((evidence,), base),
                )
                self.assertEqual(
                    routing_profiles.normalize_task_text(outside),
                    routing_profiles.normalize_task_text(base),
                )
                self.assertEqual(
                    routing_profiles.build_task_profile(outside),
                    routing_profiles.build_task_profile(base),
                )

        for suffix in release_variants:
            with self.subTest(suffix=suffix):
                base = "x" * routing_profiles.MAX_SCAN_CHARACTERS
                outside = base + suffix
                exact = "x" * (len(base) - len(suffix)) + suffix
                self.assertFalse(source_supports_release_action(outside))
                self.assertTrue(source_supports_release_action(exact))
    def test_contains_and_mentions_only_suppress_governance_enumerations(self):
        cases = [
            ("Build a website that contains a dashboard", ["website_build"]),
            ("Review code that contains a security bug", ["code_review"]),
        ]

        for task, expected_task_types in cases:
            with self.subTest(task=task):
                result = decompose_task_detailed(task)
                self.assertEqual(
                    [intent.task_type for intent in result.intent_graph.intents],
                    expected_task_types,
                )
                self.assertEqual(result.diagnostics.status, "complete")

    def test_adversative_boundary_drops_negated_release_before_plus_enumeration(self):
        cases = [
            "Do not publish update, but code review + analyze a spreadsheet",
            "不要发布更新，但是代码审查 + 老板简报",
        ]

        for task in cases:
            with self.subTest(task=task):
                result = decompose_task_detailed(task)
                self.assertEqual(
                    [intent.task_type for intent in result.intent_graph.intents],
                    ["code_review", "data_analysis"],
                )
                self.assertNotIn(
                    "open_source_release",
                    [intent.task_type for intent in result.intent_graph.intents],
                )

    def test_how_to_context_is_local_to_adversative_segment(self):
        negative_cases = [
            "how to push to GitHub + code review",
            "learn how to push to GitHub + code review",
        ]
        positive_cases = [
            "Research how to configure tests, but push changes to GitHub",
            "Write a guide about Git, but push changes to GitHub",
        ]

        for task in negative_cases:
            with self.subTest(task=task):
                result = decompose_task_detailed(task)
                self.assertNotIn(
                    "open_source_release",
                    [intent.task_type for intent in result.intent_graph.intents],
                )
        for task in positive_cases:
            with self.subTest(task=task):
                result = decompose_task_detailed(task)
                self.assertIn(
                    "open_source_release",
                    [intent.task_type for intent in result.intent_graph.intents],
                )

    def test_task_scan_boundary_excludes_tail_relation_markers(self):
        inside = "code review"
        padded = inside + "x" * (routing_profiles.MAX_SCAN_CHARACTERS - len(inside))
        outside = padded + " then publish update; in parallel analyze a spreadsheet"

        base = decompose_task_detailed(padded)
        tailed = decompose_task_detailed(outside)
        self.assertEqual(
            [intent.task_type for intent in tailed.intent_graph.intents],
            [intent.task_type for intent in base.intent_graph.intents],
        )
        self.assertEqual(
            [intent.depends_on for intent in tailed.intent_graph.intents],
            [intent.depends_on for intent in base.intent_graph.intents],
        )

        suffix = " then publish update"
        exact = (
            "code review"
            + "x" * (routing_profiles.MAX_SCAN_CHARACTERS - len("code review") - len(suffix))
            + suffix
        )
        exact_result = decompose_task_detailed(exact)
        self.assertIn(
            "open_source_release",
            [intent.task_type for intent in exact_result.intent_graph.intents],
        )

    def test_decomposition_records_structured_internal_evidence(self):
        result = decompose_task_detailed(
            "代码审查 + 老板简报 + 发布清单"
        )

        evidence = getattr(result.intent_graph, "intent_evidence", ())
        self.assertTrue(evidence)
        self.assertEqual([item.task_type for item in evidence], [
            "code_review",
            "data_analysis",
            "open_source_release",
        ])
        self.assertEqual(evidence[-1].release_mode, "readiness")
        self.assertTrue(all(item.relation_mode == "enumeration" for item in evidence))
        self.assertNotIn("intent_evidence", result.intent_graph.to_json())

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

    def test_labeled_descriptive_lists_remain_one_intent(self):
        cases = [
            "Artifacts: website, pull request, PDF, spreadsheet, SEO",
            "Objects: website, pull request, PDF, spreadsheet, SEO",
            "Terms: website, code review, PDF, spreadsheet, SEO",
            "File list: website, code review, PDF, spreadsheet, SEO",
            "Supported files: website, code review, PDF, spreadsheet, SEO",
            "File types: website, code review, PDF, spreadsheet, SEO",
            "产物：网站、代码审查、PDF、表格、SEO",
            "对象：网站、代码审查、PDF、表格、SEO",
            "术语：网站、代码审查、PDF、表格、SEO",
            "文件列表：网站、代码审查、PDF、表格、SEO",
            "支持的文件：网站、代码审查、PDF、表格、SEO",
            "文件类型：网站、代码审查、PDF、表格、SEO",
        ]

        for task in cases:
            with self.subTest(task=task):
                self.assertEqual(len(decompose_task_detailed(task).intent_graph.intents), 1)

    def test_action_enumeration_with_objects_still_splits(self):
        result = decompose_task_detailed(
            "Build a website, review the pull request, analyze a spreadsheet, write an SEO article"
        )

        self.assertEqual(
            [intent.task_type for intent in result.intent_graph.intents],
            ["website_build", "code_review", "data_analysis", "content_seo"],
        )

    def test_terminology_in_action_sentence_does_not_trigger_list_guard(self):
        result = decompose_task_detailed(
            "Define terminology, build a website, review the pull request"
        )

        self.assertEqual(
            [intent.task_type for intent in result.intent_graph.intents],
            ["website_build", "code_review"],
        )

    def test_file_list_words_later_in_action_sentence_do_not_trigger_guard(self):
        result = decompose_task_detailed(
            "Build a website, review the pull request for the supported file list"
        )

        self.assertEqual(
            [intent.task_type for intent in result.intent_graph.intents],
            ["website_build", "code_review"],
        )

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

    def test_chinese_review_brief_release_enumeration_preserves_source_order(self):
        cases = [
            "代码审查 + 老板简报 + 发布清单",
            "代码审查＋管理层简报＋发布清单",
            "代码审查 ＋ 老板简报 ＋ 发布清单",
            "code review + executive brief + release checklist",
            "code review + management brief + release checklist",
        ]

        for task in cases:
            with self.subTest(task=task):
                self.assertEqual(
                    [
                        intent.task_type
                        for intent in decompose_task_detailed(task).intent_graph.intents
                    ],
                    ["code_review", "data_analysis", "open_source_release"],
                )

    def test_plus_connector_requires_distinct_action_profile_evidence(self):
        cases = [
            "术语：代码审查 + 老板简报 + 发布清单",
            "The description mentions code review + executive brief + release checklist",
            "计算 1 + 2 并报告结果",
            "Calculate 12 + 30 and report the result",
            "code review + 1 + release checklist",
        ]

        for task in cases:
            with self.subTest(task=task):
                self.assertEqual(len(decompose_task_detailed(task).intent_graph.intents), 1)

    def test_brief_and_checklist_are_not_unbounded_profile_aliases(self):
        spans, _, _ = intent_spans.find_profile_signal_spans(
            "website brief + implementation checklist"
        )

        self.assertNotIn("data_analysis", [span.task_type for span in spans])
        self.assertNotIn("open_source_release", [span.task_type for span in spans])

    def test_push_actions_disambiguate_github_as_release_profile_evidence(self):
        cases = [
            "代码审查 + 推送到 GitHub",
            "代码审查 + 推送代码到 GitHub",
            "code review + push changes to GitHub",
            "代码审查 + 发布更新",
            "code review + publish update",
        ]

        for task in cases:
            with self.subTest(task=task):
                result = decompose_task_detailed(task).intent_graph
                self.assertEqual(
                    [intent.task_type for intent in result.intents],
                    ["code_review", "open_source_release"],
                )
                self.assertEqual(result.intents[1].depends_on, ("i1",))

    def test_github_research_context_remains_research_evidence(self):
        result = decompose_task_detailed(
            "multi-platform search on GitHub + code review"
        )

        self.assertEqual(
            [intent.task_type for intent in result.intent_graph.intents],
            ["multi_platform_research_discovery", "code_review"],
        )
        github_only, _, _ = intent_spans.find_profile_signal_spans("GitHub + code review")
        self.assertNotIn(
            "open_source_release", [span.task_type for span in github_only]
        )

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

    def test_unicode_case_expansion_preserves_original_offsets_and_summaries(self):
        result = decompose_task_detailed("İİİİİ landing page, code review")

        self.assertEqual(
            [intent.task_type for intent in result.intent_graph.intents],
            ["website_build", "code_review"],
        )
        self.assertIn("landing page", result.intent_graph.intents[0].summary)
        self.assertIn("code review", result.intent_graph.intents[1].summary)

    def test_unmatched_connector_local_requirement_attaches_to_preceding_intent(self):
        result = decompose_task_detailed(
            "Build a landing page, with dark mode, and analyze a spreadsheet"
        )

        self.assertEqual(
            [intent.task_type for intent in result.intent_graph.intents],
            ["website_build", "data_analysis"],
        )
        self.assertIn("dark mode", result.intent_graph.intents[0].summary)
        self.assertIn("spreadsheet", result.intent_graph.intents[1].summary)

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

    def test_coordinated_negation_propagates_across_conjunctions(self):
        cases = [
            "Build a website, do not perform code review or write an SEO article",
            "构建网站，不要代码审查和SEO文章",
        ]

        for task in cases:
            with self.subTest(task=task):
                task_types = [
                    intent.task_type
                    for intent in decompose_task_detailed(task).intent_graph.intents
                ]
                self.assertNotIn("code_review", task_types)
                self.assertNotIn("content_seo", task_types)
                self.assertIn("website_build", task_types)

    def test_negation_scope_stops_at_new_comma_delimited_action(self):
        result = decompose_task_detailed(
            "Build a website, do not perform code review or write an SEO article, analyze a spreadsheet"
        )

        self.assertEqual(
            [intent.task_type for intent in result.intent_graph.intents],
            ["website_build", "data_analysis"],
        )

    def test_comma_or_continues_coordinated_negation(self):
        cases = [
            "Build a website, do not perform code review, or write an SEO article",
            "构建网站，不要代码审查，或写SEO文章",
        ]

        for task in cases:
            with self.subTest(task=task):
                self.assertEqual(
                    [
                        intent.task_type
                        for intent in decompose_task_detailed(task).intent_graph.intents
                    ],
                    ["website_build"],
                )

    def test_adversative_connector_starts_new_positive_action(self):
        cases = [
            "Build a website, do not perform code review but analyze a spreadsheet",
            "构建网站，不要代码审查但要分析表格",
            "构建网站，不要代码审查但是分析表格",
        ]

        for task in cases:
            with self.subTest(task=task):
                self.assertEqual(
                    [
                        intent.task_type
                        for intent in decompose_task_detailed(task).intent_graph.intents
                    ],
                    ["website_build", "data_analysis"],
                )

    def test_additional_chinese_negators_have_bounded_scope(self):
        for negator in ["不做", "不需要"]:
            task = f"构建网站，{negator}代码审查，分析表格"
            with self.subTest(task=task):
                self.assertEqual(
                    [
                        intent.task_type
                        for intent in decompose_task_detailed(task).intent_graph.intents
                    ],
                    ["website_build", "data_analysis"],
                )

    def test_candidate_signal_limit_is_explicit_and_incomplete(self):
        task = ", ".join(["SEO"] * 129)
        result = decompose_task_detailed(task)

        self.assertTrue(result.diagnostics.candidate_signal_limit_exceeded)
        self.assertEqual(result.diagnostics.observed_candidate_count, 129)
        self.assertEqual(result.diagnostics.reason_codes, ("candidate_signal_limit_exceeded",))
        self.assertEqual(result.diagnostics.status, "incomplete")

    def test_signal_iteration_is_lazy_and_span_collection_stops_at_129(self):
        task = ", ".join(["SEO"] * 10000)
        matches = routing_profiles.iter_profile_signal_matches(task)

        self.assertNotIsInstance(matches, list)
        self.assertEqual(len(list(islice(matches, 3))), 3)

        yielded = 0
        real_iterator = routing_profiles.iter_profile_signal_matches

        def instrumented_iterator(text):
            nonlocal yielded
            for match in real_iterator(text):
                yielded += 1
                yield match

        with patch.object(
            intent_spans,
            "iter_profile_signal_matches",
            side_effect=instrumented_iterator,
        ):
            _, observed, exceeded = intent_spans.find_profile_signal_spans(task)

        self.assertEqual(observed, 129)
        self.assertTrue(exceeded)
        self.assertEqual(yielded, 129)

    def test_large_input_constructs_at_most_129_match_records(self):
        configured_signals = []
        for profile in routing_profiles.SCENARIO_PROFILES:
            configured_signals.extend(profile["signals"])
            configured_signals.extend(
                routing_profiles.PROFILE_SIGNAL_ALIASES.get(profile["task_type"], ())
            )
        task = ", ".join(configured_signals * 20)
        constructed = 0
        real_constructor = routing_profiles._profile_signal_match_item

        def instrumented_constructor(*args, **kwargs):
            nonlocal constructed
            constructed += 1
            return real_constructor(*args, **kwargs)

        with patch.object(
            routing_profiles,
            "_profile_signal_match_item",
            side_effect=instrumented_constructor,
        ):
            _, observed, exceeded = intent_spans.find_profile_signal_spans(task)

        self.assertEqual(observed, 129)
        self.assertTrue(exceeded)
        self.assertLessEqual(constructed, 129)

    def test_no_match_scan_attempts_and_diagnostics_are_bounded(self):
        class CountingText(str):
            scan_attempts = 0

            def lower(self):
                return self

            def __getitem__(self, key):
                value = super().__getitem__(key)
                return type(self)(value) if isinstance(key, slice) else value

            def __iter__(self):
                for character in super().__iter__():
                    type(self).scan_attempts += 1
                    yield character

        text = CountingText("x" * 25001)

        self.assertEqual(list(routing_profiles.iter_profile_signal_matches(text)), [])
        self.assertLessEqual(CountingText.scan_attempts, 20000)

        result = decompose_task_detailed(str(text))
        self.assertEqual(result.diagnostics.reason_codes, ("task_scan_limit_exceeded",))
        self.assertEqual(result.diagnostics.status, "incomplete")

    def test_scan_limit_is_global_across_strong_clauses(self):
        task = f"{'x' * 10001}; {'y' * 10001}, landing page, code review"
        result = decompose_task_detailed(task)

        self.assertNotIn(
            "website_build",
            [intent.task_type for intent in result.intent_graph.intents],
        )
        self.assertNotIn(
            "code_review",
            [intent.task_type for intent in result.intent_graph.intents],
        )
        self.assertIn("task_scan_limit_exceeded", result.diagnostics.reason_codes)

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
