import unittest

from onecode_skill_sanitizer.intent import Intent, decompose_task
from onecode_skill_sanitizer.intent_dependencies import (
    IntentRelation,
    apply_intent_relations,
    infer_intent_relations,
)


class IntentDependenciesTest(unittest.TestCase):
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
            self.intent("i1", "Review the PR"),
            self.intent("i2", "build the website"),
            self.intent("i3", "prepare an open-source release", "open_source_release"),
        )

        self.assertEqual(
            infer_intent_relations(
                "Review the PR; build the website; prepare an open-source release",
                intents,
            ),
            (
                IntentRelation("i1", "i2", "semicolon_sequence"),
                IntentRelation("i1", "i3", "release_gate"),
                IntentRelation("i2", "i3", "release_gate"),
            ),
        )

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

    def test_release_depends_on_every_explicitly_preceding_path(self):
        intents = (
            self.intent("i1", "review code"),
            self.intent("i2", "verify website"),
            self.intent("i3", "publish update", "open_source_release"),
        )

        self.assertEqual(
            infer_intent_relations("review code; verify website; publish update", intents),
            (
                IntentRelation("i1", "i2", "semicolon_sequence"),
                IntentRelation("i1", "i3", "release_gate"),
                IntentRelation("i2", "i3", "release_gate"),
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
