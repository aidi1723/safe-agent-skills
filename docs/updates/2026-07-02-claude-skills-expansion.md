# Claude Skills Expansion

Date: 2026-07-02

This update evaluates the public `claude-skills` repository as a metadata-only
reference source and adds six locally authored OneCode-safe expansion batches.

## What Changed

- Added `docs/claude-skills-candidate-map.json` with 336 canonical, deduped,
  ranked upstream candidates.
- Added `docs/claude-skills-expansion-audit.md` summarizing ranking,
  conversion, and remaining gaps.
- Added `batch-016-claude-skills-expansion` with 6 locally authored skills.
- Added `batch-017-claude-skills-depth` with 8 locally authored skills.
- Added `batch-018-claude-skills-ops` with 8 locally authored skills.
- Added `batch-019-claude-skills-research-comms` with 8 locally authored skills.
- Added `batch-020-claude-skills-overlap-depth` with 3 locally authored skills.
- Added `batch-021-claude-skills-bulk-draft` with 50 metadata-only local
  draft folders for bulk review. These drafts are not catalog entries and are
  not trusted.
- Added `batch-022-claude-skills-bulk-draft` through
  `batch-027-claude-skills-bulk-draft` with the remaining 253 metadata-only
  local draft folders from the ranked bulk review plan. The 7 bulk draft
  batches now cover all 303 actionable `reference_only` candidates.
- Added `claude-skills-bulk-assess` to rank the full draft pool before
  promotion. The current assessment identifies 15 candidates for merge review,
  283 to keep reference-only, and 38 already converted; no
  `author_local_skill` candidates remain after the authoring wave.
- Added `batch-028-claude-skills-authoring-wave` with 5 locally authored
  trusted skills from the bulk assessment shortlist.
- Imported and approved 38 new trusted catalog entries, including:
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
  `business-process-mapping-review`,
  `commerce-commercial-policy-review`,
  `commerce-partnerships-strategy-review`,
  `commerce-channel-economics-review`,
  `business-product-management-review`,
  `business-jira-workflow-review`,
  `business-confluence-knowledge-review`,
  `business-internal-comms-review`, and
  `business-capacity-planning-review`,
  `business-meeting-analysis-review`,
  `business-team-communications-review`,
  `business-contract-proposal-review`,
  `business-sales-engineering-review`,
  `research-market-analysis-review`,
  `research-product-analysis-review`,
  `research-finance-analysis-review`, and
  `business-investment-memo-review`,
  `business-atlassian-admin-governance-review`,
  `business-atlassian-template-governance-review`, and
  `content-marketing-pricing-strategy-review`,
  `commerce-commercial-operations-review`,
  `business-finance-operations-review`,
  `business-growth-operations-review`,
  `business-project-management-operations-review`, and
  `research-operations-governance-review`.

## Boundary

Upstream `claude-skills` material remains reference-only. The catalog does not
copy, install, execute, or trust upstream skill bodies. Converted skills are
local OneCode-authored guidance with provenance, static scan reports, sealed
hashes, schema validation, and trusted approval.
