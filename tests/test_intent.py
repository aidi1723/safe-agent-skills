import dataclasses
import json
from pathlib import Path
import unittest

from onecode_skill_sanitizer.intent import (
    Intent,
    IntentGraph,
    TaskDecomposition,
    decompose_task,
    normalize_task,
    split_task_clauses,
)


class IntentTest(unittest.TestCase):
    def test_explicit_sequences_create_dependency_chains(self):
        cases = [
            (
                "first analyze the spreadsheet, then write the SEO article",
                [(), ("i1",)],
            ),
            (
                "先做短视频脚本，再接入 agentic media workflow",
                [(), ("i1",)],
            ),
            (
                "Review the PR; build the website; prepare an open-source release",
                [(), ("i1",), ("i1", "i2")],
            ),
            (
                "Govern the role library before planning the multi-agent workflow",
                [(), ("i1",)],
            ),
        ]

        for task, expected_dependencies in cases:
            with self.subTest(task=task):
                graph = decompose_task(task)
                self.assertEqual(
                    [intent.depends_on for intent in graph.intents],
                    expected_dependencies,
                )

    def test_parallel_and_plain_enumerations_do_not_create_dependencies(self):
        cases = [
            "In parallel: review code, analyze the spreadsheet, and draft an SEO article",
            "同时做 UI 设计、代码审查和表格分析",
            "review code, analyze the spreadsheet, and draft an SEO article",
            "做 UI 设计、代码审查和表格分析",
        ]

        for task in cases:
            with self.subTest(task=task):
                graph = decompose_task(task)
                self.assertTrue(graph.intents)
                self.assertTrue(all(not intent.depends_on for intent in graph.intents))

    def test_decompose_task_remains_graph_only_compatibility_wrapper(self):
        graph = decompose_task("审计 skill router")

        self.assertIsInstance(graph, IntentGraph)
        self.assertNotIsInstance(graph, TaskDecomposition)

    def test_normalize_task_preserves_structured_context(self):
        normalized = normalize_task(
            "历史：之前在写官网\n当前任务：审计 skill 路由器\n过期上下文：发布旧版本"
        )

        self.assertEqual(normalized.current, "审计 skill 路由器")
        self.assertEqual(normalized.history, "之前在写官网")
        self.assertEqual(normalized.stale, "发布旧版本")
        self.assertEqual(normalized.stale_policy, "ignore_for_routing")

    def test_stale_context_is_ignored_for_routing(self):
        graph = decompose_task(
            "历史：之前在写官网\n当前任务：审计 skill 路由器\n过期上下文：发布旧版本"
        )

        self.assertEqual([intent.task_type for intent in graph.intents], ["skill_router_review"])

    def test_decompose_compound_release_task(self):
        graph = decompose_task("构建官网，同时审计 skill 路由器，验证通过后发布更新")

        self.assertEqual(
            [intent.task_type for intent in graph.intents],
            ["website_build", "skill_router_review", "open_source_release"],
        )
        self.assertEqual(graph.intents[2].depends_on, ("i1", "i2"))
        self.assertEqual(graph.intents[2].required_artifacts, ("release_record",))
        self.assertEqual(graph.intents[2].risk_flags, ("public_release",))
        self.assertEqual(graph.validate(), [])

    def test_release_boundary_without_object_depends_on_website_build(self):
        graph = decompose_task("构建官网，验证通过后发布")

        self.assertEqual(
            [intent.task_type for intent in graph.intents],
            ["website_build", "open_source_release"],
        )
        self.assertEqual(graph.intents[1].depends_on, ("i1",))

    def test_test_passed_go_live_boundary_creates_release_dependency(self):
        graph = decompose_task("完成测试，测试通过后上线")

        self.assertEqual(len(graph.intents), 2)
        self.assertEqual(graph.intents[1].task_type, "open_source_release")
        self.assertEqual(graph.intents[1].depends_on, ("i1",))

    def test_completed_build_push_boundary_creates_release_dependency(self):
        graph = decompose_task("完成构建，完成后推送")

        self.assertEqual(len(graph.intents), 2)
        self.assertEqual(graph.intents[1].task_type, "open_source_release")
        self.assertEqual(graph.intents[1].depends_on, ("i1",))

    def test_does_not_over_split_code_review_lifecycle(self):
        graph = decompose_task("审查代码并补强测试后合并 PR")

        self.assertEqual(len(graph.intents), 1)
        self.assertEqual(graph.intents[0].task_type, "code_review")

    def test_lifecycle_exception_applies_per_candidate_clause(self):
        graph = decompose_task("审查代码并补强测试后合并 PR，同时构建官网")

        self.assertEqual(
            [intent.task_type for intent in graph.intents],
            ["code_review", "website_build"],
        )

    def test_mixed_lifecycle_release_depends_on_prior_intents(self):
        graph = decompose_task("审查代码并补强测试后合并 PR，同时构建官网；发布更新")

        self.assertEqual(
            [intent.task_type for intent in graph.intents],
            ["code_review", "website_build", "open_source_release"],
        )
        self.assertEqual(graph.intents[2].depends_on, ("i1", "i2"))

    def test_numbered_steps_create_release_dependencies(self):
        graph = decompose_task("1. 分析数据\n2. 生成报告\n3. 发布结果")

        self.assertEqual(len(graph.intents), 3)
        self.assertEqual(graph.intents[2].depends_on, ("i1", "i2"))

    def test_release_detection_rejects_negation_preconditions_and_nouns(self):
        cases = [
            (
                "不要发布，只审计 skill 路由器",
                "skill_router_review",
                ("skill_pack", "catalog", "router_report"),
                ("tool_overload", "policy_fragmentation", "misrouting"),
            ),
            (
                "发布前先审计 skill 路由器",
                "skill_router_review",
                ("skill_pack", "catalog", "router_report"),
                ("tool_overload", "policy_fragmentation", "misrouting"),
            ),
            ("生成 release notes", "general", (), ()),
            ("publishable package audit", "general", (), ()),
        ]

        for task, expected_task_type, expected_artifacts, expected_risks in cases:
            with self.subTest(task=task):
                intent = decompose_task(task).intents[0]
                self.assertEqual(intent.task_type, expected_task_type)
                self.assertEqual(intent.required_artifacts, expected_artifacts)
                self.assertEqual(intent.risk_flags, expected_risks)

    def test_release_detection_accepts_explicit_actions(self):
        for task in [
            "发布更新",
            "发布结果",
            "publish update",
            "release the package",
            "推送 GitHub",
            "push to GitHub",
            "push the repository",
        ]:
            with self.subTest(task=task):
                intent = decompose_task(task).intents[0]
                self.assertEqual(intent.task_type, "open_source_release")
                self.assertEqual(intent.required_artifacts, ("release_record",))
                self.assertEqual(intent.risk_flags, ("public_release",))

    def test_push_release_detection_rejects_negation_and_preconditions(self):
        for task in [
            "不要推送 GitHub",
            "do not push to GitHub",
            "never push to GitHub",
            "before pushing to GitHub",
            "推送 GitHub 前",
        ]:
            with self.subTest(task=task):
                intent = decompose_task(task).intents[0]
                self.assertNotEqual(intent.task_type, "open_source_release")
                self.assertNotEqual(intent.required_artifacts, ("release_record",))

    def test_natural_push_phrases_reject_negation_and_preconditions(self):
        for task in [
            "不要推送到 GitHub",
            "推送到 GitHub 前",
            "do not push changes to GitHub",
            "before pushing changes to GitHub",
            "do not push the repository to GitHub",
            "before pushing the repository to GitHub",
        ]:
            with self.subTest(task=task):
                intent = decompose_task(task).intents[0]
                self.assertNotEqual(intent.task_type, "open_source_release")
                self.assertNotEqual(intent.required_artifacts, ("release_record",))

    def test_natural_push_phrases_accept_explicit_actions(self):
        for task in [
            "推送到 GitHub",
            "push changes to GitHub",
            "push the repository to GitHub",
        ]:
            with self.subTest(task=task):
                intent = decompose_task(task).intents[0]
                self.assertEqual(intent.task_type, "open_source_release")
                self.assertEqual(intent.required_artifacts, ("release_record",))

    def test_mixed_release_polarity_is_evaluated_per_adversative_segment(self):
        for task in [
            "Do not push to GitHub, but publish the update",
            "Publish the update, but do not push to GitHub",
            "不要推送 GitHub，但是发布更新",
            "发布更新，但要不推送 GitHub",
        ]:
            with self.subTest(task=task):
                intent = decompose_task(task).intents[0]
                self.assertEqual(intent.task_type, "open_source_release")
                self.assertEqual(intent.required_artifacts, ("release_record",))

    def test_ambiguous_english_and_phrases_remain_single_intents(self):
        for task in [
            "Research and Development roadmap",
            "AT&T and Verizon data",
            "command and control risks",
        ]:
            with self.subTest(task=task):
                self.assertEqual(len(decompose_task(task).intents), 1)

    def test_clear_english_then_sequence_splits(self):
        graph = decompose_task("audit the skill router then publish update")

        self.assertEqual(len(graph.intents), 2)
        self.assertEqual(graph.intents[1].task_type, "open_source_release")
        self.assertEqual(graph.intents[1].depends_on, ("i1",))

    def test_models_are_frozen_and_convert_tuples_to_json_arrays(self):
        normalized = normalize_task("构建官网")
        graph = decompose_task("构建官网，同时发布更新")

        with self.assertRaises(dataclasses.FrozenInstanceError):
            normalized.current = "changed"
        with self.assertRaises(dataclasses.FrozenInstanceError):
            graph.intents[0].summary = "changed"
        with self.assertRaises(dataclasses.FrozenInstanceError):
            graph.intents = ()

        payload = graph.to_json()
        self.assertIsInstance(payload["intents"], list)
        self.assertIsInstance(payload["intents"][0]["required_artifacts"], list)
        self.assertIsInstance(payload["intents"][0]["risk_flags"], list)
        self.assertIsInstance(payload["intents"][1]["depends_on"], list)
        json.dumps(payload)

    def test_validate_reports_unknown_dependencies(self):
        graph = IntentGraph(
            intents=(self.intent("i1", depends_on=("i9",)),),
            unresolved_dependencies=(),
        )

        self.assertEqual(graph.validate(), ["intent i1 depends on unknown intent i9"])

    def test_validate_rejects_duplicate_ids_before_dependency_analysis(self):
        graph = IntentGraph(
            intents=(
                self.intent("i1"),
                self.intent("i1", depends_on=("i9",)),
            ),
            unresolved_dependencies=(),
        )

        self.assertEqual(graph.validate(), ["duplicate intent id: i1"])

    def test_validate_reports_cycles(self):
        graph = IntentGraph(
            intents=(
                self.intent("i1", depends_on=("i2",)),
                self.intent("i2", depends_on=("i1",)),
            ),
            unresolved_dependencies=(),
        )

        self.assertEqual(graph.validate(), ["intent dependency cycle detected: i1 -> i2 -> i1"])

    def test_validate_rejects_empty_graph_and_invalid_intent_fields(self):
        invalid_intent = Intent(
            id="bad-id",
            summary=" ",
            task_type="",
            required_artifacts=("",),
            risk_flags=("",),
            depends_on=("bad-dependency",),
            source="model",
            confidence=1.1,
        )

        self.assertEqual(IntentGraph(intents=(), unresolved_dependencies=()).validate(), ["intent graph is empty"])
        self.assertEqual(
            IntentGraph(intents=(invalid_intent,), unresolved_dependencies=("",)).validate(),
            [
                "invalid intent id: bad-id",
                "intent bad-id summary must be nonempty",
                "intent bad-id task_type must be nonempty",
                "intent bad-id required_artifacts must contain nonempty strings",
                "intent bad-id risk_flags must contain nonempty strings",
                "intent bad-id has invalid dependency id: bad-dependency",
                "intent bad-id depends on unknown intent bad-dependency",
                "intent bad-id has invalid source: model",
                "intent bad-id confidence must be between 0 and 1",
                "unresolved_dependencies must contain nonempty strings",
            ],
        )

    def test_validate_reports_malformed_collection_fields_without_raising(self):
        invalid_intent = Intent(
            id="i1",
            summary="audit",
            task_type="code_review",
            required_artifacts=None,
            risk_flags="risk",
            depends_on=None,
            source="deterministic",
            confidence=True,
        )

        self.assertEqual(
            IntentGraph(intents=(invalid_intent,), unresolved_dependencies=None).validate(),
            [
                "intent i1 required_artifacts must contain nonempty strings",
                "intent i1 risk_flags must contain nonempty strings",
                "intent i1 depends_on must contain valid intent IDs",
                "intent i1 confidence must be between 0 and 1",
                "unresolved_dependencies must contain nonempty strings",
            ],
        )

    def test_numbered_and_bulleted_lists_preserve_continuation_lines(self):
        self.assertEqual(
            split_task_clauses("1. 分析数据\n   包含季度趋势\n2. 发布结果"),
            ["分析数据 包含季度趋势", "发布结果"],
        )
        self.assertEqual(
            split_task_clauses("- 审计 skill 路由器\n  检查依赖图\n- 构建官网"),
            ["审计 skill 路由器 检查依赖图", "构建官网"],
        )

    def test_schema_uses_2020_12_and_strict_intent_objects(self):
        schema_path = Path(__file__).resolve().parents[1] / "schemas" / "intent-graph.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        intent_schema = schema["properties"]["intents"]["items"]

        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["properties"]["intents"]["minItems"], 1)
        self.assertEqual(set(schema["required"]), {"intents", "unresolved_dependencies"})
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            set(intent_schema["required"]),
            {
                "id",
                "summary",
                "task_type",
                "required_artifacts",
                "risk_flags",
                "depends_on",
                "source",
                "confidence",
            },
        )
        self.assertFalse(intent_schema["additionalProperties"])
        self.assertEqual(intent_schema["properties"]["id"]["pattern"], "^i[1-9][0-9]*$")
        self.assertEqual(intent_schema["properties"]["summary"]["minLength"], 1)
        self.assertEqual(intent_schema["properties"]["task_type"]["minLength"], 1)
        self.assertEqual(
            intent_schema["properties"]["required_artifacts"]["items"]["minLength"],
            1,
        )
        self.assertEqual(intent_schema["properties"]["risk_flags"]["items"]["minLength"], 1)
        self.assertEqual(
            schema["properties"]["unresolved_dependencies"]["items"]["minLength"],
            1,
        )
        self.assertEqual(
            intent_schema["properties"]["source"]["enum"],
            ["deterministic", "semantic", "hybrid"],
        )
        self.assertEqual(intent_schema["properties"]["confidence"]["minimum"], 0)
        self.assertEqual(intent_schema["properties"]["confidence"]["maximum"], 1)

    def test_generated_payload_matches_required_schema_shape(self):
        payload = decompose_task("构建官网，同时发布更新").to_json()
        self.assertEqual(set(payload), {"intents", "unresolved_dependencies"})
        self.assertGreaterEqual(len(payload["intents"]), 1)
        for intent in payload["intents"]:
            self.assertEqual(
                set(intent),
                {
                    "id",
                    "summary",
                    "task_type",
                    "required_artifacts",
                    "risk_flags",
                    "depends_on",
                    "source",
                    "confidence",
                },
            )
            self.assertRegex(intent["id"], r"^i[1-9][0-9]*$")
            self.assertTrue(intent["summary"].strip())
            self.assertTrue(intent["task_type"].strip())
            self.assertIn(intent["source"], {"deterministic", "semantic", "hybrid"})
            self.assertGreaterEqual(intent["confidence"], 0)
            self.assertLessEqual(intent["confidence"], 1)
            for field in ["required_artifacts", "risk_flags", "depends_on"]:
                self.assertIsInstance(intent[field], list)
                self.assertTrue(all(isinstance(value, str) and value for value in intent[field]))

    @staticmethod
    def intent(intent_id, depends_on=()):
        return Intent(
            id=intent_id,
            summary=intent_id,
            task_type="general",
            required_artifacts=(),
            risk_flags=(),
            depends_on=depends_on,
            source="deterministic",
            confidence=1.0,
        )


if __name__ == "__main__":
    unittest.main()
