# Auto Orchestration Pipeline Plan Design

Date: 2026-06-27

Project: `Safe-Agent-Skills`

## Goal

Add a method-only automatic orchestration layer to `smart` and scenario
`task-pack` output.

The new layer should help host agents apply selected trusted skill guidance as
a clear pipeline with stages, inputs, outputs, gates, verification checks, and
runtime boundaries. It should learn from agentic pipeline systems such as
OpenMontage without importing runtime code, invoking media tools, installing
external dependencies, or granting execution authority.

Target flow:

```text
user task
  -> deterministic task profile
  -> trusted scenario bundle
  -> selected trusted skills
  -> existing execution graph
  -> new pipeline_plan with stages and gates
  -> host agent executes under its own permissions
```

## Current Problem

`smart` already returns a deterministic mesh execution graph:

```text
preflight -> source -> planning -> review -> execution -> verification
```

That graph is useful, but still too generic for complex agent work:

- Stage nodes do not describe concrete inputs and outputs.
- Gate semantics are limited.
- Host agents still have to infer what evidence must be produced before
  moving between stages.
- Scenario bundles define skill order, but not a full stage contract.
- Runtime boundaries are present as text, but not attached to each stage.

The result is safe but not yet as operationally clear as a pipeline-oriented
agent workflow.

## Non-Goals

This change must not:

- execute selected skills
- install or run OpenMontage, Headroom, Remotion, FFmpeg, MCP servers, proxies,
  wrappers, or external tools
- grant filesystem, network, browser, shell, connector, account, media render,
  publish, or production permissions
- call an LLM to plan routes
- select quarantined, rejected, disabled, or review-required skills in default
  mode
- claim token, cost, render, benchmark, or production savings that are not
  locally measured

The feature is an orchestration plan, not an orchestration runtime.

## Recommended Approach

Add a new `pipeline_plan` field to `smart` output and to
`task-pack --router scenario` output.

Do not replace the existing `execution_graph`. Keep it for compatibility and
use `pipeline_plan` as the richer, human-readable and machine-readable contract
for host agents that can consume stage plans.

This is the best balance because:

- it preserves existing API shape
- it reuses trusted bundles and selected skills
- it gives agents clearer stop conditions
- it stays deterministic and testable
- it keeps method guidance separate from runtime authority

## Output Shape

`pipeline_plan` should be a JSON object:

```json
{
  "id": "content-video-production",
  "name": "Content Video Production",
  "mode": "method_only",
  "source": "trusted_scenario_bundle",
  "runtime_boundary": "Skills provide method only; host runtime controls permissions.",
  "stages": [
    {
      "id": "preflight",
      "name": "Preflight",
      "purpose": "Confirm task scope, safety boundary, required inputs, and missing information.",
      "skills": ["business-requirements-brief"],
      "inputs": ["user_task", "task_profile", "invariants"],
      "outputs": ["scope_summary", "missing_inputs", "runtime_boundary"],
      "gate": {
        "id": "preflight_complete",
        "condition": "Required inputs are known or explicitly marked missing.",
        "failure_action": "stop_and_request_missing_inputs"
      },
      "verification": ["trusted skill status checked", "runtime boundary recorded"]
    }
  ],
  "approval_gates": [
    {
      "stage": "execution",
      "required_for": ["tool execution", "dependency install", "publish action"],
      "owner": "host_runtime_or_operator"
    }
  ]
}
```

Field rules:

- `id`: scenario bundle id when present, otherwise `general`.
- `mode`: always `method_only` for this release.
- `source`: `trusted_scenario_bundle`, `direct_skill_selection`, or
  `fallback_general`.
- `stages`: ordered list derived from selected scenario, selected skills, and
  current graph stages.
- `approval_gates`: explicit list of actions outside this repository's
  authority.
- `runtime_boundary`: concise boundary repeated at plan level.

## Stage Model

Use a small fixed stage vocabulary:

| Stage | Purpose |
| --- | --- |
| `preflight` | Scope, permissions, required inputs, constraints, invariants |
| `source` | Source inventory, provenance, citations, retrieved context |
| `planning` | Task decomposition, selected method, output contract |
| `production` | Method-only execution guidance for the host agent |
| `review` | Safety, quality, compliance, schema, or rights review |
| `verification` | Tests, browser checks, schema checks, evidence capture |
| `handoff` | Final summary, unresolved risks, next approval boundary |

The router should map existing skills into stages with deterministic rules.
Prefer explicit scenario execution order. If no scenario is selected, map
selected skills by category and known verifier role.

## Scenario Mapping

For selected trusted bundles, derive a scenario-specific pipeline. Examples:

### Content Video Production

```text
preflight:
  content-strategy-matrix, content-seo-brief
planning:
  content-brand-voice-boundary, media-video-script-review
production:
  media-remotion-video-production-boundary
review:
  content-editorial-review, content-claims-compliance-filter, media-asset-review
verification:
  execution-publish-check
handoff:
  record asset, render, upload, and publish approval boundaries
```

This remains planning-only. It must not render, generate media, download
assets, or publish content.

### Skill Router Quality Review

```text
preflight:
  ai-opensquilla-metaskill-workflow
planning:
  ai-opensquilla-token-routing-pattern, ai-langchain-agent-orchestration
review:
  ai-tool-schema-protocol-check, ai-output-schema-eval
verification:
  code-test-regression, engineering-ci-troubleshoot
handoff:
  ai-rule-failure-log-synthesis, security-supply-chain-review
```

This should produce router selection findings, coverage gaps, contract checks,
and regression recommendations.

### General Fallback

When no trusted scenario matches:

- create `id: "general"`
- keep `source: "direct_skill_selection"`
- create only stages that have selected skills
- do not invent a scenario
- include a low-confidence note in `handoff`

## Approval And Runtime Boundary

Every plan must explicitly say that selected skills do not grant runtime
authority.

The generated plan should mark these as approval-required when they appear in
task intent, skill descriptions, or scenario boundaries:

- dependency install
- shell command execution
- browser automation
- network access
- MCP server exposure
- proxy/wrapper startup
- account or API-key use
- file upload or publication
- media rendering
- paid model or provider call
- destructive filesystem or git action

These gates are advisory to the host agent. The host runtime remains the
enforcement layer.

## Data Flow

Implementation should reuse existing router data:

```text
route_scenario_task / route_mesh_task
  -> task_profile
  -> selected_scenario
  -> selected skills
  -> capability coverage
  -> execution_graph
  -> build_pipeline_plan(...)
```

`build_pipeline_plan` should be a focused helper, not a large addition to CLI
formatting code.

Inputs:

- task text
- task profile
- selected scenario bundle
- selected skill records
- coverage records
- execution graph nodes
- invariants, if present

Output:

- normalized `pipeline_plan` dictionary

## Error Handling

If scenario metadata is incomplete:

- keep the selected skills
- create a generic stage plan
- mark missing stage mappings in `handoff.unresolved_risks`

If a selected skill cannot be mapped:

- place it in `review` when it is security, compliance, schema, output eval, or
  code review related
- place it in `planning` for AI orchestration or requirements skills
- place it in `verification` for test, browser, CI, or publish-check skills
- otherwise place it in `production`

If required capabilities are missing:

- include them in `handoff.unresolved_risks`
- do not invent untrusted skills

## Testing

Add regression tests for:

- `smart` includes `pipeline_plan`
- `task-pack --router scenario` includes `pipeline_plan`
- known scenario maps to stable stages
- no-scenario task returns a `general` plan without forced bundle selection
- every stage has `id`, `name`, `purpose`, `skills`, `inputs`, `outputs`,
  `gate`, and `verification`
- approval gates are present for runtime-sensitive scenarios such as video,
  publishing, browser automation, dependency install, and proxy/MCP tasks
- existing router outputs remain backward compatible

Verification commands:

```bash
PYTHONPATH=src python3 -m unittest tests.test_router tests.test_registry_cli
PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry catalog
PYTHONPATH=src python3 -m onecode_skill_sanitizer schema-check --registry catalog
PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check \
  --registry catalog \
  --bundles bundles/index.json \
  --references external-references/index.json
```

## Documentation

Update:

- `docs/smart-skill-router.md`
- `docs/agent-task-pack.md`
- `README.md` router section, if output examples change

Docs should emphasize:

- `pipeline_plan` is method-only
- `execution_graph` remains available
- hosts may use `pipeline_plan` for step ordering, stop conditions, and
  verification prompts
- runtime authority stays with the host agent and operator approval policy

## Open Questions

None for the first implementation. The design intentionally avoids runtime
execution, external dependencies, and LLM planning.

Future work may add measured context-budget estimates, but only after local
measurement rules are defined.
