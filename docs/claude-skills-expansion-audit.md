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
- converted skills: 14 local OneCode-authored skills across two batches

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

## Ranking Method

Candidates were scored by domain gap priority, keyword relevance, overlap with
the existing catalog, and whether the item was a real skill rather than a
router or platform mirror. The resulting candidate map is stored at
`docs/claude-skills-candidate-map.json`.

## Remaining High-Value Gaps

- commercial policy review
- partnerships and channel strategy review
- Jira and Atlassian administration review
- research operations beyond clinical study design

## Governance Notes

The converted skills use `local_authoring` provenance and are trusted only
after the OneCode import, approval, reindex, schema, maintain, and verification
checks. Upstream `claude-skills` remains an external reference, not a trusted
runtime dependency.
