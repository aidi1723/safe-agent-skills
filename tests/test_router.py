import unittest

from onecode_skill_sanitizer.router import (
    build_capability_coverage,
    build_execution_graph,
    build_execution_plan,
    build_selection_explanations,
    build_task_profile,
    parse_invariant_capabilities,
    route_mesh_task,
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

    def test_build_task_profile_detects_chinese_website_launch(self):
        profile = build_task_profile("构建产品官网并准备上线发布检查")

        self.assertEqual(profile["task_type"], "website_build")
        self.assertEqual(profile["primary_domain"], "web")
        self.assertIn("publish_check", profile["required_capabilities"])

    def test_build_task_profile_detects_ai_interface_design_polish(self):
        profile = build_task_profile("用 UI-UX-Pro-Max 定设计系统，Visual Designer 把控视觉，CSS 动画工具提升 AI 界面质感")

        self.assertEqual(profile["task_type"], "website_build")
        self.assertEqual(profile["primary_domain"], "web")
        self.assertIn("design_consistency", profile["required_capabilities"])
        self.assertIn("ui_review", profile["required_capabilities"])

    def test_build_task_profile_detects_codebase_change_lifecycle(self):
        profile = build_task_profile(
            "Explore 摸清项目地图，Code Review 把关质量，Debugger 定位疑难 bug，Test Engineer 和 Simplify 完善工程全流程"
        )

        self.assertEqual(profile["task_type"], "codebase_change_lifecycle")
        self.assertEqual(profile["primary_domain"], "code")
        self.assertIn("project_context", profile["required_capabilities"])
        self.assertIn("regression_test", profile["required_capabilities"])

    def test_build_task_profile_detects_content_video_production(self):
        profile = build_task_profile("Copywriting 写文案，Content Strategy 规划内容矩阵，Remotion 实现一句话灵感到成片")

        self.assertEqual(profile["task_type"], "content_video_production")
        self.assertEqual(profile["primary_domain"], "content")
        self.assertIn("video_script", profile["required_capabilities"])
        self.assertIn("asset_review", profile["required_capabilities"])

    def test_build_task_profile_detects_agent_planning_orchestration(self):
        profile = build_task_profile("Deep Interview 厘清模糊需求，Plan 和 RALPlan 做方案拆解，Team 实现多 Agent 协同")

        self.assertEqual(profile["task_type"], "agent_planning_orchestration")
        self.assertEqual(profile["primary_domain"], "ai")
        self.assertIn("requirements", profile["required_capabilities"])
        self.assertIn("multi_agent_review", profile["required_capabilities"])

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

    def test_general_task_profile_does_not_select_scenario_bundle(self):
        profile = build_task_profile("帮我看一下这个事情是否合理")
        bundle = {
            "id": "website-build-launch",
            "name": "Website Build Launch",
            "scenario": "Build or polish a website and prepare it for release.",
            "status": "trusted",
            "task_signals": ["website", "launch"],
            "skills": ["business-requirements-brief", "design-ui-review"],
            "required_capabilities": [
                {"id": "requirements", "required": True, "preferred_skills": ["business-requirements-brief"]},
                {"id": "ui_review", "required": True, "preferred_skills": ["design-ui-review"]},
            ],
            "execution_order": ["business-requirements-brief", "design-ui-review"],
        }
        selected = [
            {"name": "business-requirements-brief", "match_score": 0},
            {"name": "design-ui-review", "match_score": 0},
            {"name": "ai-opensquilla-metaskill-workflow", "match_score": 13},
        ]

        routed = route_scenario_task(
            task="帮我看一下这个事情是否合理",
            selected_skills=selected,
            bundles_index={"bundles": [bundle]},
            trusted_skill_names={"business-requirements-brief", "design-ui-review", "ai-opensquilla-metaskill-workflow"},
            max_skills=8,
        )

        self.assertEqual(profile["task_type"], "general")
        self.assertEqual(score_bundle_for_profile(bundle, profile), 0)
        self.assertEqual(routed["selected_scenario"]["id"], "")
        self.assertEqual(routed["selected_scenario"]["match_score"], 0)
        self.assertEqual([skill["name"] for skill in routed["skills"]], ["ai-opensquilla-metaskill-workflow"])
        self.assertEqual(routed["coverage"], [])

    def test_build_task_profile_detects_skill_router_quality_review(self):
        profile = build_task_profile("复查 safe-agent-skills 项目是否达到智能选择和自动搭配 skill 的目标")

        self.assertEqual(profile["task_type"], "skill_router_review")
        self.assertEqual(profile["primary_domain"], "ai")
        self.assertIn("catalog", profile["artifact_types"])
        self.assertIn("skill_selection_quality", profile["required_capabilities"])
        self.assertIn("bundle_quality", profile["required_capabilities"])

    def test_route_scenario_task_selects_skill_router_quality_review_bundle(self):
        bundle = {
            "id": "skill-router-quality-review",
            "name": "Skill Router Quality Review",
            "scenario": "Review skill router quality, automatic selection, and bundle composition behavior.",
            "status": "trusted",
            "task_signals": ["safe-agent-skills", "skill router", "smart skill", "智能选择", "自动搭配"],
            "skills": [
                "ai-opensquilla-metaskill-workflow",
                "ai-opensquilla-token-routing-pattern",
                "ai-tool-schema-protocol-check",
                "ai-output-schema-eval",
                "ai-rule-failure-log-synthesis",
                "code-test-regression",
                "engineering-ci-troubleshoot",
            ],
            "required_capabilities": [
                {
                    "id": "skill_selection_quality",
                    "required": True,
                    "preferred_skills": ["ai-opensquilla-token-routing-pattern"],
                },
                {
                    "id": "bundle_quality",
                    "required": True,
                    "preferred_skills": ["ai-opensquilla-metaskill-workflow"],
                },
                {
                    "id": "schema_contract",
                    "required": True,
                    "preferred_skills": ["ai-tool-schema-protocol-check", "ai-output-schema-eval"],
                },
                {
                    "id": "regression_test",
                    "required": True,
                    "preferred_skills": ["code-test-regression"],
                },
            ],
            "execution_order": [
                "ai-opensquilla-metaskill-workflow",
                "ai-opensquilla-token-routing-pattern",
                "ai-tool-schema-protocol-check",
                "ai-output-schema-eval",
                "ai-rule-failure-log-synthesis",
                "code-test-regression",
                "engineering-ci-troubleshoot",
            ],
        }
        selected = [{"name": name, "match_score": 0} for name in bundle["skills"]]

        routed = route_scenario_task(
            task="复查 safe-agent-skills 项目是否达到智能选择和自动搭配 skill 的目标",
            selected_skills=selected,
            bundles_index={"bundles": [bundle]},
            trusted_skill_names={skill["name"] for skill in selected},
            max_skills=8,
        )

        self.assertEqual(routed["selected_scenario"]["id"], "skill-router-quality-review")
        self.assertIn("skill_selection_quality", [item["capability"] for item in routed["coverage"]])
        self.assertEqual(routed["skills"][0]["name"], "ai-opensquilla-metaskill-workflow")

    def test_route_scenario_task_selects_codebase_change_lifecycle_bundle(self):
        bundle = {
            "id": "codebase-change-lifecycle",
            "name": "Codebase Change Lifecycle",
            "scenario": "Explore a codebase, implement or debug changes, simplify the result, test it, and review before handoff.",
            "status": "trusted",
            "task_signals": ["explore", "debugger", "test engineer", "simplify", "项目地图", "疑难 bug", "工程全流程"],
            "skills": [
                "ecc-agent-coding-safety",
                "code-python-debug",
                "code-review-risk",
                "code-test-regression",
                "code-ast-refactor-safety",
                "code-dead-path-cleanup-review",
                "engineering-build-release",
                "engineering-ci-troubleshoot",
            ],
            "required_capabilities": [
                {"id": "project_context", "required": True, "preferred_skills": ["ecc-agent-coding-safety"]},
                {"id": "debugging", "required": True, "preferred_skills": ["code-python-debug"]},
                {"id": "code_review", "required": True, "preferred_skills": ["code-review-risk"]},
                {"id": "regression_test", "required": True, "preferred_skills": ["code-test-regression"]},
                {"id": "simplification", "required": False, "preferred_skills": ["code-dead-path-cleanup-review"]},
            ],
            "execution_order": [
                "ecc-agent-coding-safety",
                "code-python-debug",
                "code-ast-refactor-safety",
                "code-dead-path-cleanup-review",
                "code-test-regression",
                "code-review-risk",
                "engineering-build-release",
                "engineering-ci-troubleshoot",
            ],
        }
        selected = [{"name": name, "match_score": 0} for name in bundle["skills"]]

        routed = route_scenario_task(
            task="Explore 摸清项目地图，Code Review 把关质量，Debugger 定位疑难 bug，Test Engineer 和 Simplify 完善工程全流程",
            selected_skills=selected,
            bundles_index={"bundles": [bundle]},
            trusted_skill_names={skill["name"] for skill in selected},
            max_skills=8,
        )

        self.assertEqual(routed["selected_scenario"]["id"], "codebase-change-lifecycle")
        self.assertEqual(routed["skills"][0]["name"], "ecc-agent-coding-safety")

    def test_route_scenario_task_selects_agent_planning_orchestration_bundle(self):
        bundle = {
            "id": "agent-planning-orchestration",
            "name": "Agent Planning Orchestration",
            "scenario": "Clarify fuzzy requirements, break down the plan, and coordinate multi-agent execution boundaries.",
            "status": "trusted",
            "task_signals": ["deep interview", "ralplan", "multi agent", "team", "模糊需求", "方案拆解", "多 agent"],
            "skills": [
                "business-requirements-brief",
                "ai-opensquilla-metaskill-workflow",
                "ai-langchain-agent-orchestration",
                "ai-crewai-role-workflow",
                "ai-autogen-multi-agent-review",
                "ai-tool-schema-protocol-check",
                "ai-output-schema-eval",
            ],
            "required_capabilities": [
                {"id": "requirements", "required": True, "preferred_skills": ["business-requirements-brief"]},
                {"id": "workflow_decomposition", "required": True, "preferred_skills": ["ai-opensquilla-metaskill-workflow"]},
                {"id": "agent_orchestration", "required": True, "preferred_skills": ["ai-langchain-agent-orchestration"]},
                {"id": "role_workflow", "required": True, "preferred_skills": ["ai-crewai-role-workflow"]},
                {"id": "multi_agent_review", "required": True, "preferred_skills": ["ai-autogen-multi-agent-review"]},
            ],
            "execution_order": [
                "business-requirements-brief",
                "ai-opensquilla-metaskill-workflow",
                "ai-langchain-agent-orchestration",
                "ai-crewai-role-workflow",
                "ai-autogen-multi-agent-review",
                "ai-tool-schema-protocol-check",
                "ai-output-schema-eval",
            ],
        }
        selected = [{"name": name, "match_score": 0} for name in bundle["skills"]]

        routed = route_scenario_task(
            task="Deep Interview 厘清模糊需求，Plan 和 RALPlan 做方案拆解，Team 实现多 Agent 协同",
            selected_skills=selected,
            bundles_index={"bundles": [bundle]},
            trusted_skill_names={skill["name"] for skill in selected},
            max_skills=8,
        )

        self.assertEqual(routed["selected_scenario"]["id"], "agent-planning-orchestration")
        self.assertEqual(routed["skills"][0]["name"], "business-requirements-brief")

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

    def test_parse_invariant_capabilities_maps_hard_boundaries(self):
        capabilities = parse_invariant_capabilities(
            "绝对不泄露 API 密钥；公开文案不能违反广告法；前端必须响应式验证"
        )

        self.assertIn("secret_redaction", capabilities)
        self.assertIn("claims_compliance", capabilities)
        self.assertIn("responsive_check", capabilities)

    def test_route_mesh_task_adds_invariant_skills_and_prunes_overlap(self):
        bundles_index = {
            "bundles": [
                {
                    "id": "website-build-launch",
                    "name": "Website Build Launch",
                    "scenario": "Build or polish a website and prepare it for release.",
                    "status": "trusted",
                    "task_signals": ["website", "landing page", "launch"],
                    "skills": [
                        "business-requirements-brief",
                        "design-ui-review",
                        "design-system-consistency",
                        "content-seo-brief",
                        "execution-browser-check",
                    ],
                    "required_capabilities": [
                        {"id": "requirements", "required": True, "preferred_skills": ["business-requirements-brief"]},
                        {"id": "ui_review", "required": True, "preferred_skills": ["design-ui-review"]},
                        {"id": "seo_copy", "required": True, "preferred_skills": ["content-seo-brief"]},
                    ],
                    "execution_order": [
                        "business-requirements-brief",
                        "design-ui-review",
                        "design-system-consistency",
                        "content-seo-brief",
                        "execution-browser-check",
                    ],
                    "expected_output": ["launch checklist"],
                    "safety_boundary": "Skills provide method only.",
                }
            ]
        }
        overlap_groups = {
            "groups": [
                {
                    "id": "ui-quality-review",
                    "status": "trusted",
                    "primary_skill": "design-ui-review",
                    "adjacent_skills": ["design-system-consistency", "design-responsive-viewport-check"],
                    "use_before": [],
                    "use_after": [],
                }
            ]
        }
        selected = [
            {"name": "business-requirements-brief", "match_score": 7, "taxonomy": {"category": "business"}},
            {"name": "design-ui-review", "match_score": 9, "taxonomy": {"category": "design"}},
            {"name": "design-system-consistency", "match_score": 8, "taxonomy": {"category": "design"}},
            {"name": "design-responsive-viewport-check", "match_score": 0, "taxonomy": {"category": "design"}},
            {"name": "content-seo-brief", "match_score": 8, "taxonomy": {"category": "content"}},
            {"name": "content-claims-compliance-filter", "match_score": 0, "taxonomy": {"category": "content"}},
            {"name": "security-secret-context-redaction", "match_score": 0, "taxonomy": {"category": "security"}},
            {"name": "execution-browser-check", "match_score": 6, "taxonomy": {"category": "execution"}},
        ]

        routed = route_mesh_task(
            task="build a landing page and prepare launch checks",
            invariants=["不能泄露密钥", "公开文案不能违反广告法", "必须响应式验证"],
            selected_skills=selected,
            bundles_index=bundles_index,
            trusted_skill_names={skill["name"] for skill in selected},
            overlap_groups=overlap_groups,
            max_skills=6,
            strategy="balanced",
        )

        names = [skill["name"] for skill in routed["skills"]]
        self.assertEqual(routed["router"]["mode"], "deterministic_mesh_router")
        self.assertIn("security-secret-context-redaction", names)
        self.assertIn("content-claims-compliance-filter", names)
        self.assertIn("design-responsive-viewport-check", names)
        self.assertIn("design-system-consistency", routed["pruned_skills"])
        self.assertEqual(routed["execution_graph"]["nodes"][0]["skill"], "security-secret-context-redaction")
        self.assertTrue(routed["execution_graph"]["edges"])

    def test_build_execution_graph_exposes_stage_gates_and_parallel_groups(self):
        graph = build_execution_graph(
            [
                {"name": "security-secret-context-redaction"},
                {"name": "research-source-check"},
                {"name": "business-requirements-brief"},
                {"name": "design-ui-review"},
                {"name": "code-test-regression"},
                {"name": "execution-publish-check"},
            ]
        )

        nodes_by_skill = {node["skill"]: node for node in graph["nodes"]}
        self.assertEqual(graph["schema_version"], 1)
        self.assertTrue(graph["acyclic"])
        self.assertEqual(nodes_by_skill["security-secret-context-redaction"]["gate"], "preflight")
        self.assertEqual(nodes_by_skill["code-test-regression"]["gate"], "verification")
        self.assertEqual(nodes_by_skill["research-source-check"]["parallel_group"], "source")
        self.assertIn(
            {"from": nodes_by_skill["business-requirements-brief"]["id"], "to": nodes_by_skill["design-ui-review"]["id"], "type": "stage_order"},
            graph["edges"],
        )
        self.assertIn("parallel_groups", graph)
        self.assertIn("source", graph["parallel_groups"])

    def test_route_mesh_strategy_changes_optional_verification_depth(self):
        bundles_index = {
            "bundles": [
                {
                    "id": "website-build-launch",
                    "name": "Website Build Launch",
                    "scenario": "Build or polish a website and prepare it for release.",
                    "status": "trusted",
                    "task_signals": ["website", "landing page", "launch"],
                    "skills": [
                        "business-requirements-brief",
                        "design-ui-review",
                        "content-seo-brief",
                        "execution-browser-check",
                        "execution-playwright-browser-automation",
                        "execution-publish-check",
                    ],
                    "required_capabilities": [
                        {"id": "requirements", "required": True, "preferred_skills": ["business-requirements-brief"]},
                        {"id": "ui_review", "required": True, "preferred_skills": ["design-ui-review"]},
                        {"id": "seo_copy", "required": True, "preferred_skills": ["content-seo-brief"]},
                        {"id": "browser_verification", "required": True, "preferred_skills": ["execution-browser-check"]},
                        {"id": "publish_check", "required": True, "preferred_skills": ["execution-publish-check"]},
                    ],
                    "execution_order": [
                        "business-requirements-brief",
                        "design-ui-review",
                        "content-seo-brief",
                        "execution-browser-check",
                        "execution-playwright-browser-automation",
                        "execution-publish-check",
                    ],
                }
            ]
        }
        selected = [
            {"name": "business-requirements-brief", "match_score": 8},
            {"name": "design-ui-review", "match_score": 9},
            {"name": "content-seo-brief", "match_score": 8},
            {"name": "execution-browser-check", "match_score": 7},
            {"name": "execution-playwright-browser-automation", "match_score": 6},
            {"name": "execution-publish-check", "match_score": 7},
            {"name": "design-system-consistency", "match_score": 6},
        ]
        trusted = {skill["name"] for skill in selected}

        fast = route_mesh_task(
            task="build a landing page and prepare launch checks",
            invariants=None,
            selected_skills=selected,
            bundles_index=bundles_index,
            trusted_skill_names=trusted,
            overlap_groups=None,
            max_skills=6,
            strategy="fast",
        )
        deep = route_mesh_task(
            task="build a landing page and prepare launch checks",
            invariants=None,
            selected_skills=selected,
            bundles_index=bundles_index,
            trusted_skill_names=trusted,
            overlap_groups=None,
            max_skills=6,
            strategy="deep",
        )

        fast_names = [skill["name"] for skill in fast["skills"]]
        deep_names = [skill["name"] for skill in deep["skills"]]
        self.assertNotIn("execution-playwright-browser-automation", fast_names)
        self.assertIn("execution-playwright-browser-automation", deep_names)
        self.assertIn("design-system-consistency", deep_names)
