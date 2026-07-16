# Documentation Index

This page is the documentation source of truth for the current repository.
Documents under updates, batches, closure reports, and superpowers records are
historical evidence unless a current guide links to them as normative input.

## Start Here

- [Project README](../README.md)
- [Architecture](architecture.md)
- [Open Source Statement](open-source-statement.md)
- [Catalog Overview](catalog-overview.md)
- [Workspace Boundary](workspace-boundary.md)

## Current Architecture And Behavior

- [Smart Skill Router](smart-skill-router.md)
- [Agent Task Pack](agent-task-pack.md)
- [Router Development Guide](router-development.md)
- [Agent-Compatible Skill Bundles](agent-compatible-skill-bundles.md)
- [Sanitization Policy](sanitization-policy.md)
- [Source Baseline](source-baseline.md)

## Router v3 Evaluation Record

Router v3 remains opt-in; Router v2 remains the default. The bounded v3 cohort
uses deterministic selection for the router entry and seven high-frequency
candidates. The public CLI opt-in mechanism is `--schema-version 3` on `smart`
or `task-pack`. Semantic providers are candidate-bounded and shadow-only;
semantic influence is disabled through the public CLI. Skills remain method
guidance, not permission grants.

The validation split passes, but the one permitted `final_test` run failed
release acceptance (`final_acceptance_failed`). No real three-arm task evidence
was generated (`task_evaluation_missing`), so neither final nor task-level
acceptance is established. The reviewed runtime examples are separate from the
isolated 120 held-out evaluator-only cases.

`bash scripts/verify.sh` is the safe routine verification command and skips
`final_test` by default. `ONECODE_RUN_ROUTER_V3_FINAL_TEST=1` is reserved for a
future fresh, explicitly authorized one-shot release evaluation. Do not set it
for the current rollout; its permitted run is exhausted and failed.

Structural delivery for this opt-in path is closed on `main`. See the closure
report for verification evidence, validation metrics, exact dependency-edge
scoring, and remaining release blockers.

- [High-Frequency Intelligent Skill Selection v3 Closure](high-frequency-intelligent-skill-selection-v3-closure-report-2026-07-16.md)
- [High-Frequency Intelligent Skill Selection Design](superpowers/specs/2026-07-15-high-frequency-intelligent-skill-selection-design.md)
- [High-Frequency Intelligent Skill Selection Implementation Plan](superpowers/plans/2026-07-15-high-frequency-intelligent-skill-selection.md)

## Operator And Maintainer Guides

- [Operator Guide](operator-guide.md)
- [Maintenance Guide](maintenance-guide.md)
- [Module Boundary Refactor Plan](module-boundary-refactor-plan.md)
- [Batch Lifecycle](../batches/README.md)
- [Delivery Checklist](delivery-checklist.md)

## Catalog And Skill Authoring

- [Catalog Status](catalog-status.md)
- [Skill Taxonomy](skill-taxonomy.md)
- [Skill Index](skill-index.md)
- [Skill Bundles](skill-bundles.md)
- [Skill Overlap Groups](skill-overlap-groups.md)
- [External Reference Roadmap](external-reference-roadmap.md)

## Historical Records

Plans, dated updates, acceptance notes, and closure reports explain how the
current system was reached. They do not override the current documents above.

- [History Map](history.md)
- [Maintenance Log](maintenance-log.md)
- [Feature Log](feature-log.md)
- [v3 Structural Delivery Update](updates/2026-07-16-high-frequency-intelligent-skill-selection-v3.md)
- [GitHub Update Summary 2026-07-16](github-update-summary-2026-07-16.md)
