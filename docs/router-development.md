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

## Router v3 Bounded Rollout

Router v3 remains opt-in; Router v2 remains the default. Its scope is the
router entry plus exactly seven high-frequency candidates:
`codebase-explore-map`, `code-review-risk`, `code-test-regression`,
`execution-browser-check`, `research-source-check`, `design-ui-review`, and
`security-supply-chain-review`. It is not whole-catalog routing.
Adding an eighth candidate requires a separate frequency, trust, examples,
evaluation, and operator-review decision.

Deterministic selection is active.
Semantic providers are candidate-bounded and run in shadow only.
Semantic influence is disabled through the public CLI.
Shadow output may be recorded for comparison, but it does not change selected
skills, ordering, execution guidance, or runtime authority.

The validation split passes, but the one permitted `final_test` run failed
release acceptance (`final_acceptance_failed`). Do not rerun that isolated
split or represent v3 as having passed final acceptance. The
`task_evaluation_missing` blocker means no real three-arm task evidence was
generated, so task-level acceptance is not established. Local missing
`jsonschema` coverage is an environment verification gap; it is not evidence
that schema validation passed.

Runtime examples are reviewed routing data and may support deterministic
selection.
The isolated 120 held-out cases are evaluator-only and must not be runtime
inputs. Application code must not load or name the held-out dataset; only the
isolated evaluator may receive its path.
Skills are method guidance, not permission grants.

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

Hybrid Router v2 contributions must satisfy these gates:

- Gold labels must be manually curated, repository-declared as not generated
  from router output, and separately reviewed before production approval. The
  evaluator must not generate or repair its own expected labels.
- Every trusted scenario must have at least five curated dataset cases.
- Decomposition changes require focused multi-intent fixtures, including
  dependency ordering and an over-splitting negative case.
- New skills added to a core scenario require Contract v2 coverage and must
  keep the eight-scenario `contract-check` ratio at or above `0.80`.
- Tests must be deterministic and provider-free. The first milestone must pass
  with `provider.requested: none` and `provider.used: none`.
- Cyclic intent graphs and incoherent blocked graphs must fail closed. A cycle
  is represented as blocked semantics, not as a ready DAG.
- Sequential fixtures must assert required dependency edges, not merely intent
  or scenario selection.

Run the focused v2 gates after installing development dependencies:

```bash
python3 -m pip install -e ".[dev]"
python3 -m ruff check .
PYTHONPATH=src python3 -m onecode_skill_sanitizer contract-check \
  --registry catalog --bundles bundles/index.json \
  --scenario website-build-launch --scenario code-review-hardening \
  --scenario codebase-change-lifecycle --scenario skill-router-quality-review \
  --scenario open-source-release --scenario rag-agent-knowledge-app \
  --scenario document-to-knowledge-base --scenario security-agent-guardrails \
  --minimum-ratio 0.80
PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval-v2 \
  --eval evals/multi-intent-gold.json --registry catalog \
  --bundles bundles/index.json
```

The complete `scripts/verify.sh` release gate includes the one-shot v3
`final_test`. Its permitted run is already exhausted for the current rollout,
so do not invoke the complete gate during this rollout.

The v2 dataset is a separate corpus from `evals/router-quality-v2.json`. Its
labels are manually curated and repository-declared as not generated from
router output. The current literal metadata values are enforced by the existing
loader, but they do not evidence an external reviewer identity or persisted
external review artifact. Independent external review remains a
production-readiness gate. Keep the fixed 100-case count, category distribution,
scenario coverage, and no-`actual_*` label contract.
Track `multi_intent_exact_match`, `scenario_precision`, `scenario_recall`,
`scenario_f1`, `dependency_edge_recall`,
`forbidden_scenario_false_positive_rate`, and `dag_validity`.

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

After changing manifests, reindex before verification. `reindex` refreshes the
catalog index and manifest integrity records for the current CLI:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer reindex --registry catalog
```

## Contract Metadata For High-Traffic Bundles

High-traffic scenario bundles should stay contract-complete in both balanced
and deep routing. If a selected skill lacks `contract`, the router must fall
back from `mode: contract` to stage ordering, which makes advanced
orchestration less precise.

For bundle skills that may appear in `smart --strategy deep`, add a compact
contract with:

- `requires_context`: upstream artifacts or external context needed to apply
  the method.
- `produces_artifacts` or `produces_evidence`: named outputs that downstream
  skills can depend on.
- `capability_vector`: dotted capability identifiers that match the skill
  purpose.
- `stage_hint`: one of `preflight`, `source`, `planning`, `review`,
  `execution`, or `verification`.
- `cost_weight`: an integer from 1 to 10.

Keep these contracts method-only. They describe ordering and evidence, not
permission to run shells, browsers, connectors, accounts, network, or
production writes.

Regression coverage should include at least one real-catalog route for each
high-frequency bundle. For `website-build-launch`, deep routing must keep
optional polish skills such as premium landing, motion polish, and browser
automation in a contract graph without fallback.

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

Router eval files can assert trace behavior with these optional fields:

- `expected_trace_selected`: skills that must appear as selected in the
  compact eval trace.
- `expected_trace_required`: skills that must be protected by required
  capabilities or invariants.
- `expected_trace_pruned`: skills that must be overlap-pruned for the case.
- `expected_trace_reason_codes`: low-confidence or route-quality reason codes
  that must appear in the trace.

Use these fields sparingly for cases where the decision path matters, not for
every ordinary scenario case. They are best for router-quality, low-confidence,
overlap-pruning, and required-capability regressions.

Focused command:

```bash
PYTHONPATH=src python3 -m unittest tests.test_router.RouterTest -v
```

The complete verification script is reserved for an explicitly authorized
release evaluation. Do not invoke it for the current v3 rollout because its
one permitted `final_test` run is already exhausted. Do not claim routing
quality improved until the applicable fresh verification passes.

## Current Gap Policy

The remaining intelligent-routing work should be implemented in this order:

1. Continue extending complete skill `contract` metadata to remaining
   high-traffic bundles.
2. Add negative and ambiguity examples to `evals/router-quality.json`.
3. Add trace-based metrics to router eval output.
4. Consider two-stage recall/rank/prune scoring only after trace coverage
   makes current deterministic behavior easy to audit.

The project should continue to prefer deterministic, reviewable metadata over
opaque model-based routing for default trusted execution packs.
