# Catalog Status

## Summary

The current public-safe catalog contains 75 sanitized skills across all
top-level taxonomy categories, including 33 community project reference skills
and 27 minimum-coverage seed skills.

Verification command:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry catalog
```

Latest verified result:

```text
status: ok
skill_count: 75
trusted_count: 70
tampered_count: 0
unknown_provenance_count: 0
```

Every top-level category now has at least 3 trusted skills.

Latest update statement:

- [Scenario Skill Router](updates/2026-06-04-scenario-skill-router.md)
- [Bundle-Aware Task Packs and OpenSquilla Reference Batch](updates/2026-06-04-bundle-aware-task-pack-opensquilla.md)

Phase 001 closure:

- [Phase 001 Closure Report](phase-001-closure-report.md)

Phase 002 closure:

- [Phase 002 Scenario Router Closure Report](phase-002-scenario-router-closure-report.md)

Scenario router status:

```text
router mode: scenario
router type: deterministic
scenario bundles: 9 trusted
sample website route: website-build-launch
sample RAG route: rag-agent-knowledge-app
```

## Completed Batches

| Batch | Skills | Trusted | Purpose |
| --- | ---: | ---: | --- |
| `batch-001-seed` | 6 | 6 | P0 operational baseline |
| `batch-002-p1-seed` | 5 | 5 | P1 research, data, content, commerce, AI |
| `batch-003-coverage-seed` | 4 | 4 | Remaining category coverage |
| `batch-004-community-hot` | 6 | 3 | Popular community project reference skills |
| `batch-005-minimum-three` | 27 | 27 | Minimum 3 trusted skills per top-level category |
| `batch-006-community-infrastructure` | 12 | 11 | Community AI infrastructure reference skills |
| `batch-007-community-agent-workflows` | 12 | 11 | Community agent workflow, RAG, browser, sandbox, and retrieval reference skills |
| `batch-008-opensquilla-reference` | 3 | 3 | OpenSquilla-inspired MetaSkill, token routing, and sandbox policy reference skills |

## Trusted Category Coverage

| Category | Trusted skills | Count |
| --- | --- | ---: |
| ai | `ai-autogen-multi-agent-review`, `ai-crewai-role-workflow`, `ai-guidance-constrained-generation`, `ai-langchain-agent-orchestration`, `ai-llama-cpp-local-inference-boundary`, `ai-llamaindex-rag-knowledge-workflow`, `ai-openai-cookbook-api-patterns`, `ai-opensquilla-metaskill-workflow`, `ai-opensquilla-token-routing-pattern`, `ai-outlines-structured-generation`, `ai-output-schema-eval`, `ai-pydantic-schema-contract`, `ai-qwen-agent-tool-workflow`, `ai-vllm-serving-capacity-plan`, `ecc-agent-coding-safety`, `headroom-context-compression` | 16 |
| business | `business-process-sop`, `business-requirements-brief`, `business-support-triage` | 3 |
| code | `code-python-debug`, `code-review-risk`, `code-test-regression` | 3 |
| commerce | `commerce-icbu-listing`, `commerce-inquiry-reply`, `commerce-product-keyword-plan` | 3 |
| compliance | `compliance-accessibility-policy`, `compliance-privacy-check`, `compliance-terms-review` | 3 |
| content | `content-editorial-review`, `content-prompt-engineering-patterns`, `content-seo-brief`, `content-social-post` | 4 |
| data | `data-haystack-rag-pipeline`, `data-marker-pdf-markdown-review`, `data-markitdown-file-to-markdown`, `data-qdrant-vector-retrieval`, `data-quality-audit`, `data-table-analysis`, `data-unstructured-document-partition`, `data-visualization-plan` | 8 |
| design | `design-accessibility-check`, `design-system-consistency`, `design-ui-review` | 3 |
| engineering | `engineering-build-release`, `engineering-ci-troubleshoot`, `engineering-performance-profile` | 3 |
| execution | `execution-browser-check`, `execution-browser-use-web-task`, `execution-e2b-sandbox-boundary`, `execution-file-batch`, `execution-playwright-browser-automation`, `execution-publish-check` | 6 |
| media | `media-asset-review`, `media-brand-asset-pack`, `media-video-script-review` | 3 |
| office | `office-docx-brief`, `office-pdf-report`, `office-spreadsheet-cleanup` | 3 |
| research | `research-competitor-brief`, `research-paper-synthesis`, `research-source-check` | 3 |
| security | `security-guardrails-output-validation`, `security-llm-guard-io-scanning`, `security-opensquilla-sandbox-policy`, `security-prompt-injection-review`, `security-supply-chain-review`, `trivy-container-security-scan` | 6 |
| vertical | `vertical-education-plan`, `vertical-manufacturing-qc`, `vertical-real-estate-listing` | 3 |

## Current Skill List

| Skill | Category | Status |
| --- | --- | --- |
| `ai-autogen-multi-agent-review` | ai | trusted |
| `ai-crewai-role-workflow` | ai | trusted |
| `ai-guidance-constrained-generation` | ai | trusted |
| `ai-langchain-agent-orchestration` | ai | trusted |
| `ai-litellm-gateway-cost-control` | ai | review_required |
| `ai-llama-cpp-local-inference-boundary` | ai | trusted |
| `ai-llamaindex-rag-knowledge-workflow` | ai | trusted |
| `ai-openai-cookbook-api-patterns` | ai | trusted |
| `ai-opensquilla-metaskill-workflow` | ai | trusted |
| `ai-opensquilla-token-routing-pattern` | ai | trusted |
| `ai-outlines-structured-generation` | ai | trusted |
| `ai-output-schema-eval` | ai | trusted |
| `ai-pydantic-schema-contract` | ai | trusted |
| `ai-qwen-agent-tool-workflow` | ai | trusted |
| `ai-vllm-serving-capacity-plan` | ai | trusted |
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
| `content-prompt-engineering-patterns` | content | trusted |
| `content-seo-brief` | content | trusted |
| `content-social-post` | content | trusted |
| `data-haystack-rag-pipeline` | data | trusted |
| `data-marker-pdf-markdown-review` | data | trusted |
| `data-markitdown-file-to-markdown` | data | trusted |
| `data-qdrant-vector-retrieval` | data | trusted |
| `data-quality-audit` | data | trusted |
| `data-table-analysis` | data | trusted |
| `data-unstructured-document-partition` | data | trusted |
| `data-visualization-plan` | data | trusted |
| `design-accessibility-check` | design | trusted |
| `design-system-consistency` | design | trusted |
| `design-ui-review` | design | trusted |
| `ecc-agent-coding-safety` | ai | trusted |
| `engineering-build-release` | engineering | trusted |
| `engineering-ci-troubleshoot` | engineering | trusted |
| `engineering-performance-profile` | engineering | trusted |
| `execution-browser-check` | execution | trusted |
| `execution-browser-use-web-task` | execution | trusted |
| `execution-e2b-sandbox-boundary` | execution | trusted |
| `execution-file-batch` | execution | trusted |
| `execution-mcp-tool-connector-review` | execution | review_required |
| `execution-playwright-browser-automation` | execution | trusted |
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
| `security-guardrails-output-validation` | security | trusted |
| `security-llm-guard-io-scanning` | security | trusted |
| `security-opensquilla-sandbox-policy` | security | trusted |
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

- `batch-009-community-depth`: additional popular community skills with clear licenses
- `batch-010-domain-depth`: deeper skills for design, code, security, and office
- `batch-011-connectors`: connector-aware skills after host adapter verification
