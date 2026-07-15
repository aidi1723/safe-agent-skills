from __future__ import annotations

import html
import re


def render_task_pack_markdown(task_pack: dict) -> str:
    lines = [
        "# OneCode Agent Task Pack",
        "",
        f"Task: {task_pack['task']}",
        f"Generated at: {task_pack['generated_at']}",
        f"Selected skills: {task_pack['skill_count']}",
        "",
        "## Safety Boundary",
        "",
        task_pack["safety_boundary"],
    ]
    if task_pack.get("router"):
        lines.extend(
            [
                "",
                "## Task Profile",
                "",
                f"- router: `{task_pack['router']['mode']}`",
                f"- task type: `{task_pack['task_profile']['task_type']}`",
                f"- primary domain: `{task_pack['task_profile']['primary_domain']}`",
                "",
                "## Selected Scenario",
                "",
                f"- id: `{task_pack['selected_scenario'].get('id', '')}`",
                f"- score: `{task_pack['selected_scenario'].get('match_score', 0)}`",
                "",
                "## Capability Coverage",
                "",
            ]
        )
        for item in task_pack.get("coverage", []):
            lines.append(f"- `{item['capability']}`: {item['status']} by `{item.get('skill') or 'missing'}`")
        if task_pack.get("invariant_capabilities"):
            lines.extend(["", "## Invariant Capabilities", ""])
            for capability in task_pack["invariant_capabilities"]:
                lines.append(f"- `{capability}`")
        if task_pack.get("pruned_skills"):
            lines.extend(["", "## Pruned Overlap Skills", ""])
            for skill_name in task_pack["pruned_skills"]:
                lines.append(f"- `{skill_name}`")
        lines.extend(["", "## Execution Plan", ""])
        for step in task_pack.get("execution_plan", []):
            lines.append(f"{step['order']}. `{step['skill']}` - {step['instruction']}")
        if task_pack.get("execution_graph"):
            lines.extend(["", "## Execution Graph", ""])
            for node in task_pack["execution_graph"].get("nodes", []):
                lines.append(f"- `{node['id']}` `{node['stage']}` -> `{node['skill']}`")
            for edge in task_pack["execution_graph"].get("edges", []):
                lines.append(f"- edge `{edge['from']}` -> `{edge['to']}`")
        if task_pack.get("pipeline_plan"):
            plan = task_pack["pipeline_plan"]
            lines.extend(
                [
                    "",
                    "## Pipeline Plan",
                    "",
                    f"- id: `{plan.get('id', 'general')}`",
                    f"- mode: `{str(plan.get('mode', 'method_only')).replace('_', '-')}`",
                    f"- source: `{plan.get('source', '')}`",
                    f"- boundary: {plan.get('runtime_boundary', 'Skills provide method only; host runtime controls permissions.')}",
                ]
            )
            for stage in plan.get("stages", []):
                gate = stage.get("gate", {})
                lines.extend(
                    [
                        "",
                        f"### {stage.get('name', stage.get('id', ''))}",
                        "",
                        f"- id: `{stage.get('id', '')}`",
                        f"- purpose: {stage.get('purpose', 'Not specified.')}",
                        f"- skills: {', '.join(f'`{skill}`' for skill in stage.get('skills', [])) or 'none'}",
                        f"- gate: {gate.get('condition', 'Not specified.')}",
                        f"- failure action: `{gate.get('failure_action', 'not_specified')}`",
                    ]
                )
                evidence_template = gate.get("evidence_template", {})
                evidence_fields = evidence_template.get("required_fields", [])
                if evidence_fields:
                    lines.append("- evidence fields: " + ", ".join(f"`{field}`" for field in evidence_fields))
            if plan.get("approval_gates"):
                lines.extend(["", "### Approval Gates", ""])
                for gate in plan["approval_gates"]:
                    required_for = ", ".join(gate.get("required_for", [])) or "not specified"
                    lines.append(
                        f"- stage `{gate.get('stage', '')}` requires approval for {required_for} "
                        f"by `{gate.get('owner', 'host_runtime_or_operator')}`"
                    )
        lines.extend(["", "## Selection Explanations", ""])
        for item in task_pack.get("selection_explanations", []):
            lines.append(f"- `{item['name']}` ({item['type']}, {item['role']}): {item['selection_reason']}")
        if task_pack.get("selection_trace"):
            trace = task_pack["selection_trace"]
            lines.extend(
                [
                    "",
                    "## Selection Trace",
                    "",
                    f"- candidates: `{trace.get('candidate_count', 0)}`",
                    f"- selected: `{trace.get('selected_count', 0)}`",
                    f"- required skills: `{trace.get('required_skill_count', 0)}`",
                ]
            )
            for item in trace.get("decision_stages", []):
                details = []
                if "decision" in item:
                    details.append(f"decision `{item['decision']}`")
                if "score" in item:
                    details.append(f"score `{item['score']}`")
                if "selected_count" in item:
                    details.append(f"selected `{item['selected_count']}`")
                if "pruned_count" in item:
                    details.append(f"pruned `{item['pruned_count']}`")
                if "covered_count" in item:
                    details.append(f"covered `{item['covered_count']}`")
                if "missing_count" in item:
                    details.append(f"missing `{item['missing_count']}`")
                if "omitted_by_limit_count" in item:
                    details.append(f"omitted `{item['omitted_by_limit_count']}`")
                lines.append(f"- `{item.get('stage', '')}`: " + ", ".join(details))
            for item in trace.get("pruned", []):
                lines.append(f"- pruned `{item.get('name', '')}`: {item.get('reason', '')}")
    if task_pack.get("selection_quality"):
        quality = task_pack["selection_quality"]
        lines.extend(
            [
                "",
                "## Selection Quality",
                "",
                f"- confidence: `{quality.get('confidence', 'low')}`",
                f"- score: `{quality.get('score', 0)}`",
                f"- coverage ratio: `{quality.get('coverage_ratio', 0)}`",
                f"- low confidence: `{quality.get('low_confidence', False)}`",
            ]
        )
        for warning in quality.get("warnings", []):
            lines.append(f"- warning: {warning}")
        for reason in quality.get("reason_codes", []):
            lines.append(f"- reason: `{reason}`")
        for explanation in quality.get("explanations", []):
            lines.append(f"- explanation: {explanation}")
        for action in quality.get("recommended_actions", []):
            lines.append(f"- recommended action: {action}")
    if task_pack.get("contract_diagnostics"):
        diagnostics = task_pack["contract_diagnostics"]
        lines.extend(
            [
                "",
                "## Contract Diagnostics",
                "",
                f"- status: `{diagnostics.get('status', 'unknown')}`",
                f"- graph mode: `{diagnostics.get('graph_mode', 'unknown')}`",
                f"- missing preconditions: `{diagnostics.get('missing_precondition_count', 0)}`",
                f"- missing ordering: `{diagnostics.get('missing_ordering_count', 0)}`",
                f"- collisions: `{diagnostics.get('collision_count', 0)}`",
            ]
        )
        for item in diagnostics.get("missing_preconditions", []):
            lines.append(f"- missing: `{item.get('skill', '')}` requires `{item.get('artifact', '')}`")
        for item in diagnostics.get("missing_ordering", []):
            lines.append(f"- ordering: `{item.get('skill', '')}` requires after `{item.get('requires_after', '')}`")
        for item in diagnostics.get("collisions", []):
            lines.append(f"- collision: `{item.get('skill', '')}` conflicts with `{item.get('conflicts_with', '')}`")
    if task_pack.get("acceptance_criteria"):
        lines.extend(["", "## Acceptance Criteria", ""])
        for criterion in task_pack["acceptance_criteria"]:
            lines.append(f"- {criterion}")
    if task_pack.get("completion_contract"):
        contract = task_pack["completion_contract"]
        lines.extend(["", "## Completion Contract", ""])
        lines.append("- final response must include: " + ", ".join(contract.get("final_response_must_include", [])))
        lines.append("- stop conditions: " + ", ".join(contract.get("stop_conditions", [])))
        lines.append("- evidence requirements: " + ", ".join(contract.get("evidence_requirements", [])))
    lines.extend(["", "## Selected Skills"])
    for skill in task_pack["skills"]:
        lines.extend(
            [
                "",
                f"### {skill['name']}",
                "",
                f"- status: `{skill['status']}`",
                f"- risk: `{skill['risk_level']}`",
                f"- match score: `{skill['match_score']}`",
                f"- category: `{skill['taxonomy']['category']}`",
                f"- source: {skill['source']['url']}",
                "",
                skill["description"],
                "",
                "#### Safe Workflow",
                "",
                skill["safe_workflow"] or "Not specified.",
                "",
                "#### Expected Output",
                "",
                skill["expected_output"] or "Not specified.",
                "",
                "#### Verifier Expectations",
                "",
                skill["verifier_expectations"] or "Not specified.",
            ]
        )
    if task_pack.get("bundles"):
        lines.extend(["", "## Scenario Bundles"])
        for bundle in task_pack["bundles"]:
            lines.extend(
                [
                    "",
                    f"### {bundle['name']}",
                    "",
                    f"- id: `{bundle['id']}`",
                    f"- status: `{bundle['status']}`",
                    f"- match score: `{bundle['match_score']}`",
                    "",
                    bundle["scenario"],
                    "",
                    "#### Skills",
                    "",
                    "\n".join(f"- `{skill_name}`" for skill_name in bundle["skills"]),
                    "",
                    "#### Expected Output",
                    "",
                    "\n".join(f"- {item}" for item in bundle["expected_output"]) or "Not specified.",
                ]
            )
    lines.extend(["", "## Agent Instructions", "", task_pack["agent_instructions"], ""])
    return "\n".join(lines)


def render_task_pack_v2_markdown(task_pack: dict) -> str:
    graph = task_pack["execution_graph"]
    lines = [
        "# OneCode Agent Task Pack v2",
        "",
        f"Route ID: {markdown_safe_line(task_pack['route_id'])}",
        f"Routing status: {markdown_safe_line(task_pack['routing_status'])}",
        "",
        "## Task",
        "",
        markdown_safe_line(task_pack["normalized_task"]["current"]),
        "",
        "## Intents",
        "",
    ]
    for intent in task_pack["intent_graph"]["intents"]:
        dependencies = ", ".join(markdown_safe_line(value) for value in intent["depends_on"]) or "none"
        lines.append(
            f"- {markdown_safe_line(intent['id'])} {markdown_safe_line(intent['task_type'])}: "
            f"{markdown_safe_line(intent['summary'])} (depends on: {dependencies})"
        )
    lines.extend(["", "## Selected Scenarios", ""])
    if task_pack["selected_scenarios"]:
        for scenario in task_pack["selected_scenarios"]:
            intent_ids = ", ".join(markdown_safe_line(value) for value in scenario["intent_ids"])
            lines.append(
                f"- {markdown_safe_line(scenario['scenario_id'])} for {intent_ids}; "
                f"score {markdown_safe_line(scenario['score'])}"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Uncovered Intents", ""])
    if task_pack["uncovered_intents"]:
        lines.extend(f"- {markdown_safe_line(intent_id)}" for intent_id in task_pack["uncovered_intents"])
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Execution Graph",
            "",
            f"- status: {markdown_safe_line(graph['status'])}",
            f"- nodes: {len(graph['nodes'])}",
            f"- edges: {len(graph['edges'])}",
            "",
            "## Routing Diagnostics",
            "",
            "",
            "## Safety Boundary",
            "",
            f"- mode: {markdown_safe_line(task_pack['host_execution_protocol']['mode'])}",
            f"- {markdown_safe_line(task_pack['host_execution_protocol']['runtime_boundary'])}",
            "",
        ]
    )
    diagnostics = [*graph.get("reason_codes", []), *graph.get("details", [])]
    diagnostics_start = lines.index("## Routing Diagnostics") + 2
    lines[diagnostics_start:diagnostics_start] = (
        [f"- {markdown_safe_line(value)}" for value in diagnostics] if diagnostics else ["- none"]
    )
    return "\n".join(lines)


def render_task_pack_v3_markdown(task_pack: dict) -> str:
    need = task_pack["need_decision"]
    selection = task_pack["selection"]
    capability = task_pack["capability_resolution"]
    confidence = task_pack["confidence"]
    provider = task_pack["provider"]
    graph = task_pack["execution_graph"]
    protocol = task_pack["host_execution_protocol"]
    contributions = {
        item["skill"]: item for item in selection["marginal_contributions"]
    }
    lines = [
        "# OneCode Agent Task Pack v3",
        "",
        "## Task",
        "",
        _v3_markdown_safe_line(task_pack["normalized_task"]["current"]),
        "",
        "## Need Decision",
        "",
        f"- decision: {_v3_markdown_safe_line(need['decision'])}",
        f"- specialized need: {_v3_markdown_safe_line(need['specialized_need'])}",
        f"- required capabilities: {_markdown_safe_values(need['required_capabilities'])}",
        f"- reason codes: {_markdown_safe_values(need['reason_codes'])}",
        "",
        "## Selected Skills",
        "",
    ]
    if selection["selected_skills"]:
        for skill in selection["selected_skills"]:
            contribution = contributions.get(skill["name"], {})
            lines.append(
                f"- {_v3_markdown_safe_line(skill['name'])}: "
                f"{_v3_markdown_safe_line(contribution.get('reason', 'not_recorded'))}; "
                f"capabilities: {_markdown_safe_values(contribution.get('capabilities', []))}"
            )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Confidence",
            "",
            f"- level: {_v3_markdown_safe_line(confidence['level'])}",
            f"- overall: {_v3_markdown_safe_line(confidence['overall'])}",
            f"- top score: {_v3_markdown_safe_line(confidence['top_score'])}",
            f"- runner up score: {_v3_markdown_safe_line(confidence['runner_up_score'])}",
            f"- margin: {_v3_markdown_safe_line(confidence['margin'])}",
            f"- reason codes: {_markdown_safe_values(confidence['reason_codes'])}",
            "",
            "## Provider",
            "",
            f"- requested: {_v3_markdown_safe_line(provider['requested'])}",
            f"- used: {_v3_markdown_safe_line(provider['used'])}",
            f"- model or adapter: {_v3_markdown_safe_line(provider['model_or_adapter'])}",
            f"- response status: {_v3_markdown_safe_line(provider['response_status'])}",
            f"- fallback reason: {_v3_markdown_safe_line(provider['fallback_reason'])}",
            f"- validation reason codes: {_markdown_safe_values(provider['validation_reason_codes'])}",
            "",
            "## Execution Graph",
            "",
            f"- status: {_v3_markdown_safe_line(graph['status'])}",
            f"- acyclic: {_v3_markdown_safe_line(graph['acyclic'])}",
        ]
    )
    if graph["nodes"]:
        for node in graph["nodes"]:
            lines.append(
                f"- node {_v3_markdown_safe_line(node['id'])}: "
                f"{_v3_markdown_safe_line(node['skill'])}; parallel: "
                f"{_v3_markdown_safe_line(node['parallel'])}"
            )
    else:
        lines.append("- nodes: none")
    if graph["edges"]:
        for edge in graph["edges"]:
            lines.append(
                f"- edge {_v3_markdown_safe_line(edge['from'])} to "
                f"{_v3_markdown_safe_line(edge['to'])}: "
                f"{_v3_markdown_safe_line(edge['type'])}; "
                f"evidence: {_v3_markdown_safe_line(edge['evidence'])}"
            )
    else:
        lines.append("- edges: none")
    lines.extend(
        [
            "",
            "## Routing Diagnostics",
            "",
            f"- routing status: {_v3_markdown_safe_line(task_pack['routing_status'])}",
            f"- capability status: {_v3_markdown_safe_line(capability['status'])}",
            f"- missing capabilities: {_markdown_safe_values(capability['missing_capabilities'])}",
            f"- missing inputs: {_markdown_safe_values(capability['missing_inputs'])}",
            f"- graph reason codes: {_markdown_safe_values(graph['reason_codes'])}",
            f"- graph details: {_markdown_safe_values(graph['details'])}",
            "",
            "## Safety Boundary",
            "",
            f"- mode: {_v3_markdown_safe_line(protocol['mode'])}",
            f"- {_v3_markdown_safe_line(protocol['runtime_boundary'])}",
            "",
        ]
    )
    return "\n".join(lines)


def _markdown_safe_values(values: object) -> str:
    if not isinstance(values, (list, tuple)) or not values:
        return "none"
    return ", ".join(_v3_markdown_safe_line(value) for value in values)


def _v3_markdown_safe_line(value: object) -> str:
    return markdown_safe_line(value).replace("~", r"\~")


def markdown_safe_line(value: object) -> str:
    normalized = " ".join(str(value).split())
    escaped = html.escape(normalized, quote=True).replace("\\", "\\\\")
    return re.sub(r"([`*_{}\[\]()#+\-.!|>])", r"\\\1", escaped)


LEGACY_CONTRACT_FIELDS = {
    "requires_context",
    "produces_artifacts",
    "produces_evidence",
    "capability_vector",
    "stage_hint",
    "conflicts_with",
    "excludes",
    "requires_after",
    "cost_weight",
}
LEGACY_CONTRACTS = {
    "ai-langchain-agent-orchestration": {
        "capability_vector": [
            "ai.orchestration",
            "ai.workflow"
        ],
        "cost_weight": 2,
        "produces_artifacts": [
            "agent_workflow_map"
        ],
        "produces_evidence": [
            "orchestration_notes"
        ],
        "requires_context": [
            "workflow_review_scope"
        ],
        "stage_hint": "planning"
    },
    "ai-opensquilla-metaskill-workflow": {
        "capability_vector": [
            "ai.metaskill",
            "ai.bundle_quality"
        ],
        "cost_weight": 2,
        "produces_artifacts": [
            "workflow_review_scope"
        ],
        "produces_evidence": [
            "bundle_quality_notes"
        ],
        "requires_context": [
            "user_request",
            "workspace_context"
        ],
        "stage_hint": "preflight"
    },
    "ai-opensquilla-token-routing-pattern": {
        "capability_vector": [
            "ai.routing",
            "ai.skill_selection"
        ],
        "cost_weight": 2,
        "produces_artifacts": [
            "routing_selection_plan"
        ],
        "produces_evidence": [
            "skill_selection_notes"
        ],
        "requires_context": [
            "workflow_review_scope"
        ],
        "stage_hint": "planning"
    },
    "ai-output-schema-eval": {
        "capability_vector": [
            "ai.eval",
            "ai.output_schema"
        ],
        "cost_weight": 2,
        "produces_evidence": [
            "output_schema_eval_report"
        ],
        "requires_context": [
            "routing_selection_plan"
        ],
        "stage_hint": "review"
    },
    "ai-rule-failure-log-synthesis": {
        "capability_vector": [
            "ai.rule_synthesis"
        ],
        "cost_weight": 2,
        "produces_evidence": [
            "failure_rule_synthesis_report"
        ],
        "requires_context": [
            "tool_schema_contract_report",
            "output_schema_eval_report",
            "regression_test_evidence",
            "ci_check_report"
        ],
        "stage_hint": "verification"
    },
    "ai-tool-schema-protocol-check": {
        "capability_vector": [
            "ai.tool_schema",
            "ai.routing_contract"
        ],
        "cost_weight": 2,
        "produces_evidence": [
            "tool_schema_contract_report"
        ],
        "requires_context": [
            "routing_selection_plan"
        ],
        "stage_hint": "review"
    },
    "business-requirements-brief": {
        "capability_vector": [
            "business.requirements"
        ],
        "cost_weight": 1,
        "produces_artifacts": [
            "requirements_brief"
        ],
        "requires_context": [
            "task_brief"
        ],
        "stage_hint": "planning"
    },
    "code-test-regression": {
        "capability_vector": [
            "code.test"
        ],
        "cost_weight": 2,
        "produces_artifacts": [
            "regression_test_plan"
        ],
        "produces_evidence": [
            "regression_test_evidence"
        ],
        "requires_context": [
            "routing_selection_plan"
        ],
        "stage_hint": "verification"
    },
    "content-seo-brief": {
        "capability_vector": [
            "content.seo"
        ],
        "cost_weight": 2,
        "produces_artifacts": [
            "seo_copy"
        ],
        "requires_context": [
            "requirements_brief"
        ],
        "stage_hint": "planning"
    },
    "content-social-post": {
        "capability_vector": [
            "content.social"
        ],
        "cost_weight": 1,
        "produces_artifacts": [
            "social_post_copy"
        ],
        "requires_context": [
            "seo_copy"
        ],
        "stage_hint": "review"
    },
    "design-motion-interaction-polish": {
        "capability_vector": [
            "design.motion_polish"
        ],
        "cost_weight": 2,
        "produces_evidence": [
            "motion_polish_report"
        ],
        "requires_context": [
            "requirements_brief",
            "build_artifact",
            "ui_review_report"
        ],
        "stage_hint": "review"
    },
    "design-premium-landing-page": {
        "capability_vector": [
            "design.premium_landing"
        ],
        "cost_weight": 3,
        "produces_evidence": [
            "premium_landing_report"
        ],
        "requires_context": [
            "requirements_brief",
            "seo_copy",
            "build_artifact"
        ],
        "stage_hint": "review"
    },
    "design-system-consistency": {
        "capability_vector": [
            "design.system_consistency"
        ],
        "cost_weight": 2,
        "produces_evidence": [
            "design_system_report"
        ],
        "requires_context": [
            "requirements_brief",
            "build_artifact"
        ],
        "stage_hint": "review"
    },
    "design-tailwind-radix-system": {
        "capability_vector": [
            "design.tailwind_radix_system"
        ],
        "cost_weight": 2,
        "produces_evidence": [
            "tailwind_radix_system_report"
        ],
        "requires_context": [
            "requirements_brief",
            "build_artifact"
        ],
        "stage_hint": "review"
    },
    "design-ui-review": {
        "capability_vector": [
            "design.ui_review"
        ],
        "cost_weight": 2,
        "produces_evidence": [
            "ui_review_report"
        ],
        "requires_context": [
            "requirements_brief",
            "build_artifact"
        ],
        "stage_hint": "review"
    },
    "design-visual-quality-review": {
        "capability_vector": [
            "design.visual_quality"
        ],
        "cost_weight": 2,
        "produces_evidence": [
            "visual_quality_report"
        ],
        "requires_context": [
            "requirements_brief",
            "build_artifact",
            "ui_review_report"
        ],
        "stage_hint": "review"
    },
    "engineering-build-release": {
        "capability_vector": [
            "engineering.build_release"
        ],
        "cost_weight": 2,
        "produces_artifacts": [
            "build_artifact"
        ],
        "produces_evidence": [
            "build_readiness_report"
        ],
        "requires_context": [
            "requirements_brief"
        ],
        "stage_hint": "execution"
    },
    "engineering-ci-troubleshoot": {
        "capability_vector": [
            "engineering.ci"
        ],
        "cost_weight": 2,
        "produces_evidence": [
            "ci_check_report"
        ],
        "requires_context": [
            "regression_test_plan"
        ],
        "stage_hint": "verification"
    },
    "execution-browser-check": {
        "capability_vector": [
            "execution.browser_check"
        ],
        "cost_weight": 2,
        "produces_evidence": [
            "browser_check_report"
        ],
        "requires_context": [
            "build_artifact",
            "ui_review_report"
        ],
        "stage_hint": "verification"
    },
    "execution-browser-use-web-task": {
        "capability_vector": [
            "execution.browser_agent"
        ],
        "cost_weight": 3,
        "produces_evidence": [
            "browser_agent_plan"
        ],
        "requires_context": [
            "requirements_brief",
            "build_artifact"
        ],
        "stage_hint": "verification"
    },
    "execution-playwright-browser-automation": {
        "capability_vector": [
            "execution.playwright_browser"
        ],
        "cost_weight": 3,
        "produces_evidence": [
            "browser_automation_report",
            "browser_check_report"
        ],
        "requires_context": [
            "build_artifact",
            "ui_review_report"
        ],
        "stage_hint": "verification"
    },
    "execution-publish-check": {
        "capability_vector": [
            "execution.publish_check"
        ],
        "cost_weight": 2,
        "produces_evidence": [
            "publish_readiness_report"
        ],
        "requires_context": [
            "requirements_brief",
            "ui_review_report",
            "browser_check_report"
        ],
        "stage_hint": "verification"
    },
    "security-supply-chain-review": {
        "capability_vector": [
            "security.supply_chain"
        ],
        "cost_weight": 2,
        "produces_evidence": [
            "supply_chain_review_report"
        ],
        "requires_context": [
            "routing_selection_plan"
        ],
        "stage_hint": "review"
    }
}
NEW_V2_CONTRACT_SKILLS = {
    "ai-llamaindex-rag-knowledge-workflow",
    "code-ast-refactor-safety",
    "code-dead-path-cleanup-review",
    "code-python-debug",
    "code-review-risk",
    "code-simplify-refactor-plan",
    "codebase-explore-map",
    "data-haystack-rag-pipeline",
    "data-marker-pdf-markdown-review",
    "data-markitdown-file-to-markdown",
    "data-qdrant-vector-retrieval",
    "data-unstructured-document-partition",
    "research-source-check",
    "security-guardrails-output-validation",
    "security-llm-guard-io-scanning",
    "security-prompt-injection-review",
}


def project_legacy_contracts(value: object) -> object:
    if isinstance(value, list):
        return [project_legacy_contracts(item) for item in value]
    if not isinstance(value, dict):
        return value
    projected = {key: project_legacy_contracts(item) for key, item in value.items()}
    contract = projected.get("contract")
    if isinstance(contract, dict):
        name = projected.get("name")
        if name in NEW_V2_CONTRACT_SKILLS:
            projected.pop("contract")
        elif name in LEGACY_CONTRACTS:
            projected["contract"] = LEGACY_CONTRACTS[name]
        else:
            projected["contract"] = {key: item for key, item in contract.items() if key in LEGACY_CONTRACT_FIELDS}
    return projected
