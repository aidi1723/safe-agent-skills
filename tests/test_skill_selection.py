from __future__ import annotations

import copy
import unittest
from pathlib import Path

from onecode_skill_sanitizer.skill_candidates import load_cohort_profiles
from onecode_skill_sanitizer.skill_selection import compose_skill_selection


ROOT = Path(__file__).resolve().parents[1]


def profile(
    name,
    capability,
    *,
    requires=(),
    produces=(),
    evidence=(),
    after=(),
    conflicts=(),
    excludes=(),
):
    return {
        "name": name,
        "capabilities": [capability],
        "requires_context": list(requires),
        "produces_artifacts": list(produces),
        "produces_evidence": list(evidence),
        "requires_after": list(after),
        "conflicts_with": list(conflicts),
        "excludes": list(excludes),
    }


def candidate(name, capability, score, *, excluded=False):
    return {
        "skill": name,
        "deterministic_score": score,
        "semantic_score": None,
        "final_score": score,
        "matched_capabilities": [capability],
        "selected": False,
        "excluded": excluded,
        "reason_codes": ["deterministic_candidate"],
    }


def need(
    decision,
    required=(),
    *,
    explicit=(),
    excluded=(),
    missing_inputs=(),
    mandatory=(),
    block_reasons=(),
    reason_codes=("specialized_need_detected",),
):
    return {
        "decision": decision,
        "required_capabilities": list(required),
        "explicit_skills": list(explicit),
        "excluded_skills": list(excluded),
        "missing_inputs": list(missing_inputs),
        "mandatory_capabilities": list(mandatory),
        "policy_block_reasons": list(block_reasons),
        "reason_codes": list(reason_codes),
    }


class SkillSelectionTest(unittest.TestCase):
    def test_selects_only_marginal_capability_contributors(self):
        requested = need("composite", ("code.review", "code.test"))
        candidates = [
            candidate("code-review-risk", "code.review", 0.9),
            candidate("code-test-regression", "code.test", 0.8),
            candidate("codebase-explore-map", "code.explore", 0.7),
        ]
        profiles = {
            "code-review-risk": profile("code-review-risk", "code.review"),
            "code-test-regression": profile("code-test-regression", "code.test"),
            "codebase-explore-map": profile("codebase-explore-map", "code.explore"),
        }
        original_need = copy.deepcopy(requested)
        original_candidates = copy.deepcopy(candidates)
        original_profiles = copy.deepcopy(profiles)

        result = compose_skill_selection(
            requested, candidates, profiles, explicit_order=[]
        )

        self.assertEqual(
            result["selected_skill_names"],
            ["code-review-risk", "code-test-regression"],
        )
        self.assertEqual(
            result["rejected_adjacent_candidates"],
            ["codebase-explore-map"],
        )
        self.assertEqual(result["execution_graph"]["edges"], [])
        self.assertTrue(
            all(node["parallel"] for node in result["execution_graph"]["nodes"])
        )
        self.assertEqual(result["confidence"]["level"], "high")
        self.assertEqual(requested, original_need)
        self.assertEqual(candidates, original_candidates)
        self.assertEqual(profiles, original_profiles)

    def test_artifact_requirement_and_explicit_order_create_only_real_edges(self):
        requested = need(
            "composite", ("design.ui_review", "execution.browser_check")
        )
        candidates = [
            candidate("design-ui-review", "design.ui_review", 0.9),
            candidate("execution-browser-check", "execution.browser_check", 0.8),
        ]
        profiles = {
            "design-ui-review": profile(
                "design-ui-review",
                "design.ui_review",
                evidence=("ui_review_report",),
            ),
            "execution-browser-check": profile(
                "execution-browser-check",
                "execution.browser_check",
                requires=("ui_review_report",),
            ),
        }

        result = compose_skill_selection(
            requested,
            candidates,
            profiles,
            explicit_order=[("design-ui-review", "execution-browser-check")],
        )

        self.assertEqual(result["routing_status"], "complete")
        self.assertEqual(
            result["execution_graph"]["edges"],
            [
                {
                    "from": "skill:design-ui-review",
                    "to": "skill:execution-browser-check",
                    "type": "artifact_dependency",
                    "evidence": "ui_review_report",
                }
            ],
        )

    def test_uncovered_capability_is_incomplete_and_cycle_is_blocked(self):
        missing = compose_skill_selection(
            need("single", ("code.test",)), [], {}, explicit_order=[]
        )
        self.assertEqual(missing["routing_status"], "incomplete")
        self.assertEqual(missing["missing_capabilities"], ["code.test"])
        self.assertEqual(
            missing["selection"]["failure_reason"], "missing_capability"
        )

        missing_input = compose_skill_selection(
            need(
                "single",
                ("code.test",),
                missing_inputs=("behavior_or_change_under_test",),
            ),
            [candidate("code-test-regression", "code.test", 0.9)],
            {"code-test-regression": profile("code-test-regression", "code.test")},
            explicit_order=[],
        )
        self.assertEqual(missing_input["routing_status"], "incomplete")
        self.assertEqual(
            missing_input["capability_resolution"]["missing_inputs"],
            ["behavior_or_change_under_test"],
        )
        self.assertEqual(
            missing_input["selection"]["failure_reason"],
            "missing_required_input",
        )

        profiles = {
            "a": profile("a", "code.review", after=("b",)),
            "b": profile("b", "code.test", after=("a",)),
        }
        cyclic = compose_skill_selection(
            need("composite", ("code.review", "code.test")),
            [candidate("a", "code.review", 0.9), candidate("b", "code.test", 0.8)],
            profiles,
            explicit_order=[],
        )
        self.assertEqual(cyclic["routing_status"], "blocked")
        self.assertFalse(cyclic["execution_graph"]["acyclic"])
        self.assertEqual(cyclic["execution_graph"]["nodes"], [])
        self.assertEqual(cyclic["execution_graph"]["edges"], [])
        self.assertIn("dependency_cycle", cyclic["execution_graph"]["reason_codes"])

    def test_close_conflicting_candidates_require_clarification(self):
        profiles = {
            "a": profile("a", "design.ui_review", conflicts=("b",)),
            "b": profile("b", "design.ui_review", conflicts=("a",)),
        }
        result = compose_skill_selection(
            need("single", ("design.ui_review",)),
            [
                candidate("a", "design.ui_review", 0.70),
                candidate("b", "design.ui_review", 0.68),
            ],
            profiles,
            explicit_order=[],
        )

        self.assertEqual(result["routing_status"], "clarify")
        self.assertEqual(
            result["selection"]["clarification_reason"],
            "conflicting_candidates_low_margin",
        )
        self.assertEqual(
            result["selection"]["conflict_resolutions"],
            [
                {
                    "winner": "",
                    "rejected": "b",
                    "reason": "insufficient_margin",
                    "margin": 0.02,
                }
            ],
        )

    def test_risk_derived_verifier_gets_a_mandatory_precondition_edge(self):
        result = compose_skill_selection(
            need(
                "composite",
                ("code.review", "code.test"),
                mandatory=("code.test",),
            ),
            [
                candidate("code-review-risk", "code.review", 0.9),
                candidate("code-test-regression", "code.test", 0.8),
            ],
            {
                "code-review-risk": profile("code-review-risk", "code.review"),
                "code-test-regression": profile(
                    "code-test-regression", "code.test"
                ),
            },
            explicit_order=[],
        )

        self.assertEqual(
            result["execution_graph"]["edges"],
            [
                {
                    "from": "skill:code-review-risk",
                    "to": "skill:code-test-regression",
                    "type": "mandatory_verification_precondition",
                    "evidence": "risk_derived_verification",
                }
            ],
        )
        self.assertEqual(
            result["selection"]["marginal_contributions"][1]["reason"],
            "mandatory_verification",
        )

    def test_private_immutable_profile_mapping_and_tuples_are_supported(self):
        profiles = load_cohort_profiles(ROOT / "catalog")
        self.assertNotIsInstance(profiles, dict)
        self.assertIsInstance(profiles["code-review-risk"]["capabilities"], tuple)

        result = compose_skill_selection(
            need("single", ("code.review",)),
            [candidate("code-review-risk", "code.review", 0.9)],
            profiles,
            explicit_order=[],
        )

        self.assertEqual(result["routing_status"], "complete")
        self.assertEqual(result["selected_skill_names"], ["code-review-risk"])

    def test_unique_eligible_artifact_producer_is_added_without_capability_credit(self):
        result = compose_skill_selection(
            need("single", ("execution.browser_check",)),
            [
                candidate(
                    "execution-browser-check", "execution.browser_check", 0.9
                ),
                candidate("design-ui-review", "design.ui_review", 0.5),
            ],
            {
                "execution-browser-check": profile(
                    "execution-browser-check",
                    "execution.browser_check",
                    requires=("ui_review_report",),
                ),
                "design-ui-review": profile(
                    "design-ui-review",
                    "design.ui_review",
                    evidence=("ui_review_report",),
                ),
            },
            explicit_order=[],
        )

        self.assertEqual(
            result["selected_skill_names"],
            ["execution-browser-check", "design-ui-review"],
        )
        self.assertEqual(
            result["selection"]["marginal_contributions"][1],
            {
                "skill": "design-ui-review",
                "capabilities": [],
                "reason": "required_artifact:ui_review_report",
            },
        )
        self.assertEqual(
            result["execution_graph"]["edges"][0]["type"],
            "artifact_dependency",
        )

    def test_high_margin_conflict_keeps_actual_higher_score_candidate(self):
        profiles = {
            "lower": profile(
                "lower", "design.ui_review", conflicts=("higher",)
            ),
            "higher": profile(
                "higher", "design.ui_review", conflicts=("lower",)
            ),
        }
        result = compose_skill_selection(
            need("single", ("design.ui_review",)),
            [
                candidate("lower", "design.ui_review", 0.65),
                candidate("higher", "design.ui_review", 0.90),
            ],
            profiles,
            explicit_order=[],
        )

        self.assertEqual(result["routing_status"], "complete")
        self.assertEqual(result["selected_skill_names"], ["higher"])
        self.assertEqual(
            result["selection"]["conflict_resolutions"],
            [
                {
                    "winner": "higher",
                    "rejected": "lower",
                    "reason": "higher_deterministic_score",
                    "margin": 0.25,
                }
            ],
        )

    def test_explicit_noncontributor_and_real_order_edges_are_preserved(self):
        result = compose_skill_selection(
            need(
                "single",
                ("code.review", "code.review"),
                explicit=("codebase-explore-map",),
            ),
            [
                candidate("code-review-risk", "code.review", 0.9),
                candidate("codebase-explore-map", "code.explore", 0.7),
            ],
            {
                "code-review-risk": profile("code-review-risk", "code.review"),
                "codebase-explore-map": profile(
                    "codebase-explore-map", "code.explore"
                ),
            },
            explicit_order=[("code-review-risk", "codebase-explore-map")],
        )

        self.assertEqual(
            result["selected_skill_names"],
            ["code-review-risk", "codebase-explore-map"],
        )
        self.assertEqual(
            result["selection"]["marginal_contributions"][1]["reason"],
            "explicit_user_request",
        )
        self.assertEqual(
            result["execution_graph"]["edges"],
            [
                {
                    "from": "skill:code-review-risk",
                    "to": "skill:codebase-explore-map",
                    "type": "explicit_user_order",
                    "evidence": "current_request",
                }
            ],
        )

    def test_policy_none_and_clarify_decisions_short_circuit(self):
        blocked = compose_skill_selection(
            need(
                "single",
                ("code.review",),
                block_reasons=("explicit_skill_excluded",),
            ),
            [candidate("code-review-risk", "code.review", 0.9)],
            {"code-review-risk": profile("code-review-risk", "code.review")},
            explicit_order=[],
        )
        self.assertEqual(blocked["routing_status"], "blocked")
        self.assertFalse(blocked["execution_graph"]["acyclic"])
        self.assertEqual(
            blocked["execution_graph"]["reason_codes"],
            ["explicit_skill_excluded"],
        )
        self.assertEqual(blocked["missing_capabilities"], ["code.review"])
        self.assertEqual(
            blocked["selection"]["failure_reason"], "explicit_skill_excluded"
        )

        none = compose_skill_selection(
            need("none", reason_codes=("no_specialized_need",)),
            [],
            {},
            explicit_order=[],
        )
        self.assertEqual(none["routing_status"], "none")
        self.assertEqual(
            none["selection"]["abstention_reason"], "no_specialized_need"
        )
        self.assertTrue(none["execution_graph"]["acyclic"])

        clarify = compose_skill_selection(
            need("clarify", reason_codes=("adjacent_capability_ambiguous",)),
            [],
            {},
            explicit_order=[],
        )
        self.assertEqual(clarify["routing_status"], "clarify")
        self.assertEqual(
            clarify["selection"]["clarification_reason"],
            "adjacent_capability_ambiguous",
        )

    def test_excluded_and_below_threshold_candidates_are_never_selected(self):
        result = compose_skill_selection(
            need("single", ("code.test",)),
            [
                candidate("excluded", "code.test", 0.9, excluded=True),
                candidate("too-low", "code.test", 0.349999),
            ],
            {
                "excluded": profile("excluded", "code.test"),
                "too-low": profile("too-low", "code.test"),
            },
            explicit_order=[],
        )

        self.assertEqual(result["routing_status"], "incomplete")
        self.assertEqual(result["selected_skill_names"], [])
        self.assertEqual(result["rejected_adjacent_candidates"], ["too-low"])
        self.assertEqual(result["confidence"]["top_score"], 0.349999)
        self.assertEqual(result["confidence"]["level"], "low")


if __name__ == "__main__":
    unittest.main()
