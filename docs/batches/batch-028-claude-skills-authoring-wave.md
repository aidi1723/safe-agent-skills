# Batch 028 Claude Skills Authoring Wave

This batch promotes the `claude-skills-bulk-assess` local-authoring shortlist
into five locally authored OneCode-safe skills. It does not copy, install,
execute, or trust upstream `claude-skills` bodies.

## Scope

- source candidate map: `docs/claude-skills-candidate-map.json`
- upstream relationship: metadata-only inspiration from `claude-skills`
- assessment source: `claude-skills-bulk-assess`
- batch directory: `batches/batch-028-claude-skills-authoring-wave`
- local skill count: 5

## Converted Skills

| Upstream Candidate | Local Skill | Category |
| --- | --- | --- |
| `commercial-skills` | `commerce-commercial-operations-review` | commerce |
| `finance-skills` | `business-finance-operations-review` | business |
| `business-growth-skills` | `business-growth-operations-review` | business |
| `pm-skills` | `business-project-management-operations-review` | business |
| `research-ops-skills` | `research-operations-governance-review` | research |

## Governance Notes

- source usage: `local_authoring`
- status after import and serial approval: `trusted`
- runtime boundary: method-only guidance; no connector, account, production,
  network, or filesystem permission grant
- trust boundary: upstream remains metadata-only reference; catalog trust comes
  from local authorship, import, serial approval, schema-check, maintain-check,
  and verify
