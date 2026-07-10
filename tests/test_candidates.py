import copy
import dataclasses
import json
import re
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
        catalog_index = json.loads(
            (ROOT / "catalog" / "index.json").read_text(encoding="utf-8")
        )
        cls.trusted_skill_names = {
            skill["name"]
            for skill in catalog_index["skills"]
            if skill.get("status") == "trusted"
        }

    def test_compound_fixture_returns_expected_top_candidate_per_intent(self):
        graph = decompose_task(COMPOUND_TASK)

        candidates = retrieve_scenario_candidates(
            graph, self.bundles_index, self.trusted_skill_names
        )

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

        self.assertEqual(
            retrieve_scenario_candidates(
                graph, self.bundles_index, self.trusted_skill_names
            ),
            (),
        )

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
                    "skills": [],
                    "execution_order": [],
                },
                *copy.deepcopy(self.bundles_index["bundles"]),
            ]
        }

        candidates = retrieve_scenario_candidates(
            graph, bundles_index, self.trusted_skill_names, top_n=2
        )

        self.assertLessEqual(len(candidates), 2)
        self.assertNotIn("untrusted-perfect-match", {item.scenario_id for item in candidates})
        self.assertTrue(all(item.deterministic_score > 0 for item in candidates))
        self.assertTrue(all(0 < item.score <= 1 for item in candidates))

    def test_equal_scores_have_stable_scenario_id_order(self):
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
                    "skills": [],
                    "execution_order": [],
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
                    "skills": [],
                    "execution_order": [],
                },
            ]
        }

        candidates = retrieve_scenario_candidates(graph, tied_bundles, set(), top_n=2)

        self.assertEqual(
            [item.scenario_id for item in candidates],
            ["first-tied-scenario", "second-tied-scenario"],
        )
        self.assertEqual(candidates[0].deterministic_score, candidates[1].deterministic_score)

    def test_equal_scores_sort_by_scenario_id_independent_of_bundle_order(self):
        graph = decompose_task("构建官网")
        tied_bundles = {
            "bundles": [
                self.bundle("z-last", skills=[]),
                self.bundle("a-first", skills=[]),
            ]
        }

        candidates = retrieve_scenario_candidates(graph, tied_bundles, set(), top_n=2)

        self.assertEqual(
            [item.scenario_id for item in candidates],
            ["a-first", "z-last"],
        )

    def test_trusted_label_with_unknown_skill_is_excluded(self):
        graph = decompose_task("构建官网")
        bundles_index = {
            "bundles": [
                self.bundle("unknown-skill", skills=["not-in-trusted-catalog"]),
                self.bundle("known-skill", skills=["business-requirements-brief"]),
            ]
        }

        candidates = retrieve_scenario_candidates(
            graph,
            bundles_index,
            {"business-requirements-brief"},
        )

        self.assertEqual([item.scenario_id for item in candidates], ["known-skill"])

    def test_rejects_malformed_bundle_records_with_deterministic_messages(self):
        graph = decompose_task("构建官网")
        cases = [
            (None, "bundles index must be an object"),
            ({"bundles": "bad"}, "bundles must be a list"),
            ({"bundles": [None]}, "bundle[0] must be an object"),
            ({"bundles": [self.bundle(" ")]}, "bundle[0].id must be a nonempty string"),
            (
                {"bundles": [self.bundle("duplicate"), self.bundle("duplicate")]},
                "duplicate bundle id: duplicate",
            ),
            (
                {"bundles": [{**self.bundle("bad-status"), "status": None}]},
                "bundle[0].status must be a string",
            ),
            (
                {"bundles": [{**self.bundle("bad-skills"), "skills": [" "]}]},
                "bundle[0].skills must be a list of nonempty strings",
            ),
            (
                {
                    "bundles": [
                        {**self.bundle("bad-order"), "execution_order": [False]}
                    ]
                },
                "bundle[0].execution_order must be a list of nonempty strings",
            ),
            (
                {
                    "bundles": [
                        {**self.bundle("bad-capabilities"), "required_capabilities": {}}
                    ]
                },
                "bundle[0].required_capabilities must be a list",
            ),
            (
                {
                    "bundles": [
                        {**self.bundle("bad-capability"), "required_capabilities": [None]}
                    ]
                },
                "bundle[0].required_capabilities[0] must be an object",
            ),
            (
                {
                    "bundles": [
                        {
                            **self.bundle("bad-capability-id"),
                            "required_capabilities": [
                                {"id": " ", "preferred_skills": []}
                            ],
                        }
                    ]
                },
                "bundle[0].required_capabilities[0].id must be a nonempty string",
            ),
            (
                {
                    "bundles": [
                        {
                            **self.bundle("bad-preferred"),
                            "required_capabilities": [
                                {"id": "requirements", "preferred_skills": [1]}
                            ],
                        }
                    ]
                },
                "bundle[0].required_capabilities[0].preferred_skills must be a list of strings",
            ),
            (
                {"bundles": [{**self.bundle("bad-signals"), "task_signals": [1]}]},
                "bundle[0].task_signals must be a list of strings",
            ),
        ]

        for bundles_index, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError, f"^{re.escape(message)}$"):
                    retrieve_scenario_candidates(graph, bundles_index, set())

    def test_top_n_must_be_non_bool_int_within_bounds(self):
        graph = decompose_task("构建官网")
        for top_n in [True, 1.5, "2", None, -1, 11]:
            with self.subTest(top_n=top_n):
                with self.assertRaisesRegex(
                    ValueError, "^top_n must be an integer between 0 and 10$"
                ):
                    retrieve_scenario_candidates(
                        graph, self.bundles_index, self.trusted_skill_names, top_n=top_n
                    )

        self.assertEqual(
            retrieve_scenario_candidates(
                graph, self.bundles_index, self.trusted_skill_names, top_n=0
            ),
            (),
        )

    def test_candidate_rejects_nonfinite_scores(self):
        for score in [float("nan"), float("inf"), float("-inf")]:
            with self.subTest(score=score):
                with self.assertRaisesRegex(ValueError, "^score must be finite$"):
                    ScenarioCandidate("i1", "scenario", score, 1)

        for deterministic_score in [True, 1.5, float("nan"), float("inf")]:
            with self.subTest(deterministic_score=deterministic_score):
                with self.assertRaisesRegex(
                    ValueError, "^deterministic_score must be an integer$"
                ):
                    ScenarioCandidate("i1", "scenario", 1.0, deterministic_score)

    def test_candidate_is_frozen_json_safe_and_does_not_mutate_inputs(self):
        graph = decompose_task("构建官网")
        bundles_index = copy.deepcopy(self.bundles_index)
        original = copy.deepcopy(bundles_index)

        candidate = retrieve_scenario_candidates(
            graph, bundles_index, self.trusted_skill_names, top_n=1
        )[0]

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

    @staticmethod
    def bundle(bundle_id, skills=None):
        skills = [] if skills is None else skills
        return {
            "id": bundle_id,
            "name": "Website",
            "scenario": "Website",
            "status": "trusted",
            "task_signals": [],
            "required_capabilities": [
                {"id": "requirements", "preferred_skills": []}
            ],
            "skills": skills,
            "execution_order": list(skills),
        }


if __name__ == "__main__":
    unittest.main()
