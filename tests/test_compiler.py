import copy
import json
from pathlib import Path
import unittest

from onecode_skill_sanitizer.compiler import compile_execution_graph
from onecode_skill_sanitizer.composer import ScenarioComposition, ScenarioSelection
from onecode_skill_sanitizer.intent import Intent, IntentGraph, decompose_task


ROOT = Path(__file__).resolve().parents[1]
COMPOUND_TASK = "构建官网，同时审计 skill 路由器，验证通过后发布更新"


class CompilerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundles_index = json.loads(
            (ROOT / "bundles" / "index.json").read_text(encoding="utf-8")
        )
        catalog_index = json.loads(
            (ROOT / "catalog" / "index.json").read_text(encoding="utf-8")
        )
        cls.trusted_skill_names = {
            skill["name"]
            for skill in catalog_index["skills"]
            if skill.get("status") == "trusted"
        }

    def test_compiles_valid_compound_dag_with_release_dependencies_from_both_paths(self):
        graph = decompose_task(COMPOUND_TASK)
        composition = ScenarioComposition(
            selections=(
                ScenarioSelection("website-build-launch", ("i1",), 1.0, 10),
                ScenarioSelection("skill-router-quality-review", ("i2",), 1.0, 10),
                ScenarioSelection("open-source-release", ("i3",), 1.0, 10),
            ),
            uncovered_intents=(),
            status="complete",
        )

        compiled = compile_execution_graph(
            graph, composition, self.bundles_index, self.trusted_skill_names
        )

        self.assertEqual(compiled["schema_version"], 2)
        self.assertEqual(compiled["status"], "ready")
        self.assertTrue(compiled["acyclic"])
        self.assertEqual(compiled["reason_codes"], [])
        release_root = self.root_node(compiled, "i3")
        incoming = {
            edge["from"]
            for edge in compiled["edges"]
            if edge["to"] == release_root and edge["type"] == "intent_dependency"
        }
        self.assertEqual(
            incoming,
            {
                self.terminal_verification_node(compiled, "i1"),
                self.terminal_verification_node(compiled, "i2"),
            },
        )
        incoming_nodes = {
            node["id"]: node for node in compiled["nodes"] if node["id"] in incoming
        }
        self.assertEqual(
            {node["stage"] for node in incoming_nodes.values()}, {"verification"}
        )
        node = compiled["nodes"][0]
        self.assertEqual(
            set(node),
            {"id", "intent_ids", "scenario_ids", "skill", "stage", "host_action"},
        )
        self.assertEqual(node["host_action"], node["skill"].startswith("execution-"))

    def test_constructed_cyclic_intent_graph_is_blocked_without_fallback(self):
        graph = IntentGraph(
            intents=(
                self.intent("i1", depends_on=("i2",)),
                self.intent("i2", depends_on=("i1",)),
            ),
            unresolved_dependencies=(),
        )
        composition = self.composition(("i1",), ("i2",))
        bundles = {"bundles": [self.bundle("first"), self.bundle("second")]}

        compiled = compile_execution_graph(
            graph, composition, bundles, {"execution-publish-check"}
        )

        self.assertEqual(compiled["status"], "blocked")
        self.assertFalse(compiled["acyclic"])
        self.assertEqual(
            compiled["reason_codes"], ["dependency_cycle", "invalid_intent_graph"]
        )
        self.assertEqual(
            compiled["details"],
            ["intent dependency cycle detected: i1 -> i2 -> i1"],
        )
        self.assertNotIn("fallback_reason", compiled)

    def test_node_and_edge_ordering_is_deterministic_for_reordered_inputs(self):
        graph = IntentGraph(
            intents=(
                self.intent("i1"),
                self.intent("i2", depends_on=("i1",)),
            ),
            unresolved_dependencies=(),
        )
        composition = ScenarioComposition(
            selections=(
                ScenarioSelection("second", ("i2",), 1.0, 1),
                ScenarioSelection("first", ("i1",), 1.0, 1),
            ),
            uncovered_intents=(),
            status="complete",
        )
        bundles = {
            "bundles": [
                self.bundle("second", ["skill-c", "execution-browser-check", "skill-d"]),
                self.bundle("first", ["skill-a", "execution-publish-check", "skill-b"]),
            ]
        }
        before = copy.deepcopy(bundles)

        first = compile_execution_graph(graph, composition, bundles, self.skill_names(bundles))
        second = compile_execution_graph(
            graph,
            ScenarioComposition(
                selections=tuple(reversed(composition.selections)),
                uncovered_intents=(),
                status="complete",
            ),
            {"bundles": list(reversed(bundles["bundles"]))},
            self.skill_names(bundles),
        )

        self.assertEqual(first, second)
        self.assertEqual(
            [node["id"] for node in first["nodes"]],
            [
                "skill:i1:skill-a",
                "skill:i1:execution-publish-check",
                "skill:i1:skill-b",
                "skill:i2:skill-c",
                "skill:i2:execution-browser-check",
                "skill:i2:skill-d",
            ],
        )
        self.assertEqual(bundles, before)

    def test_missing_scenario_bundle_is_blocked_with_reason_code(self):
        graph = IntentGraph((self.intent("i1"),), ())
        composition = self.composition(("i1",))

        compiled = compile_execution_graph(graph, composition, {"bundles": []}, set())

        self.assertEqual(compiled["status"], "blocked")
        self.assertEqual(compiled["reason_codes"], ["missing_scenario_bundle"])
        self.assertEqual(compiled["nodes"], [])
        self.assertEqual(compiled["edges"], [])

    def test_empty_execution_order_is_blocked_with_reason_code(self):
        graph = IntentGraph((self.intent("i1"),), ())
        composition = self.composition(("i1",))
        bundles = {"bundles": [self.bundle("first", [])]}

        compiled = compile_execution_graph(graph, composition, bundles, set())

        self.assertEqual(compiled["status"], "blocked")
        self.assertEqual(compiled["reason_codes"], ["empty_execution_order"])

    def test_duplicate_dependencies_do_not_create_duplicate_edges(self):
        graph = IntentGraph(
            intents=(
                self.intent("i1"),
                self.intent("i2", depends_on=("i1", "i1")),
            ),
            unresolved_dependencies=(),
        )
        composition = self.composition(("i1",), ("i2",))
        bundles = {"bundles": [self.bundle("first"), self.bundle("second")]}

        compiled = compile_execution_graph(
            graph, composition, bundles, {"execution-publish-check"}
        )

        edge_keys = [(edge["from"], edge["to"], edge["type"]) for edge in compiled["edges"]]
        self.assertEqual(len(edge_keys), len(set(edge_keys)))

    def test_forged_composition_cannot_select_untrusted_bundle_or_skill(self):
        graph = IntentGraph((self.intent("i1"),), ())
        composition = self.composition(("i1",))
        quarantined = {"bundles": [{**self.bundle("first"), "status": "quarantined"}]}

        untrusted_bundle = compile_execution_graph(
            graph, composition, quarantined, {"execution-publish-check"}
        )
        untrusted_skill = compile_execution_graph(
            graph,
            composition,
            {"bundles": [self.bundle("first")]},
            set(),
        )

        self.assertEqual(untrusted_bundle["reason_codes"], ["untrusted_scenario"])
        self.assertEqual(untrusted_skill["reason_codes"], ["untrusted_scenario"])
        self.assertEqual(untrusted_bundle["status"], "blocked")
        self.assertEqual(untrusted_skill["status"], "blocked")

    def test_incomplete_unknown_duplicate_and_malformed_inputs_return_reason_codes(self):
        graph = IntentGraph((self.intent("i1"),), ())
        incomplete = ScenarioComposition((), ("i1",), "incomplete")
        unknown = ScenarioComposition(
            (ScenarioSelection("first", ("i9",), 1.0, 1),), (), "complete"
        )
        duplicate_bundle = {
            "bundles": [
                self.bundle(
                    "first", ["execution-publish-check", "execution-publish-check"]
                )
            ]
        }
        malformed_graph = IntentGraph((self.intent("i1", depends_on=None),), ())

        cases = [
            (
                compile_execution_graph(graph, incomplete, {"bundles": []}, set()),
                "incomplete_composition",
            ),
            (
                compile_execution_graph(
                    graph,
                    unknown,
                    {"bundles": [self.bundle("first")]},
                    {"execution-publish-check"},
                ),
                "unknown_intent_id",
            ),
            (
                compile_execution_graph(
                    graph,
                    self.composition(("i1",)),
                    duplicate_bundle,
                    {"execution-publish-check"},
                ),
                "duplicate_skill_name",
            ),
            (
                compile_execution_graph(
                    malformed_graph,
                    self.composition(("i1",)),
                    {"bundles": [self.bundle("first")]},
                    {"execution-publish-check"},
                ),
                "malformed_intent_dependency",
            ),
        ]

        for compiled, reason_code in cases:
            with self.subTest(reason_code=reason_code):
                self.assertEqual(compiled["status"], "blocked")
                self.assertIn(reason_code, compiled["reason_codes"])

    def test_dependency_without_verification_anchor_is_blocked(self):
        graph = IntentGraph(
            intents=(
                self.intent("i1"),
                self.intent("i2", depends_on=("i1",)),
            ),
            unresolved_dependencies=(),
        )
        composition = self.composition(("i1",), ("i2",))
        bundles = {
            "bundles": [
                self.bundle("first", ["skill-a"]),
                self.bundle("second", ["execution-publish-check"]),
            ]
        }

        compiled = compile_execution_graph(
            graph, composition, bundles, {"skill-a", "execution-publish-check"}
        )

        self.assertEqual(compiled["status"], "blocked")
        self.assertEqual(compiled["reason_codes"], ["missing_intent_verification"])

    def test_intent_graph_validation_issues_and_unresolved_dependencies_block(self):
        graph = IntentGraph(
            intents=(self.intent("i1"),),
            unresolved_dependencies=("release target unresolved", "artifact unresolved"),
        )

        compiled = compile_execution_graph(
            graph,
            self.composition(("i1",)),
            {"bundles": [self.bundle("first")]},
            {"execution-publish-check"},
        )

        self.assertEqual(compiled["status"], "blocked")
        self.assertEqual(compiled["reason_codes"], ["invalid_intent_graph"])
        self.assertEqual(
            compiled["details"],
            [
                "unresolved dependency: artifact unresolved",
                "unresolved dependency: release target unresolved",
            ],
        )

    def test_compiler_boundary_rejects_invalid_intent_id_pattern(self):
        graph = IntentGraph((self.intent("intent-1"),), ())
        composition = ScenarioComposition(
            (ScenarioSelection("first", ("intent-1",), 1.0, 1),), (), "complete"
        )

        compiled = compile_execution_graph(
            graph,
            composition,
            {"bundles": [self.bundle("first")]},
            {"execution-publish-check"},
        )

        self.assertEqual(compiled["status"], "blocked")
        self.assertEqual(compiled["reason_codes"], ["invalid_intent_graph"])
        self.assertEqual(compiled["details"], ["invalid intent id: intent-1"])

    def test_reason_codes_and_details_are_sorted_independent_of_selection_order(self):
        graph = IntentGraph(
            intents=(self.intent("i1"), self.intent("i2")),
            unresolved_dependencies=("z unresolved", "a unresolved"),
        )
        selections = (
            ScenarioSelection("missing-z", ("i2",), 1.0, 1),
            ScenarioSelection("missing-a", ("i1",), 1.0, 1),
        )

        first = compile_execution_graph(
            graph,
            ScenarioComposition(selections, (), "complete"),
            {"bundles": []},
            set(),
        )
        second = compile_execution_graph(
            graph,
            ScenarioComposition(tuple(reversed(selections)), (), "complete"),
            {"bundles": []},
            set(),
        )

        self.assertEqual(first, second)
        self.assertEqual(
            first["reason_codes"], ["invalid_intent_graph", "missing_scenario_bundle"]
        )
        self.assertEqual(
            first["details"],
            ["unresolved dependency: a unresolved", "unresolved dependency: z unresolved"],
        )

    @staticmethod
    def intent(intent_id, depends_on=()):
        return Intent(
            id=intent_id,
            summary="test intent",
            task_type="code_review",
            required_artifacts=(),
            risk_flags=(),
            depends_on=depends_on,
            source="deterministic",
            confidence=1.0,
        )

    @staticmethod
    def bundle(bundle_id, execution_order=None):
        order = ["execution-publish-check"] if execution_order is None else execution_order
        return {
            "id": bundle_id,
            "name": bundle_id,
            "scenario": bundle_id,
            "status": "trusted",
            "task_signals": [],
            "required_capabilities": [],
            "execution_order": order,
            "skills": list(dict.fromkeys(order)),
            "expected_output": [],
            "safety_boundary": "method only",
        }

    @staticmethod
    def composition(*intent_ids):
        selections = tuple(
            ScenarioSelection(
                "first" if index == 0 else "second", ids, 1.0, 1
            )
            for index, ids in enumerate(intent_ids)
        )
        return ScenarioComposition(selections, (), "complete")

    @staticmethod
    def skill_names(bundles):
        return {
            skill_name
            for bundle in bundles["bundles"]
            for skill_name in bundle["execution_order"]
        }

    @staticmethod
    def root_node(compiled, intent_id):
        return next(
            node["id"] for node in compiled["nodes"] if node["intent_ids"] == [intent_id]
        )

    @staticmethod
    def terminal_node(compiled, intent_id):
        node_ids = [
            node["id"] for node in compiled["nodes"] if node["intent_ids"] == [intent_id]
        ]
        return next(
            node_id
            for node_id in reversed(node_ids)
            if not any(
                edge["from"] == node_id and edge["type"] == "scenario_order"
                for edge in compiled["edges"]
            )
        )

    @staticmethod
    def terminal_verification_node(compiled, intent_id):
        verification_ids = [
            node["id"]
            for node in compiled["nodes"]
            if node["intent_ids"] == [intent_id] and node["stage"] == "verification"
        ]
        return next(
            node_id
            for node_id in reversed(verification_ids)
            if not any(
                edge["from"] == node_id
                and edge["to"] in verification_ids
                and edge["type"] == "scenario_order"
                for edge in compiled["edges"]
            )
        )


if __name__ == "__main__":
    unittest.main()
