from __future__ import annotations

import unittest

from onecode_skill_sanitizer.intent import normalize_task
from onecode_skill_sanitizer.need_gate import decide_skill_need
from onecode_skill_sanitizer.skill_candidates import HIGH_FREQUENCY_SKILL_NAMES


class NeedGateTest(unittest.TestCase):
    def test_none_for_greeting_inventory_explanation_and_negation(self):
        cases = (
            ("hi", "no_specialized_need"),
            ("list the seven high-frequency skills; do not invoke them", "inventory_only"),
            ("解释 code-review-risk 是什么，不要使用它", "explanation_only"),
            ("do not use any skill; just answer yes", "all_candidates_excluded"),
        )
        for task, reason in cases:
            with self.subTest(task=task):
                decision = decide_skill_need(normalize_task(task))
                self.assertEqual(decision["decision"], "none")
                self.assertIn(reason, decision["reason_codes"])
                self.assertEqual(decision["required_capabilities"], [])

    def test_single_and_composite_capabilities_are_distinct(self):
        single = decide_skill_need(normalize_task("review this patch for regressions"))
        composite = decide_skill_need(
            normalize_task("polish the dashboard, then verify it in a real browser")
        )

        self.assertEqual(single["decision"], "single")
        self.assertEqual(single["required_capabilities"], ["code.review"])
        self.assertEqual(composite["decision"], "composite")
        self.assertEqual(
            composite["required_capabilities"],
            ["design.ui_review", "execution.browser_check"],
        )

    def test_current_request_overrides_stale_history(self):
        normalized = normalize_task(
            "Earlier we planned browser testing. Current request: only review the patch; do not open a browser."
        )
        decision = decide_skill_need(normalized)

        self.assertEqual(decision["required_capabilities"], ["code.review"])
        self.assertIn("execution-browser-check", decision["excluded_skills"])

    def test_specialized_but_ambiguous_request_clarifies(self):
        for task in ("check the UI", "看一下这个变更", "review the package"):
            with self.subTest(task=task):
                decision = decide_skill_need(normalize_task(task))
                self.assertEqual(decision["decision"], "clarify")
                self.assertEqual(decision["reason_codes"], ["adjacent_capability_ambiguous"])

    def test_conflicting_explicit_skill_constraint_clarifies(self):
        decision = decide_skill_need(
            normalize_task("Use design-ui-review and do not use design-ui-review")
        )
        self.assertEqual(decision["decision"], "clarify")
        self.assertEqual(decision["reason_codes"], ["conflicting_explicit_constraint"])

    def test_missing_inputs_and_risk_derived_verification_are_structured(self):
        missing = decide_skill_need(
            normalize_task("Add regression coverage, but the behavior under test is unknown")
        )
        risky = decide_skill_need(normalize_task("Fix this shared parser bug"))

        self.assertEqual(missing["missing_inputs"], ["behavior_or_change_under_test"])
        self.assertEqual(risky["mandatory_capabilities"], ["code.test"])
        self.assertIn("code.test", risky["required_capabilities"])

    def test_mandatory_verification_requires_an_affirmative_action(self):
        decision = decide_skill_need(normalize_task("do not fix the parser bug"))

        self.assertEqual(decision["decision"], "none")
        self.assertEqual(decision["required_capabilities"], [])
        self.assertEqual(decision["mandatory_capabilities"], [])

    def test_mandatory_verification_respects_explicit_exclusions(self):
        cases = (
            ("fix the parser bug; do not test it", False),
            ("fix the parser bug; do not use any skills", True),
            ("不要使用任何技能；修复解析器", True),
        )
        for task, excludes_all in cases:
            with self.subTest(task=task):
                decision = decide_skill_need(normalize_task(task))
                self.assertEqual(decision["decision"], "clarify")
                self.assertEqual(
                    decision["reason_codes"], ["conflicting_explicit_constraint"]
                )
                self.assertEqual(decision["required_capabilities"], [])
                self.assertEqual(decision["mandatory_capabilities"], [])
                self.assertIn("code-test-regression", decision["excluded_skills"])
                if excludes_all:
                    self.assertEqual(
                        decision["excluded_skills"],
                        list(HIGH_FREQUENCY_SKILL_NAMES),
                    )

    def test_canonical_skill_matching_survives_current_intent_normalization(self):
        test_request = decide_skill_need(
            normalize_task(
                "History: use code-review-risk. Current request: use code-test-regression"
            )
        )
        conflict = decide_skill_need(
            normalize_task(
                "History: x. Current request: Use design-ui-review and do not use design-ui-review"
            )
        )

        self.assertEqual(test_request["decision"], "single")
        self.assertEqual(test_request["explicit_skills"], ["code-test-regression"])
        self.assertEqual(test_request["required_capabilities"], ["code.test"])
        self.assertNotIn("code-review-risk", test_request["explicit_skills"])
        self.assertEqual(conflict["decision"], "clarify")
        self.assertEqual(conflict["explicit_skills"], ["design-ui-review"])
        self.assertIn("design-ui-review", conflict["excluded_skills"])
        self.assertEqual(
            conflict["reason_codes"], ["conflicting_explicit_constraint"]
        )

    def test_canonical_skill_matching_uses_token_boundaries(self):
        decision = decide_skill_need(normalize_task("use xcode-test-regressioner"))

        self.assertEqual(decision["decision"], "none")
        self.assertEqual(decision["explicit_skills"], [])
        self.assertEqual(decision["required_capabilities"], [])

    def test_negation_is_clause_and_object_scoped(self):
        canonical = decide_skill_need(
            normalize_task("do not use design-ui-review; use code-review-risk")
        )
        mixed_review = decide_skill_need(
            normalize_task("do not review the UI; review this patch")
        )

        self.assertEqual(canonical["decision"], "single")
        self.assertEqual(canonical["required_capabilities"], ["code.review"])
        self.assertEqual(canonical["explicit_skills"], ["code-review-risk"])
        self.assertIn("design-ui-review", canonical["excluded_skills"])
        self.assertNotIn("code-review-risk", canonical["excluded_skills"])
        self.assertEqual(mixed_review["decision"], "single")
        self.assertEqual(mixed_review["required_capabilities"], ["code.review"])
        self.assertIn("design-ui-review", mixed_review["excluded_skills"])
        self.assertNotIn("code-review-risk", mixed_review["excluded_skills"])

    def test_negation_scope_stops_at_required_clause_boundaries(self):
        for separator in (".", ";", "\n", "。", "；", "！", "？", "!", "?"):
            task = f"do not review the UI{separator} review this patch"
            with self.subTest(separator=separator):
                decision = decide_skill_need(normalize_task(task))
                self.assertEqual(decision["decision"], "single")
                self.assertEqual(decision["required_capabilities"], ["code.review"])
                self.assertIn("design-ui-review", decision["excluded_skills"])
                self.assertNotIn("code-review-risk", decision["excluded_skills"])

    def test_guarded_negative_code_review_does_not_hide_supply_chain_action(self):
        for task in (
            "Audit package provenance only; this is not a general code review.",
            "Audit package provenance only; no general code review.",
        ):
            with self.subTest(task=task):
                decision = decide_skill_need(normalize_task(task))
                self.assertEqual(decision["decision"], "single")
                self.assertEqual(
                    decision["required_capabilities"], ["security.supply_chain"]
                )
                self.assertIn("code-review-risk", decision["excluded_skills"])

    def test_explanation_and_inventory_clauses_take_precedence(self):
        explanation_cases = (
            "Explain test strategy; do not create regression coverage.",
            "什么是浏览器检查 Skill？只解释。",
        )
        for task in explanation_cases:
            with self.subTest(task=task):
                decision = decide_skill_need(normalize_task(task))
                self.assertEqual(decision["decision"], "none")
                self.assertTrue(decision["explanation_only"])
                self.assertFalse(decision["inventory_only"])
                self.assertEqual(decision["required_capabilities"], [])
                self.assertEqual(decision["reason_codes"], ["explanation_only"])

        inventory = decide_skill_need(
            normalize_task("list the seven skills and show which supports browser testing")
        )
        self.assertEqual(inventory["decision"], "none")
        self.assertFalse(inventory["explanation_only"])
        self.assertTrue(inventory["inventory_only"])
        self.assertEqual(inventory["required_capabilities"], [])
        self.assertEqual(inventory["reason_codes"], ["inventory_only"])

    def test_separate_action_clause_survives_explanation_or_inventory(self):
        explained = decide_skill_need(
            normalize_task("Explain code-review-risk, then review this patch")
        )
        inventoried = decide_skill_need(
            normalize_task("list the skills, then open the page in a real browser")
        )

        self.assertEqual(explained["decision"], "single")
        self.assertEqual(explained["required_capabilities"], ["code.review"])
        self.assertEqual(explained["explicit_skills"], [])
        self.assertFalse(explained["explanation_only"])
        self.assertEqual(inventoried["decision"], "single")
        self.assertEqual(
            inventoried["required_capabilities"], ["execution.browser_check"]
        )
        self.assertFalse(inventoried["inventory_only"])

    def test_positive_explicit_requests_are_distinct_from_exclusions(self):
        negative_only = decide_skill_need(
            normalize_task("review this patch; do not use code-test-regression")
        )
        partial_conflict = decide_skill_need(
            normalize_task(
                "Use execution-browser-check and code-test-regression; "
                "do not use execution-browser-check"
            )
        )

        self.assertEqual(negative_only["decision"], "single")
        self.assertEqual(negative_only["required_capabilities"], ["code.review"])
        self.assertEqual(negative_only["explicit_skills"], [])
        self.assertIn("code-test-regression", negative_only["excluded_skills"])
        self.assertEqual(partial_conflict["decision"], "clarify")
        self.assertEqual(
            partial_conflict["explicit_skills"],
            ["code-test-regression", "execution-browser-check"],
        )
        self.assertIn("execution-browser-check", partial_conflict["excluded_skills"])
        self.assertEqual(partial_conflict["required_capabilities"], [])
        self.assertEqual(
            partial_conflict["reason_codes"], ["conflicting_explicit_constraint"]
        )

    def test_non_action_browser_evidence_is_clause_local(self):
        combined = decide_skill_need(
            normalize_task(
                "Screenshot is attached; open the page in a real browser and verify the flow"
            )
        )
        attachment = decide_skill_need(normalize_task("Screenshot is attached"))

        self.assertEqual(combined["decision"], "single")
        self.assertEqual(
            combined["required_capabilities"], ["execution.browser_check"]
        )
        self.assertEqual(attachment["decision"], "none")
        self.assertEqual(attachment["required_capabilities"], [])

    def test_latin_skill_names_allow_natural_cjk_adjacency(self):
        requested = decide_skill_need(normalize_task("使用code-test-regression"))
        excluded = decide_skill_need(
            normalize_task("修复解析器；不要使用code-test-regression")
        )

        self.assertEqual(requested["decision"], "single")
        self.assertEqual(requested["explicit_skills"], ["code-test-regression"])
        self.assertEqual(requested["required_capabilities"], ["code.test"])
        self.assertEqual(excluded["decision"], "clarify")
        self.assertIn("code-test-regression", excluded["excluded_skills"])
        self.assertEqual(excluded["required_capabilities"], [])
        self.assertEqual(excluded["mandatory_capabilities"], [])

    def test_cjk_capability_negation_allows_natural_adjacency(self):
        cases = (
            ("不要优化页面的视觉一致性", "design-ui-review"),
            ("不要打开浏览器验证页面", "execution-browser-check"),
        )
        for task, excluded_skill in cases:
            with self.subTest(task=task):
                decision = decide_skill_need(normalize_task(task))
                self.assertEqual(decision["decision"], "none")
                self.assertIn(excluded_skill, decision["excluded_skills"])
                self.assertEqual(decision["required_capabilities"], [])

    def test_same_clause_information_only_suppresses_later_evidence(self):
        review = decide_skill_need(
            normalize_task("Review this patch and explain regression test coverage")
        )
        explicit = decide_skill_need(
            normalize_task("Use code-review-risk to explain this patch")
        )

        self.assertEqual(review["decision"], "single")
        self.assertEqual(review["required_capabilities"], ["code.review"])
        self.assertFalse(review["explanation_only"])
        self.assertEqual(explicit["decision"], "single")
        self.assertEqual(explicit["required_capabilities"], ["code.review"])
        self.assertEqual(explicit["explicit_skills"], ["code-review-risk"])
        self.assertFalse(explicit["explanation_only"])

        for task in ("Explain code-review-risk", "Explain how to use code-review-risk"):
            with self.subTest(task=task):
                explanation = decide_skill_need(normalize_task(task))
                self.assertEqual(explanation["decision"], "none")
                self.assertTrue(explanation["explanation_only"])
                self.assertEqual(explanation["explicit_skills"], [])
                self.assertEqual(explanation["required_capabilities"], [])

    def test_bare_canonical_exclusion_is_distinct_from_positive_request(self):
        for task in (
            "Use design-ui-review, not code-review-risk",
            "Use design-ui-review, but not code-review-risk",
        ):
            with self.subTest(task=task):
                decision = decide_skill_need(normalize_task(task))
                self.assertEqual(decision["decision"], "single")
                self.assertEqual(
                    decision["required_capabilities"], ["design.ui_review"]
                )
                self.assertEqual(decision["explicit_skills"], ["design-ui-review"])
                self.assertIn("code-review-risk", decision["excluded_skills"])

        conflict = decide_skill_need(
            normalize_task(
                "Use design-ui-review and code-review-risk, but not code-review-risk"
            )
        )
        self.assertEqual(conflict["decision"], "clarify")
        self.assertEqual(
            conflict["explicit_skills"],
            ["code-review-risk", "design-ui-review"],
        )
        self.assertIn("code-review-risk", conflict["excluded_skills"])
        self.assertEqual(conflict["required_capabilities"], [])
        self.assertEqual(
            conflict["reason_codes"], ["conflicting_explicit_constraint"]
        )

        not_only = decide_skill_need(normalize_task("Use not only design-ui-review"))
        self.assertEqual(not_only["decision"], "single")
        self.assertEqual(not_only["explicit_skills"], ["design-ui-review"])
        self.assertNotIn("design-ui-review", not_only["excluded_skills"])

    def test_quoted_current_request_marker_stays_in_explanation_scope(self):
        decision = decide_skill_need(
            normalize_task('Explain the phrase "current request: review this patch"')
        )

        self.assertEqual(decision["decision"], "none")
        self.assertTrue(decision["explanation_only"])
        self.assertEqual(decision["required_capabilities"], [])

    def test_ambiguous_match_negation_is_local_to_the_match(self):
        mixed = decide_skill_need(normalize_task("do not test, review this change"))
        negated = decide_skill_need(normalize_task("do not review this change"))

        self.assertEqual(mixed["decision"], "clarify")
        self.assertEqual(mixed["reason_codes"], ["adjacent_capability_ambiguous"])
        self.assertIn("code-test-regression", mixed["excluded_skills"])
        self.assertEqual(negated["decision"], "none")
        self.assertNotIn("adjacent_capability_ambiguous", negated["reason_codes"])

    def test_browser_flow_action_survives_design_exclusion(self):
        decision = decide_skill_need(
            normalize_task(
                "Do not critique design; run the existing UI flow in a browser"
            )
        )

        self.assertEqual(decision["decision"], "single")
        self.assertEqual(
            decision["required_capabilities"], ["execution.browser_check"]
        )
        self.assertIn("design-ui-review", decision["excluded_skills"])
        self.assertNotIn("execution-browser-check", decision["excluded_skills"])


if __name__ == "__main__":
    unittest.main()
