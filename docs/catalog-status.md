# Catalog Status

## Summary

The current public-safe catalog contains 95 sanitized skills across all
top-level taxonomy categories, including 33 community project reference skills
and 20 local guardrail, governance, safety operations, and code quality seed skills.

Verification command:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry catalog
PYTHONPATH=src python3 -m onecode_skill_sanitizer schema-check --registry catalog
PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check --registry catalog --bundles bundles/index.json
```

Latest verified result:

```text
status: ok
skill_count: 95
trusted_count: 90
tampered_count: 0
unknown_provenance_count: 0
schema-check: ok
maintain-check: ok
```

Every top-level category now has at least 3 trusted skills.

Latest update statement:

- [Code Quality Guardrails](updates/2026-06-05-code-quality-guardrails.md)
- [Safety Operations Guardrails](updates/2026-06-05-safety-operations-guardrails.md)
- [Domain Governance Extensions](updates/2026-06-05-domain-governance-extensions.md)
- [Domain Guardrail Skills](updates/2026-06-05-domain-guardrails.md)
- [Verification Hardening](updates/2026-06-05-verification-hardening.md)
- [Single-Entry Router Skill](updates/2026-06-05-router-skill-single-entry.md)
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
| `batch-009-domain-guardrails` | 5 | 5 | Domain guardrails for responsive UI, claims, contradictions, Markdown structure, and table calculations |
| `batch-010-domain-governance-extensions` | 5 | 5 | Domain governance extensions for brand voice, tracking links, source lineage, learning refresh, and rule synthesis |
| `batch-011-safety-operations-guardrails` | 5 | 5 | Safety operations guardrails for command risk, context redaction, licensing, rollback, and AI budgets |
| `batch-012-code-quality-guardrails` | 5 | 5 | Code quality guardrails for AST refactors, dependency cycles, dead paths, schema contracts, and log triage |

## Trusted Category Coverage

| Category | Trusted skills | Count |
| --- | --- | ---: |
| ai | `ai-autogen-multi-agent-review`, `ai-crewai-role-workflow`, `ai-guidance-constrained-generation`, `ai-langchain-agent-orchestration`, `ai-llama-cpp-local-inference-boundary`, `ai-llamaindex-rag-knowledge-workflow`, `ai-openai-cookbook-api-patterns`, `ai-opensquilla-metaskill-workflow`, `ai-opensquilla-token-routing-pattern`, `ai-outlines-structured-generation`, `ai-output-schema-eval`, `ai-pydantic-schema-contract`, `ai-qwen-agent-tool-workflow`, `ai-rule-failure-log-synthesis`, `ai-token-rate-budget-guard`, `ai-vllm-serving-capacity-plan`, `ecc-agent-coding-safety`, `headroom-context-compression` | 18 |
| business | `business-process-sop`, `business-requirements-brief`, `business-support-triage` | 3 |
| code | `code-ast-refactor-safety`, `code-dead-path-cleanup-review`, `code-dependency-cycle-review`, `code-python-debug`, `code-review-risk`, `code-test-regression` | 6 |
| commerce | `commerce-icbu-listing`, `commerce-inquiry-reply`, `commerce-link-tracking-audit`, `commerce-product-keyword-plan` | 4 |
| compliance | `compliance-accessibility-policy`, `compliance-license-policy-gate`, `compliance-privacy-check`, `compliance-terms-review` | 4 |
| content | `content-brand-voice-boundary`, `content-claims-compliance-filter`, `content-editorial-review`, `content-fact-contradiction-review`, `content-prompt-engineering-patterns`, `content-seo-brief`, `content-social-post` | 7 |
| data | `data-haystack-rag-pipeline`, `data-marker-pdf-markdown-review`, `data-markitdown-file-to-markdown`, `data-qdrant-vector-retrieval`, `data-quality-audit`, `data-schema-field-contract-check`, `data-table-analysis`, `data-table-calculation-verify`, `data-unstructured-document-partition`, `data-visualization-plan` | 10 |
| design | `design-accessibility-check`, `design-responsive-viewport-check`, `design-system-consistency`, `design-ui-review` | 4 |
| engineering | `engineering-build-release`, `engineering-ci-troubleshoot`, `engineering-error-log-noise-triage`, `engineering-performance-profile` | 4 |
| execution | `execution-browser-check`, `execution-browser-use-web-task`, `execution-e2b-sandbox-boundary`, `execution-file-batch`, `execution-playwright-browser-automation`, `execution-publish-check`, `execution-rollback-checkpoint-plan` | 7 |
| media | `media-asset-review`, `media-brand-asset-pack`, `media-video-script-review` | 3 |
| office | `office-docx-brief`, `office-markdown-structure-lint`, `office-pdf-report`, `office-spreadsheet-cleanup` | 4 |
| research | `research-competitor-brief`, `research-paper-synthesis`, `research-source-check`, `research-source-lineage-trace` | 4 |
| security | `security-command-risk-preflight`, `security-guardrails-output-validation`, `security-llm-guard-io-scanning`, `security-opensquilla-sandbox-policy`, `security-prompt-injection-review`, `security-secret-context-redaction`, `security-supply-chain-review`, `trivy-container-security-scan` | 8 |
| vertical | `vertical-education-plan`, `vertical-learning-memory-refresh`, `vertical-manufacturing-qc`, `vertical-real-estate-listing` | 4 |

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
| `ai-rule-failure-log-synthesis` | ai | trusted |
| `ai-token-rate-budget-guard` | ai | trusted |
| `ai-vllm-serving-capacity-plan` | ai | trusted |
| `business-process-sop` | business | trusted |
| `business-requirements-brief` | business | trusted |
| `business-support-triage` | business | trusted |
| `code-ast-refactor-safety` | code | trusted |
| `code-dead-path-cleanup-review` | code | trusted |
| `code-dependency-cycle-review` | code | trusted |
| `code-python-debug` | code | trusted |
| `code-review-risk` | code | trusted |
| `code-test-regression` | code | trusted |
| `commerce-icbu-listing` | commerce | trusted |
| `commerce-inquiry-reply` | commerce | trusted |
| `commerce-link-tracking-audit` | commerce | trusted |
| `commerce-product-keyword-plan` | commerce | trusted |
| `compliance-accessibility-policy` | compliance | trusted |
| `compliance-license-policy-gate` | compliance | trusted |
| `compliance-privacy-check` | compliance | trusted |
| `compliance-terms-review` | compliance | trusted |
| `content-brand-voice-boundary` | content | trusted |
| `content-claims-compliance-filter` | content | trusted |
| `content-editorial-review` | content | trusted |
| `content-fact-contradiction-review` | content | trusted |
| `content-prompt-engineering-patterns` | content | trusted |
| `content-seo-brief` | content | trusted |
| `content-social-post` | content | trusted |
| `data-haystack-rag-pipeline` | data | trusted |
| `data-marker-pdf-markdown-review` | data | trusted |
| `data-markitdown-file-to-markdown` | data | trusted |
| `data-qdrant-vector-retrieval` | data | trusted |
| `data-quality-audit` | data | trusted |
| `data-schema-field-contract-check` | data | trusted |
| `data-table-analysis` | data | trusted |
| `data-table-calculation-verify` | data | trusted |
| `data-unstructured-document-partition` | data | trusted |
| `data-visualization-plan` | data | trusted |
| `design-accessibility-check` | design | trusted |
| `design-responsive-viewport-check` | design | trusted |
| `design-system-consistency` | design | trusted |
| `design-ui-review` | design | trusted |
| `ecc-agent-coding-safety` | ai | trusted |
| `engineering-build-release` | engineering | trusted |
| `engineering-ci-troubleshoot` | engineering | trusted |
| `engineering-error-log-noise-triage` | engineering | trusted |
| `engineering-performance-profile` | engineering | trusted |
| `execution-browser-check` | execution | trusted |
| `execution-browser-use-web-task` | execution | trusted |
| `execution-e2b-sandbox-boundary` | execution | trusted |
| `execution-file-batch` | execution | trusted |
| `execution-mcp-tool-connector-review` | execution | review_required |
| `execution-playwright-browser-automation` | execution | trusted |
| `execution-publish-check` | execution | trusted |
| `execution-rollback-checkpoint-plan` | execution | trusted |
| `headroom-context-compression` | ai | trusted |
| `hermes-agent-memory-assistant` | ai | quarantined |
| `media-asset-review` | media | trusted |
| `media-brand-asset-pack` | media | trusted |
| `media-video-script-review` | media | trusted |
| `office-docx-brief` | office | trusted |
| `office-markdown-structure-lint` | office | trusted |
| `office-pdf-report` | office | trusted |
| `office-spreadsheet-cleanup` | office | trusted |
| `research-competitor-brief` | research | trusted |
| `research-paper-synthesis` | research | trusted |
| `research-source-check` | research | trusted |
| `research-source-lineage-trace` | research | trusted |
| `security-command-risk-preflight` | security | trusted |
| `security-guardrails-output-validation` | security | trusted |
| `security-llm-guard-io-scanning` | security | trusted |
| `security-opensquilla-sandbox-policy` | security | trusted |
| `security-prompt-injection-review` | security | trusted |
| `security-secret-context-redaction` | security | trusted |
| `security-supply-chain-review` | security | trusted |
| `supermemory-memory-engine-reference` | ai | quarantined |
| `trivy-container-security-scan` | security | trusted |
| `vertical-education-plan` | vertical | trusted |
| `vertical-learning-memory-refresh` | vertical | trusted |
| `vertical-manufacturing-qc` | vertical | trusted |
| `vertical-real-estate-listing` | vertical | trusted |
| `vibe-trading-research-assistant` | compliance | quarantined |

## Next Collection Waves

Recommended next waves:

- `batch-013-community-depth`: additional popular community skills with clear licenses
- `batch-014-domain-depth`: deeper skills for design, code, security, and office
- `batch-015-connectors`: connector-aware skills after host adapter verification
