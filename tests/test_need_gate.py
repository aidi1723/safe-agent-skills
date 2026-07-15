from __future__ import annotations

import unittest

from onecode_skill_sanitizer.intent import normalize_task
from onecode_skill_sanitizer.need_gate import decide_skill_need


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


if __name__ == "__main__":
    unittest.main()
