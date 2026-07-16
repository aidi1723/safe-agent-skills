from __future__ import annotations

import unittest

from onecode_skill_sanitizer.intent import normalize_task
from onecode_skill_sanitizer.need_gate import (
    _canonical_action_events,
    decide_skill_need,
    positive_explicit_skill_occurrences,
)
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

    def test_repo_mapping_accepts_target_aliases_in_both_word_orders(self):
        tasks = (
            "Map the monorepo before changing the billing boundary.",
            "repo map please: identify module owners and entrypoints",
        )
        for task in tasks:
            with self.subTest(task=task):
                decision = decide_skill_need(normalize_task(task))
                self.assertEqual(decision["decision"], "single")
                self.assertEqual(decision["required_capabilities"], ["code.explore"])

    def test_implementation_ownership_questions_require_code_exploration(self):
        decision = decide_skill_need(
            normalize_task(
                "Where is quota enforcement implemented, and which services consume it?"
            )
        )

        self.assertEqual(decision["decision"], "single")
        self.assertEqual(decision["required_capabilities"], ["code.explore"])

    def test_qualified_patch_and_diff_review_phrases_require_code_review(self):
        tasks = (
            "Review the authorization patch for race-condition risks.",
            "Inspect only the payment diff for correctness defects.",
        )
        for task in tasks:
            with self.subTest(task=task):
                decision = decide_skill_need(normalize_task(task))
                self.assertEqual(decision["decision"], "single")
                self.assertEqual(decision["required_capabilities"], ["code.review"])

    def test_source_freshness_with_citation_request_requires_research(self):
        decision = decide_skill_need(
            normalize_task(
                "Determine whether this benchmark remains up to date and cite the publication."
            )
        )

        self.assertEqual(decision["decision"], "single")
        self.assertEqual(decision["required_capabilities"], ["research.source"])

    def test_freshness_words_without_source_verification_do_not_require_research(self):
        negatives = (
            "Change the current source file before release.",
            "Return the latest record from the local cache.",
            "Verify the current source file compiles before commit.",
        )
        positives = (
            "Verify whether the current source is authoritative and cite it.",
            "Verify whether the current official source is authoritative and cite it.",
            "Research the latest official record and cite the publication.",
        )

        for task in negatives:
            with self.subTest(task=task, expected="none"):
                decision = decide_skill_need(normalize_task(task))
                self.assertEqual(decision["decision"], "none")
                self.assertEqual(decision["required_capabilities"], [])
        for task in positives:
            with self.subTest(task=task, expected="research"):
                decision = decide_skill_need(normalize_task(task))
                self.assertEqual(decision["decision"], "single")
                self.assertEqual(
                    decision["required_capabilities"], ["research.source"]
                )

    def test_specific_ui_critique_language_requires_design_review(self):
        tasks = (
            "UI critique: inspect density, surfaces, and empty states.",
            "评审这个界面的配色、布局和信息密度。",
        )
        for task in tasks:
            with self.subTest(task=task):
                decision = decide_skill_need(normalize_task(task))
                self.assertEqual(decision["decision"], "single")
                self.assertEqual(
                    decision["required_capabilities"], ["design.ui_review"]
                )

    def test_code_review_color_mentions_need_ui_context_for_design_review(self):
        code_only = decide_skill_need(
            normalize_task("Review the patch that changes CLI error colors.")
        )
        code_and_database = decide_skill_need(
            normalize_task(
                "Review the patch that changes CLI colors and the database layout."
            )
        )
        design_only = decide_skill_need(
            normalize_task("Review the checkout UI colors and layout.")
        )

        self.assertEqual(code_only["decision"], "single")
        self.assertEqual(code_only["required_capabilities"], ["code.review"])
        self.assertEqual(code_and_database["decision"], "single")
        self.assertEqual(
            code_and_database["required_capabilities"], ["code.review"]
        )
        self.assertEqual(design_only["decision"], "single")
        self.assertEqual(
            design_only["required_capabilities"], ["design.ui_review"]
        )

    def test_qualified_code_review_does_not_span_a_negated_pr_object(self):
        source_only = decide_skill_need(
            normalize_task("Review the primary source, not the PR.")
        )
        review_only = decide_skill_need(
            normalize_task("Review the payment PR for regression risks.")
        )

        self.assertEqual(source_only["decision"], "single")
        self.assertEqual(
            source_only["required_capabilities"], ["research.source"]
        )
        self.assertEqual(review_only["decision"], "single")
        self.assertEqual(review_only["required_capabilities"], ["code.review"])

    def test_hyphenated_browser_check_is_an_execution_action(self):
        decision = decide_skill_need(
            normalize_task(
                "Browser-check the checkout route before release."
            )
        )

        self.assertEqual(decision["decision"], "single")
        self.assertEqual(
            decision["required_capabilities"], ["execution.browser_check"]
        )

    def test_running_a_ui_flow_is_a_browser_execution_action(self):
        decision = decide_skill_need(
            normalize_task("Run the UI flow for signup and record the result.")
        )
        excluded = decide_skill_need(
            normalize_task("Do not run the UI flow for signup; only summarize the request.")
        )

        self.assertEqual(decision["decision"], "single")
        self.assertEqual(
            decision["required_capabilities"], ["execution.browser_check"]
        )
        self.assertEqual(excluded["decision"], "none")
        self.assertIn("execution-browser-check", excluded["excluded_skills"])

    def test_ui_flow_unit_tests_without_a_browser_are_not_browser_execution(self):
        unit_tests = decide_skill_need(
            normalize_task(
                "Run the UI flow unit tests without opening a browser."
            )
        )
        browser_flow = decide_skill_need(
            normalize_task("Run the UI flow in a browser.")
        )

        self.assertEqual(unit_tests["decision"], "none")
        self.assertEqual(unit_tests["required_capabilities"], [])
        self.assertEqual(browser_flow["decision"], "single")
        self.assertEqual(
            browser_flow["required_capabilities"], ["execution.browser_check"]
        )

    def test_browser_visible_smoke_test_is_an_execution_action(self):
        positive = decide_skill_need(
            normalize_task("Smoke-test the browser-visible checkout behavior.")
        )
        negative = decide_skill_need(
            normalize_task(
                "Do not smoke-test the browser-visible checkout behavior; just describe it."
            )
        )

        self.assertEqual(
            positive["required_capabilities"], ["execution.browser_check"]
        )
        self.assertEqual(negative["decision"], "none")
        self.assertIn("execution-browser-check", negative["excluded_skills"])

    def test_package_source_and_license_audit_requires_supply_chain_review(self):
        decision = decide_skill_need(
            normalize_task(
                "npm audit the package source, license, and release chain before adoption."
            )
        )

        self.assertEqual(decision["decision"], "single")
        self.assertEqual(
            decision["required_capabilities"], ["security.supply_chain"]
        )

    def test_chinese_repository_alias_requires_code_exploration(self):
        decision = decide_skill_need(
            normalize_task("先梳理仓库，再定位订单状态的所有者。")
        )

        self.assertEqual(decision["decision"], "single")
        self.assertEqual(decision["required_capabilities"], ["code.explore"])

    def test_primary_source_text_does_not_alias_the_pr_token(self):
        decision = decide_skill_need(
            normalize_task(
                "Consult primary sources and review package provenance before adoption."
            )
        )

        self.assertEqual(
            decision["required_capabilities"],
            ["research.source", "security.supply_chain"],
        )

    def test_mapping_local_integration_is_code_exploration(self):
        decision = decide_skill_need(
            normalize_task(
                "Research official documentation, assess package trust, and map the local wiring."
            )
        )

        self.assertEqual(decision["decision"], "composite")
        self.assertEqual(
            set(decision["required_capabilities"]),
            {"code.explore", "research.source", "security.supply_chain"},
        )

    def test_qualified_claim_verification_requires_research(self):
        decision = decide_skill_need(
            normalize_task(
                "Verify supplier warranty claims before evaluating package trust."
            )
        )

        self.assertEqual(decision["decision"], "composite")
        self.assertEqual(
            decision["required_capabilities"],
            ["research.source", "security.supply_chain"],
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

    def test_then_inherits_an_explicit_canonical_skill_directive(self):
        decision = decide_skill_need(
            normalize_task(
                "Use code-review-risk, then code-test-regression."
            )
        )
        explanation = decide_skill_need(
            normalize_task(
                "Explain code-review-risk, then code-test-regression."
            )
        )

        self.assertEqual(decision["decision"], "composite")
        self.assertEqual(
            decision["required_capabilities"], ["code.review", "code.test"]
        )
        self.assertEqual(
            decision["explicit_skills"],
            ["code-review-risk", "code-test-regression"],
        )
        self.assertEqual(explanation["decision"], "none")
        self.assertEqual(explanation["explicit_skills"], [])

    def test_positive_explicit_skill_occurrences_are_span_local(self):
        informational = (
            "Use code-review-risk and code-test-regression, but explain "
            "code-review-risk before code-test-regression."
        )
        repeated = (
            "Use code-review-risk before code-test-regression, then use "
            "code-test-regression after code-review-risk."
        )

        informational_occurrences = positive_explicit_skill_occurrences(
            informational
        )
        repeated_occurrences = positive_explicit_skill_occurrences(repeated)

        self.assertEqual(
            [name for name, _, _ in informational_occurrences],
            ["code-review-risk", "code-test-regression"],
        )
        self.assertEqual(
            [name for name, _, _ in repeated_occurrences],
            [
                "code-review-risk",
                "code-test-regression",
                "code-test-regression",
                "code-review-risk",
            ],
        )
        active_cases = (
            "Use, as planned, code-review-risk before code-test-regression.",
            "As discussed, use code-review-risk before code-test-regression.",
            "The documentation mentions old routing. Now use code-review-risk "
            "before code-test-regression.",
            "Explain code-review-risk, then use code-review-risk before "
            "code-test-regression.",
        )
        active_occurrences = [
            positive_explicit_skill_occurrences(task) for task in active_cases
        ]
        for task, occurrences in zip(active_cases, active_occurrences):
            with self.subTest(task=task):
                self.assertEqual(
                    [name for name, _, _ in occurrences],
                    ["code-review-risk", "code-test-regression"],
                )
        for text, occurrences in (
            (informational, informational_occurrences),
            (repeated, repeated_occurrences),
            *zip(active_cases, active_occurrences),
        ):
            for name, start, end in occurrences:
                self.assertEqual(text[start:end], name)

    def test_capability_actions_use_local_information_transitions(self):
        reopened = decide_skill_need(
            normalize_task(
                "The documentation mentions old routing, but review this patch."
            )
        )
        reported = decide_skill_need(
            normalize_task("The documentation mentions review this patch.")
        )
        passive_reported = decide_skill_need(
            normalize_task(
                "code-test-regression appeared in docs with review this patch."
            )
        )
        before_report = decide_skill_need(
            normalize_task(
                "Review this patch, but the documentation mentions old routing."
            )
        )
        negated = decide_skill_need(
            normalize_task(
                "The documentation mentions old routing, but do not review this patch."
            )
        )

        self.assertEqual(reopened["required_capabilities"], ["code.review"])
        self.assertEqual(reported["decision"], "none")
        self.assertEqual(reported["required_capabilities"], [])
        self.assertEqual(passive_reported["decision"], "none")
        self.assertEqual(passive_reported["required_capabilities"], [])
        self.assertEqual(before_report["required_capabilities"], ["code.review"])
        self.assertEqual(negated["decision"], "none")
        self.assertIn("code-review-risk", negated["excluded_skills"])

    def test_action_span_events_distinguish_reporting_from_directives(self):
        imperative = (
            "Be sure to use code-review-risk before code-test-regression."
        )
        reports = (
            "The documentation mentioned code-review-risk before "
            "code-test-regression.",
            "The documentation listed code-review-risk before "
            "code-test-regression.",
            "The documentation recorded code-review-risk before "
            "code-test-regression.",
            "The documentation showed code-review-risk before "
            "code-test-regression.",
            "Previously, we discussed code-review-risk before "
            "code-test-regression.",
        )

        self.assertEqual(
            [
                name
                for name, _, _ in positive_explicit_skill_occurrences(imperative)
            ],
            ["code-review-risk", "code-test-regression"],
        )
        for task in reports:
            with self.subTest(task=task):
                self.assertIn(
                    "information",
                    [event for _, _, event, _ in _canonical_action_events(task)],
                )
                self.assertEqual(positive_explicit_skill_occurrences(task), [])

        explanations = (
            "Explain the use of code-review-risk before "
            "code-test-regression.",
            "Explain how best to use code-review-risk before "
            "code-test-regression.",
            "解释如何正确使用 code-review-risk before "
            "code-test-regression.",
        )
        for task in explanations:
            with self.subTest(task=task):
                self.assertNotIn(
                    "positive",
                    [event for _, _, event, _ in _canonical_action_events(task)],
                )
                self.assertEqual(positive_explicit_skill_occurrences(task), [])

        passive = (
            "Use code-review-risk, while code-test-regression was mentioned "
            "in the documentation before execution-browser-check."
        )
        passive_events = _canonical_action_events(passive)
        reported_start = passive.index("code-test-regression")
        self.assertEqual(
            [event for start, _, event, _ in passive_events if start == reported_start],
            ["information", "skill"],
        )

    def test_bare_negative_action_event_requires_an_adjacent_skill(self):
        unrelated = (
            "Use code-review-risk, not the generic reviewer, before "
            "code-test-regression."
        )
        adjacent = (
            "Use code-review-risk, not use code-test-regression."
        )

        self.assertNotIn(
            "negative",
            [event for _, _, event, _ in _canonical_action_events(unrelated)],
        )
        self.assertEqual(
            [
                name
                for name, _, _ in positive_explicit_skill_occurrences(unrelated)
            ],
            ["code-review-risk", "code-test-regression"],
        )
        self.assertIn(
            "negative",
            [event for _, _, event, _ in _canonical_action_events(adjacent)],
        )
        self.assertEqual(
            [name for name, _, _ in positive_explicit_skill_occurrences(adjacent)],
            ["code-review-risk"],
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

    def test_completed_code_review_artifact_is_not_a_new_review_action(self):
        completed = decide_skill_need(
            normalize_task(
                "The code review report is complete; only add regression tests."
            )
        )
        later_action = decide_skill_need(
            normalize_task(
                "The code review report is complete; review the new billing patch."
            )
        )

        self.assertEqual(completed["required_capabilities"], ["code.test"])
        self.assertEqual(later_action["required_capabilities"], ["code.review"])

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

    def test_browser_flow_mentions_require_action_evidence(self):
        for task in (
            "Summarize the existing UI flow in a browser compatibility guide",
            "The existing UI flow in a browser is documented",
        ):
            with self.subTest(task=task):
                decision = decide_skill_need(normalize_task(task))
                self.assertEqual(decision["decision"], "none")
                self.assertNotIn(
                    "execution.browser_check", decision["required_capabilities"]
                )

        negated = decide_skill_need(
            normalize_task("Do not critique the UI flow in a browser")
        )
        self.assertNotIn(
            "execution.browser_check", negated["required_capabilities"]
        )
        self.assertIn("design-ui-review", negated["excluded_skills"])

    def test_browser_flow_actions_honor_negation(self):
        for task in (
            "Do not run the existing UI flow in a browser",
            "Don't test the UI flow in a browser",
            "Never exercise the UI flow in a browser",
        ):
            with self.subTest(task=task):
                decision = decide_skill_need(normalize_task(task))
                self.assertNotIn(
                    "execution.browser_check", decision["required_capabilities"]
                )
                self.assertIn(
                    "execution-browser-check", decision["excluded_skills"]
                )


if __name__ == "__main__":
    unittest.main()
