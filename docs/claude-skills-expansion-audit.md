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
- converted skills: 33 local OneCode-authored skills across five batches

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

  The current map produces 303 actionable `reference_only` items across 7
  large review batches when using `--batch-size 50`.

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
- `batch-021-claude-skills-bulk-draft` materializes the first 50-item bulk
  review wave as local draft folders. Catalog counts and trusted counts are
  unchanged by this draft batch.
- Connector-aware skills should wait for host adapter verification.

## Governance Notes

The converted skills use `local_authoring` provenance and are trusted only
after the OneCode import, approval, reindex, schema, maintain, and verification
checks. Upstream `claude-skills` remains an external reference, not a trusted
runtime dependency.
