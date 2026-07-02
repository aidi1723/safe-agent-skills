# Batch 021 Claude Skills Bulk Draft

This batch materializes the first `claude-skills` bulk review wave as local
metadata-only draft folders. It does not copy, install, execute, or trust
upstream skill bodies.

## Scope

- source candidate map: `docs/claude-skills-candidate-map.json`
- bulk command: `claude-skills-bulk-draft`
- batch index: 1
- batch size: 50
- draft count: 50
- output directory: `batches/batch-021-claude-skills-bulk-draft`

## Governance Notes

- source usage: `local_authoring`
- draft status: `draft`
- external relationship: metadata-only inspiration from the ranked
  `claude-skills` candidate map
- runtime boundary: drafts provide review scaffolds only
- trust boundary: drafts are not catalog entries and are not trusted until
  locally edited, imported, approved serially, schema-checked,
  maintain-checked, and verified

## Next Step

Review the generated draft folders, merge duplicates into existing trusted
skills where appropriate, and only promote locally authored, non-duplicative
skills through the normal import and approval pipeline.
