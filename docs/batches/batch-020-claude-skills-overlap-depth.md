# Batch 020 Claude Skills Overlap Depth

This batch completes the remaining P0 candidate queue from the metadata-only
`claude-skills` audit. It does not copy, install, execute, or trust upstream
skill bodies.

## Included Skills

- `business-atlassian-admin-governance-review`
- `business-atlassian-template-governance-review`
- `content-marketing-pricing-strategy-review`

## Governance Notes

- source usage: `local_authoring`
- external relationship: metadata-only inspiration from the ranked candidate
  audit
- runtime boundary: skills provide method guidance only
- trust boundary: catalog entries are trusted only after local scan, manifest
  hash sealing, schema validation, and maintain checks
