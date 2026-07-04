# Maintenance Guide

## Workspace Boundary

Maintain this project only from the standalone repository:

```text
<safe-agent-skills-checkout>
```

Before any maintenance work, run:

```bash
cd "<safe-agent-skills-checkout>"
git status --short
```

See [Workspace Boundary](workspace-boundary.md).

## Public Baseline

The catalog is ready for public maintenance when:

- every top-level category has at least 3 `trusted` skills
- every entry has source URL, source path, author, license, reference, collector,
  source hash, and sanitized hash
- `verify` reports no tamper or unknown provenance issues
- normal selection excludes quarantined and review-required skills
- `task-pack` can emit a trusted-skill instruction pack for a representative
  task
- scenario bundles reference only existing `trusted` skills

Current baseline:

- total skills: 172
- trusted skills: 166
- quarantined skills: 3
- review-required skills: 3
- categories meeting 3 trusted skills: 15 / 15
- scenario bundles: 23 trusted
- external references: 19
- router eval cases: 42
- full verification tests: 162
- phase status: maintenance boundary refactor in progress

Closure report:

- [Auto Orchestration Pipeline Plan Closure Report](auto-orchestration-pipeline-plan-closure-report.md)
- [Scenario Capability Expansion Closure Report](scenario-capability-expansion-closure-report.md)
- [Smart Router And Claude Skills Closure Report](smart-router-claude-skills-closure-report.md)
- [Claude Skills Reference-Only Backlog](claude-skills-reference-only-backlog.md)
- [Phase 001 Closure Report](phase-001-closure-report.md)
- [Phase 002 Scenario Router Closure Report](phase-002-scenario-router-closure-report.md)
- [Audit Hardening Closure Report](audit-hardening-closure-report.md)

Next development:

- [Next Development Plan](next-development-plan.md)

Latest update:

- [Structured Context Routing](updates/2026-07-04-structured-context-routing.md)
- [Current Intent Routing](updates/2026-07-04-current-intent-routing.md)
- [Requires After Contract Ordering](updates/2026-07-04-requires-after-contract-ordering.md)
- [Contract Diagnostics](updates/2026-07-04-contract-diagnostics.md)
- [Router Eval Quality Classification](updates/2026-07-03-router-eval-quality-classification.md)
- [GitHub Update Summary](github-update-summary-2026-07-03.md)
- [Final Closure Report](final-closure-report.md)
- [Source Import Capture Gate](updates/2026-07-03-source-import-capture-gate.md)
- [Delivery Readiness Report](delivery-readiness-report.md)
- [Router Quality Summary](updates/2026-07-03-router-quality-summary.md)
- [Scanner Variable Path Hardening](updates/2026-07-03-scanner-variable-path-hardening.md)
- [Scanner Substitution Download Hardening](updates/2026-07-03-scanner-substitution-download-hardening.md)
- [Scanner Variable Download Hardening](updates/2026-07-03-scanner-variable-download-hardening.md)
- [Project-Wide Review Follow-Up](updates/2026-07-03-project-wide-review-follow-up.md)
- [Router Eval Constraint Schema](updates/2026-07-03-router-eval-constraint-schema.md)
- [Router Eval Taxonomy Constraints](updates/2026-07-03-router-eval-taxonomy-constraints.md)
- [Router Eval Prefix Constraints](updates/2026-07-03-router-eval-prefix-constraints.md)
- [Router Eval Negative Constraints](updates/2026-07-03-router-eval-negative-constraints.md)
- [Lightweight General Fallback](updates/2026-07-03-lightweight-general-fallback.md)
- [Vague Continue Optimization Guard](updates/2026-07-03-vague-continue-optimization-guard.md)
- [Update Record Follow-Up Routing](updates/2026-07-03-update-record-followup-routing.md)
- [Skill Router Execution Order](updates/2026-07-03-skill-router-execution-order.md)
- [Typo Skill Orchestration Routing](updates/2026-07-03-typo-skill-orchestration-routing.md)
- [Project Release Follow-Up Routing](updates/2026-07-03-project-release-follow-up-routing.md)
- [Project Check Follow-Up](updates/2026-07-03-project-check-follow-up.md)
- [Reference Pattern Expansion](updates/2026-07-03-reference-pattern-expansion.md)
- [Agentic Reference Patterns](updates/2026-07-03-agentic-reference-patterns.md)
- [Industry Application Orchestration](updates/2026-07-03-industry-application-orchestration.md)
- [Claude Skills Backlog Cluster Coverage](updates/2026-07-03-claude-skills-backlog-cluster-coverage.md)
- [Smart Router And Claude Skills Closure](updates/2026-07-02-smart-router-claude-skills-closure.md)
- [Claude Skills Expansion](updates/2026-07-02-claude-skills-expansion.md)
- [Claude Skills Expansion Audit](claude-skills-expansion-audit.md)
- [Claude Skills Reference-Only Backlog](claude-skills-reference-only-backlog.md)
- [Auto Orchestration Pipeline Plan](updates/2026-06-27-auto-orchestration-pipeline-plan.md)
- [Scenario System Expansion](updates/2026-06-16-scenario-system-expansion.md)
- [Community Skill Reference Review](updates/2026-06-16-community-skill-reference-review.md)
- [Headroom Agent I/O Compression Closure Report](headroom-agent-io-compression-closure-report.md)

## Code Maintenance Boundary

Keep command wiring thin and move reusable logic into focused modules:

- `src/onecode_skill_sanitizer/cli.py`: argparse setup, command orchestration,
  JSON/Markdown output, and compatibility wrappers.
- `src/onecode_skill_sanitizer/paths.py`: repository asset path resolution,
  including `SAFE_AGENT_SKILLS_HOME`.
- `src/onecode_skill_sanitizer/validation.py`: manifest hashing, sealing,
  schema checks, policy checks, and other pure validation helpers.
- `src/onecode_skill_sanitizer/references.py`: external reference index file
  loading and metadata-only reference validation.
- `src/onecode_skill_sanitizer/router.py`: deterministic task profiling,
  scenario scoring, mesh routing, contract graphs, pipeline plans, and
  selection quality.
- `src/onecode_skill_sanitizer/scanner.py`: deterministic source text risk
  scanning.
- `src/onecode_skill_sanitizer/taxonomy.py`: skill and task taxonomy
  classification.

When adding behavior, prefer the narrowest module that owns the domain. Keep
`cli.py` as the adapter layer unless the behavior is command-specific and not
needed by tests, maintain-check, router-eval, or future callers.

## Refactor Workflow

Use small compatibility-preserving moves:

1. Identify the command behavior and the smallest reusable boundary.
2. Add or move a focused test that imports the target module directly.
3. Run the focused test and confirm it fails for the expected missing boundary.
4. Move the implementation without changing command output or registry data.
5. Re-run the focused test and the affected CLI regression tests.
6. Update [Module Boundary Refactor Plan](module-boundary-refactor-plan.md)
   when the move is complete.
7. Run the release verification commands before reporting completion.

Avoid mixing pure module moves with catalog hash changes, skill status changes,
router scoring changes, or batch content updates. Those require separate
review notes and regression coverage.

## Intake Rule

Do not execute third-party skills during intake.

New community entries should be added as reference-style workflows unless the
license and reuse rights are clear. Runtime connectors require separate review.
External reference-only entries are maintained in
`external-references/index.json` and must remain `metadata_only: true` until
they are converted through the sanitization and approval path.
Operator-specific maintenance notes, local paths, account details, and private
handoff information must stay in ignored local files, not public docs.

## Review States

- `trusted`: allowed for normal skill selection
- `quarantined`: recorded but excluded from normal selection
- `review_required`: needs operator review before use
- `rejected`: known unsuitable entry
- `disabled`: previously accepted but no longer active

## Release Checklist

Before publishing or updating the public repository:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
ruff check .
PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry catalog
PYTHONPATH=src python3 -m onecode_skill_sanitizer task-pack \
  "review security risk in this package" \
  --registry catalog \
  --top 2 \
  --format markdown
PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check \
  --registry catalog \
  --bundles bundles/index.json \
  --references external-references/index.json \
  --claude-skills-candidate-map docs/claude-skills-candidate-map.json
PYTHONPATH=src python3 -m onecode_skill_sanitizer schema-check \
  --registry catalog
PYTHONPATH=src python3 -m onecode_skill_sanitizer task-pack \
  "build a product website and prepare launch checks" \
  --registry catalog \
  --include-bundles \
  --bundles bundles/index.json \
  --router scenario \
  --max-skills 8 \
  --format json
PYTHONPATH=src python3 -m onecode_skill_sanitizer task-pack \
  "design a RAG document agent with vector retrieval and citation checks" \
  --registry catalog \
  --include-bundles \
  --bundles bundles/index.json \
  --router scenario \
  --max-skills 8 \
  --format json
PYTHONPATH=src python3 -m onecode_skill_sanitizer smart \
  "build a landing page and prepare launch checks" \
  --invariants "不能泄露密钥；公开文案必须合规；必须响应式验证" \
  --format json
bash scripts/verify.sh
git diff --check
```

Confirm:

- unit tests report the expected test count for the current baseline
- ruff reports no lint errors
- `status: ok`
- `unknown_provenance_count: 0`
- `tampered_count: 0`
- `reference-check` reports the expected `reference_count`
- each category has at least 3 trusted skills
- task-pack output contains only trusted skills unless review mode is explicitly
  requested
- every bundle in `bundles/index.json` references existing trusted skills
- every overlap group in `catalog/overlap-groups.json`, when present,
  references existing trusted skills
- `maintain-check` reports `status: ok`
- `schema-check` reports `status: ok`
- scenario router website sample selects `website-build-launch`
- scenario router RAG sample selects `rag-agent-knowledge-app`
- smart router reports `deterministic_mesh_router`
- batch docs exist for new entries
- public docs mention any new module boundary, router behavior, or catalog
  governance change before release

## Contribution Standard

Each new skill should include:

- concise `SKILL.md`
- `skill.json` with taxonomy and source records
- clear category and subcategory
- bounded workflow
- verifier expectations
- failure handling

Do not add hidden execution behavior, install instructions, broad file access,
credential handling, or policy override language to a skill.
