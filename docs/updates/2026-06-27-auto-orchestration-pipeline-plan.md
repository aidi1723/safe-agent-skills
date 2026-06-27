# Auto Orchestration Pipeline Plan

Date: 2026-06-27

## Summary

Added a method-only `pipeline_plan` orchestration contract to routed task-pack
outputs so host agents can follow staged execution guidance without gaining new
runtime authority.

## Decision

Do not import runtime-heavy orchestration systems directly.

Adopt only the useful method layer:

- explicit stage ordering
- stage-level inputs and outputs
- gate conditions
- verification notes
- approval-gate hints
- failure-handling guidance

Keep the result deterministic, trusted-catalog-bound, and permission-neutral.

## Local Impact

`pipeline_plan` is now included in:

- `smart`
- `task-pack --router scenario`
- `task-pack --router mesh`

The simple non-routed task-pack flow stays unchanged for compatibility.

JSON, Markdown, and `agent_instructions` output now expose the new plan.

## Safety Boundary

`pipeline_plan` does not grant permissions.

Dependency installation, shell execution, browser automation, network access,
MCP or proxy startup, account or API-key use, file upload, media rendering,
paid provider calls, and destructive filesystem or git actions remain under
host runtime and operator approval policy.

## Verification

- router unit tests required
- CLI unit tests required
- full test discovery required
- registry verification required
- schema check required
- maintain check required
- smoke check required for review-only approval-gate false positives

## Closure

Implementation and verification details are recorded in
[Auto Orchestration Pipeline Plan Closure Report](../auto-orchestration-pipeline-plan-closure-report.md).
