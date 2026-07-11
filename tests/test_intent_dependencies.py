import dataclasses
import unittest
from unittest.mock import patch

from onecode_skill_sanitizer import intent as intent_module
from onecode_skill_sanitizer.intent import Intent, decompose_task
from onecode_skill_sanitizer.intent_evidence import (
    IntentEvidence,
    bind_intent_evidence,
)
from onecode_skill_sanitizer.intent_dependencies import (
    IntentRelation,
    apply_intent_relations,
    infer_intent_relations,
)


class IntentDependenciesTest(unittest.TestCase):
    def test_nonempty_evidence_inference_parses_canonical_source_once(self):
        source = "code review then build a website"
        graph = decompose_task(source)

        with patch.object(
            intent_module,
            "_parse_bounded_intent_source",
            wraps=intent_module._parse_bounded_intent_source,
        ) as parser:
            relations = infer_intent_relations(
                source, graph.intents, graph.intent_evidence
            )

        self.assertEqual(relations, graph.dependency_relations)
        self.assertEqual(parser.call_count, 1)

    def test_approval_release_variants_have_one_canonical_release_gate(self):
        tasks = (
            "在 PR 审批通过后发布更新",
            "在PR审批通过后发布更新",
            "在 PR 审批通过后，发布更新",
            "After the PR is approved, publish update",
            "After the PR is approved，publish update",
            "After PR approval, publish update",
        )

        for task in tasks:
            with self.subTest(task=task):
                graph = decompose_task(task)
                self.assertEqual(
                    [item.task_type for item in graph.intents],
                    ["code_review", "open_source_release"],
                )
                self.assertEqual(
                    [item.depends_on for item in graph.intents], [(), ("i1",)]
                )
                self.assertEqual(
                    graph.dependency_relations,
                    (IntentRelation("i1", "i2", "release_gate", True),),
                )
                self.assertEqual(
                    [item.gate_mode for item in graph.intent_evidence],
                    ["verification", "none"],
                )
                self.assertEqual(graph.intent_evidence[1].release_mode, "action")
                self.assertEqual(graph.validate(), [])
    def test_direct_relation_inference_ignores_markers_after_scan_boundary(self):
        intents = (
            self.intent("i1", "review code"),
            self.intent("i2", "build website"),
        )
        text = "x" * 20_000 + " then"

        self.assertEqual(infer_intent_relations(text, intents), ())

    def test_unordered_bullets_remain_parallel_but_numbered_steps_chain(self):
        unordered = decompose_task("- code review\n- build a website")
        numbered = decompose_task("1. code review\n2. build a website")

        self.assertEqual(
            [intent.depends_on for intent in unordered.intents], [(), ()]
        )
        self.assertEqual(
            [intent.depends_on for intent in numbered.intents], [(), ("i1",)]
        )

    def test_mixed_sequence_only_chains_intents_before_parallel_scope(self):
        graph = decompose_task(
            "first code review, then build a website; "
            "in parallel analyze a spreadsheet"
        )

        self.assertEqual(
            [intent.depends_on for intent in graph.intents],
            [(), ("i1",), ()],
        )
        self.assertEqual(
            [item.relation_mode for item in graph.intent_evidence],
            ["explicit_sequence", "explicit_sequence", "parallel"],
        )

    def test_plain_plus_cannot_forge_explicit_relation_metadata(self):
        graph = decompose_task("code review + analyze a spreadsheet")
        forged = tuple(
            dataclasses.replace(item, relation_mode="explicit_sequence")
            for item in graph.intent_evidence
        )
        forged = bind_intent_evidence(
            forged, "code review + analyze a spreadsheet"
        )
        forged_graph = dataclasses.replace(graph, intent_evidence=forged)

        self.assertTrue(forged_graph.validate())
        self.assertEqual(
            infer_intent_relations(
                "code review + analyze a spreadsheet",
                forged_graph.intents,
                forged,
            ),
            (),
        )

    def test_malformed_structured_evidence_fails_closed_without_relations(self):
        intents = (
            self.intent("i1", "review code", "code_review"),
            self.intent("i2", "publish update", "open_source_release"),
        )
        malformed = (
            IntentEvidence(
                "code_review", "invalid", "positive", "none", "enumeration", (), 2
            ),
            IntentEvidence(
                "open_source_release",
                "action",
                "positive",
                "action",
                "enumeration",
                ("publish update",),
                4,
            ),
        )

        self.assertEqual(
            infer_intent_relations(
                "code review + publish update", intents, malformed
            ),
            (),
        )

    def test_infers_first_then_and_chinese_first_then(self):
        cases = [
            (
                "first analyze the spreadsheet, then write the SEO article",
                (
                    self.intent("i1", "first analyze the spreadsheet"),
                    self.intent("i2", "write the SEO article"),
                ),
            ),
            (
                "先做短视频脚本，再接入 agentic media workflow",
                (
                    self.intent("i1", "先做短视频脚本"),
                    self.intent("i2", "再接入 agentic media workflow"),
                ),
            ),
        ]

        for text, intents in cases:
            with self.subTest(text=text):
                self.assertEqual(
                    infer_intent_relations(text, intents),
                    (IntentRelation("i1", "i2", "first_then"),),
                )

    def test_semicolon_steps_chain_in_source_order(self):
        intents = (
            self.intent("i1", "Review the PR", "code_review"),
            self.intent("i2", "build the website", "website_build"),
            self.intent("i3", "prepare an open-source release", "open_source_release"),
        )

        self.assertEqual(
            infer_intent_relations(
                "Review the PR; build the website; prepare an open-source release",
                intents,
            ),
            (
                IntentRelation("i1", "i2", "semicolon_sequence"),
                IntentRelation("i1", "i3", "release_gate", True),
                IntentRelation("i2", "i3", "release_gate", True),
            ),
        )

    def test_unrelated_semicolon_compound_remains_parallel(self):
        graph = decompose_task(
            "Prepare a value-investing memo with a bear case; "
            "govern the expert agent role library"
        )

        self.assertEqual(
            [intent.task_type for intent in graph.intents],
            ["investment_research_diligence", "agent_role_library_governance"],
        )
        self.assertEqual([intent.depends_on for intent in graph.intents], [(), ()])

    def test_semicolon_transition_is_consistent_with_or_without_third_stage(self):
        cases = [
            "Analyze the spreadsheet; write an SEO article",
            "Analyze the spreadsheet; write an SEO article; produce a short video",
        ]

        for task in cases:
            with self.subTest(task=task):
                graph = decompose_task(task)
                self.assertEqual(graph.intents[1].depends_on, ("i1",))

    def test_parallel_marker_suppresses_ordered_nonrelease_relations(self):
        intents = (
            self.intent("i1", "review code"),
            self.intent("i2", "analyze the spreadsheet"),
            self.intent("i3", "draft an SEO article"),
        )
        for text in [
            "In parallel: review code; analyze the spreadsheet; draft an SEO article",
            "并行做代码审查；表格分析；SEO 文章",
            "同时做 UI 设计、代码审查和表格分析",
        ]:
            with self.subTest(text=text):
                self.assertEqual(infer_intent_relations(text, intents), ())

    def test_parallel_scope_does_not_erase_preceding_explicit_sequence(self):
        cases = [
            "First review the PR, then build the website; in parallel, analyze the spreadsheet",
            "先做代码审查，再构建官网；同时分析表格",
        ]

        for task in cases:
            with self.subTest(task=task):
                graph = decompose_task(task)
                self.assertEqual(
                    [intent.task_type for intent in graph.intents],
                    ["code_review", "website_build", "data_analysis"],
                )
                self.assertEqual(
                    [intent.depends_on for intent in graph.intents],
                    [(), ("i1",), ()],
                )

    def test_plain_enumeration_order_does_not_imply_relations(self):
        intents = (
            self.intent("i1", "review code"),
            self.intent("i2", "analyze spreadsheet"),
            self.intent("i3", "write article"),
        )

        self.assertEqual(
            infer_intent_relations(
                "review code, analyze spreadsheet, and write article", intents
            ),
            (),
        )

    def test_before_and_completion_gate_orientation(self):
        cases = [
            (
                "Govern the role library before planning the multi-agent workflow",
                (
                    self.intent("i1", "Govern the role library"),
                    self.intent("i2", "planning the multi-agent workflow"),
                ),
                IntentRelation("i1", "i2", "before"),
            ),
            (
                "After reviewing the PR, build the website",
                (
                    self.intent("i1", "reviewing the PR"),
                    self.intent("i2", "build the website"),
                ),
                IntentRelation("i1", "i2", "completion_gate"),
            ),
            (
                "Build the website after completing the PR review",
                (
                    self.intent("i1", "Build the website"),
                    self.intent("i2", "completing the PR review"),
                ),
                IntentRelation("i2", "i1", "completion_gate"),
            ),
        ]

        for text, intents, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(infer_intent_relations(text, intents), (expected,))

    def test_before_orientation_through_decomposition(self):
        cases = [
            (
                "Before building the website, review the PR",
                ["website_build", "code_review"],
                [("i2",), ()],
            ),
            (
                "Review the PR before building the website",
                ["code_review", "website_build"],
                [(), ("i1",)],
            ),
            (
                "构建官网前，先做代码审查",
                ["website_build", "code_review"],
                [("i2",), ()],
            ),
            (
                "做代码审查先于构建官网",
                ["code_review", "website_build"],
                [(), ("i1",)],
            ),
        ]

        for text, task_types, dependencies in cases:
            with self.subTest(text=text):
                graph = decompose_task(text)
                self.assertEqual(
                    [intent.task_type for intent in graph.intents], task_types
                )
                self.assertEqual(
                    [intent.depends_on for intent in graph.intents], dependencies
                )

    def test_after_completion_splits_and_reverses_dependency(self):
        graph = decompose_task("Build the website after completing the PR review")

        self.assertEqual(
            [intent.task_type for intent in graph.intents],
            ["website_build", "code_review"],
        )
        self.assertEqual(
            [intent.depends_on for intent in graph.intents], [("i2",), ()]
        )

    def test_target_first_verification_splits_reverses_and_marks_gate(self):
        graph = decompose_task("Build the website after verification of the PR")

        self.assertEqual(
            [intent.task_type for intent in graph.intents],
            ["website_build", "code_review"],
        )
        self.assertEqual(
            [intent.depends_on for intent in graph.intents], [("i2",), ()]
        )
        relation = graph.dependency_relations[0]
        self.assertEqual((relation.source_id, relation.target_id), ("i2", "i1"))
        self.assertTrue(relation.requires_verification)

    def test_target_first_approval_splits_reverses_and_marks_gate(self):
        cases = [
            "Build the website after approval of the PR",
            "Build the website after the PR is approved",
            "构建官网在 PR 审批通过后",
            "构建官网在PR审批通过后",
            "构建官网在拉取请求审批通过后",
        ]

        for task in cases:
            with self.subTest(task=task):
                graph = decompose_task(task)
                self.assertEqual(
                    [intent.task_type for intent in graph.intents],
                    ["website_build", "code_review"],
                )
                self.assertEqual(
                    [intent.depends_on for intent in graph.intents],
                    [("i2",), ()],
                )
                relation = graph.dependency_relations[0]
                self.assertEqual(
                    (relation.source_id, relation.target_id), ("i2", "i1")
                )
                self.assertTrue(relation.requires_verification)

    def test_verification_gate_precedes_semicolon_inference(self):
        cases = [
            "After verifying the PR; build the website",
            "PR 验证通过后；构建官网",
        ]

        for task in cases:
            with self.subTest(task=task):
                graph = decompose_task(task)
                self.assertEqual(
                    [intent.depends_on for intent in graph.intents], [(), ("i1",)]
                )
                self.assertEqual(len(graph.dependency_relations), 1)
                self.assertTrue(
                    graph.dependency_relations[0].requires_verification
                )

    def test_approval_gates_require_verification(self):
        cases = [
            "After the PR is approved, build the website",
            "PR 审批通过后，构建官网",
        ]

        for task in cases:
            with self.subTest(task=task):
                graph = decompose_task(task)
                self.assertEqual(
                    [intent.depends_on for intent in graph.intents], [(), ("i1",)]
                )
                self.assertTrue(
                    graph.dependency_relations[0].requires_verification
                )

    def test_later_parallel_verification_does_not_contaminate_completion_relation(self):
        graph = decompose_task(
            "After completing the PR review, build the website; "
            "in parallel, verify the spreadsheet"
        )

        self.assertEqual(
            [intent.task_type for intent in graph.intents],
            ["code_review", "website_build", "data_analysis"],
        )
        self.assertEqual(
            [intent.depends_on for intent in graph.intents], [(), ("i1",), ()]
        )
        self.assertFalse(graph.dependency_relations[0].requires_verification)

    def test_before_publishing_website_is_ordering_not_release(self):
        for task in [
            "Review the PR before publishing the website",
            "Review the PR before publishing our website",
            "Review the PR before publishing a website",
            "Review the PR before publishing the site",
        ]:
            with self.subTest(task=task):
                graph = decompose_task(task)
                self.assertEqual(
                    [intent.task_type for intent in graph.intents],
                    ["code_review", "website_build"],
                )
                self.assertEqual(
                    [intent.depends_on for intent in graph.intents], [(), ("i1",)]
                )
                self.assertTrue(
                    all(
                        intent.task_type != "open_source_release"
                        for intent in graph.intents
                    )
                )

    def test_first_then_release_preserves_the_preceding_action(self):
        cases = [
            "先审查代码，再发布更新",
            "first review the PR, then publish the update",
        ]

        for text in cases:
            with self.subTest(text=text):
                graph = decompose_task(text)
                self.assertEqual(
                    [intent.task_type for intent in graph.intents],
                    ["code_review", "open_source_release"],
                )
                self.assertEqual(
                    [intent.depends_on for intent in graph.intents], [(), ("i1",)]
                )

    def test_repeated_then_chains_nonrelease_steps_before_release(self):
        graph = decompose_task(
            "Review the pull request and regression tests, then map the code "
            "lifecycle change, then release the verified package"
        )

        self.assertEqual(
            [intent.task_type for intent in graph.intents],
            ["code_review", "codebase_change_lifecycle", "open_source_release"],
        )
        self.assertEqual(
            [intent.depends_on for intent in graph.intents],
            [(), ("i1",), ("i1", "i2")],
        )

    def test_release_depends_on_every_explicitly_preceding_path(self):
        intents = (
            self.intent("i1", "analyze data", "data_analysis"),
            self.intent("i2", "write article", "content_seo"),
            self.intent("i3", "publish update", "open_source_release"),
        )

        self.assertEqual(
            infer_intent_relations("analyze data; write article; publish update", intents),
            (
                IntentRelation("i1", "i2", "semicolon_sequence"),
                IntentRelation("i1", "i3", "release_gate", True),
                IntentRelation("i2", "i3", "release_gate", True),
            ),
        )

    def test_apply_deduplicates_rejects_self_edges_and_preserves_relation_order(self):
        intents = (
            self.intent("i1", "one"),
            self.intent("i2", "two", depends_on=("i4",)),
            self.intent("i3", "three"),
        )
        relations = (
            IntentRelation("i3", "i2", "before"),
            IntentRelation("i1", "i2", "before"),
            IntentRelation("i3", "i2", "duplicate"),
            IntentRelation("i2", "i2", "self"),
        )

        applied = apply_intent_relations(intents, relations)

        self.assertEqual(applied[1].depends_on, ("i4", "i3", "i1"))
        self.assertEqual(applied[0].depends_on, ())
        self.assertEqual(applied[2].depends_on, ())

    def test_unknown_textual_completion_reference_is_unresolved(self):
        graph = decompose_task(
            "After the external procurement approval is complete, build the website"
        )

        self.assertEqual(len(graph.intents), 1)
        self.assertTrue(graph.unresolved_dependencies)
        self.assertTrue(all(value.strip() for value in graph.unresolved_dependencies))
        self.assertEqual(graph.intents[0].depends_on, ())

    @staticmethod
    def intent(intent_id, summary, task_type="general", depends_on=()):
        return Intent(
            id=intent_id,
            summary=summary,
            task_type=task_type,
            required_artifacts=(),
            risk_flags=(),
            depends_on=depends_on,
            source="deterministic",
            confidence=0.8,
        )


if __name__ == "__main__":
    unittest.main()
