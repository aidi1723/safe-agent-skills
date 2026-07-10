import dataclasses
import json
from pathlib import Path
import unittest

from onecode_skill_sanitizer.intent import (
    Intent,
    IntentGraph,
    decompose_task,
    normalize_task,
)


class IntentTest(unittest.TestCase):
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

    def test_does_not_over_split_code_review_lifecycle(self):
        graph = decompose_task("审查代码并补强测试后合并 PR")

        self.assertEqual(len(graph.intents), 1)
        self.assertEqual(graph.intents[0].task_type, "code_review")

    def test_numbered_steps_create_release_dependencies(self):
        graph = decompose_task("1. 分析数据\n2. 生成报告\n3. 发布结果")

        self.assertEqual(len(graph.intents), 3)
        self.assertEqual(graph.intents[2].depends_on, ("i1", "i2"))

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

    def test_validate_reports_cycles(self):
        graph = IntentGraph(
            intents=(
                self.intent("i1", depends_on=("i2",)),
                self.intent("i2", depends_on=("i1",)),
            ),
            unresolved_dependencies=(),
        )

        self.assertEqual(graph.validate(), ["intent dependency cycle detected: i1 -> i2 -> i1"])

    def test_schema_uses_2020_12_and_strict_intent_objects(self):
        schema_path = Path(__file__).resolve().parents[1] / "schemas" / "intent-graph.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        intent_schema = schema["properties"]["intents"]["items"]

        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["properties"]["intents"]["minItems"], 1)
        self.assertFalse(intent_schema["additionalProperties"])
        self.assertEqual(intent_schema["properties"]["id"]["pattern"], "^i[1-9][0-9]*$")
        self.assertEqual(
            intent_schema["properties"]["source"]["enum"],
            ["deterministic", "semantic", "hybrid"],
        )

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
