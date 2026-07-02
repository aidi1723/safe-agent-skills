# Claude Skills Expansion Audit

Date: 2026-07-02

## Scope

The audit reviewed the public `claude-skills` repository as a metadata-only
reference. Upstream skills were not installed, executed, copied into the
catalog, or marked trusted.

## Evaluation Result

- raw `SKILL.md` files observed: 772
- canonical deduped candidates: 336
- priority distribution: P0 27, P1 12, P2 19, P3 278
- converted or covered upstream candidates: 53
- distinct local OneCode-authored catalog skills from this expansion: 38 across
  six batches

Top source domains by canonical candidates:

| Source Domain | Candidates |
| --- | ---: |
| engineering | 74 |
| c-level-advisor | 62 |
| engineering-team | 49 |
| marketing-skill | 48 |
| product-team | 17 |
| ra-qm-team | 17 |
| project-management | 9 |
| research | 9 |
| compliance-os | 9 |
| commercial | 8 |
| business-operations | 7 |

## Converted Skills

| Upstream Candidate | Local Skill | Category |
| --- | --- | --- |
| `saas-metrics-coach` | `business-saas-metrics-review` | business |
| `rfp-responder` | `commerce-rfp-response-review` | commerce |
| `procurement-optimizer` | `business-procurement-optimization-review` | business |
| `pricing-strategist` | `commerce-pricing-strategy-review` | commerce |
| `customer-success-manager` | `business-customer-success-health-review` | business |
| `clinical-research` | `research-clinical-study-design-review` | research |
| `vendor-management` | `business-vendor-management-review` | business |
| `commercial-forecaster` | `commerce-commercial-forecast-review` | commerce |
| `revenue-operations` | `business-revenue-operations-review` | business |
| `deal-desk` | `commerce-deal-desk-review` | commerce |
| `financial-analyst` | `business-financial-analysis-review` | business |
| `scrum-master` | `business-scrum-project-review` | business |
| `knowledge-ops` | `business-knowledge-operations-review` | business |
| `process-mapper` | `business-process-mapping-review` | business |
| `commercial-policy` | `commerce-commercial-policy-review` | commerce |
| `partnerships-architect` | `commerce-partnerships-strategy-review` | commerce |
| `channel-economics` | `commerce-channel-economics-review` | commerce |
| `senior-pm` | `business-product-management-review` | business |
| `jira-expert` | `business-jira-workflow-review` | business |
| `confluence-expert` | `business-confluence-knowledge-review` | business |
| `internal-comms` | `business-internal-comms-review` | business |
| `capacity-planner` | `business-capacity-planning-review` | business |
| `meeting-analyzer` | `business-meeting-analysis-review` | business |
| `team-communications` | `business-team-communications-review` | business |
| `contract-and-proposal-writer` | `business-contract-proposal-review` | business |
| `sales-engineer` | `business-sales-engineering-review` | business |
| `market-research` | `research-market-analysis-review` | research |
| `product-research` | `research-product-analysis-review` | research |
| `research-finance` | `research-finance-analysis-review` | research |
| `business-investment-advisor` | `business-investment-memo-review` | business |
| `atlassian-admin` | `business-atlassian-admin-governance-review` | business |
| `atlassian-templates` | `business-atlassian-template-governance-review` | business |
| `pricing-strategy` | `content-marketing-pricing-strategy-review` | content |
| `commercial-skills` | `commerce-commercial-operations-review` | commerce |
| `finance-skills` | `business-finance-operations-review` | business |
| `business-growth-skills` | `business-growth-operations-review` | business |
| `pm-skills` | `business-project-management-operations-review` | business |
| `research-ops-skills` | `research-operations-governance-review` | research |
| `business-operations-skills` | `business-finance-operations-review` | business |
| `landing-page-generator` | `design-premium-landing-page` | design |
| `marketing-strategy-pmm` | `content-marketing-pricing-strategy-review` | content |
| `review` | `code-review-risk` | code |
| `ui-design-system` | `design-system-consistency` | design |
| `content-strategy` | `content-strategy-matrix` | content |
| `social-content` | `content-social-post` | content |
| `eval` | `ai-output-schema-eval` | ai |
| `report` | `office-pdf-report` | office |
| `research` | `research-citation-evidence-map` | research |
| `browser-automation` | `execution-playwright-browser-automation` | execution |
| `data-quality-auditor` | `data-quality-audit` | data |
| `design-system` | `design-system-consistency` | design |
| `landing` | `design-premium-landing-page` | design |
| `brief` | `business-requirements-brief` | business |

## Ranking Method

Candidates were scored by domain gap priority, keyword relevance, overlap with
the existing catalog, and whether the item was a real skill rather than a
router or platform mirror. The resulting candidate map is stored at
`docs/claude-skills-candidate-map.json`.

## Remaining Expansion Direction

- No ranked `candidate` entries remain in the current candidate map.
- Future waves should mine `reference_only` clusters for deeper engineering,
  product, marketing, compliance, and RA/QM domain depth.
- Use the bulk planner instead of manual small waves:

  ```bash
  onecode-skill-sanitizer claude-skills-bulk-plan \
    --candidate-map docs/claude-skills-candidate-map.json \
    --batch-size 50
  ```

  The current map produces 283 actionable `reference_only` items across 6
  large review batches when using `--batch-size 50`. The existing historical
  draft pool still contains 303 metadata-only folders from the earlier bulk
  materialization pass.

- To materialize one large review wave as local draft folders, use:

  ```bash
  onecode-skill-sanitizer claude-skills-bulk-draft \
    --candidate-map docs/claude-skills-candidate-map.json \
    --out batches/batch-XXX-claude-skills-bulk-draft \
    --batch-size 50 \
    --batch-index 1
  ```

  Drafts are not catalog entries and are not trusted. They must be edited,
  imported, approved serially, and verified before any catalog inclusion.
- `batch-021-claude-skills-bulk-draft` through
  `batch-027-claude-skills-bulk-draft` materialized the original 303
  metadata-only review inputs as local draft folders. After the coverage pass,
  53 candidates are converted or covered by trusted local skills and 283 remain
  reference-only. Catalog counts and trusted counts are unchanged by these
  draft batches.
- The bulk draft pool now contains 303 draft skill folders and 606 draft files
  across 7 batches. These are review inputs, not trusted runtime skills.
- Use `claude-skills-bulk-assess` after draft generation to rank promotion
  work before any import or approval:

  ```bash
  onecode-skill-sanitizer claude-skills-bulk-assess \
    --candidate-map docs/claude-skills-candidate-map.json \
    --draft-root batches \
    --registry catalog
  ```

  Current assessment after the coverage pass: 283 `keep_reference_only` and
  53 `already_converted`. The command only reviews metadata-only drafts; it
  does not approve or trust them.
- Connector-aware skills should wait for host adapter verification.

## Governance Notes

Distinct converted catalog skills use `local_authoring` provenance and are
trusted only after the OneCode import, approval, reindex, schema, maintain, and
verification checks. Coverage-only mappings reuse existing trusted catalog
skills and do not add duplicate runtime skills. Upstream `claude-skills`
remains an external reference, not a trusted runtime dependency.
