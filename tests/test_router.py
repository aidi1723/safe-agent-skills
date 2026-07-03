import unittest

from onecode_skill_sanitizer.router import (
    build_capability_coverage,
    build_contract_diagnostics,
    build_contract_graph,
    build_execution_graph,
    build_execution_plan,
    build_pipeline_plan,
    build_selection_quality,
    build_selection_explanations,
    build_task_profile,
    execution_role_for_stage,
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

    def test_build_task_profile_prioritizes_chinese_current_intent_over_history(self):
        profile = build_task_profile("历史上下文：构建产品官网并准备发布检查。当前请求：继续优化任务")

        self.assertEqual(profile["task_type"], "general")
        self.assertEqual(profile["primary_domain"], "general")
        self.assertEqual(profile["matched_signal_score"], 0)
        self.assertTrue(profile["current_intent_detected"])
        self.assertIn("继续优化任务", profile["current_intent_text"])
        self.assertIn("构建产品官网", profile["history_context_text"])
        self.assertEqual(profile["current_intent_weight"], 1.0)
        self.assertEqual(profile["history_context_weight"], 0.25)

    def test_build_task_profile_parses_structured_chinese_context_contract(self):
        profile = build_task_profile("当前意图：继续优化任务\n历史摘要：构建产品官网并准备发布检查\n过期上下文：发布、浏览器、官网")

        self.assertEqual(profile["task_type"], "general")
        self.assertEqual(profile["primary_domain"], "general")
        self.assertEqual(profile["matched_signal_score"], 0)
        self.assertTrue(profile["structured_context_detected"])
        self.assertTrue(profile["current_intent_detected"])
        self.assertIn("继续优化任务", profile["current_intent_text"])
        self.assertIn("构建产品官网", profile["history_context_text"])
        self.assertIn("发布", profile["stale_context_text"])
        self.assertEqual(profile["stale_context_policy"], "ignore_for_routing")

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

    def test_build_task_profile_detects_multi_platform_research_discovery(self):
        profile = build_task_profile("用 Agent-Reach 做 Reddit、YouTube、GitHub 和小红书的全平台搜索采集，并输出带引用的研究简报")

        self.assertEqual(profile["task_type"], "multi_platform_research_discovery")
        self.assertEqual(profile["primary_domain"], "research")
        self.assertIn("platform_boundary", profile["required_capabilities"])
        self.assertIn("source_check", profile["required_capabilities"])

    def test_build_task_profile_detects_investment_research_diligence(self):
        profile = build_task_profile("参考 ai-berkshire 四大师方法论做价值投资研究，输出反方观点、估值假设和决策边界")

        self.assertEqual(profile["task_type"], "investment_research_diligence")
        self.assertEqual(profile["primary_domain"], "business")
        self.assertIn("investment_framework", profile["required_capabilities"])
        self.assertIn("regulated_boundary", profile["required_capabilities"])

    def test_build_task_profile_detects_agent_role_library_governance(self):
        profile = build_task_profile("借鉴 agency-agents 的全栈智能体团队服务，治理专家角色库、handoff 和多 agent 编排")

        self.assertEqual(profile["task_type"], "agent_role_library_governance")
        self.assertEqual(profile["primary_domain"], "ai")
        self.assertIn("role_library_governance", profile["required_capabilities"])
        self.assertIn("agent_orchestration", profile["required_capabilities"])

    def test_build_task_profile_detects_design_md_system_governance(self):
        profile = build_task_profile("按 Google design.md 规范整理 DESIGN.md，统一设计系统 token、组件状态和可访问性检查")

        self.assertEqual(profile["task_type"], "design_md_system_governance")
        self.assertEqual(profile["primary_domain"], "design")
        self.assertIn("design_md_contract", profile["required_capabilities"])
        self.assertIn("accessibility", profile["required_capabilities"])

    def test_build_task_profile_detects_private_communication_governance(self):
        profile = build_task_profile("参考 SimpleX Chat 的隐私通讯模型，设计无用户标识、端到端加密和元数据最小化边界")

        self.assertEqual(profile["task_type"], "private_communication_governance")
        self.assertEqual(profile["primary_domain"], "compliance")
        self.assertIn("private_comms_boundary", profile["required_capabilities"])
        self.assertIn("privacy_check", profile["required_capabilities"])

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
        self.assertEqual(routed["pipeline_plan"]["id"], "general")
        self.assertEqual(routed["pipeline_plan"]["source"], "direct_skill_selection")

    def test_build_task_profile_detects_skill_router_quality_review(self):
        profile = build_task_profile("复查 safe-agent-skills 项目是否达到智能选择和自动搭配 skill 的目标")

        self.assertEqual(profile["task_type"], "skill_router_review")
        self.assertEqual(profile["primary_domain"], "ai")
        self.assertIn("catalog", profile["artifact_types"])
        self.assertIn("skill_selection_quality", profile["required_capabilities"])
        self.assertIn("bundle_quality", profile["required_capabilities"])
        self.assertIn("supply_chain_review", profile["required_capabilities"])

    def test_build_task_profile_routes_current_audit_followup_to_skill_router_review(self):
        profile = build_task_profile("继续，按照步骤，完成全部任务，以及审计报告给出的，更智能的解决方法")

        self.assertEqual(profile["task_type"], "skill_router_review")
        self.assertEqual(profile["primary_domain"], "ai")
        self.assertIn("skill_selection_quality", profile["required_capabilities"])

    def test_build_task_profile_routes_project_release_followup_to_skill_router_review(self):
        profile = build_task_profile("继续项目复查收尾，写好更新日志和 GitHub 更新说明，验证后发布")

        self.assertEqual(profile["task_type"], "skill_router_review")
        self.assertEqual(profile["primary_domain"], "ai")
        self.assertIn("bundle_quality", profile["required_capabilities"])
        self.assertIn("publish_check", profile["required_capabilities"])

    def test_build_task_profile_routes_typo_skill_orchestration_followup_to_skill_router_review(self):
        profile = build_task_profile("继续，优化和编排sikll，继续补充和优化，做好记录和测试")

        self.assertEqual(profile["task_type"], "skill_router_review")
        self.assertEqual(profile["primary_domain"], "ai")
        self.assertIn("skill_selection_quality", profile["required_capabilities"])
        self.assertIn("bundle_quality", profile["required_capabilities"])

    def test_build_task_profile_routes_update_record_followup_to_skill_router_review(self):
        profile = build_task_profile("写好更新记录后，继续优化任务")

        self.assertEqual(profile["task_type"], "skill_router_review")
        self.assertEqual(profile["primary_domain"], "ai")
        self.assertIn("skill_selection_quality", profile["required_capabilities"])
        self.assertIn("bundle_quality", profile["required_capabilities"])

    def test_build_task_profile_does_not_route_vague_continue_optimization_to_skill_router_review(self):
        profile = build_task_profile("继续优化任务")

        self.assertEqual(profile["task_type"], "general")
        self.assertEqual(profile["matched_signal_score"], 0)

    def test_build_task_profile_detects_chinese_skill_router_synonyms(self):
        for task in [
            "优化技能库的自动推荐和编排能力",
            "让技能选择和任务编排更聪明",
        ]:
            with self.subTest(task=task):
                profile = build_task_profile(task)

                self.assertEqual(profile["task_type"], "skill_router_review")
                self.assertEqual(profile["primary_domain"], "ai")
                self.assertGreater(profile["matched_signal_score"], 0)

    def test_build_task_profile_does_not_treat_report_alone_as_data_analysis(self):
        profile = build_task_profile("根据审计报告继续优化项目")

        self.assertNotEqual(profile["task_type"], "data_analysis")

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
        self.assertEqual(routed["pipeline_plan"]["id"], "skill-router-quality-review")
        self.assertEqual(routed["pipeline_plan"]["mode"], "method_only")
        self.assertEqual(routed["pipeline_plan"]["source"], "trusted_scenario_bundle")

    def test_route_scenario_task_keeps_required_capability_skills_beyond_max(self):
        bundle = {
            "id": "skill-router-quality-review",
            "name": "Skill Router Quality Review",
            "scenario": "Review skill catalog routing, automatic skill selection, bundle composition, and supply-chain risk.",
            "status": "trusted",
            "task_signals": ["safe-agent-skills", "skill router", "smart skill", "智能选择"],
            "skills": [
                "ai-opensquilla-metaskill-workflow",
                "ai-opensquilla-token-routing-pattern",
                "ai-langchain-agent-orchestration",
                "ai-tool-schema-protocol-check",
                "ai-output-schema-eval",
                "ai-rule-failure-log-synthesis",
                "code-test-regression",
                "engineering-ci-troubleshoot",
                "security-supply-chain-review",
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
                    "id": "routing_contract",
                    "required": True,
                    "preferred_skills": ["ai-tool-schema-protocol-check"],
                },
                {
                    "id": "output_schema_eval",
                    "required": True,
                    "preferred_skills": ["ai-output-schema-eval"],
                },
                {
                    "id": "regression_test",
                    "required": True,
                    "preferred_skills": ["code-test-regression"],
                },
                {
                    "id": "supply_chain_review",
                    "required": True,
                    "preferred_skills": ["security-supply-chain-review"],
                },
            ],
            "execution_order": [
                "ai-opensquilla-metaskill-workflow",
                "ai-opensquilla-token-routing-pattern",
                "ai-langchain-agent-orchestration",
                "ai-tool-schema-protocol-check",
                "ai-output-schema-eval",
                "ai-rule-failure-log-synthesis",
                "code-test-regression",
                "engineering-ci-troubleshoot",
                "security-supply-chain-review",
            ],
        }
        selected = [{"name": name, "match_score": 0} for name in bundle["skills"]]

        routed = route_scenario_task(
            task="继续补充维护 safe-agent-skills，使 skill 选择和执行更智能",
            selected_skills=selected,
            bundles_index={"bundles": [bundle]},
            trusted_skill_names={skill["name"] for skill in selected},
            max_skills=8,
        )

        skill_names = [skill["name"] for skill in routed["skills"]]
        coverage_by_capability = {item["capability"]: item for item in routed["coverage"]}
        self.assertIn("security-supply-chain-review", skill_names)
        self.assertEqual(coverage_by_capability["supply_chain_review"]["status"], "covered")
        self.assertEqual(routed["selection_quality"]["missing_required_count"], 0)

    def test_route_scenario_task_ignores_stale_history_for_vague_current_intent(self):
        bundle = {
            "id": "website-build-launch",
            "name": "Website Build Launch",
            "status": "trusted",
            "skills": ["business-requirements-brief", "design-ui-review", "execution-publish-check"],
            "execution_order": ["business-requirements-brief", "design-ui-review", "execution-publish-check"],
            "required_capabilities": [
                {"id": "requirements", "required": True, "preferred_skills": ["business-requirements-brief"]},
                {"id": "ui_review", "required": True, "preferred_skills": ["design-ui-review"]},
                {"id": "publish_check", "required": True, "preferred_skills": ["execution-publish-check"]},
            ],
        }
        selected = [{"name": name, "match_score": 0} for name in bundle["skills"]]

        routed = route_scenario_task(
            task="History: build a product website and prepare launch checks. Current request: continue optimizing this task",
            selected_skills=selected,
            bundles_index={"bundles": [bundle]},
            trusted_skill_names={skill["name"] for skill in selected},
            max_skills=8,
        )

        self.assertEqual(routed["task_profile"]["task_type"], "general")
        self.assertEqual(routed["selected_scenario"]["id"], "")
        self.assertTrue(routed["selection_quality"]["low_confidence"])
        self.assertNotIn("execution-publish-check", [skill["name"] for skill in routed["skills"]])

    def test_route_scenario_task_ignores_structured_stale_context_for_vague_current_intent(self):
        bundle = {
            "id": "website-build-launch",
            "name": "Website Build Launch",
            "status": "trusted",
            "skills": ["business-requirements-brief", "design-ui-review", "execution-publish-check"],
            "execution_order": ["business-requirements-brief", "design-ui-review", "execution-publish-check"],
            "required_capabilities": [
                {"id": "requirements", "required": True, "preferred_skills": ["business-requirements-brief"]},
                {"id": "ui_review", "required": True, "preferred_skills": ["design-ui-review"]},
                {"id": "publish_check", "required": True, "preferred_skills": ["execution-publish-check"]},
            ],
        }
        selected = [{"name": name, "match_score": 0} for name in bundle["skills"]]

        routed = route_scenario_task(
            task="当前意图：继续优化任务\n历史摘要：构建产品官网并准备发布检查\n过期上下文：发布、浏览器、官网",
            selected_skills=selected,
            bundles_index={"bundles": [bundle]},
            trusted_skill_names={skill["name"] for skill in selected},
            max_skills=8,
        )

        self.assertEqual(routed["task_profile"]["task_type"], "general")
        self.assertEqual(routed["selected_scenario"]["id"], "")
        self.assertEqual(routed["pipeline_plan"]["approval_gates"], [])
        self.assertNotIn("execution-publish-check", [skill["name"] for skill in routed["skills"]])

    def test_route_scenario_task_uses_structured_current_intent_over_unrelated_history(self):
        bundle = {
            "id": "skill-router-quality-review",
            "name": "Skill Router Quality Review",
            "scenario": "Review skill router quality, automatic selection, and bundle composition behavior.",
            "status": "trusted",
            "task_signals": ["safe-agent-skills", "skill router", "smart skill", "智能选择", "自动搭配"],
            "skills": [
                "ai-opensquilla-metaskill-workflow",
                "ai-opensquilla-token-routing-pattern",
                "code-test-regression",
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
                    "id": "regression_test",
                    "required": True,
                    "preferred_skills": ["code-test-regression"],
                },
            ],
            "execution_order": [
                "ai-opensquilla-metaskill-workflow",
                "ai-opensquilla-token-routing-pattern",
                "code-test-regression",
            ],
        }
        selected = [{"name": name, "match_score": 0} for name in bundle["skills"]]

        routed = route_scenario_task(
            task=(
                "current_intent: review safe-agent-skills router quality and skill selection order\n"
                "history_summary: build a product website and prepare launch checks\n"
                "stale_context: website, publish, browser automation"
            ),
            selected_skills=selected,
            bundles_index={"bundles": [bundle]},
            trusted_skill_names={skill["name"] for skill in selected},
            max_skills=8,
        )

        self.assertEqual(routed["task_profile"]["task_type"], "skill_router_review")
        self.assertTrue(routed["task_profile"]["structured_context_detected"])
        self.assertEqual(routed["selected_scenario"]["id"], "skill-router-quality-review")
        self.assertIn("ai-opensquilla-token-routing-pattern", [skill["name"] for skill in routed["skills"]])

    def test_build_pipeline_plan_for_skill_router_quality_review(self):
        profile = build_task_profile("复查 safe-agent-skills 项目是否达到智能选择和自动搭配 skill 的目标")
        bundle = {
            "id": "skill-router-quality-review",
            "name": "Skill Router Quality Review",
            "safety_boundary": "Skills provide method only; runtime permissions remain controlled by the host agent.",
        }
        skills = [
            {"name": "ai-opensquilla-metaskill-workflow", "match_score": 0},
            {"name": "ai-opensquilla-token-routing-pattern", "match_score": 0},
            {"name": "ai-tool-schema-protocol-check", "match_score": 0},
            {"name": "ai-output-schema-eval", "match_score": 0},
            {"name": "security-supply-chain-review", "match_score": 0},
            {"name": "code-test-regression", "match_score": 0},
            {"name": "engineering-ci-troubleshoot", "match_score": 0},
            {"name": "ai-rule-failure-log-synthesis", "match_score": 0},
        ]
        coverage = [
            {
                "capability": "skill_selection_quality",
                "required": True,
                "status": "covered",
                "skill": "ai-opensquilla-token-routing-pattern",
                "preferred_skills": ["ai-opensquilla-token-routing-pattern"],
            }
        ]

        plan = build_pipeline_plan(
            task="复查 safe-agent-skills 项目是否达到智能选择和自动搭配 skill 的目标",
            task_profile=profile,
            selected_bundle=bundle,
            selected_skills=skills,
            coverage=coverage,
            execution_graph={},
            invariants=None,
        )

        self.assertEqual(plan["id"], "skill-router-quality-review")
        self.assertEqual(plan["mode"], "method_only")
        self.assertEqual(plan["source"], "trusted_scenario_bundle")
        self.assertIn("runtime permissions", plan["runtime_boundary"])
        self.assertEqual(plan["approval_gates"], [])
        self.assertEqual(
            [stage["id"] for stage in plan["stages"]],
            ["preflight", "planning", "review", "verification", "handoff"],
        )
        self.assertIn("ai-opensquilla-metaskill-workflow", plan["stages"][0]["skills"])
        self.assertIn("ai-tool-schema-protocol-check", plan["stages"][2]["skills"])
        self.assertIn("security-supply-chain-review", plan["stages"][2]["skills"])
        self.assertIn("code-test-regression", plan["stages"][3]["skills"])
        self.assertIn("ai-rule-failure-log-synthesis", plan["stages"][4]["skills"])
        self.assertNotIn("security-supply-chain-review", plan["stages"][4]["skills"])
        for stage in plan["stages"]:
            self.assertIn("id", stage)
            self.assertIn("name", stage)
            self.assertIn("purpose", stage)
            self.assertIn("skills", stage)
            self.assertIn("inputs", stage)
            self.assertIn("outputs", stage)
            self.assertIn("gate", stage)
            self.assertIn("verification", stage)
            self.assertIn("condition", stage["gate"])
            self.assertIn("failure_action", stage["gate"])
            self.assertIn("evidence_template", stage["gate"])
            self.assertEqual(
                stage["gate"]["evidence_template"]["status_values"],
                ["pending", "passed", "failed", "blocked", "skipped"],
            )
            self.assertIn("evidence", stage["gate"]["evidence_template"]["required_fields"])
            self.assertIn("residual_risks", stage["gate"]["evidence_template"]["required_fields"])

    def test_build_pipeline_plan_general_fallback_does_not_invent_scenario(self):
        profile = build_task_profile("帮我看一下这个事情是否合理")
        skills = [
            {"name": "ai-opensquilla-metaskill-workflow", "match_score": 12},
            {"name": "research-source-check", "match_score": 4},
        ]

        plan = build_pipeline_plan(
            task="帮我看一下这个事情是否合理",
            task_profile=profile,
            selected_bundle={},
            selected_skills=skills,
            coverage=[],
            execution_graph={},
            invariants=None,
        )

        self.assertEqual(plan["id"], "general")
        self.assertEqual(plan["name"], "General")
        self.assertEqual(plan["source"], "direct_skill_selection")
        self.assertEqual(plan["mode"], "method_only")
        self.assertEqual(plan["low_confidence_note"], "No trusted scenario matched; use direct selected skills only.")
        self.assertEqual([stage["id"] for stage in plan["stages"]], ["source", "planning", "handoff"])
        self.assertIn("research-source-check", plan["stages"][0]["skills"])
        self.assertIn("ai-opensquilla-metaskill-workflow", plan["stages"][1]["skills"])
        self.assertEqual(plan["approval_gates"], [])

    def test_build_pipeline_plan_includes_low_confidence_reason_codes(self):
        profile = build_task_profile("帮我看一下这个事情是否合理")
        skills = [{"name": "execution-file-batch", "match_score": 0}]

        plan = build_pipeline_plan(
            task="帮我看一下这个事情是否合理",
            task_profile=profile,
            selected_bundle={},
            selected_skills=skills,
            coverage=[],
            execution_graph={},
            invariants=None,
        )

        self.assertIn("no_trusted_scenario_match", plan["low_confidence_reasons"])
        self.assertIn("low_signal_task_profile", plan["low_confidence_reasons"])

    def test_build_pipeline_plan_uses_current_intent_for_runtime_approval_gates(self):
        task = "历史上下文：构建产品官网并准备上线发布检查。当前请求：继续优化任务"
        profile = build_task_profile(task)
        skills = [{"name": "execution-file-batch", "match_score": 0}]

        plan = build_pipeline_plan(
            task=task,
            task_profile=profile,
            selected_bundle={},
            selected_skills=skills,
            coverage=[],
            execution_graph={},
            invariants=None,
        )

        self.assertEqual(plan["approval_gates"], [])

    def test_build_pipeline_plan_marks_video_runtime_approval_gates(self):
        profile = build_task_profile("Copywriting 写文案，Content Strategy 规划内容矩阵，Remotion 实现一句话灵感到成片")
        bundle = {
            "id": "content-video-production",
            "name": "Content Video Production",
            "safety_boundary": "Programmatic video execution needs separate runtime and license review.",
        }
        skills = [
            {"name": "content-strategy-matrix", "match_score": 0},
            {"name": "media-video-script-review", "match_score": 0},
            {"name": "media-remotion-video-production-boundary", "match_score": 0},
            {"name": "media-asset-review", "match_score": 0},
            {"name": "execution-publish-check", "match_score": 0},
        ]

        plan = build_pipeline_plan(
            task="Copywriting 写文案，Content Strategy 规划内容矩阵，Remotion 实现一句话灵感到成片",
            task_profile=profile,
            selected_bundle=bundle,
            selected_skills=skills,
            coverage=[],
            execution_graph={},
            invariants=None,
        )

        approval_required = {
            item
            for gate in plan["approval_gates"]
            for item in gate["required_for"]
        }
        self.assertIn("media rendering", approval_required)
        self.assertIn("file upload or publication", approval_required)
        self.assertIn("dependency install", approval_required)
        self.assertIn("paid model or provider call", approval_required)
        self.assertIn("media-remotion-video-production-boundary", [skill for stage in plan["stages"] for skill in stage["skills"]])

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

    def test_build_capability_coverage_marks_available_unselected_skills_as_omitted(self):
        bundle = {
            "required_capabilities": [
                {
                    "id": "ui_review",
                    "required": True,
                    "preferred_skills": ["design-ui-review"],
                },
                {
                    "id": "premium_landing_design",
                    "required": False,
                    "preferred_skills": ["design-premium-landing-page"],
                },
            ]
        }

        coverage = build_capability_coverage(
            bundle,
            selected_skill_names={"design-ui-review"},
            available_skill_names={"design-ui-review", "design-premium-landing-page"},
        )

        self.assertEqual(coverage[0]["status"], "covered")
        self.assertEqual(coverage[1]["status"], "omitted_by_limit")
        self.assertEqual(coverage[1]["skill"], "design-premium-landing-page")
        self.assertEqual(coverage[1]["omission_reason"], "available_not_selected")

    def test_route_mesh_task_marks_optional_bundle_capabilities_omitted_by_limit(self):
        bundles_index = {
            "bundles": [
                {
                    "id": "website-build-launch",
                    "name": "Website Build Launch",
                    "scenario": "Build or polish a website, landing page, dashboard, or product page.",
                    "status": "trusted",
                    "task_signals": ["website", "landing page", "launch"],
                    "skills": [
                        "business-requirements-brief",
                        "design-ui-review",
                        "design-premium-landing-page",
                    ],
                    "required_capabilities": [
                        {"id": "requirements", "required": True, "preferred_skills": ["business-requirements-brief"]},
                        {"id": "ui_review", "required": True, "preferred_skills": ["design-ui-review"]},
                        {
                            "id": "premium_landing_design",
                            "required": False,
                            "preferred_skills": ["design-premium-landing-page"],
                        },
                    ],
                    "execution_order": [
                        "business-requirements-brief",
                        "design-ui-review",
                        "design-premium-landing-page",
                    ],
                }
            ]
        }
        selected = [
            {"name": "business-requirements-brief", "match_score": 5},
            {"name": "design-ui-review", "match_score": 5},
            {"name": "design-premium-landing-page", "match_score": 0},
        ]

        routed = route_mesh_task(
            task="build a landing page and prepare launch checks",
            invariants=None,
            selected_skills=selected,
            bundles_index=bundles_index,
            trusted_skill_names={skill["name"] for skill in selected},
            overlap_groups=None,
            max_skills=2,
            strategy="balanced",
        )

        coverage = {item["capability"]: item for item in routed["coverage"]}
        self.assertEqual(coverage["requirements"]["status"], "covered")
        self.assertEqual(coverage["ui_review"]["status"], "covered")
        self.assertEqual(coverage["premium_landing_design"]["status"], "omitted_by_limit")
        self.assertEqual(coverage["premium_landing_design"]["skill"], "design-premium-landing-page")
        self.assertEqual(routed["selection_quality"]["missing_required_count"], 0)

    def test_route_mesh_task_promotes_profile_required_capability_over_limit(self):
        skill_names = [
            "ai-opensquilla-metaskill-workflow",
            "ai-opensquilla-token-routing-pattern",
            "ai-langchain-agent-orchestration",
            "ai-tool-schema-protocol-check",
            "ai-output-schema-eval",
            "ai-rule-failure-log-synthesis",
            "code-test-regression",
            "engineering-ci-troubleshoot",
            "security-supply-chain-review",
        ]
        bundles_index = {
            "bundles": [
                {
                    "id": "skill-router-quality-review",
                    "name": "Skill Router Quality Review",
                    "scenario": "Review skill catalog routing and automatic skill selection.",
                    "status": "trusted",
                    "task_signals": ["skill router", "skill selection", "自动推荐", "任务编排"],
                    "skills": skill_names,
                    "execution_order": skill_names,
                    "required_capabilities": [
                        {
                            "id": "skill_selection_quality",
                            "required": True,
                            "preferred_skills": ["ai-opensquilla-token-routing-pattern"],
                        },
                        {"id": "bundle_quality", "required": True, "preferred_skills": ["ai-opensquilla-metaskill-workflow"]},
                        {"id": "routing_contract", "required": True, "preferred_skills": ["ai-tool-schema-protocol-check"]},
                        {"id": "output_schema_eval", "required": True, "preferred_skills": ["ai-output-schema-eval"]},
                        {"id": "regression_test", "required": True, "preferred_skills": ["code-test-regression"]},
                        {"id": "failure_synthesis", "required": False, "preferred_skills": ["ai-rule-failure-log-synthesis"]},
                        {"id": "ci_check", "required": False, "preferred_skills": ["engineering-ci-troubleshoot"]},
                        {"id": "supply_chain_review", "required": True, "preferred_skills": ["security-supply-chain-review"]},
                    ],
                }
            ]
        }
        selected = [{"name": name, "match_score": 0} for name in skill_names]

        routed = route_mesh_task(
            task="优化技能库的自动推荐和任务编排能力",
            invariants=None,
            selected_skills=selected,
            bundles_index=bundles_index,
            trusted_skill_names=set(skill_names),
            overlap_groups=None,
            max_skills=8,
            strategy="balanced",
        )

        selected_names = {skill["name"] for skill in routed["skills"]}
        coverage = {item["capability"]: item for item in routed["coverage"]}
        self.assertIn("engineering-ci-troubleshoot", selected_names)
        self.assertEqual(coverage["ci_check"]["status"], "covered")
        self.assertTrue(coverage["ci_check"]["required"])

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

    def test_build_selection_quality_reports_required_coverage_and_warnings(self):
        bundle = {"id": "code-review-hardening", "name": "Code Review Hardening"}
        coverage = [
            {
                "capability": "code_review",
                "required": True,
                "status": "covered",
                "skill": "code-review-risk",
                "preferred_skills": ["code-review-risk"],
            },
            {
                "capability": "supply_chain_review",
                "required": True,
                "status": "missing",
                "skill": "",
                "preferred_skills": ["security-supply-chain-review"],
            },
            {
                "capability": "schema_contract",
                "required": False,
                "status": "missing",
                "skill": "",
                "preferred_skills": ["ai-output-schema-eval"],
            },
        ]

        quality = build_selection_quality(
            task_profile={"task_type": "code_review", "matched_signal_score": 8},
            selected_bundle=bundle,
            selected_scenario={"id": "code-review-hardening", "match_score": 12},
            coverage=coverage,
            pruned_skills=["code-dead-path-cleanup-review"],
        )

        self.assertEqual(quality["confidence"], "medium")
        self.assertEqual(quality["covered_required_count"], 1)
        self.assertEqual(quality["missing_required_count"], 1)
        self.assertEqual(quality["required_count"], 2)
        self.assertAlmostEqual(quality["coverage_ratio"], 0.5)
        self.assertFalse(quality["low_confidence"])
        self.assertIn("Missing required capability: supply_chain_review", quality["warnings"])
        self.assertEqual(quality["pruned_skills"], ["code-dead-path-cleanup-review"])

    def test_build_selection_quality_marks_general_fallback_low_confidence(self):
        quality = build_selection_quality(
            task_profile={"task_type": "general", "matched_signal_score": 0},
            selected_bundle={},
            selected_scenario={"id": "", "match_score": 0},
            coverage=[],
            pruned_skills=[],
        )

        self.assertEqual(quality["confidence"], "low")
        self.assertTrue(quality["low_confidence"])
        self.assertEqual(quality["coverage_ratio"], 0)
        self.assertIn("No trusted scenario matched; using direct selected skills only.", quality["warnings"])

    def test_build_selection_quality_explains_low_confidence_general_fallback(self):
        quality = build_selection_quality(
            task_profile={"task_type": "general", "matched_signal_score": 0},
            selected_bundle={},
            selected_scenario={"id": "", "match_score": 0},
            coverage=[],
            pruned_skills=[],
        )

        self.assertEqual(
            quality["reason_codes"],
            ["no_trusted_scenario_match", "low_signal_task_profile", "direct_skill_selection_fallback"],
        )
        self.assertIn("No trusted scenario bundle matched the task.", quality["explanations"])
        self.assertIn("Record low-confidence route as a residual risk.", quality["recommended_actions"])

    def test_selection_explanations_include_execution_roles(self):
        bundle = {
            "id": "skill-router-quality-review",
            "name": "Skill Router Quality Review",
        }
        skills = [
            {"name": "ai-opensquilla-metaskill-workflow", "match_score": 0},
            {"name": "ai-tool-schema-protocol-check", "match_score": 0},
            {"name": "code-test-regression", "match_score": 0},
        ]
        coverage = [
            {
                "capability": "bundle_quality",
                "required": True,
                "status": "covered",
                "skill": "ai-opensquilla-metaskill-workflow",
                "preferred_skills": ["ai-opensquilla-metaskill-workflow"],
            },
            {
                "capability": "routing_contract",
                "required": True,
                "status": "covered",
                "skill": "ai-tool-schema-protocol-check",
                "preferred_skills": ["ai-tool-schema-protocol-check"],
            },
            {
                "capability": "regression_test",
                "required": True,
                "status": "covered",
                "skill": "code-test-regression",
                "preferred_skills": ["code-test-regression"],
            },
        ]

        explanations = build_selection_explanations(bundle, skills, coverage)
        by_name = {item["name"]: item for item in explanations}

        self.assertEqual(by_name["ai-opensquilla-metaskill-workflow"]["execution_role"], "preflight")
        self.assertEqual(by_name["ai-tool-schema-protocol-check"]["execution_role"], "reviewer")
        self.assertEqual(by_name["code-test-regression"]["execution_role"], "verifier")
        self.assertEqual(execution_role_for_stage("production"), "producer")

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

    def test_route_mesh_task_includes_pipeline_plan(self):
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
                "code-test-regression",
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
                    "id": "routing_contract",
                    "required": True,
                    "preferred_skills": ["ai-tool-schema-protocol-check"],
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
                "code-test-regression",
            ],
            "safety_boundary": "method-only",
        }
        selected = [{"name": name, "match_score": 0} for name in bundle["skills"]]

        routed = route_mesh_task(
            task="复查 safe-agent-skills 项目是否达到智能选择和自动搭配 skill 的目标",
            invariants=None,
            selected_skills=selected,
            bundles_index={"bundles": [bundle]},
            trusted_skill_names={skill["name"] for skill in selected},
            overlap_groups=None,
            max_skills=8,
            strategy="balanced",
        )

        self.assertEqual(routed["pipeline_plan"]["id"], "skill-router-quality-review")
        self.assertEqual(routed["pipeline_plan"]["mode"], "method_only")
        self.assertEqual(routed["pipeline_plan"]["source"], "trusted_scenario_bundle")

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

    def test_build_contract_graph_uses_artifact_dependencies_and_parallel_layers(self):
        graph = build_contract_graph(
            [
                {
                    "name": "business-requirements-brief",
                    "contract": {
                        "produces_artifacts": ["requirements_brief"],
                        "requires_context": ["task_brief"],
                        "capability_vector": ["business.requirements"],
                    },
                },
                {
                    "name": "design-ui-review",
                    "contract": {
                        "produces_evidence": ["ui_review_report"],
                        "requires_context": ["requirements_brief", "build_artifact"],
                        "capability_vector": ["design.ui_review"],
                    },
                },
                {
                    "name": "content-seo-brief",
                    "contract": {
                        "produces_artifacts": ["seo_copy"],
                        "requires_context": ["requirements_brief"],
                        "capability_vector": ["content.seo"],
                    },
                },
            ]
        )

        nodes_by_skill = {node["skill"]: node for node in graph["nodes"]}
        self.assertEqual(graph["mode"], "contract")
        self.assertTrue(graph["acyclic"])
        self.assertIn(
            {
                "from": nodes_by_skill["business-requirements-brief"]["id"],
                "to": nodes_by_skill["design-ui-review"]["id"],
                "type": "contract_dependency",
                "artifacts": ["requirements_brief"],
            },
            graph["edges"],
        )
        self.assertEqual(nodes_by_skill["business-requirements-brief"]["topology_layer"], 0)
        self.assertEqual(nodes_by_skill["design-ui-review"]["topology_layer"], 1)
        self.assertEqual(nodes_by_skill["content-seo-brief"]["topology_layer"], 1)
        self.assertIn("layer_1", graph["parallel_groups"])

    def test_build_contract_graph_uses_requires_after_ordering_edges(self):
        graph = build_contract_graph(
            [
                {
                    "name": "business-requirements-brief",
                    "contract": {
                        "produces_artifacts": ["requirements_brief"],
                        "requires_context": ["task_brief"],
                    },
                },
                {
                    "name": "design-ui-review",
                    "contract": {
                        "produces_evidence": ["ui_review_report"],
                        "requires_after": ["business-requirements-brief"],
                    },
                },
            ]
        )

        nodes_by_skill = {node["skill"]: node for node in graph["nodes"]}
        self.assertEqual(graph["mode"], "contract")
        self.assertTrue(graph["acyclic"])
        self.assertIn(
            {
                "from": nodes_by_skill["business-requirements-brief"]["id"],
                "to": nodes_by_skill["design-ui-review"]["id"],
                "type": "contract_requires_after",
                "skills": ["business-requirements-brief"],
            },
            graph["edges"],
        )
        self.assertLess(
            nodes_by_skill["business-requirements-brief"]["topology_layer"],
            nodes_by_skill["design-ui-review"]["topology_layer"],
        )

    def test_build_contract_graph_falls_back_when_contracts_are_missing(self):
        graph = build_contract_graph(
            [
                {"name": "business-requirements-brief"},
                {
                    "name": "design-ui-review",
                    "contract": {
                        "requires_context": ["requirements_brief"],
                        "produces_evidence": ["ui_review_report"],
                        "capability_vector": ["design.ui_review"],
                    },
                },
            ]
        )

        self.assertEqual(graph["mode"], "stage_fallback")
        self.assertEqual(graph["fallback_reason"], "missing_contract")

    def test_build_contract_diagnostics_reports_missing_requires_after(self):
        skills = [
            {
                "name": "design-ui-review",
                "contract": {
                    "produces_evidence": ["ui_review_report"],
                    "requires_after": ["business-requirements-brief"],
                },
            }
        ]

        diagnostics = build_contract_diagnostics(skills, build_contract_graph(skills))

        self.assertEqual(diagnostics["status"], "warning")
        self.assertEqual(diagnostics["missing_ordering_count"], 1)
        self.assertEqual(
            diagnostics["missing_ordering"],
            [
                {
                    "skill": "design-ui-review",
                    "requires_after": "business-requirements-brief",
                    "source": "contract.requires_after",
                }
            ],
        )

    def test_build_contract_diagnostics_reports_missing_preconditions_and_collisions(self):
        skills = [
            {
                "name": "business-requirements-brief",
                "contract": {
                    "requires_context": ["task_brief"],
                    "produces_artifacts": ["requirements_brief"],
                },
            },
            {
                "name": "design-ui-review",
                "contract": {
                    "requires_context": ["requirements_brief", "build_artifact"],
                    "produces_evidence": ["ui_review_report"],
                    "conflicts_with": ["design-visual-quality-review"],
                },
            },
            {
                "name": "design-visual-quality-review",
                "contract": {
                    "produces_evidence": ["visual_review_report"],
                    "excludes": ["content-seo-brief"],
                },
            },
            {
                "name": "content-seo-brief",
                "contract": {
                    "produces_artifacts": ["seo_copy"],
                },
            },
            {
                "name": "execution-publish-check",
                "contract": {
                    "requires_context": ["ui_review_report", "browser_check_report"],
                    "produces_evidence": ["publish_readiness_report"],
                },
            },
        ]
        graph = build_contract_graph(skills)

        diagnostics = build_contract_diagnostics(skills, graph)

        self.assertEqual(diagnostics["status"], "warning")
        self.assertEqual(diagnostics["missing_precondition_count"], 2)
        self.assertEqual(
            {
                (item["skill"], item["artifact"])
                for item in diagnostics["missing_preconditions"]
            },
            {
                ("design-ui-review", "build_artifact"),
                ("execution-publish-check", "browser_check_report"),
            },
        )
        self.assertEqual(diagnostics["collision_count"], 2)
        self.assertEqual(
            diagnostics["collisions"],
            [
                {
                    "skill": "design-ui-review",
                    "conflicts_with": "design-visual-quality-review",
                    "source": "contract.conflicts_with",
                },
                {
                    "skill": "design-visual-quality-review",
                    "conflicts_with": "content-seo-brief",
                    "source": "contract.excludes",
                }
            ],
        )
        self.assertEqual(diagnostics["graph_mode"], "contract")
        self.assertEqual(diagnostics["fallback_reason"], "")

    def test_route_mesh_task_uses_contract_graph_when_complete(self):
        bundles_index = {
            "bundles": [
                {
                    "id": "website-build-launch",
                    "name": "Website Build Launch",
                    "scenario": "Build a website.",
                    "status": "trusted",
                    "task_signals": ["website"],
                    "skills": [
                        "business-requirements-brief",
                        "design-ui-review",
                        "engineering-build-release",
                        "content-social-post",
                    ],
                    "required_capabilities": [
                        {"id": "requirements", "required": True, "preferred_skills": ["business-requirements-brief"]},
                        {"id": "ui_review", "required": True, "preferred_skills": ["design-ui-review"]},
                        {"id": "engineering_release", "required": True, "preferred_skills": ["engineering-build-release"]},
                    ],
                    "execution_order": [
                        "business-requirements-brief",
                        "design-ui-review",
                        "engineering-build-release",
                        "content-social-post",
                    ],
                }
            ]
        }
        selected = [
            {
                "name": "design-ui-review",
                "match_score": 9,
                "contract": {
                    "requires_context": ["requirements_brief"],
                    "produces_evidence": ["ui_review_report"],
                    "capability_vector": ["design.ui_review"],
                },
            },
            {
                "name": "engineering-build-release",
                "match_score": 7,
                "contract": {
                    "requires_context": ["requirements_brief"],
                    "produces_artifacts": ["build_artifact"],
                    "capability_vector": ["engineering.build_release"],
                },
            },
            {
                "name": "business-requirements-brief",
                "match_score": 8,
                "contract": {
                    "requires_context": ["task_brief"],
                    "produces_artifacts": ["requirements_brief"],
                    "capability_vector": ["business.requirements"],
                },
            },
            {
                "name": "content-social-post",
                "match_score": 7,
                "contract": {
                    "requires_context": ["requirements_brief"],
                    "produces_artifacts": ["social_post_copy"],
                    "capability_vector": ["content.social"],
                },
            },
        ]

        routed = route_mesh_task(
            task="build a website",
            invariants=None,
            selected_skills=selected,
            bundles_index=bundles_index,
            trusted_skill_names={skill["name"] for skill in selected},
            overlap_groups=None,
            max_skills=4,
        )

        self.assertEqual(routed["execution_graph"]["mode"], "contract")
        self.assertEqual([skill["name"] for skill in routed["skills"]][0], "business-requirements-brief")
        self.assertEqual(
            [node["skill"] for node in routed["execution_graph"]["nodes"]],
            [skill["name"] for skill in routed["skills"]],
        )

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
