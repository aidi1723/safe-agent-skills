# High-Frequency Intelligent Skill Selection v3

Date: 2026-07-16

## Summary

Closed structural delivery of the opt-in Router v3 high-frequency cohort path
on local `main` at `6710ba8`, then removed the
`feature/intelligent-skill-selection-v3` worktree and branch.

The path decides whether specialized guidance is needed, recalls only the fixed
seven high-frequency candidates, composes a minimum capability-complete set,
compiles real dependency edges, and emits a strict task-pack v3 contract. It is
method-only: it does not execute skills, grant permissions, or replace the host
runtime.

## What Landed

- Public opt-in: `--schema-version 3` on `smart` and `task-pack` (v2 default).
- Modules: need gate, cohort candidates, selection, task-pack v3, semantic
  shadow provider, compatibility loss, `router-eval-v3`.
- Data: `catalog/routing-examples.json` (runtime reviewed examples) and
  `evals/high-frequency-skill-selection.json` (120 held-out evaluator-only cases).
- Schema: `schemas/task-pack-v3.schema.json` with `maxItems: 7` candidates and
  `cohortSkillName` enum binding.
- Evaluation rigor at wrap-up: exact dependency-edge set equality; aggregate
  `dependency_edge_precision` and `dependency_edge_recall` floors at `0.70`.

## Gate Status

| Gate | Status |
| --- | --- |
| Structural delivery | PASS / closed |
| `bash scripts/verify.sh` | PASS (577 tests) |
| Validation-split acceptance | PASS |
| One-shot `final_test` | FAIL / exhausted (`final_acceptance_failed`) |
| Three-arm task oracle evidence | Missing (`task_evaluation_missing`) |
| Semantic influence via public CLI | Disabled |
| v3 as default schema | Not decided |

## Operator Boundaries

- Do not set `ONECODE_RUN_ROUTER_V3_FINAL_TEST=1` for the current rollout.
- Do not retune against the exhausted failed final-test one-shot.
- Do not load the held-out eval file at runtime.
- Adding an eighth candidate requires a separate frequency, trust, examples,
  evaluation, and operator-review decision.

## Authoritative Write-Up

- [v3 Closure Report](../high-frequency-intelligent-skill-selection-v3-closure-report-2026-07-16.md)
- [Design](../superpowers/specs/2026-07-15-high-frequency-intelligent-skill-selection-design.md)
- [Implementation Plan](../superpowers/plans/2026-07-15-high-frequency-intelligent-skill-selection.md)
