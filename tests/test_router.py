import unittest

from onecode_skill_sanitizer.router import (
    build_capability_coverage,
    build_execution_plan,
    build_selection_explanations,
    build_task_profile,
    route_scenario_task,
    score_bundle_for_profile,
)


class RouterTest(unittest.TestCase):
    def test_build_task_profile_detects_website_launch(self):
        profile = build_task_profile("build a product website and prepare launch checks")

        self.assertEqual(profile["task_type"], "website_build")
        self.assertEqual(profile["primary_domain"], "web")
        self.assertIn("design", profile["secondary_domains"])
        self.assertIn("website", profile["artifact_types"])
        self.assertIn("public_release", profile["risk_flags"])
        self.assertIn("ui_review", profile["required_capabilities"])
        self.assertIn("publish_check", profile["required_capabilities"])

    def test_score_bundle_prefers_matching_scenario(self):
        profile = build_task_profile("review generated code and harden tests before accepting the PR")
        code_bundle = {
            "id": "code-review-hardening",
            "scenario": "Review generated code, pull requests, bug fixes, or automation changes before acceptance.",
            "task_signals": ["code review", "pull request", "generated code", "bug fix", "refactor"],
        }
        website_bundle = {
            "id": "website-build-launch",
            "scenario": "Build or polish a website, landing page, dashboard, or product page.",
            "task_signals": ["website", "landing page", "launch"],
        }

        self.assertGreater(
            score_bundle_for_profile(code_bundle, profile),
            score_bundle_for_profile(website_bundle, profile),
        )

    def test_build_capability_coverage_marks_covered_and_missing(self):
        bundle = {
            "required_capabilities": [
                {
                    "id": "ui_review",
                    "required": True,
                    "preferred_skills": ["design-ui-review"],
                },
                {
                    "id": "seo_copy",
                    "required": True,
                    "preferred_skills": ["content-seo-brief"],
                },
            ]
        }
        skill_names = {"design-ui-review"}

        coverage = build_capability_coverage(bundle, skill_names)

        self.assertEqual(coverage[0]["capability"], "ui_review")
        self.assertEqual(coverage[0]["status"], "covered")
        self.assertEqual(coverage[0]["skill"], "design-ui-review")
        self.assertEqual(coverage[1]["capability"], "seo_copy")
        self.assertEqual(coverage[1]["status"], "missing")
        self.assertEqual(coverage[1]["skill"], "")

    def test_build_execution_plan_uses_bundle_order_and_selected_skills(self):
        bundle = {
            "execution_order": [
                "business-requirements-brief",
                "design-ui-review",
                "content-seo-brief",
            ]
        }
        selected_skills = [
            {"name": "content-seo-brief"},
            {"name": "design-ui-review"},
        ]

        plan = build_execution_plan(bundle, selected_skills)

        self.assertEqual([step["skill"] for step in plan], ["design-ui-review", "content-seo-brief"])
        self.assertEqual(plan[0]["order"], 1)
        self.assertIn("Apply", plan[0]["instruction"])

    def test_build_selection_explanations_assigns_roles(self):
        bundle = {"id": "website-build-launch", "name": "Website Build Launch"}
        coverage = [
            {"capability": "ui_review", "status": "covered", "skill": "design-ui-review"},
            {"capability": "seo_copy", "status": "covered", "skill": "content-seo-brief"},
        ]
        selected_skills = [{"name": "design-ui-review"}, {"name": "content-seo-brief"}]

        explanations = build_selection_explanations(bundle, selected_skills, coverage)

        self.assertEqual(explanations[0]["name"], "website-build-launch")
        self.assertEqual(explanations[0]["type"], "bundle")
        skill_explanations = [item for item in explanations if item["type"] == "skill"]
        self.assertEqual({item["name"] for item in skill_explanations}, {"design-ui-review", "content-seo-brief"})
        self.assertTrue(all(item["confidence"] > 0 for item in skill_explanations))

    def test_route_scenario_task_selects_bundle_skills_first(self):
        bundles_index = {
            "bundles": [
                {
                    "id": "website-build-launch",
                    "name": "Website Build Launch",
                    "scenario": "Build or polish a website and prepare it for release.",
                    "status": "trusted",
                    "task_signals": ["website", "launch"],
                    "skills": ["business-requirements-brief", "design-ui-review", "content-seo-brief"],
                    "required_capabilities": [
                        {"id": "requirements", "required": True, "preferred_skills": ["business-requirements-brief"]},
                        {"id": "ui_review", "required": True, "preferred_skills": ["design-ui-review"]},
                        {"id": "seo_copy", "required": True, "preferred_skills": ["content-seo-brief"]},
                    ],
                    "execution_order": ["business-requirements-brief", "design-ui-review", "content-seo-brief"],
                    "expected_output": ["launch checklist"],
                    "safety_boundary": "Skills provide method only.",
                }
            ]
        }
        selected = [
            {"name": "content-seo-brief", "match_score": 8},
            {"name": "design-ui-review", "match_score": 9},
            {"name": "business-requirements-brief", "match_score": 7},
        ]

        routed = route_scenario_task(
            task="build a product website and prepare launch checks",
            selected_skills=selected,
            bundles_index=bundles_index,
            trusted_skill_names={"business-requirements-brief", "design-ui-review", "content-seo-brief"},
            max_skills=5,
        )

        self.assertEqual(routed["router"]["mode"], "deterministic_scenario_router")
        self.assertEqual(routed["selected_scenario"]["id"], "website-build-launch")
        self.assertEqual(
            [skill["name"] for skill in routed["skills"]],
            [
                "business-requirements-brief",
                "design-ui-review",
                "content-seo-brief",
            ],
        )
        self.assertEqual(
            [step["skill"] for step in routed["execution_plan"]],
            [
                "business-requirements-brief",
                "design-ui-review",
                "content-seo-brief",
            ],
        )
