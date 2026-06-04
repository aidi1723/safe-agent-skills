# Maintenance Guide

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

- total skills: 60
- trusted skills: 56
- quarantined skills: 3
- review-required skills: 1
- categories meeting 3 trusted skills: 15 / 15

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
