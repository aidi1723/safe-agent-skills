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

- total skills: 72
- trusted skills: 67
- quarantined skills: 3
- review-required skills: 2
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
| ai | `ai-autogen-multi-agent-review`, `ai-crewai-role-workflow`, `ai-guidance-constrained-generation`, `ai-langchain-agent-orchestration`, `ai-litellm-gateway-cost-control`, `ai-llama-cpp-local-inference-boundary`, `ai-llamaindex-rag-knowledge-workflow`, `ai-openai-cookbook-api-patterns`, `ai-outlines-structured-generation`, `ai-output-schema-eval`, `ai-pydantic-schema-contract`, `ai-qwen-agent-tool-workflow`, `ai-vllm-serving-capacity-plan`, `ecc-agent-coding-safety`, `headroom-context-compression`, `hermes-agent-memory-assistant`, `supermemory-memory-engine-reference` |
| business | `business-process-sop`, `business-requirements-brief`, `business-support-triage` |
| code | `code-python-debug`, `code-review-risk`, `code-test-regression` |
| commerce | `commerce-icbu-listing`, `commerce-inquiry-reply`, `commerce-product-keyword-plan` |
| compliance | `compliance-accessibility-policy`, `compliance-privacy-check`, `compliance-terms-review`, `vibe-trading-research-assistant` |
| content | `content-editorial-review`, `content-prompt-engineering-patterns`, `content-seo-brief`, `content-social-post` |
| data | `data-haystack-rag-pipeline`, `data-marker-pdf-markdown-review`, `data-markitdown-file-to-markdown`, `data-qdrant-vector-retrieval`, `data-quality-audit`, `data-table-analysis`, `data-unstructured-document-partition`, `data-visualization-plan` |
| design | `design-accessibility-check`, `design-system-consistency`, `design-ui-review` |
| engineering | `engineering-build-release`, `engineering-ci-troubleshoot`, `engineering-performance-profile` |
| execution | `execution-browser-check`, `execution-browser-use-web-task`, `execution-e2b-sandbox-boundary`, `execution-file-batch`, `execution-mcp-tool-connector-review`, `execution-playwright-browser-automation`, `execution-publish-check` |
| media | `media-asset-review`, `media-brand-asset-pack`, `media-video-script-review` |
| office | `office-docx-brief`, `office-pdf-report`, `office-spreadsheet-cleanup` |
| research | `research-competitor-brief`, `research-paper-synthesis`, `research-source-check` |
| security | `security-guardrails-output-validation`, `security-llm-guard-io-scanning`, `security-prompt-injection-review`, `security-supply-chain-review`, `trivy-container-security-scan` |
| vertical | `vertical-education-plan`, `vertical-manufacturing-qc`, `vertical-real-estate-listing` |

## Trusted Coverage

| Category | Trusted skills | Count |
| --- | --- | ---: |
| ai | `ai-autogen-multi-agent-review`, `ai-crewai-role-workflow`, `ai-guidance-constrained-generation`, `ai-langchain-agent-orchestration`, `ai-llama-cpp-local-inference-boundary`, `ai-llamaindex-rag-knowledge-workflow`, `ai-openai-cookbook-api-patterns`, `ai-outlines-structured-generation`, `ai-output-schema-eval`, `ai-pydantic-schema-contract`, `ai-qwen-agent-tool-workflow`, `ai-vllm-serving-capacity-plan`, `ecc-agent-coding-safety`, `headroom-context-compression` | 14 |
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
| security | `security-guardrails-output-validation`, `security-llm-guard-io-scanning`, `security-prompt-injection-review`, `security-supply-chain-review`, `trivy-container-security-scan` | 5 |
| vertical | `vertical-education-plan`, `vertical-manufacturing-qc`, `vertical-real-estate-listing` | 3 |

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

Current quarantined reference skills are intentionally excluded from normal
selection until separate runtime, connector, and compliance review is complete:

- `hermes-agent-memory-assistant`
- `ai-litellm-gateway-cost-control`
- `execution-mcp-tool-connector-review`
- `supermemory-memory-engine-reference`
- `vibe-trading-research-assistant`
