# High-Frequency Intelligent Skill Selection v3 Closure Report

Date: 2026-07-16

## Closure Decision

The high-frequency intelligent skill-selection v3 **structural delivery
milestone is closed** and merged into local `main` at structural tip
`6710ba8`. Documentation alignment for this report follows on the same
`main` line after that tip.

The delivered system is an **opt-in** Router v3 path for the router entry plus
exactly seven high-frequency candidates. It decides whether a specialized skill
is needed, recalls only trusted cohort candidates, composes a minimum
capability-complete set, compiles real dependency edges, and emits a strict
task-pack v3 contract. It remains **method-only**: it does not execute skills,
grant permissions, or replace the host runtime.

| Gate | Status |
| --- | --- |
| Structural delivery (code, schema, routine verify) | **PASS / closed** |
| Validation-split acceptance (`router-eval-v3 --split validation`) | **PASS** |
| One-shot `final_test` release acceptance | **FAIL / exhausted** (`final_acceptance_failed`) |
| Three-arm task-level oracle evidence | **Not established** (`task_evaluation_missing`) |
| Semantic influence through public CLI | **Disabled** (shadow-only only) |
| v3 as default routing schema | **Not decided** (v2 remains default) |

Do not describe this merge as production-ready final acceptance for v3. Do not
rerun the exhausted `final_test` one-shot without a new, explicitly authorized
evaluation.

## Delivered Scope

### Public surface

- Opt-in CLI: `--schema-version 3` on `smart` and `task-pack`.
- Router v2 remains the default schema.
- Commands: `router-eval-v3`, `router-task-eval-v3`.
- Safe routine gate: `bash scripts/verify.sh` (skips `final_test` by default).
- One-shot flag: `ONECODE_RUN_ROUTER_V3_FINAL_TEST=1` is reserved for a future
  fresh, explicitly authorized release evaluation. Do not set it for the
  current rollout; its permitted run is exhausted and failed.

### Intelligent cohort

Entry plus seven candidates (fixed allowlist):

| Role | Name |
| --- | --- |
| Entry | `safe-agent-router` |
| Candidate | `codebase-explore-map` |
| Candidate | `code-review-risk` |
| Candidate | `code-test-regression` |
| Candidate | `execution-browser-check` |
| Candidate | `research-source-check` |
| Candidate | `design-ui-review` |
| Candidate | `security-supply-chain-review` |

Adding an eighth candidate requires a separate frequency, trust, examples,
evaluation, and operator-review decision.

### Runtime modules

| Module | Responsibility |
| --- | --- |
| `need_gate.py` | Current-intent need decision, negation, explanation-only suppression, capability extraction, action-span boundaries |
| `skill_candidates.py` | Fixed cohort constants, reviewed routing-example load, trusted candidate recall |
| `semantic_provider.py` | Candidate-bounded semantic shadow validation; no public influence path |
| `skill_selection.py` | Marginal composition, conflicts, real dependency edges, `none` / `clarify` / `incomplete` / `blocked` |
| `task_pack_v3.py` | Strict v3 task pack builder and compatibility loss reporting |
| `router_eval_v3.py` | 120-case held-out loader, case scoring, exact dependency edges, acceptance gates |
| `compatibility.py` | Explicit v3→legacy loss dimensions |

### Contracts and data

- `schemas/task-pack-v3.schema.json` — strict top-level v3 pack; candidates
  `maxItems: 7`; skill names constrained by `cohortSkillName` enum.
- `schemas/semantic-rerank-response.schema.json` — shadow response bound to the
  same seven-skill enum.
- `catalog/routing-examples.json` — reviewed runtime routing examples only.
- `evals/high-frequency-skill-selection.json` — isolated 120 held-out cases;
  evaluator-only; must not be runtime inputs.

### Evaluation rigor raised at closure

Branch-review wrap-up before merge:

1. **Exact dependency edges.** A case fails when
   `actual_edges != expected_edges` (missing **or** unexpected edges).
2. **Dependency-edge precision.** Aggregate metric
   `dependency_edge_precision` with acceptance threshold `>= 0.70`, tracked
   alongside `dependency_edge_recall`.
3. **Schema cohort bound.** Task-pack v3 candidates and selected / execution
   skill names cannot leave the fixed seven-skill set.

## Final Verification Evidence

Verification was rerun on `main` after the local fast-forward merge of
`feature/intelligent-skill-selection-v3`.

| Verification | Result |
| --- | --- |
| `bash scripts/verify.sh` | Passed |
| Unit and integration tests | 577 passed, 0 failed |
| `router-eval-v3 --split validation` | Acceptance **passed** |
| Feature worktree | Removed after merge |
| Feature branch | Deleted after merge (`feature/intelligent-skill-selection-v3`) |
| Structural tip on `main` | `6710ba8` |
| Docs alignment | On `main` after structural tip (see history for the docs commit) |
| Delivery delta vs pre-merge `origin/main` baseline | Structural merge was 57 commits ahead; docs alignment adds further commits |

### Validation-split metrics (held-out validation cases)

Recorded on `main` at closure (60 validation cases; 2 case failures that did
not breach acceptance thresholds):

| Metric | Value | Gate | Status |
| --- | ---: | ---: | --- |
| forbidden_skill_false_positive_rate | 0.0 | `< 0.02` | Pass |
| forbidden_scenario_false_positive_rate | 0.0 | `< 0.02` | Pass |
| dag_validity | 1.0 | `>= 0.98` | Pass |
| dependency_edge_precision | 1.0 | `>= 0.70` | Pass |
| dependency_edge_recall | 0.7143 | `>= 0.70` | Pass |
| multi_intent_exact_match | 0.9231 | `>= 0.92` | Pass |
| scenario_f1 | 0.9848 | `>= 0.96` | Pass |
| skill_f1 | 0.9848 | `>= 0.96` | Pass |
| recall_at_3 | 1.0 | `>= 0.95` | Pass |
| top_1_accuracy | 1.0 | `>= 0.90` | Pass |
| no_skill_accuracy | 1.0 | `>= 0.90` | Pass |
| exact_selected_set_accuracy | 0.9833 | `>= 0.85` | Pass |

### Final-test and task-level status (not passed)

| Item | Status |
| --- | --- |
| Permitted `final_test` one-shot | Failed release acceptance (`final_acceptance_failed`) |
| Three-arm task evidence (v3 / oracle / no-skill) | Missing (`task_evaluation_missing`) |
| Aggregate task pass-rate vs oracle | Not established |
| Semantic influence default | Not enabled |

These blockers remain authoritative until a **new**, explicitly authorized
evaluation generates fresh evidence. Historical failed one-shot results must
not be retuned against.

## Objective Capability Assessment

| Capability | Assessment |
| --- | --- |
| Opt-in v3 task pack | Delivered |
| Need gate (`none` / `single` / `composite` / `clarify`) | Delivered |
| Seven-skill cohort recall and hard exclusions | Delivered |
| Exact selected-set composition | Delivered for cohort scope |
| Real dependency edges + exact edge evaluation | Delivered |
| DAG validity on validation split | Delivered (1.0) |
| Candidate-bounded semantic shadow plumbing | Delivered |
| Semantic influence on selection | Intentionally not delivered via public CLI |
| Whole-catalog intelligent routing | Intentionally not delivered |
| Autonomous execution / permission grants | Intentionally not delivered |
| Final-test release acceptance | Not passed |
| Task-level oracle acceptance | Not established |
| Making v3 the default schema | Out of milestone |

## Normative Operator Truths

These statements remain required documentation truth after closure:

1. Router v3 remains opt-in; Router v2 remains the default.
2. Scope is the router entry plus exactly seven high-frequency candidates.
3. Deterministic selection is active.
4. Semantic providers are candidate-bounded and run in shadow only.
5. Semantic influence is disabled through the public CLI.
6. The validation split passes; the one permitted `final_test` run failed
   release acceptance.
7. No real three-arm task evidence was generated.
8. Runtime examples are reviewed routing data.
9. The isolated 120 held-out cases are evaluator-only and must not be runtime
   inputs.
10. Skills are method guidance, not permission grants.
11. `bash scripts/verify.sh` skips `final_test` by default.
12. `ONECODE_RUN_ROUTER_V3_FINAL_TEST=1` is only for a future fresh, explicitly
    authorized one-shot release evaluation; do not set it for the current
    rollout.
13. Adding an eighth candidate requires a separate frequency, trust, examples,
    evaluation, and operator-review decision.
14. Dependency edges are scored for **exact set equality** and both precision
    and recall; schema skill names cannot leave the fixed cohort.

## Design And Plan Alignment

| Artifact | Role after closure |
| --- | --- |
| [Design](superpowers/specs/2026-07-15-high-frequency-intelligent-skill-selection-design.md) | Normative intent for the milestone; historical baseline metrics remain design-time evidence |
| [Implementation plan](superpowers/plans/2026-07-15-high-frequency-intelligent-skill-selection.md) | Execution record; structural tasks delivered |
| This closure report | Authoritative delivery and gate status on `main` |
| [Router Development Guide](router-development.md) | Current maintainer behavior and boundaries |
| [Agent Task Pack](agent-task-pack.md) | Current operator contract for packs |
| [Documentation Index](index.md) | Source of truth for current vs historical docs |

Relative to the design acceptance list, structural and validation-split metric
gates for the deterministic cohort path are met on validation. Task-level
oracle gates and final-test acceptance are **not** met. Phase 4 (opt-in
semantic influence) and Phase 5 (default-schema decision) remain future work.

## Required Next Work

Before treating v3 as release-accepted or default:

1. Generate real three-arm task outcomes (v3 pack, independent oracle pack,
   no-skill control) without cross-contamination.
2. Obtain a **new**, explicitly authorized one-shot `final_test` evaluation only
   after task evidence exists; do not reuse the exhausted failed run as a
   tuning loop.
3. Keep semantic influence disabled until shadow disagreement analysis and all
   acceptance gates pass under a reviewed decision.
4. Preserve v1/v2 frozen behavior and the method-only host boundary.
5. Keep the seven-skill allowlist closed unless a full cohort-expansion review
   lands.

Optional maintenance (not blocking structural closure): decide whether to
commit or ignore root `uv.lock` leftovers from local `uv` installs.

## Final Repository State

- Branch: `main`
- Structural tip commit: `6710ba8`
  (`fix: require exact dependency edges and bound v3 cohort skills`)
- Docs alignment: committed on `main` after the structural tip (message
  prefix `docs: close intelligent skill selection v3`)
- Pre-delivery design commit on the same line: `13fe4de`
- Structural milestone: **PASS**
- Validation-split quality gate: **PASS**
- Final-test / task-level release gate: **FAIL / not established**
- Release statement: suitable for repository publication as an **opt-in
  deterministic v3 cohort router**, with the limitations in this report
  retained in README, operator docs, and the documentation index
