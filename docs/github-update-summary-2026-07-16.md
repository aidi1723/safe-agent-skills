# GitHub Update Summary

Date: 2026-07-16

## Summary

This update publishes the **opt-in Router v3** high-frequency intelligent
skill-selection structural milestone for `safe-agent-skills`.

The work adds a method-only need gate, a fixed seven-skill cohort path, strict
task-pack v3, held-out evaluation with exact dependency-edge scoring, and
candidate-bounded semantic shadow plumbing. Schema v2 remains the default.
Semantic influence is disabled on the public CLI. Final-test release acceptance
and three-arm task oracle evidence are **not** claimed.

Authoritative closure:

- [High-Frequency Intelligent Skill Selection v3 Closure](high-frequency-intelligent-skill-selection-v3-closure-report-2026-07-16.md)

## What Was Updated

### Router v3 surface

- Opt-in CLI: `--schema-version 3` on `smart` and `task-pack`.
- New modules: need gate, cohort recall, selection, task-pack v3, semantic
  shadow provider, compatibility loss, `router-eval-v3` / `router-task-eval-v3`.
- Schemas: `schemas/task-pack-v3.schema.json`,
  `schemas/semantic-rerank-response.schema.json`.
- Runtime examples: `catalog/routing-examples.json` (reviewed; not the held-out
  set).
- Held-out evaluator data: `evals/high-frequency-skill-selection.json`
  (120 cases; evaluator-only; must not be runtime inputs).

### Cohort scope

Entry plus exactly seven candidates:

1. `safe-agent-router` (entry)
2. `codebase-explore-map`
3. `code-review-risk`
4. `code-test-regression`
5. `execution-browser-check`
6. `research-source-check`
7. `design-ui-review`
8. `security-supply-chain-review`

Candidates are schema-bounded (`maxItems: 7`, `cohortSkillName` enum). Adding an
eighth candidate requires a separate frequency, trust, examples, evaluation,
and operator-review decision.

### Evaluation rigor

- Dependency edges require **exact set equality** (missing or unexpected edges
  fail the case).
- Aggregate gates track both `dependency_edge_precision` and
  `dependency_edge_recall` (floor `0.70` on validation).
- `bash scripts/verify.sh` remains the safe routine gate and skips `final_test`
  by default.
- `ONECODE_RUN_ROUTER_V3_FINAL_TEST=1` is reserved for a future fresh,
  explicitly authorized one-shot release evaluation. Do not set it for this
  rollout; the permitted run is exhausted and failed.

### Documentation

- Closure report, dated update note, README / index / operator / router /
  task-pack alignment.
- Design and implementation plan retain historical execution detail with
  delivery status banners pointing at the closure report.
- Architecture, delivery checklist, feature log, and history map updated for
  the same gate language.

## Gate Status (Do Not Overclaim)

| Gate | Status |
| --- | --- |
| Structural delivery | PASS |
| Validation-split acceptance | PASS |
| Routine `bash scripts/verify.sh` | PASS (577 tests at structural closure) |
| One-shot `final_test` | FAIL / exhausted (`final_acceptance_failed`) |
| Three-arm task oracle evidence | Missing (`task_evaluation_missing`) |
| Semantic influence via public CLI | Disabled |
| v3 as default schema | Not decided (v2 remains default) |

## Operator Example

```bash
onecode-skill-sanitizer smart "review this patch" \
  --schema-version 3 --format json

PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval-v3 \
  --eval evals/high-frequency-skill-selection.json \
  --registry catalog --bundles bundles/index.json \
  --routing-examples catalog/routing-examples.json \
  --split validation
```

Skills remain method guidance, not permission grants. Host runtimes still own
filesystem, network, shell, browser, connector, and production authority.

## Privacy And Publication Hygiene

Before this GitHub publication:

- Local absolute home paths and private workspace markers remain blocked by
  `scripts/verify.sh` private-path checks.
- Local-only review drafts (`/项目审查报告*.md`) stay gitignored and are not
  published.
- Untracked local lockfiles (for example root `uv.lock` from a private install)
  are not included in this push.
- No API keys, tokens, or credential material are added by this release.
- Fixture strings used only to test redaction stay synthetic.

## Related Links

- [v3 Closure Report](high-frequency-intelligent-skill-selection-v3-closure-report-2026-07-16.md)
- [Design](superpowers/specs/2026-07-15-high-frequency-intelligent-skill-selection-design.md)
- [Implementation Plan](superpowers/plans/2026-07-15-high-frequency-intelligent-skill-selection.md)
- [Dated Update](updates/2026-07-16-high-frequency-intelligent-skill-selection-v3.md)
- [Router Development Guide](router-development.md)
- [Documentation Index](index.md)
