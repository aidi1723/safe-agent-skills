import copy
import dataclasses
import json
from pathlib import Path
import unittest

from onecode_skill_sanitizer.candidates import (
    ScenarioCandidate,
    retrieve_scenario_candidates,
)
from onecode_skill_sanitizer.intent import decompose_task
from onecode_skill_sanitizer.router import build_profile_for_task_type, build_task_profile


ROOT = Path(__file__).resolve().parents[1]
COMPOUND_TASK = "构建官网，同时审计 skill 路由器，验证通过后发布更新"


class CandidateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundles_index = json.loads(
            (ROOT / "bundles" / "index.json").read_text(encoding="utf-8")
        )

    def test_compound_fixture_returns_expected_top_candidate_per_intent(self):
        graph = decompose_task(COMPOUND_TASK)

        candidates = retrieve_scenario_candidates(graph, self.bundles_index)

        first_by_intent = {}
        for candidate in candidates:
            first_by_intent.setdefault(candidate.intent_id, candidate.scenario_id)
        self.assertEqual(
            first_by_intent,
            {
                "i1": "website-build-launch",
                "i2": "skill-router-quality-review",
                "i3": "open-source-release",
            },
        )

    def test_vague_general_intent_returns_no_candidates(self):
        graph = decompose_task("继续做完它")

        self.assertEqual(retrieve_scenario_candidates(graph, self.bundles_index), ())

    def test_candidates_exclude_untrusted_bundles_and_respect_top_n(self):
        graph = decompose_task("构建官网")
        bundles_index = {
            "bundles": [
                {
                    "id": "untrusted-perfect-match",
                    "name": "Website Build Launch",
                    "scenario": "website launch",
                    "status": "quarantined",
                    "task_signals": ["website", "launch"],
                    "required_capabilities": [],
                },
                *copy.deepcopy(self.bundles_index["bundles"]),
            ]
        }

        candidates = retrieve_scenario_candidates(graph, bundles_index, top_n=2)

        self.assertLessEqual(len(candidates), 2)
        self.assertNotIn("untrusted-perfect-match", {item.scenario_id for item in candidates})
        self.assertTrue(all(item.deterministic_score > 0 for item in candidates))
        self.assertTrue(all(0 < item.score <= 1 for item in candidates))

    def test_equal_scores_preserve_bundle_input_order(self):
        graph = decompose_task("构建官网")
        tied_bundles = {
            "bundles": [
                {
                    "id": "first-tied-scenario",
                    "name": "Website",
                    "scenario": "Website",
                    "status": "trusted",
                    "task_signals": [],
                    "required_capabilities": [
                        {"id": "requirements", "preferred_skills": []}
                    ],
                },
                {
                    "id": "second-tied-scenario",
                    "name": "Website",
                    "scenario": "Website",
                    "status": "trusted",
                    "task_signals": [],
                    "required_capabilities": [
                        {"id": "requirements", "preferred_skills": []}
                    ],
                },
            ]
        }

        candidates = retrieve_scenario_candidates(graph, tied_bundles, top_n=2)

        self.assertEqual(
            [item.scenario_id for item in candidates],
            ["first-tied-scenario", "second-tied-scenario"],
        )
        self.assertEqual(candidates[0].deterministic_score, candidates[1].deterministic_score)

    def test_candidate_is_frozen_json_safe_and_does_not_mutate_inputs(self):
        graph = decompose_task("构建官网")
        bundles_index = copy.deepcopy(self.bundles_index)
        original = copy.deepcopy(bundles_index)

        candidate = retrieve_scenario_candidates(graph, bundles_index, top_n=1)[0]

        with self.assertRaises(dataclasses.FrozenInstanceError):
            candidate.score = 0
        self.assertIsInstance(candidate, ScenarioCandidate)
        self.assertEqual(json.loads(json.dumps(candidate.to_json())), candidate.to_json())
        self.assertEqual(bundles_index, original)

    def test_explicit_task_type_profile_does_not_change_v1_profile_or_config(self):
        task = "构建官网"
        before = build_task_profile(task)

        explicit = build_profile_for_task_type(task, "open_source_release")

        self.assertEqual(build_task_profile(task), before)
        self.assertEqual(explicit["task_type"], "open_source_release")
        explicit["required_capabilities"].append("mutated")
        self.assertNotIn(
            "mutated",
            build_profile_for_task_type(task, "open_source_release")["required_capabilities"],
        )


if __name__ == "__main__":
    unittest.main()
