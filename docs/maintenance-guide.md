# Maintenance Guide

## Workspace Boundary

Maintain this project only from the standalone repository:

```text
/Users/aidi/大字典/safe-agent-skills
```

Do not maintain it from the old nested OneCode path:

```text
/Users/aidi/大字典/one code/onecode-skill-sanitizer
```

That nested copy has been removed to avoid polluting the OneCode core project.
Before any maintenance work, run:

```bash
cd "/Users/aidi/大字典/safe-agent-skills"
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

- total skills: 105
- trusted skills: 100
- quarantined skills: 3
- review-required skills: 2
- categories meeting 3 trusted skills: 15 / 15
- scenario bundles: 9
- phase status: Phase 002 scenario router closed for today's delivery

Closure report:

- [Phase 001 Closure Report](phase-001-closure-report.md)
- [Phase 002 Scenario Router Closure Report](phase-002-scenario-router-closure-report.md)

Latest update:

- [Document Evidence Guardrails](updates/2026-06-05-document-evidence-guardrails.md)

## Intake Rule

Do not execute third-party skills during intake.

New community entries should be added as reference-style workflows unless the
license and reuse rights are clear. Runtime connectors require separate review.

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
  --bundles bundles/index.json
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
bash scripts/verify.sh
```

Confirm:

- `status: ok`
- `unknown_provenance_count: 0`
- `tampered_count: 0`
- each category has at least 3 trusted skills
- task-pack output contains only trusted skills unless review mode is explicitly
  requested
- every bundle in `bundles/index.json` references existing trusted skills
- `maintain-check` reports `status: ok`
- `schema-check` reports `status: ok`
- scenario router website sample selects `website-build-launch`
- scenario router RAG sample selects `rag-agent-knowledge-app`
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
