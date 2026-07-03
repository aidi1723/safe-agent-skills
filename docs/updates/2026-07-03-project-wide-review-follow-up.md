# Project-Wide Review Follow-Up

Date: 2026-07-03

## Summary

Reviewed the current project state against earlier audit, closure, roadmap,
and release-follow-up reports. The current repository verification is clean,
but several improvement tracks remain open as next-phase work.

Fresh verified baseline:

```text
catalog skills: 172
trusted skills: 166
trusted scenario bundles: 23
external references: 19
trusted overlap groups: 7
tracked claude-skills candidates: 336
covered claude-skills candidates: 336
router eval cases: 39
full verification tests: 144
```

## Review Inputs

This pass checked the current repository against:

- `docs/audit-hardening-closure-report.md`
- `docs/smart-router-claude-skills-closure-report.md`
- `docs/project-closure-report.md`
- `docs/reference-pattern-expansion-closure-report.md`
- `docs/auto-orchestration-pipeline-plan-closure-report.md`
- `docs/scenario-capability-expansion-closure-report.md`
- `docs/claude-skills-expansion-audit.md`
- `docs/headroom-agent-io-compression-closure-report.md`
- `docs/next-development-plan.md`
- `docs/scheduler-hardening-roadmap.md`
- `docs/external-reference-roadmap.md`
- `docs/maintenance-log.md`
- `docs/maintenance-guide.md`
- `docs/catalog-status.md`

## Findings

### P1: Scanner Engine Hardening Remains The Main Technical Gap

Earlier audit reports correctly treated the scanner as a deterministic
preflight guardrail, not a full malware detector. The current tests include a
larger bypass suite, but the next durable improvement is still the Phase 1
scanner engine upgrade from `docs/next-development-plan.md`:

- tokenized command extraction
- variable assignment and command-substitution tracking
- source-to-execution path tracking for downloaded files
- dedicated false-positive examples for broad scanner families

This remains the highest-value next implementation slice because it improves
intake safety without changing runtime permissions.

### P1: Source Import Command Is Still Deliberately Missing

The repository has strong `reference_only` and `local_authoring` semantics.
It now also rejects `source_import` records that do not include upstream
capture metadata. The remaining missing piece is a bounded source-import
command that records upstream commit or release, upstream content hashes,
license snapshots, and capture metadata directly.

Until that command exists, `source.usage = source_import` remains tightly
restricted and schema-checked.

### P2: Router Quality Metrics Now Include Classification

The original roadmap asked for router quality metrics. The project now has
39 fixed router-eval cases plus negative, prefix, taxonomy, and schema
constraints. Same-day follow-up added explicit false-positive /
false-negative classification fields and low-confidence route trend tracking.

What remains:

- stale-baseline warnings for historical docs that are easy to misread as
  current status

### P2: Collision And Preconditions Are Not Yet First-Class Contracts

Scenario bundles and overlap groups already reduce redundant skill selection.
However, skill preconditions, exclusions, and collision diagnostics are still
roadmap items rather than enforced metadata.

Useful next contracts:

- `preconditions`
- `excludes`
- `requires_after`
- bundle-level collision diagnostics

### P2: Semantic Gateway And Context Records Remain Future Host Work

The pipeline plan now records stages, gates, evidence fields, and approval
boundaries. It is still method-only guidance. Runtime semantic gateways,
pre-tool-call assertions, and compact completed-stage context records remain
future host-integration work.

This should stay separate from trusted skill content so skills never become
permission grants.

### P3: Historical Closure Reports Have Stale Baselines

Older closure reports correctly record their historical baselines, but they
contain outdated counts such as:

- 109 / 103 skills in June audit and Headroom closure reports
- 114 / 108 skills in orchestration closure reports
- 161 / 155 skills in the smart-router Claude-skills closure
- 36 router-eval cases and 131 tests in the reference-pattern closure

Those documents are historical and should not be rewritten as if they were
current. The improvement is documentation consolidation: make current status
obvious from `docs/maintenance-guide.md`, `docs/catalog-status.md`, and this
follow-up note, and treat old closure baselines as dated evidence.

## Closed Or Bounded Items

- Claude-skills backlog is covered: 336 / 336 mapped or converted.
- Reference-pattern expansion is covered for the user-supplied projects.
- Low-confidence vague continuation tasks now stay lightweight.
- Router-eval now has positive and negative checks plus schema validation for
  control, expectation, and constraint fields.
- Router-eval now includes compact quality-summary metrics by scenario,
  task type, and issue id.
- Source-import usage now requires auditable `source.capture` metadata.
- Current verification, maintain-check, reference-check, registry verify, and
  router-eval pass.

## Recommended Next Work Order

1. Start scanner engine Phase 1 with a small failing-test slice for shell
   tokenization and command substitution.
2. Router false-positive / false-negative classification and low-confidence
   trend tracking are completed in
   [Router Eval Quality Classification](2026-07-03-router-eval-quality-classification.md).
3. Add networked source-import automation only after preserving the current
   capture-metadata schema gate.
4. Add skill precondition/exclusion metadata after router quality summaries
   make collision behavior measurable.
5. Keep semantic gateway and context-record work as host-integration design,
   not catalog-skill content.

## Verification Performed

- `bash scripts/verify.sh`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval --eval evals/router-quality.json --registry catalog --bundles bundles/index.json`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check --registry catalog --bundles bundles/index.json --references external-references/index.json --claude-skills-candidate-map docs/claude-skills-candidate-map.json`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry catalog`

## Boundary

This follow-up is a review and maintenance-log update. It does not change
router matching behavior, catalog trust state, runtime permissions, external
reference adoption, source-import policy, browser/network/tool permissions, or
publication authority.
