# Batch 018 Claude Skills Ops

This batch continues the local OneCode-authored expansion from the
metadata-only `claude-skills` audit. It does not copy, install, execute, or
trust upstream skill bodies.

## Included Skills

- `commerce-commercial-policy-review`
- `commerce-partnerships-strategy-review`
- `commerce-channel-economics-review`
- `business-product-management-review`
- `business-jira-workflow-review`
- `business-confluence-knowledge-review`
- `business-internal-comms-review`
- `business-capacity-planning-review`

## Governance Notes

- source usage: `local_authoring`
- external relationship: metadata-only inspiration from the ranked candidate
  audit
- runtime boundary: skills provide method guidance only
- trust boundary: catalog entries are trusted only after local scan, manifest
  hash sealing, schema validation, and maintain checks
