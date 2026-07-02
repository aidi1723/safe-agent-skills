# Smart Skill Selection And Execution Design

Date: 2026-07-02

Project: `Safe-Agent-Skills`

## Goal

Improve the project so selected skills are more accurate, task packs are more
actionable, and host agents complete work with clearer evidence, acceptance
criteria, and residual-risk reporting.

This design follows three phases:

```text
user task
  -> stronger task profile and selection quality signal
  -> clearer trusted skill and bundle rationale
  -> richer task-pack execution protocol
  -> verified catalog maintenance and targeted skill-library updates
```

The guiding principle is practical task completion quality. The router should
select fewer, better skills; explain why they matter; give the host agent a
stage-by-stage contract; and make incomplete coverage visible instead of
letting the agent imply that a task is fully handled.

## Current Problem

The repository already has a deterministic router, scenario bundles, mesh
routing, pipeline plans, overlap pruning, invariant capabilities, and router
evals. These are strong foundations, but the task-pack output still leaves too
much interpretation to the host agent:

- Selection confidence is implied by scores and coverage, but not summarized.
- Required capability gaps appear in coverage, but are not promoted as a
  first-class quality signal.
- Skill explanations identify covered capabilities, but do not consistently
  label execution roles such as planner, reviewer, verifier, or handoff.
- Agent instructions list stages, but do not yet provide a compact completion
  contract that forces evidence, assumptions, failed checks, and residual risks
  into the final answer.
- External skill-library references such as `claude-skills` are useful market
  and ecosystem signals, but should remain metadata-only references until each
  local adoption passes provenance, sanitization, and trusted review.

## Non-Goals

This change must not:

- execute selected skills
- call an LLM to route skills
- install, run, or copy third-party skill repositories
- select quarantined, rejected, disabled, or review-required skills in default
  mode
- grant filesystem, network, browser, shell, connector, account, publishing, or
  production permissions
- bypass provenance, hash, schema, or registry verification
- optimize for catalog size over trusted coverage and task completion quality
- rewrite the router around a new architecture before improving the existing
  deterministic path

## Recommended Approach

Use a small, backward-compatible enhancement to the existing router and
task-pack contract.

Add new metadata rather than replacing existing fields:

- `selection_quality`: summary of confidence, coverage, missing required
  capabilities, pruned skills, and route warnings.
- richer `selection_explanations`: deterministic role labels and clearer
  selection reasons.
- `acceptance_criteria`: task-pack-level requirements the host agent should
  satisfy before claiming completion.
- `completion_contract`: final response requirements for evidence, selected
  skills, verification, failed checks, unresolved assumptions, and residual
  risks.

Keep `scenario`, `mesh`, `pipeline_plan`, `execution_graph`, `coverage`,
`invariant_capabilities`, and `pruned_skills` compatible with the current JSON
shape.

## Phase 1: Smarter Skill Selection

### Selection Quality

For `task-pack --router scenario` and `task-pack --router mesh`, add a
`selection_quality` object:

```json
{
  "confidence": "high",
  "score": 0.86,
  "covered_required_count": 6,
  "missing_required_count": 1,
  "coverage_ratio": 0.86,
  "low_confidence": false,
  "warnings": [
    "Missing required capability: supply_chain_review"
  ],
  "pruned_skills": [
    "design-accessibility-check"
  ]
}
```

Rules:

- `coverage_ratio` is covered required capabilities divided by total required
  capabilities when a trusted scenario is selected.
- General fallback routes have lower confidence and a warning that no trusted
  scenario matched.
- Missing required capabilities always produce warnings.
- Pruned skills are surfaced when mesh overlap pruning removes them.
- Confidence labels are deterministic: `high`, `medium`, or `low`.

### Selection Explanation Roles

Extend each skill explanation with a deterministic `execution_role`:

| Role | Meaning |
| --- | --- |
| `preflight` | Clarifies task scope, constraints, and permission boundaries |
| `planner` | Decomposes work and defines the method or output contract |
| `producer` | Guides artifact creation or task execution under host control |
| `reviewer` | Checks quality, safety, compliance, schema, or source risks |
| `verifier` | Defines tests, checks, evidence, or CI expectations |
| `handoff` | Summarizes unresolved risks and future rule candidates |
| `supplemental` | Useful trusted guidance without a required capability match |

The role should be derived from the existing pipeline stage map, scenario
stage map, verifier keywords, and skill naming conventions. This makes the
agent understand how to use each selected skill, not only why it was selected.

## Phase 2: Better Task-Pack Execution

### Acceptance Criteria

Add task-pack-level `acceptance_criteria` generated from:

- selected scenario expected output
- required capability coverage
- pipeline stage gates
- invariants
- approval gates

Example:

```json
[
  "Record selected scenario and trusted skills before execution.",
  "Complete every pipeline stage gate or record the failed gate.",
  "Record verification evidence before claiming completion.",
  "List residual risks for missing required capabilities."
]
```

These criteria are method-only. They tell the host agent what must be reported;
they do not authorize runtime actions.

### Completion Contract

Add `completion_contract`:

```json
{
  "final_response_must_include": [
    "selected_scenario",
    "selected_skills",
    "verification_performed",
    "unresolved_assumptions",
    "residual_risks"
  ],
  "stop_conditions": [
    "required input missing",
    "registry verification failed",
    "approval-required runtime action blocked",
    "required capability missing and no fallback exists"
  ],
  "evidence_requirements": [
    "commands or checks run",
    "schema or format checks",
    "source or provenance checks when relevant"
  ]
}
```

`agent_instructions` should render this contract in Markdown so host agents
that only consume text still follow the same execution discipline.

### Failure Handling

The task pack should make failure states explicit:

- registry verification failure blocks task-pack creation
- low confidence routes must say why they are low confidence
- missing required capabilities must be listed as residual risks
- approval-required actions must stop until the host runtime or operator grants
  permission
- unavailable verification must be reported instead of treated as success

## Phase 3: Skill Library Update And Maintenance

After phases 1 and 2 pass verification, update and maintain the skill library.

### External Reference Capture

Add `claude-skills` to `external-references/index.json` as metadata-only:

- source URL: `https://github.com/alirezarezvani/claude-skills`
- author: `alirezarezvani`
- source type: `github_reference`
- adoption status: `reference_only`
- capabilities: broad skill templates, multi-agent distribution, domain
  packaging, companion scripts, persona and command patterns
- runtime notes: do not install, copy, execute, or promote upstream skills into
  trusted status without per-skill review

The reference is useful for product packaging and coverage-gap analysis, not
as a trusted runtime source.

### Targeted Catalog Expansion

Use the external reference only to identify gaps. Prioritize local or
reference-only candidates in these areas:

- finance and SaaS metrics review
- project management and delivery operations
- business operations and procurement
- commercial workflows such as pricing, RFP, deal desk, and partnerships
- research operations, including clinical, product, market, and research
  finance workflows

Each new local skill must include `SKILL.md`, `skill.json`,
`SANITIZATION_REPORT.json`, trusted status only after approval, provenance
records, verifier expectations, and schema validation.

### Public Catalog Overview

Add or update a catalog overview that maps:

```text
domain -> trusted skill count -> key scenarios -> example task-pack command
```

This should improve usability without changing runtime authority.

## Tests And Verification

Implementation should add or update tests for:

- `selection_quality` in scenario routes
- `selection_quality` in mesh routes with invariant capabilities and pruned
  skills
- low-confidence general fallback routes
- missing required capability warnings
- `selection_explanations` role labeling
- `acceptance_criteria` and `completion_contract` in JSON task packs
- Markdown rendering of the completion contract in `agent_instructions`
- `claude-skills` metadata-only reference validation
- router eval coverage for the improved task-pack contract

Required verification before completion:

```bash
bash scripts/verify.sh
```

If catalog files are updated, also confirm that `maintain-check`,
`reference-check`, `router-eval`, and `schema-check` remain covered by the
verify script.

## Acceptance Criteria

The work is complete when:

- scenario and mesh task packs expose `selection_quality`
- task packs expose `acceptance_criteria` and `completion_contract`
- agent instructions render the new execution contract
- tests prove missing capabilities and low-confidence routes are visible
- `claude-skills` is recorded as metadata-only external reference
- any catalog additions are trusted only after existing governance checks
- `bash scripts/verify.sh` passes

## Open Risks

- More metadata can make task packs longer. The implementation should keep
  fields concise and avoid duplicating full skill text.
- Confidence scoring must stay deterministic and explainable. It should not
  imply statistical certainty.
- Catalog expansion can increase noise if added before router quality improves.
  For this reason, phases 1 and 2 must land before broad skill-library updates.
- External popularity is not safety evidence. Upstream star count and skill
  count may guide prioritization, but not trusted status.
