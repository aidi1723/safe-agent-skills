# OneCode Safe Skill Catalog

This catalog contains sanitized, provenance-recorded skills that passed the
local OneCode Skill Sanitizer workflow.

Every published catalog entry has passed OneCode safety validation and
cleaning: provenance recording, static risk scan, unsafe-instruction cleanup,
status review, sanitized hash recording, and registry integrity verification.
Normal selection is limited to `trusted` skills by default, so this catalog is
safer and more reliable than copying unverified prompts or agent instructions
directly from the open internet.

## Current Catalog Status

- total skills: 152
- trusted skills: 146
- quarantined skills: 3
- review-required skills: 3
- tampered skills: 0
- unknown provenance records: 0
- registry verification: `ok`
- top-level category coverage: 15 / 15
- minimum trusted coverage: 3 trusted skills per top-level category

## Category Coverage

Detailed category coverage and one-line capability descriptions live in:

- [Catalog Status](../docs/catalog-status.md)
- [Skill Index](../docs/skill-index.md)

## Trust Rule

Only skills with `status: trusted` are intended for normal task selection.
`trusted` means the skill passed the current OneCode safety validation and
cleaning process. It does not grant unrestricted runtime permissions;
connector, filesystem, network, and production actions remain controlled by the
host runtime policy.

Before runtime use, verify:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry catalog
```

## Provenance Rule

Every catalog entry records:

- source URL
- source path
- author
- license
- reference document
- collector identity
- capture timestamp
- source hash
- sanitized hash

## Publication Notes

The seed batches are OneCode Project original content under Apache-2.0.
Community hot-project entries are reference-style rewrites with explicit source
records and licenses. They credit the original projects but do not copy their
runtime code or prompt bodies.

Current non-trusted reference skills are intentionally excluded from normal
selection until separate runtime, connector, and compliance review is complete:

- `hermes-agent-memory-assistant`
- `ai-litellm-gateway-cost-control`
- `execution-mcp-tool-connector-review`
- `research-recent-social-signal-brief`
- `supermemory-memory-engine-reference`
- `vibe-trading-research-assistant`
