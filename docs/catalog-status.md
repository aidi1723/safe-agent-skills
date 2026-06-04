# Catalog Status

## Summary

The current public-safe catalog contains 48 sanitized skills across all
top-level taxonomy categories, including 6 community hot-project reference
skills and 27 minimum-coverage seed skills.

Verification command:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry catalog
```

Latest verified result:

```text
status: ok
skill_count: 48
trusted_count: 45
tampered_count: 0
unknown_provenance_count: 0
```

Every top-level category now has at least 3 trusted skills.

## Completed Batches

| Batch | Skills | Trusted | Purpose |
| --- | ---: | ---: | --- |
| `batch-001-seed` | 6 | 6 | P0 operational baseline |
| `batch-002-p1-seed` | 5 | 5 | P1 research, data, content, commerce, AI |
| `batch-003-coverage-seed` | 4 | 4 | Remaining category coverage |
| `batch-004-community-hot` | 6 | 3 | Popular community project reference skills |
| `batch-005-minimum-three` | 27 | 27 | Minimum 3 trusted skills per top-level category |

## Trusted Category Coverage

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

## Current Skill List

| Skill | Category | Status |
| --- | --- | --- |
| `ai-output-schema-eval` | ai | trusted |
| `business-process-sop` | business | trusted |
| `business-requirements-brief` | business | trusted |
| `business-support-triage` | business | trusted |
| `code-python-debug` | code | trusted |
| `code-review-risk` | code | trusted |
| `code-test-regression` | code | trusted |
| `commerce-icbu-listing` | commerce | trusted |
| `commerce-inquiry-reply` | commerce | trusted |
| `commerce-product-keyword-plan` | commerce | trusted |
| `compliance-accessibility-policy` | compliance | trusted |
| `compliance-privacy-check` | compliance | trusted |
| `compliance-terms-review` | compliance | trusted |
| `content-editorial-review` | content | trusted |
| `content-seo-brief` | content | trusted |
| `content-social-post` | content | trusted |
| `data-quality-audit` | data | trusted |
| `data-table-analysis` | data | trusted |
| `data-visualization-plan` | data | trusted |
| `design-accessibility-check` | design | trusted |
| `design-system-consistency` | design | trusted |
| `design-ui-review` | design | trusted |
| `ecc-agent-coding-safety` | ai | trusted |
| `engineering-build-release` | engineering | trusted |
| `engineering-ci-troubleshoot` | engineering | trusted |
| `engineering-performance-profile` | engineering | trusted |
| `execution-browser-check` | execution | trusted |
| `execution-file-batch` | execution | trusted |
| `execution-publish-check` | execution | trusted |
| `headroom-context-compression` | ai | trusted |
| `hermes-agent-memory-assistant` | ai | quarantined |
| `media-asset-review` | media | trusted |
| `media-brand-asset-pack` | media | trusted |
| `media-video-script-review` | media | trusted |
| `office-docx-brief` | office | trusted |
| `office-pdf-report` | office | trusted |
| `office-spreadsheet-cleanup` | office | trusted |
| `research-competitor-brief` | research | trusted |
| `research-paper-synthesis` | research | trusted |
| `research-source-check` | research | trusted |
| `security-prompt-injection-review` | security | trusted |
| `security-supply-chain-review` | security | trusted |
| `supermemory-memory-engine-reference` | ai | quarantined |
| `trivy-container-security-scan` | security | trusted |
| `vertical-education-plan` | vertical | trusted |
| `vertical-manufacturing-qc` | vertical | trusted |
| `vertical-real-estate-listing` | vertical | trusted |
| `vibe-trading-research-assistant` | compliance | quarantined |

## Next Collection Waves

Recommended next waves:

- `batch-006-community-depth`: additional popular community skills with clear licenses
- `batch-007-domain-depth`: deeper skills for design, code, security, and office
- `batch-008-connectors`: connector-aware skills after host adapter verification
