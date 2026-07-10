import copy
import dataclasses
import json
from pathlib import Path
import unittest

from onecode_skill_sanitizer.candidates import ScenarioCandidate, retrieve_scenario_candidates
from onecode_skill_sanitizer.composer import (
    ScenarioComposition,
    ScenarioSelection,
    compose_scenarios,
)
from onecode_skill_sanitizer.intent import Intent, IntentGraph, decompose_task


ROOT = Path(__file__).resolve().parents[1]
COMPOUND_TASK = "构建官网，同时审计 skill 路由器，验证通过后发布更新"


class ComposerTest(unittest.TestCase):
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

    def test_compound_fixture_selects_three_scenarios_in_intent_order(self):
        graph = decompose_task(COMPOUND_TASK)
        candidates = retrieve_scenario_candidates(
            graph, self.bundles_index, self.trusted_skill_names
        )

        composition = compose_scenarios(
            graph, candidates, self.bundles_index, self.trusted_skill_names
        )

        self.assertEqual(composition.status, "complete")
        self.assertEqual(composition.uncovered_intents, ())
        self.assertEqual(
            [selection.scenario_id for selection in composition.selections],
            [
                "website-build-launch",
                "skill-router-quality-review",
                "open-source-release",
            ],
        )
        self.assertEqual(
            [selection.intent_ids for selection in composition.selections],
            [("i1",), ("i2",), ("i3",)],
        )

    def test_vague_fixture_is_incomplete_with_uncovered_intent(self):
        graph = decompose_task("继续做完它")

        composition = compose_scenarios(
            graph, (), self.bundles_index, self.trusted_skill_names
        )

        self.assertEqual(composition.selections, ())
        self.assertEqual(composition.uncovered_intents, ("i1",))
        self.assertEqual(composition.status, "incomplete")

    def test_same_scenario_is_merged_without_reordering_intents(self):
        graph = IntentGraph(
            intents=(self.intent("i1"), self.intent("i2"), self.intent("i3")),
            unresolved_dependencies=(),
        )
        candidates = (
            ScenarioCandidate("i1", "shared", 1.0, 10),
            ScenarioCandidate("i2", "other", 1.0, 8),
            ScenarioCandidate("i3", "shared", 1.0, 9),
        )

        bundles_index = {
            "bundles": [
                self.bundle("shared"),
                self.bundle("other"),
            ]
        }
        composition = compose_scenarios(graph, candidates, bundles_index, set())

        self.assertEqual(
            composition.selections,
            (
                ScenarioSelection("shared", ("i1", "i3"), 1.0, 19),
                ScenarioSelection("other", ("i2",), 1.0, 8),
            ),
        )

    def test_composition_is_frozen_json_safe_and_inputs_remain_unchanged(self):
        graph = decompose_task(COMPOUND_TASK)
        candidates = retrieve_scenario_candidates(
            graph, self.bundles_index, self.trusted_skill_names
        )
        candidates_before = copy.deepcopy(candidates)

        composition = compose_scenarios(
            graph, candidates, self.bundles_index, self.trusted_skill_names
        )

        with self.assertRaises(dataclasses.FrozenInstanceError):
            composition.status = "changed"
        with self.assertRaises(dataclasses.FrozenInstanceError):
            composition.selections[0].score = 0
        self.assertIsInstance(composition, ScenarioComposition)
        self.assertEqual(json.loads(json.dumps(composition.to_json())), composition.to_json())
        self.assertEqual(candidates, candidates_before)

    def test_forged_untrusted_candidate_is_uncovered(self):
        graph = IntentGraph(
            intents=(self.intent("i1"),),
            unresolved_dependencies=(),
        )
        candidates = (ScenarioCandidate("i1", "evil-untrusted", 1.0, 999),)
        bundles_index = {
            "bundles": [
                {
                    **self.bundle("evil-untrusted"),
                    "status": "quarantined",
                }
            ]
        }

        composition = compose_scenarios(graph, candidates, bundles_index, set())

        self.assertEqual(composition.selections, ())
        self.assertEqual(composition.uncovered_intents, ("i1",))
        self.assertEqual(composition.status, "incomplete")

    def test_forged_candidate_with_unknown_skill_is_uncovered(self):
        graph = IntentGraph(
            intents=(self.intent("i1"),),
            unresolved_dependencies=(),
        )
        candidates = (ScenarioCandidate("i1", "unknown-skill", 1.0, 999),)
        bundles_index = {
            "bundles": [
                self.bundle("unknown-skill", skills=["not-trusted"]),
            ]
        }

        composition = compose_scenarios(graph, candidates, bundles_index, set())

        self.assertEqual(composition.selections, ())
        self.assertEqual(composition.uncovered_intents, ("i1",))
        self.assertEqual(composition.status, "incomplete")

    @staticmethod
    def intent(intent_id):
        return Intent(
            id=intent_id,
            summary="build website",
            task_type="website_build",
            required_artifacts=(),
            risk_flags=(),
            depends_on=(),
            source="deterministic",
            confidence=1.0,
        )

    @staticmethod
    def bundle(bundle_id, skills=None):
        skills = [] if skills is None else skills
        return {
            "id": bundle_id,
            "name": bundle_id,
            "scenario": bundle_id,
            "status": "trusted",
            "task_signals": [],
            "required_capabilities": [],
            "skills": skills,
            "execution_order": list(skills),
        }


if __name__ == "__main__":
    unittest.main()
