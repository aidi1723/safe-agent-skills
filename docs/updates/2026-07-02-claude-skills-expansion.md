# Claude Skills Expansion

Date: 2026-07-02

This update evaluates the public `claude-skills` repository as a metadata-only
reference source and adds two locally authored OneCode-safe expansion batches.

## What Changed

- Added `docs/claude-skills-candidate-map.json` with 336 canonical, deduped,
  ranked upstream candidates.
- Added `docs/claude-skills-expansion-audit.md` summarizing ranking,
  conversion, and remaining gaps.
- Added `batch-016-claude-skills-expansion` with 6 locally authored skills.
- Added `batch-017-claude-skills-depth` with 8 locally authored skills.
- Imported and approved 14 new trusted catalog entries, including:
  `business-saas-metrics-review`,
  `commerce-rfp-response-review`,
  `business-procurement-optimization-review`,
  `commerce-pricing-strategy-review`,
  `business-customer-success-health-review`,
  `research-clinical-study-design-review`,
  `business-vendor-management-review`,
  `commerce-commercial-forecast-review`,
  `business-revenue-operations-review`,
  `commerce-deal-desk-review`,
  `business-financial-analysis-review`,
  `business-scrum-project-review`,
  `business-knowledge-operations-review`, and
  `business-process-mapping-review`.

## Boundary

Upstream `claude-skills` material remains reference-only. The catalog does not
copy, install, execute, or trust upstream skill bodies. Converted skills are
local OneCode-authored guidance with provenance, static scan reports, sealed
hashes, schema validation, and trusted approval.
