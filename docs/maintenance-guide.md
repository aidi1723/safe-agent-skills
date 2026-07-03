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
- router eval cases: 39
- phase status: reference-pattern expansion and project-check follow-up closed
  for today's delivery

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
```

Confirm:

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
