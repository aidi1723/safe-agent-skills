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

        self.assertEqual(result["routing_status"], "incomplete")
        self.assertEqual(result["selected_skill_names"], ["code-review-risk"])
        self.assertEqual(
            result["capability_resolution"]["missing_inputs"],
            ["change_set", "review_scope"],
        )

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

    def test_artifact_producer_conflict_rejects_lower_and_marks_context_missing(self):
        result = compose_skill_selection(
            need(
                "single",
                ("execution.browser_check",),
                missing_inputs=("target_page_or_flow",),
            ),
            [
                candidate("browser-check", "execution.browser_check", 0.9),
                candidate("review-producer", "design.ui_review", 0.5),
            ],
            {
                "browser-check": profile(
                    "browser-check",
                    "execution.browser_check",
                    requires=("ui_review_report",),
                    excludes=("review-producer",),
                ),
                "review-producer": profile(
                    "review-producer",
                    "design.ui_review",
                    evidence=("ui_review_report",),
                ),
            },
            explicit_order=[],
        )

        self.assertEqual(result["routing_status"], "incomplete")
        self.assertEqual(result["selected_skill_names"], ["browser-check"])
        self.assertEqual(
            result["capability_resolution"]["missing_inputs"],
            ["target_page_or_flow", "ui_review_report"],
        )
        self.assertEqual(
            result["selection"]["failure_reason"], "missing_required_input"
        )
        self.assertEqual(
            result["selection"]["conflict_resolutions"],
            [
                {
                    "winner": "browser-check",
                    "rejected": "review-producer",
                    "reason": "higher_final_score",
                    "margin": 0.4,
                }
            ],
        )
        self.assertEqual(result["execution_graph"]["edges"], [])

    def test_low_margin_artifact_conflict_clarifies_when_other_inputs_complete(self):
        result = compose_skill_selection(
            need("single", ("execution.browser_check",)),
            [
                candidate("browser-check", "execution.browser_check", 0.70),
                candidate("review-producer", "design.ui_review", 0.68),
            ],
            {
                "browser-check": profile(
                    "browser-check",
                    "execution.browser_check",
                    requires=("ui_review_report",),
                ),
                "review-producer": profile(
                    "review-producer",
                    "design.ui_review",
                    evidence=("ui_review_report",),
                    conflicts=("browser-check",),
                ),
            },
            explicit_order=[],
        )

        self.assertEqual(result["routing_status"], "clarify")
        self.assertEqual(result["selected_skill_names"], [])
        self.assertEqual(result["missing_capabilities"], [])
        self.assertEqual(result["capability_resolution"]["missing_inputs"], [])
        self.assertEqual(
            result["selection"]["clarification_reason"],
            "conflicting_candidates_low_margin",
        )
        self.assertEqual(
            result["selection"]["conflict_resolutions"],
            [
                {
                    "winner": "",
                    "rejected": "review-producer",
                    "reason": "insufficient_margin",
                    "margin": 0.02,
                }
            ],
        )

    def test_transitive_artifact_closure_applies_conflicts_at_every_step(self):
        result = compose_skill_selection(
            need("single", ("execution.browser_check",)),
            [
                candidate("browser-check", "execution.browser_check", 0.9),
                candidate("review-producer", "design.ui_review", 0.8),
                candidate("source-producer", "code.explore", 0.5),
            ],
            {
                "browser-check": profile(
                    "browser-check",
                    "execution.browser_check",
                    requires=("ui_review_report",),
                ),
                "review-producer": profile(
                    "review-producer",
                    "design.ui_review",
                    requires=("source_map",),
                    evidence=("ui_review_report",),
                    conflicts=("source-producer",),
                ),
                "source-producer": profile(
                    "source-producer",
                    "code.explore",
                    produces=("source_map",),
                ),
            },
            explicit_order=[],
        )

        self.assertEqual(result["routing_status"], "incomplete")
        self.assertEqual(
            result["selected_skill_names"],
            ["browser-check", "review-producer"],
        )
        self.assertEqual(
            result["capability_resolution"]["missing_inputs"], ["source_map"]
        )
        self.assertEqual(
            result["selection"]["conflict_resolutions"],
            [
                {
                    "winner": "review-producer",
                    "rejected": "source-producer",
                    "reason": "higher_final_score",
                    "margin": 0.3,
                }
            ],
        )

    def test_unreachable_adjacent_conflict_does_not_affect_selection(self):
        result = compose_skill_selection(
            need("single", ("execution.browser_check",)),
            [
                candidate("browser-check", "execution.browser_check", 0.70),
                candidate("unrelated-review", "design.ui_review", 0.68),
            ],
            {
                "browser-check": profile(
                    "browser-check",
                    "execution.browser_check",
                    conflicts=("unrelated-review",),
                ),
                "unrelated-review": profile(
                    "unrelated-review", "design.ui_review"
                ),
            },
            explicit_order=[],
        )

        self.assertEqual(result["routing_status"], "complete")
        self.assertEqual(result["selected_skill_names"], ["browser-check"])
        self.assertEqual(result["selection"]["conflict_resolutions"], [])

    def test_missing_capability_takes_precedence_over_conflict_clarification(self):
        result = compose_skill_selection(
            need("composite", ("design.ui_review", "code.test")),
            [
                candidate("a", "design.ui_review", 0.70),
                candidate("b", "design.ui_review", 0.68),
            ],
            {
                "a": profile("a", "design.ui_review", conflicts=("b",)),
                "b": profile("b", "design.ui_review", conflicts=("a",)),
            },
            explicit_order=[],
        )

        self.assertEqual(result["routing_status"], "incomplete")
        self.assertEqual(result["selected_skill_names"], [])
        self.assertEqual(result["missing_capabilities"], ["code.test"])
        self.assertEqual(
            result["selection"]["failure_reason"], "missing_capability"
        )
        self.assertEqual(
            result["selection"]["clarification_reason"],
            "conflicting_candidates_low_margin",
        )
        self.assertEqual(
            result["selection"]["conflict_resolutions"][0]["reason"],
            "insufficient_margin",
        )

    def test_missing_input_takes_precedence_over_conflict_clarification(self):
        result = compose_skill_selection(
            need(
                "single",
                ("design.ui_review",),
                missing_inputs=("behavior_or_change_under_test",),
            ),
            [
                candidate("a", "design.ui_review", 0.70),
                candidate("b", "design.ui_review", 0.68),
            ],
            {
                "a": profile("a", "design.ui_review", conflicts=("b",)),
                "b": profile("b", "design.ui_review", conflicts=("a",)),
            },
            explicit_order=[],
        )

        self.assertEqual(result["routing_status"], "incomplete")
        self.assertEqual(
            result["capability_resolution"]["missing_inputs"],
            ["behavior_or_change_under_test"],
        )
        self.assertEqual(
            result["selection"]["failure_reason"], "missing_required_input"
        )
        self.assertEqual(
            result["selection"]["clarification_reason"],
            "conflicting_candidates_low_margin",
        )
        self.assertEqual(
            result["selection"]["conflict_resolutions"][0]["reason"],
            "insufficient_margin",
        )

    def test_clarification_coverage_excludes_prior_high_margin_losers(self):
        result = compose_skill_selection(
            need(
                "composite",
                ("code.review", "code.test", "execution.browser_check"),
            ),
            [
                candidate("review", "code.review", 0.95),
                candidate("browser", "execution.browser_check", 0.80),
                candidate("review-producer", "design.ui_review", 0.78),
                candidate("test-loser", "code.test", 0.50),
            ],
            {
                "review": profile(
                    "review", "code.review", conflicts=("test-loser",)
                ),
                "browser": profile(
                    "browser",
                    "execution.browser_check",
                    requires=("ui_review_report",),
                ),
                "review-producer": profile(
                    "review-producer",
                    "design.ui_review",
                    evidence=("ui_review_report",),
                    conflicts=("browser",),
                ),
                "test-loser": profile("test-loser", "code.test"),
            },
            explicit_order=[],
        )

        self.assertEqual(result["routing_status"], "incomplete")
        self.assertEqual(result["missing_capabilities"], ["code.test"])
        self.assertEqual(
            [item["reason"] for item in result["selection"]["conflict_resolutions"]],
            ["higher_final_score", "insufficient_margin"],
        )

    def test_multiple_valid_producers_leave_required_context_incomplete(self):
        result = compose_skill_selection(
            need("single", ("execution.browser_check",)),
            [
                candidate("target", "execution.browser_check", 0.9),
                candidate("producer-a", "design.ui_review", 0.7),
                candidate("producer-b", "code.explore", 0.6),
            ],
            {
                "target": profile(
                    "target",
                    "execution.browser_check",
                    requires=("report",),
                ),
                "producer-a": profile(
                    "producer-a", "design.ui_review", evidence=("report",)
                ),
                "producer-b": profile(
                    "producer-b", "code.explore", produces=("report",)
                ),
            },
            explicit_order=[],
        )

        self.assertEqual(result["routing_status"], "incomplete")
        self.assertEqual(result["selected_skill_names"], ["target"])
        self.assertEqual(
            result["capability_resolution"]["missing_inputs"], ["report"]
        )
        self.assertEqual(
            result["selection"]["failure_reason"], "missing_required_input"
        )
        self.assertEqual(result["execution_graph"]["edges"], [])

    def test_uniqueness_is_computed_after_prior_conflict_losers(self):
        result = compose_skill_selection(
            need(
                "composite",
                ("code.review", "execution.browser_check"),
                explicit=("producer-loser",),
            ),
            [
                candidate("review-root", "code.review", 0.95),
                candidate("target", "execution.browser_check", 0.90),
                candidate("valid-producer", "design.ui_review", 0.70),
                candidate("producer-loser", "code.explore", 0.50),
            ],
            {
                "review-root": profile(
                    "review-root",
                    "code.review",
                    conflicts=("producer-loser",),
                ),
                "target": profile(
                    "target",
                    "execution.browser_check",
                    requires=("report",),
                ),
                "valid-producer": profile(
                    "valid-producer",
                    "design.ui_review",
                    evidence=("report",),
                ),
                "producer-loser": profile(
                    "producer-loser",
                    "code.explore",
                    produces=("report",),
                ),
            },
            explicit_order=[],
        )

        self.assertEqual(result["routing_status"], "complete")
        self.assertEqual(
            result["selected_skill_names"],
            ["review-root", "target", "valid-producer"],
        )
        self.assertEqual(
            result["selection"]["marginal_contributions"][-1],
            {
                "skill": "valid-producer",
                "capabilities": [],
                "reason": "required_artifact:report",
            },
        )
        self.assertEqual(
            result["execution_graph"]["edges"],
            [
                {
                    "from": "skill:valid-producer",
                    "to": "skill:target",
                    "type": "artifact_dependency",
                    "evidence": "report",
                }
            ],
        )
        self.assertNotIn("producer-loser", result["selected_skill_names"])

    def test_initial_clarification_does_not_hide_independent_cycle(self):
        result = compose_skill_selection(
            need(
                "composite",
                ("code.review", "code.test", "design.ui_review"),
            ),
            [
                candidate("a", "code.review", 0.90),
                candidate("b", "code.test", 0.85),
                candidate("review-1", "design.ui_review", 0.70),
                candidate("review-2", "design.ui_review", 0.68),
            ],
            {
                "a": profile("a", "code.review", after=("b",)),
                "b": profile("b", "code.test", after=("a",)),
                "review-1": profile(
                    "review-1", "design.ui_review", conflicts=("review-2",)
                ),
                "review-2": profile("review-2", "design.ui_review"),
            },
            explicit_order=[],
        )

        self.assertEqual(result["routing_status"], "blocked")
        self.assertEqual(result["selected_skill_names"], ["a", "b"])
        self.assertFalse(result["execution_graph"]["acyclic"])
        self.assertEqual(
            result["execution_graph"]["reason_codes"], ["dependency_cycle"]
        )
        self.assertEqual(
            result["selection"]["failure_reason"], "dependency_cycle"
        )
        self.assertEqual(
            result["selection"]["clarification_reason"],
            "conflicting_candidates_low_margin",
        )
        self.assertEqual(
            result["selection"]["conflict_resolutions"][-1]["reason"],
            "insufficient_margin",
        )

    def test_artifact_clarification_does_not_hide_independent_cycle(self):
        result = compose_skill_selection(
            need(
                "composite",
                ("code.review", "code.test", "execution.browser_check"),
            ),
            [
                candidate("a", "code.review", 0.90),
                candidate("b", "code.test", 0.85),
                candidate("target", "execution.browser_check", 0.70),
                candidate("producer", "design.ui_review", 0.68),
            ],
            {
                "a": profile("a", "code.review", after=("b",)),
                "b": profile("b", "code.test", after=("a",)),
                "target": profile(
                    "target",
                    "execution.browser_check",
                    requires=("report",),
                    conflicts=("producer",),
                ),
                "producer": profile(
                    "producer", "design.ui_review", evidence=("report",)
                ),
            },
            explicit_order=[],
        )

        self.assertEqual(result["routing_status"], "blocked")
        self.assertEqual(result["selected_skill_names"], ["a", "b"])
        self.assertFalse(result["execution_graph"]["acyclic"])
        self.assertEqual(
            result["execution_graph"]["reason_codes"], ["dependency_cycle"]
        )
        self.assertEqual(
            result["selection"]["failure_reason"], "dependency_cycle"
        )
        self.assertEqual(
            result["selection"]["clarification_reason"],
            "conflicting_candidates_low_margin",
        )

    def test_consumer_loser_restarts_selection_and_prunes_orphan_producer(self):
        result = compose_skill_selection(
            need("single", ("execution.browser_check",)),
            [
                candidate("target", "execution.browser_check", 0.50),
                candidate("producer", "design.ui_review", 0.90),
                candidate("fallback", "execution.browser_check", 0.70),
            ],
            {
                "target": profile(
                    "target",
                    "execution.browser_check",
                    requires=("report",),
                    conflicts=("producer",),
                ),
                "producer": profile(
                    "producer", "design.ui_review", evidence=("report",)
                ),
                "fallback": profile(
                    "fallback", "execution.browser_check"
                ),
            },
            explicit_order=[],
        )

        self.assertEqual(result["routing_status"], "complete")
        self.assertEqual(result["selected_skill_names"], ["fallback"])
        self.assertEqual(
            result["selection"]["marginal_contributions"],
            [
                {
                    "skill": "fallback",
                    "capabilities": ["execution.browser_check"],
                    "reason": "marginal_capability_coverage",
                }
            ],
        )
        self.assertEqual(
            result["selection"]["conflict_resolutions"],
            [
                {
                    "winner": "producer",
                    "rejected": "target",
                    "reason": "higher_final_score",
                    "margin": 0.4,
                }
            ],
        )

    def test_consumer_loser_without_fallback_does_not_leave_orphan_producer(self):
        result = compose_skill_selection(
            need("single", ("execution.browser_check",)),
            [
                candidate("target", "execution.browser_check", 0.50),
                candidate("producer", "design.ui_review", 0.90),
            ],
            {
                "target": profile(
                    "target",
                    "execution.browser_check",
                    requires=("report",),
                    conflicts=("producer",),
                ),
                "producer": profile(
                    "producer", "design.ui_review", evidence=("report",)
                ),
            },
            explicit_order=[],
        )

        self.assertEqual(result["routing_status"], "incomplete")
        self.assertEqual(result["selected_skill_names"], [])
        self.assertEqual(
            result["missing_capabilities"], ["execution.browser_check"]
        )
        self.assertEqual(result["selection"]["marginal_contributions"], [])

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
                    "reason": "higher_final_score",
                    "margin": 0.25,
                }
            ],
        )

    def test_semantic_final_score_winner_has_truthful_conflict_evidence(self):
        deterministic_winner = candidate(
            "deterministic-winner", "design.ui_review", 0.525
        )
        deterministic_winner["deterministic_score"] = 0.70
        deterministic_winner["semantic_score"] = 0.35
        semantic_winner = candidate(
            "semantic-winner", "design.ui_review", 0.70
        )
        semantic_winner["deterministic_score"] = 0.60
        semantic_winner["semantic_score"] = 0.80
        result = compose_skill_selection(
            need("single", ("design.ui_review",)),
            [deterministic_winner, semantic_winner],
            {
                "deterministic-winner": profile(
                    "deterministic-winner",
                    "design.ui_review",
                    conflicts=("semantic-winner",),
                ),
                "semantic-winner": profile(
                    "semantic-winner",
                    "design.ui_review",
                    conflicts=("deterministic-winner",),
                ),
            },
            explicit_order=[],
        )

        self.assertEqual(result["selected_skill_names"], ["semantic-winner"])
        self.assertEqual(
            result["selection"]["conflict_resolutions"],
            [
                {
                    "winner": "semantic-winner",
                    "rejected": "deterministic-winner",
                    "reason": "higher_final_score",
                    "margin": 0.175,
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
