# Router Development Guide

## Purpose

This guide explains how to extend the Safe-Agent-Skills router without losing
its core guarantees: deterministic trusted-skill selection, auditable
orchestration, compact task packs, and method-only safety boundaries.

The router should become smarter by improving local metadata, scoring,
contracts, traces, and regression tests. It must not become a hidden runtime
executor, unverified plugin loader, or permission grant.

## Design Goals

- Choose a small useful skill pack instead of loading the whole catalog.
- Prefer trusted scenario bundles when task intent is clear.
- Keep vague tasks low-confidence instead of attaching an unrelated workflow.
- Preserve required safety, verification, and release capabilities even when
  `max_skills` is small.
- Emit enough evidence for maintainers to understand why each skill was
  selected, omitted, or pruned.
- Keep all execution guidance advisory; host runtimes still control files,
  shell, network, browsers, accounts, connectors, and production writes.

## Reference Patterns

Community projects are useful references, but their runtime trust model should
not be copied directly into this repository.

- AnyTool-style retrieval: use staged candidate narrowing and quality-aware
  selection to avoid tool context overload. In this repo, that maps to
  deterministic profile detection, trusted scenario bundles, capability
  coverage, overlap pruning, and `selection_trace`.
- LangGraph-style orchestration: model work as stages and graph edges instead
  of a flat list. In this repo, that maps to `execution_graph`,
  `contract_graph`, and `pipeline_plan`.
- Semantic Kernel / AutoGen / CrewAI-style agent composition: keep roles,
  functions, and handoffs explicit. In this repo, that maps to stage roles,
  selected skill reasons, and method-only handoff contracts.
- MCP-style tool discovery: expose a simple host entry point while keeping the
  discovered capability contract explicit. In this repo, that maps to the
  installed `safe-agent-router` skill and the read-only task-pack command.

External projects can inspire design, but external tools, MCP servers,
community skills, or runtime connectors must still pass provenance capture,
sanitization, trusted status, registry verification, and operator approval
before they can affect default routing.

## Router Flow

The `smart` command is the recommended default:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer smart \
  "review safe-agent-skills router quality and skill selection order" \
  --registry catalog \
  --bundles bundles/index.json \
  --max-skills 8 \
  --format json
```

The mesh router performs these deterministic stages:

1. Normalize task text with audited aliases.
2. Build a task profile from current intent, scenario signals, domains,
   artifacts, risks, and required capabilities.
3. Select the best trusted scenario bundle, or stay in direct-skill fallback.
4. Recall candidate skills from bundle order, preferred capability skills,
   invariants, and direct task matches.
5. Preserve required capability skills even if the normal skill cap is reached.
6. Prune known overlap groups when the adjacent skill is not required.
7. Sort by contract graph when complete contracts exist; otherwise use stage
   ordering.
8. Emit `coverage`, `selection_quality`, `selection_trace`,
   `execution_graph`, `contract_diagnostics`, and `pipeline_plan`.

## Selection Trace Contract

`selection_trace` is the maintainer-facing audit trail for intelligent
selection. It is intentionally deterministic and machine-readable.

Required top-level fields:

- `schema_version`: current trace schema version.
- `router_mode`: `deterministic_mesh_router` or
  `deterministic_scenario_router`.
- `strategy`: `fast`, `balanced`, or `deep`.
- `task_profile`: compact task type, primary domain, and signal score.
- `scenario`: selected scenario id, name, and score.
- `candidate_count`: number of skill candidates considered.
- `selected_count`: number of skills emitted in the final pack.
- `required_skill_count`: number of skills protected by required capabilities
  or invariants.
- `invariant_capabilities`: mapped hard-boundary capabilities.
- `coverage`: covered, missing, and omitted capability ids.
- `pruned`: overlap-pruned skill names and reasons.
- `candidates`: one record per considered skill, with `status`, `selected`,
  `required`, `match_score`, `stage`, `matched_capabilities`, and `reason`.
- `quality`: confidence, score, low-confidence flag, reason codes, and
  warnings.
- `decision_stages`: profile, scenario, coverage, pruning, and final-pack
  summary.

Allowed candidate `status` values:

- `selected`
- `pruned`
- `available_not_selected`

Allowed candidate `reason` values should stay narrow and auditable. Current
values include:

- `required_capability`
- `direct_task_match`
- `scenario_bundle`
- `router_selected`
- `overlap_group_non_required`
- `not_needed_for_current_route`

Do not put private task content, credentials, raw logs, or full external tool
schemas inside `selection_trace`.

## Adding Or Changing A Scenario

Change these files together:

- `src/onecode_skill_sanitizer/router.py`
  - Add or update `SCENARIO_PROFILES`.
  - Add aliases only when they are common, audited, and low collision.
  - Add explicit stage mapping in `SCENARIO_STAGE_SKILLS` when generic stage
    inference is not good enough.
- `bundles/index.json`
  - Add or update the trusted bundle, required capabilities, preferred skills,
    execution order, expected output, and safety boundary.
- Skill manifests under `catalog/**/skill.json`
  - Add `contract` metadata when ordering, dependencies, outputs, or conflicts
    matter.
- `tests/test_router.py`
  - Add profile detection, scenario selection, coverage, trace, and negative
    misrouting tests.
- `docs/smart-skill-router.md` and `docs/agent-task-pack.md`
  - Document any new output fields or operator behavior.

After changing manifests, re-seal and reindex before verification:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer reindex --registry catalog --seal-manifests
```

## TDD Requirements

For router behavior changes, write tests before implementation.

Minimum test set:

- Positive profile detection for the intended task phrasing.
- Negative profile detection for likely false positives.
- Scenario bundle selection.
- Required capability coverage.
- `selection_trace` for selected, pruned, required, and low-confidence paths.
- Contract graph or fallback graph behavior when ordering changes.
- CLI task-pack JSON or Markdown exposure when output fields change.

Focused command:

```bash
PYTHONPATH=src python3 -m unittest tests.test_router.RouterTest -v
```

Full verification:

```bash
bash scripts/verify.sh
```

Do not claim routing quality improved until fresh verification passes.

## Current Gap Policy

The remaining intelligent-routing work should be implemented in this order:

1. Expand `selection_trace` consumers and eval assertions.
2. Add more complete skill `contract` metadata for high-traffic bundles.
3. Add negative and ambiguity examples to `evals/router-quality.json`.
4. Add trace-based metrics to router eval output.
5. Consider two-stage recall/rank/prune scoring only after trace coverage
   makes current deterministic behavior easy to audit.

The project should continue to prefer deterministic, reviewable metadata over
opaque model-based routing for default trusted execution packs.
