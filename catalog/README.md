# OneCode Safe Skill Catalog

This catalog contains sanitized, provenance-recorded skills that passed the
local OneCode Skill Sanitizer workflow.

## Current Catalog Status

- total skills: 48
- trusted skills: 45
- quarantined skills: 3
- tampered skills: 0
- unknown provenance records: 0
- registry verification: `ok`
- top-level category coverage: 15 / 15
- minimum trusted coverage: 3 trusted skills per top-level category

## Category Coverage

For one-line capability descriptions, see
[Skill Index](../docs/skill-index.md).

| Category | Skill |
| --- | --- |
| ai | `ai-output-schema-eval`, `ecc-agent-coding-safety`, `headroom-context-compression`, `hermes-agent-memory-assistant`, `supermemory-memory-engine-reference` |
| business | `business-process-sop`, `business-requirements-brief`, `business-support-triage` |
| code | `code-python-debug`, `code-review-risk`, `code-test-regression` |
| commerce | `commerce-icbu-listing`, `commerce-inquiry-reply`, `commerce-product-keyword-plan` |
| compliance | `compliance-accessibility-policy`, `compliance-privacy-check`, `compliance-terms-review`, `vibe-trading-research-assistant` |
| content | `content-editorial-review`, `content-seo-brief`, `content-social-post` |
| data | `data-quality-audit`, `data-table-analysis`, `data-visualization-plan` |
| design | `design-accessibility-check`, `design-system-consistency`, `design-ui-review` |
| engineering | `engineering-build-release`, `engineering-ci-troubleshoot`, `engineering-performance-profile` |
| execution | `execution-browser-check`, `execution-file-batch`, `execution-publish-check` |
| media | `media-asset-review`, `media-brand-asset-pack`, `media-video-script-review` |
| office | `office-docx-brief`, `office-pdf-report`, `office-spreadsheet-cleanup` |
| research | `research-competitor-brief`, `research-paper-synthesis`, `research-source-check` |
| security | `security-prompt-injection-review`, `security-supply-chain-review`, `trivy-container-security-scan` |
| vertical | `vertical-education-plan`, `vertical-manufacturing-qc`, `vertical-real-estate-listing` |

## Trusted Coverage

| Category | Trusted skills | Count |
| --- | --- | ---: |
| ai | `ai-output-schema-eval`, `ecc-agent-coding-safety`, `headroom-context-compression` | 3 |
| business | `business-process-sop`, `business-requirements-brief`, `business-support-triage` | 3 |
| code | `code-python-debug`, `code-review-risk`, `code-test-regression` | 3 |
| commerce | `commerce-icbu-listing`, `commerce-inquiry-reply`, `commerce-product-keyword-plan` | 3 |
| compliance | `compliance-accessibility-policy`, `compliance-privacy-check`, `compliance-terms-review` | 3 |
| content | `content-editorial-review`, `content-seo-brief`, `content-social-post` | 3 |
| data | `data-quality-audit`, `data-table-analysis`, `data-visualization-plan` | 3 |
| design | `design-accessibility-check`, `design-system-consistency`, `design-ui-review` | 3 |
| engineering | `engineering-build-release`, `engineering-ci-troubleshoot`, `engineering-performance-profile` | 3 |
| execution | `execution-browser-check`, `execution-file-batch`, `execution-publish-check` | 3 |
| media | `media-asset-review`, `media-brand-asset-pack`, `media-video-script-review` | 3 |
| office | `office-docx-brief`, `office-pdf-report`, `office-spreadsheet-cleanup` | 3 |
| research | `research-competitor-brief`, `research-paper-synthesis`, `research-source-check` | 3 |
| security | `security-prompt-injection-review`, `security-supply-chain-review`, `trivy-container-security-scan` | 3 |
| vertical | `vertical-education-plan`, `vertical-manufacturing-qc`, `vertical-real-estate-listing` | 3 |

## Trust Rule

Only skills with `status: trusted` are intended for normal task selection.

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

Current quarantined reference skills are intentionally excluded from normal
selection until separate runtime, connector, and compliance review is complete:

- `hermes-agent-memory-assistant`
- `supermemory-memory-engine-reference`
- `vibe-trading-research-assistant`
