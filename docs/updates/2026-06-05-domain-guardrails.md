# Update Statement: Domain Guardrail Skills

Date: 2026-06-05

Repository:

```text
https://github.com/aidi1723/safe-agent-skills
```

## Summary

This update adds `batch-009-domain-guardrails`, a local seed batch focused on
deterministic review workflows outside core coding tasks.

The new skills cover design responsiveness, content claim risk, content
contradiction review, Markdown structure linting, and numeric table
calculation checks.

## What Changed

- Added `design-responsive-viewport-check`.
- Added `content-claims-compliance-filter`.
- Added `content-fact-contradiction-review`.
- Added `office-markdown-structure-lint`.
- Added `data-table-calculation-verify`.
- Imported and approved the five entries as trusted local seed skills.
- Updated catalog status, skill index, public baseline docs, and schema-check
  baseline.

## Source Boundary

The batch uses local OneCode-authored source records.

The community Sill lists that motivated these themes contained unverified
repository names and Star counts, so those names were not used as source
provenance. This keeps the catalog aligned with its provenance and hash
verification rules.

## Verification Evidence

Release gate:

```bash
bash scripts/verify.sh
PYTHONPATH=src python3 -m onecode_skill_sanitizer schema-check --registry catalog
PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check --registry catalog --bundles bundles/index.json
```

Expected baseline:

```text
skill_count: 80
trusted_count: 75
quarantined skills: 3
review_required skills: 2
trusted_bundle_count: 9
tampered_count: 0
unknown_provenance_count: 0
```

## Files Added

- `batches/batch-009-domain-guardrails/`
- `catalog/content/content-claims-compliance-filter/`
- `catalog/content/content-fact-contradiction-review/`
- `catalog/data/data-table-calculation-verify/`
- `catalog/design/design-responsive-viewport-check/`
- `catalog/office/office-markdown-structure-lint/`
- `docs/batches/batch-009-domain-guardrails.md`
