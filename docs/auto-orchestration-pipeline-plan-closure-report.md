# Auto Orchestration Pipeline Plan Closure Report

Date: 2026-06-27

Repository:

```text
https://github.com/aidi1723/safe-agent-skills
```

## Status

The auto orchestration pipeline-plan delivery is closed for the current scope.

This work studied the useful orchestration shape behind recent agent workflow
infrastructure patterns and applied only the method-level orchestration layer to
this repository. The result is a richer, deterministic task-pack contract for
host agents without adding any new runtime authority.

## Closure Baseline

Current verified baseline:

```text
total skills: 114
trusted skills: 108
scenario bundles: 13
trusted scenario bundles: 13
overlap groups: 7
tampered skills: 0
unknown provenance records: 0
verify: ok
schema-check: ok
maintain-check: ok
full tests: 89 passed
```

## What Was Closed

### 1. Method-Only Pipeline Contract

A new `pipeline_plan` field was added to deterministic routed outputs:

- `smart`
- `task-pack --router scenario`
- `task-pack --router mesh`

The plan is a method-only stage contract. It gives host agents explicit stage
ordering, expected inputs and outputs, gate conditions, verification notes,
approval-gate hints, and failure-handling guidance.

It does not execute tools, install dependencies, start servers, or grant host
permissions.

### 2. Backward-Compatible Router Behavior

The simple non-routed task-pack flow remains unchanged.

This means hosts that only consume basic task-pack output do not receive a new
field unexpectedly, while hosts that use scenario or mesh routing can adopt the
new contract immediately.

`execution_graph` was kept for compatibility. `pipeline_plan` is the richer
human-readable and machine-readable orchestration layer on top.

### 3. CLI And Rendering Support

The CLI now exposes `pipeline_plan` in both JSON and Markdown outputs, and
includes the same orchestration guidance in `agent_instructions`.

This makes the feature usable by:

- programmatic host runtimes
- plain-text agents
- operators inspecting packs manually

### 4. Approval Gate Narrowing

Approval-gate detection was tightened before closure.

The final implementation avoids deriving approval requirements from broad skill
names or descriptions. Instead, it uses explicit task and scenario action
signals plus a small boundary map for known runtime-sensitive skills. This
prevents false positives for review-only tasks such as router-quality review.

### 5. Public Documentation

The following docs were updated or added for this delivery:

- `docs/smart-skill-router.md`
- `docs/agent-task-pack.md`
- `docs/updates/2026-06-27-auto-orchestration-pipeline-plan.md`
- `docs/auto-orchestration-pipeline-plan-closure-report.md`

## Verification Evidence

Commands run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_router
PYTHONPATH=src python3 -m unittest tests.test_registry_cli
PYTHONPATH=src python3 -m unittest discover -s tests
PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry catalog
PYTHONPATH=src python3 -m onecode_skill_sanitizer schema-check --registry catalog
PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check \
  --registry catalog \
  --bundles bundles/index.json \
  --references external-references/index.json
PYTHONPATH=src python3 -m onecode_skill_sanitizer smart \
  "复查 safe-agent-skills 项目是否达到智能选择和自动搭配 skill 的目标" \
  --format json \
  --max-skills 8
```

Verified result:

```text
tests.test_router: 27 passed
tests.test_registry_cli: 44 passed
full test suite: 89 passed
verify: status ok
schema-check: status ok
maintain-check: status ok
review-only smart route: pipeline_plan.approval_gates == []
```

## What Is Not Claimed

This closure does not claim:

- OpenMontage runtime adoption
- Headroom proxy, wrapper, MCP, or network-layer integration
- automatic media generation, rendering, upload, or publication
- new shell, browser, network, MCP, filesystem, account, or production-write
  permissions
- that a task pack may bypass host approval rules

The delivery is orchestration guidance only.

## Remaining Boundary

The current `pipeline_plan` is deterministic and advisory.

Future work may separately review:

- runtime execution adapters
- approval-policy handoff formats
- operator checkpoints with resumable state
- richer stage templates for additional scenario bundles

Those would require separate design and safety review. They are not part of
this closure.

## Closure Decision

The method-only auto orchestration pipeline-plan work is complete for this
delivery.

The repository now has a stronger default orchestration contract for trusted
skill composition while preserving the existing permission-neutral model.
