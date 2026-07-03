# Catalog Status

## Summary

The current public-safe catalog contains 172 sanitized skills across all
top-level taxonomy categories, including 39 community project reference skills
and 133 local guardrail, governance, safety operations, code quality, AI runtime, document evidence, design, business, commerce, content, research, claude-skills backlog cluster, vertical industry orchestration, and agentic reference-pattern skills.
It also records 7 status-backed trusted-only overlap groups for router and
operator skill selection hints.

Verification command:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry catalog
PYTHONPATH=src python3 -m onecode_skill_sanitizer schema-check --registry catalog
PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check --registry catalog --bundles bundles/index.json
PYTHONPATH=src python3 -m onecode_skill_sanitizer reference-check --references external-references/index.json
```

Latest verified result:

```text
status: ok
skill_count: 172
trusted_count: 166
tampered_count: 0
unknown_provenance_count: 0
schema-check: ok
maintain-check: ok
reference-check: ok
external references: 19
overlap groups: 7
overlap group status: trusted
```

Every top-level category now has at least 3 trusted skills.

Latest update statement:

- [Router Eval Negative Constraints](updates/2026-07-03-router-eval-negative-constraints.md)
- [Lightweight General Fallback](updates/2026-07-03-lightweight-general-fallback.md)
- [Project Check Follow-Up](updates/2026-07-03-project-check-follow-up.md)
- [Reference Pattern Expansion](updates/2026-07-03-reference-pattern-expansion.md)
- [Industry Application Orchestration](updates/2026-07-03-industry-application-orchestration.md)
- [Agentic Reference Patterns](updates/2026-07-03-agentic-reference-patterns.md)
- [Project Closure Report](project-closure-report.md)
- [Maintenance Log](maintenance-log.md)
- [Feature Log](feature-log.md)
- [Claude Skills Backlog Cluster Coverage](updates/2026-07-03-claude-skills-backlog-cluster-coverage.md)
- [Smart Router And Claude Skills Closure](updates/2026-07-02-smart-router-claude-skills-closure.md)
- [Auto Orchestration Pipeline Plan](updates/2026-06-27-auto-orchestration-pipeline-plan.md)
- [Claude Skills Expansion](updates/2026-07-02-claude-skills-expansion.md)
- [Claude Skills Expansion Audit](claude-skills-expansion-audit.md)
- [Auto Orchestration Pipeline Plan Closure Report](auto-orchestration-pipeline-plan-closure-report.md)
- [Manifest Integrity and Contract Router Hardening](updates/2026-06-18-manifest-contract-router-hardening.md)
- [Scenario Capability Expansion Closure Report](scenario-capability-expansion-closure-report.md)
- [Scenario System Expansion](updates/2026-06-16-scenario-system-expansion.md)
- [Community Skill Reference Review](updates/2026-06-16-community-skill-reference-review.md)
- [Headroom Agent I/O Compression Closure Report](headroom-agent-io-compression-closure-report.md)
- [Headroom Agent I/O Compression Update](updates/2026-06-14-headroom-agent-io-compression.md)
- [CLAUDE.md Reference Closure Report](claude-md-reference-closure-report.md)
- [CLAUDE.md Reference Review](updates/2026-06-14-claude-md-reference.md)
- [Audit Hardening Closure Report](audit-hardening-closure-report.md)
- [Next Development Plan](next-development-plan.md)
- [Structural Scanner Hardening](updates/2026-06-12-structural-scanner-hardening.md)
- [Consistency Rule Hardening](updates/2026-06-12-consistency-rule-hardening.md)
- [Report Schema and Scanner Hardening](updates/2026-06-12-report-schema-scanner-hardening.md)
- [Provenance Usage Hardening](updates/2026-06-12-provenance-usage-hardening.md)
- [Scanner and Documentation Hardening](updates/2026-06-12-scanner-docs-hardening.md)
- [Design Skill Expansion](updates/2026-06-11-design-skill-expansion.md)
- [Smart Skill Router](updates/2026-06-06-smart-skill-router.md)
- [Recent Social Signal Reference](updates/2026-06-10-recent-social-signal-reference.md)
- [Skill Overlap Groups](skill-overlap-groups.md)
- [Document Evidence Guardrails](updates/2026-06-05-document-evidence-guardrails.md)
- [AI Runtime Guardrails](updates/2026-06-05-ai-runtime-guardrails.md)
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

Scenario capability expansion closure:

- [Scenario Capability Expansion Closure Report](scenario-capability-expansion-closure-report.md)

Scenario router status:

```text
router mode: scenario
router type: deterministic
scenario bundles: 23 trusted
sample website route: website-build-launch
sample RAG route: rag-agent-knowledge-app
sample skill-router route: skill-router-quality-review
smart router mode: deterministic_mesh_router
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
| `batch-013-ai-runtime-guardrails` | 5 | 5 | AI runtime guardrails for model routing, tool schemas, streamed JSON, RAG namespaces, and context compression |
| `batch-014-document-evidence-guardrails` | 5 | 5 | Document evidence guardrails for citation maps, link integrity, table source reconciliation, freshness, and public claims |
| `batch-015-scenario-capability-expansion` | 5 | 5 | Scenario capability expansion for visual review, codebase exploration, simplification, content strategy, and programmatic video boundaries |
| `batch-016-claude-skills-expansion` | 6 | 6 | Locally authored business, commerce, and clinical research skills from the metadata-only claude-skills audit |
| `batch-017-claude-skills-depth` | 8 | 8 | Second local claude-skills depth batch for vendor, forecast, RevOps, deal desk, finance, Scrum, knowledge ops, and process mapping |
| `batch-018-claude-skills-ops` | 8 | 8 | Third local claude-skills operations batch for commercial policy, partnerships, channel economics, product management, Jira, Confluence, internal communications, and capacity planning |
| `batch-019-claude-skills-research-comms` | 8 | 8 | Fourth local claude-skills research and communications batch for meeting analysis, team communications, contract proposals, sales engineering, market research, product research, research finance, and investment memo review |
| `batch-020-claude-skills-overlap-depth` | 3 | 3 | Fifth local claude-skills overlap-depth batch for Atlassian admin governance, Atlassian template governance, and marketing pricing strategy review |
| `batch-028-claude-skills-authoring-wave` | 5 | 5 | Local claude-skills authoring wave for commercial operations, finance operations, growth operations, project management operations, and research operations governance |
| `batch-029-claude-skills-backlog-clusters` | 9 | 9 | Local cluster coverage for the former claude-skills reference-only backlog |
| `batch-030-industry-application-orchestration` | 3 | 3 | Industry intake, regulated boundary review, and solution packaging for multi-vertical AI application plans |
| `batch-031-agentic-reference-patterns` | 3 | 3 | Agentic media production, long-term memory governance, and code graph intelligence reference patterns |
| `batch-032-reference-pattern-expansion` | 5 | 5 | Multi-platform research, investment diligence, agent role-library governance, DESIGN.md governance, and private communication boundaries |

## Trusted Category Coverage

| Category | Trusted skills | Count |
| --- | --- | ---: |
| ai | `ai-agent-role-library-governance`, `ai-autogen-multi-agent-review`, `ai-claude-skills-meta-workflow-review`, `ai-context-compression-budget-plan`, `ai-crewai-role-workflow`, `ai-graph-memory-contract`, `ai-guidance-constrained-generation`, `ai-langchain-agent-orchestration`, `ai-llama-cpp-local-inference-boundary`, `ai-llamaindex-rag-knowledge-workflow`, `ai-model-route-fallback-review`, `ai-openai-cookbook-api-patterns`, `ai-opensquilla-metaskill-workflow`, `ai-opensquilla-token-routing-pattern`, `ai-outlines-structured-generation`, `ai-output-schema-eval`, `ai-pydantic-schema-contract`, `ai-qwen-agent-tool-workflow`, `ai-rule-failure-log-synthesis`, `ai-stream-json-boundary-review`, `ai-token-rate-budget-guard`, `ai-tool-schema-protocol-check`, `ai-vllm-serving-capacity-plan`, `ecc-agent-coding-safety`, `headroom-context-compression` | 25 |
| business | `business-atlassian-admin-governance-review`, `business-atlassian-template-governance-review`, `business-capacity-planning-review`, `business-claude-skills-backlog-orchestration`, `business-confluence-knowledge-review`, `business-contract-proposal-review`, `business-customer-success-health-review`, `business-finance-operations-review`, `business-financial-analysis-review`, `business-growth-operations-review`, `business-internal-comms-review`, `business-investment-memo-review`, `business-jira-workflow-review`, `business-knowledge-operations-review`, `business-meeting-analysis-review`, `business-process-mapping-review`, `business-process-sop`, `business-procurement-optimization-review`, `business-product-management-review`, `business-project-management-operations-review`, `business-requirements-brief`, `business-revenue-operations-review`, `business-saas-metrics-review`, `business-sales-engineering-review`, `business-scrum-project-review`, `business-support-triage`, `business-team-communications-review`, `business-value-investment-research-framework`, `business-vendor-management-review` | 29 |
| code | `code-ast-refactor-safety`, `code-claude-skills-engineering-role-review`, `code-codebase-graph-index-boundary`, `code-dead-path-cleanup-review`, `code-dependency-cycle-review`, `code-python-debug`, `code-review-risk`, `code-simplify-refactor-plan`, `code-test-regression`, `codebase-explore-map` | 10 |
| commerce | `commerce-channel-economics-review`, `commerce-commercial-forecast-review`, `commerce-commercial-operations-review`, `commerce-commercial-policy-review`, `commerce-deal-desk-review`, `commerce-icbu-listing`, `commerce-inquiry-reply`, `commerce-link-tracking-audit`, `commerce-partnerships-strategy-review`, `commerce-pricing-strategy-review`, `commerce-product-keyword-plan`, `commerce-rfp-response-review` | 12 |
| compliance | `compliance-accessibility-policy`, `compliance-claude-skills-regulated-review`, `compliance-license-policy-gate`, `compliance-privacy-check`, `compliance-private-communication-boundary`, `compliance-public-claim-risk-register`, `compliance-regulated-industry-boundary`, `compliance-terms-review` | 8 |
| content | `content-brand-voice-boundary`, `content-claims-compliance-filter`, `content-claude-skills-growth-review`, `content-editorial-review`, `content-fact-contradiction-review`, `content-freshness-expiry-review`, `content-marketing-pricing-strategy-review`, `content-prompt-engineering-patterns`, `content-seo-brief`, `content-social-post`, `content-strategy-matrix` | 11 |
| data | `data-haystack-rag-pipeline`, `data-marker-pdf-markdown-review`, `data-markitdown-file-to-markdown`, `data-qdrant-vector-retrieval`, `data-quality-audit`, `data-rag-namespace-boundary-check`, `data-schema-field-contract-check`, `data-table-analysis`, `data-table-calculation-verify`, `data-unstructured-document-partition`, `data-visualization-plan` | 11 |
| design | `design-accessibility-check`, `design-design-md-system-contract`, `design-motion-interaction-polish`, `design-premium-landing-page`, `design-responsive-viewport-check`, `design-system-consistency`, `design-tailwind-radix-system`, `design-ui-review`, `design-visual-quality-review` | 9 |
| engineering | `engineering-build-release`, `engineering-ci-troubleshoot`, `engineering-claude-skills-operations-review`, `engineering-error-log-noise-triage`, `engineering-performance-profile` | 5 |
| execution | `execution-browser-check`, `execution-browser-use-web-task`, `execution-claude-skills-productivity-review`, `execution-e2b-sandbox-boundary`, `execution-file-batch`, `execution-playwright-browser-automation`, `execution-publish-check`, `execution-rollback-checkpoint-plan` | 8 |
| media | `media-agentic-video-pipeline-plan`, `media-asset-review`, `media-brand-asset-pack`, `media-remotion-video-production-boundary`, `media-video-script-review` | 5 |
| office | `office-claude-skills-document-review`, `office-docx-brief`, `office-link-reference-integrity`, `office-markdown-structure-lint`, `office-pdf-report`, `office-spreadsheet-cleanup`, `office-table-source-reconciliation` | 7 |
| research | `research-citation-evidence-map`, `research-claude-skills-evidence-review`, `research-clinical-study-design-review`, `research-competitor-brief`, `research-finance-analysis-review`, `research-market-analysis-review`, `research-multi-platform-search-boundary`, `research-operations-governance-review`, `research-paper-synthesis`, `research-product-analysis-review`, `research-source-check`, `research-source-lineage-trace` | 12 |
| security | `security-command-risk-preflight`, `security-guardrails-output-validation`, `security-llm-guard-io-scanning`, `security-opensquilla-sandbox-policy`, `security-prompt-injection-review`, `security-secret-context-redaction`, `security-supply-chain-review`, `trivy-container-security-scan` | 8 |
| vertical | `vertical-education-plan`, `vertical-industry-intake-orchestration`, `vertical-industry-solution-packaging`, `vertical-learning-memory-refresh`, `vertical-manufacturing-qc`, `vertical-real-estate-listing` | 6 |

## Current Skill List

| Skill | Category | Status |
| --- | --- | --- |
| `ai-agent-role-library-governance` | ai | trusted |
| `ai-autogen-multi-agent-review` | ai | trusted |
| `ai-claude-skills-meta-workflow-review` | ai | trusted |
| `ai-context-compression-budget-plan` | ai | trusted |
| `ai-crewai-role-workflow` | ai | trusted |
| `ai-graph-memory-contract` | ai | trusted |
| `ai-guidance-constrained-generation` | ai | trusted |
| `ai-langchain-agent-orchestration` | ai | trusted |
| `ai-litellm-gateway-cost-control` | ai | review_required |
| `ai-llama-cpp-local-inference-boundary` | ai | trusted |
| `ai-llamaindex-rag-knowledge-workflow` | ai | trusted |
| `ai-model-route-fallback-review` | ai | trusted |
| `ai-openai-cookbook-api-patterns` | ai | trusted |
| `ai-opensquilla-metaskill-workflow` | ai | trusted |
| `ai-opensquilla-token-routing-pattern` | ai | trusted |
| `ai-outlines-structured-generation` | ai | trusted |
| `ai-output-schema-eval` | ai | trusted |
| `ai-pydantic-schema-contract` | ai | trusted |
| `ai-qwen-agent-tool-workflow` | ai | trusted |
| `ai-rule-failure-log-synthesis` | ai | trusted |
| `ai-stream-json-boundary-review` | ai | trusted |
| `ai-token-rate-budget-guard` | ai | trusted |
| `ai-tool-schema-protocol-check` | ai | trusted |
| `ai-vllm-serving-capacity-plan` | ai | trusted |
| `ecc-agent-coding-safety` | ai | trusted |
| `headroom-context-compression` | ai | trusted |
| `hermes-agent-memory-assistant` | ai | quarantined |
| `supermemory-memory-engine-reference` | ai | quarantined |
| `business-atlassian-admin-governance-review` | business | trusted |
| `business-atlassian-template-governance-review` | business | trusted |
| `business-capacity-planning-review` | business | trusted |
| `business-claude-skills-backlog-orchestration` | business | trusted |
| `business-confluence-knowledge-review` | business | trusted |
| `business-contract-proposal-review` | business | trusted |
| `business-customer-success-health-review` | business | trusted |
| `business-finance-operations-review` | business | trusted |
| `business-financial-analysis-review` | business | trusted |
| `business-growth-operations-review` | business | trusted |
| `business-internal-comms-review` | business | trusted |
| `business-investment-memo-review` | business | trusted |
| `business-jira-workflow-review` | business | trusted |
| `business-knowledge-operations-review` | business | trusted |
| `business-meeting-analysis-review` | business | trusted |
| `business-process-mapping-review` | business | trusted |
| `business-process-sop` | business | trusted |
| `business-procurement-optimization-review` | business | trusted |
| `business-product-management-review` | business | trusted |
| `business-project-management-operations-review` | business | trusted |
| `business-requirements-brief` | business | trusted |
| `business-revenue-operations-review` | business | trusted |
| `business-saas-metrics-review` | business | trusted |
| `business-sales-engineering-review` | business | trusted |
| `business-scrum-project-review` | business | trusted |
| `business-support-triage` | business | trusted |
| `business-team-communications-review` | business | trusted |
| `business-value-investment-research-framework` | business | trusted |
| `business-vendor-management-review` | business | trusted |
| `code-ast-refactor-safety` | code | trusted |
| `code-claude-skills-engineering-role-review` | code | trusted |
| `code-codebase-graph-index-boundary` | code | trusted |
| `code-dead-path-cleanup-review` | code | trusted |
| `code-dependency-cycle-review` | code | trusted |
| `code-python-debug` | code | trusted |
| `code-review-risk` | code | trusted |
| `code-simplify-refactor-plan` | code | trusted |
| `code-test-regression` | code | trusted |
| `codebase-explore-map` | code | trusted |
| `commerce-channel-economics-review` | commerce | trusted |
| `commerce-commercial-forecast-review` | commerce | trusted |
| `commerce-commercial-operations-review` | commerce | trusted |
| `commerce-commercial-policy-review` | commerce | trusted |
| `commerce-deal-desk-review` | commerce | trusted |
| `commerce-icbu-listing` | commerce | trusted |
| `commerce-inquiry-reply` | commerce | trusted |
| `commerce-link-tracking-audit` | commerce | trusted |
| `commerce-partnerships-strategy-review` | commerce | trusted |
| `commerce-pricing-strategy-review` | commerce | trusted |
| `commerce-product-keyword-plan` | commerce | trusted |
| `commerce-rfp-response-review` | commerce | trusted |
| `compliance-accessibility-policy` | compliance | trusted |
| `compliance-claude-skills-regulated-review` | compliance | trusted |
| `compliance-license-policy-gate` | compliance | trusted |
| `compliance-privacy-check` | compliance | trusted |
| `compliance-private-communication-boundary` | compliance | trusted |
| `compliance-public-claim-risk-register` | compliance | trusted |
| `compliance-regulated-industry-boundary` | compliance | trusted |
| `compliance-terms-review` | compliance | trusted |
| `vibe-trading-research-assistant` | compliance | quarantined |
| `content-brand-voice-boundary` | content | trusted |
| `content-claims-compliance-filter` | content | trusted |
| `content-claude-skills-growth-review` | content | trusted |
| `content-editorial-review` | content | trusted |
| `content-fact-contradiction-review` | content | trusted |
| `content-freshness-expiry-review` | content | trusted |
| `content-marketing-pricing-strategy-review` | content | trusted |
| `content-prompt-engineering-patterns` | content | trusted |
| `content-seo-brief` | content | trusted |
| `content-social-post` | content | trusted |
| `content-strategy-matrix` | content | trusted |
| `data-haystack-rag-pipeline` | data | trusted |
| `data-marker-pdf-markdown-review` | data | trusted |
| `data-markitdown-file-to-markdown` | data | trusted |
| `data-qdrant-vector-retrieval` | data | trusted |
| `data-quality-audit` | data | trusted |
| `data-rag-namespace-boundary-check` | data | trusted |
| `data-schema-field-contract-check` | data | trusted |
| `data-table-analysis` | data | trusted |
| `data-table-calculation-verify` | data | trusted |
| `data-unstructured-document-partition` | data | trusted |
| `data-visualization-plan` | data | trusted |
| `design-accessibility-check` | design | trusted |
| `design-design-md-system-contract` | design | trusted |
| `design-motion-interaction-polish` | design | trusted |
| `design-premium-landing-page` | design | trusted |
| `design-responsive-viewport-check` | design | trusted |
| `design-system-consistency` | design | trusted |
| `design-tailwind-radix-system` | design | trusted |
| `design-ui-review` | design | trusted |
| `design-visual-quality-review` | design | trusted |
| `engineering-build-release` | engineering | trusted |
| `engineering-ci-troubleshoot` | engineering | trusted |
| `engineering-claude-skills-operations-review` | engineering | trusted |
| `engineering-error-log-noise-triage` | engineering | trusted |
| `engineering-performance-profile` | engineering | trusted |
| `execution-browser-check` | execution | trusted |
| `execution-browser-use-web-task` | execution | trusted |
| `execution-claude-skills-productivity-review` | execution | trusted |
| `execution-e2b-sandbox-boundary` | execution | trusted |
| `execution-file-batch` | execution | trusted |
| `execution-mcp-tool-connector-review` | execution | review_required |
| `execution-playwright-browser-automation` | execution | trusted |
| `execution-publish-check` | execution | trusted |
| `execution-rollback-checkpoint-plan` | execution | trusted |
| `media-agentic-video-pipeline-plan` | media | trusted |
| `media-asset-review` | media | trusted |
| `media-brand-asset-pack` | media | trusted |
| `media-remotion-video-production-boundary` | media | trusted |
| `media-video-script-review` | media | trusted |
| `office-claude-skills-document-review` | office | trusted |
| `office-docx-brief` | office | trusted |
| `office-link-reference-integrity` | office | trusted |
| `office-markdown-structure-lint` | office | trusted |
| `office-pdf-report` | office | trusted |
| `office-spreadsheet-cleanup` | office | trusted |
| `office-table-source-reconciliation` | office | trusted |
| `research-citation-evidence-map` | research | trusted |
| `research-claude-skills-evidence-review` | research | trusted |
| `research-clinical-study-design-review` | research | trusted |
| `research-competitor-brief` | research | trusted |
| `research-finance-analysis-review` | research | trusted |
| `research-market-analysis-review` | research | trusted |
| `research-multi-platform-search-boundary` | research | trusted |
| `research-operations-governance-review` | research | trusted |
| `research-paper-synthesis` | research | trusted |
| `research-product-analysis-review` | research | trusted |
| `research-recent-social-signal-brief` | research | review_required |
| `research-source-check` | research | trusted |
| `research-source-lineage-trace` | research | trusted |
| `security-command-risk-preflight` | security | trusted |
| `security-guardrails-output-validation` | security | trusted |
| `security-llm-guard-io-scanning` | security | trusted |
| `security-opensquilla-sandbox-policy` | security | trusted |
| `security-prompt-injection-review` | security | trusted |
| `security-secret-context-redaction` | security | trusted |
| `security-supply-chain-review` | security | trusted |
| `trivy-container-security-scan` | security | trusted |
| `vertical-education-plan` | vertical | trusted |
| `vertical-industry-intake-orchestration` | vertical | trusted |
| `vertical-industry-solution-packaging` | vertical | trusted |
| `vertical-learning-memory-refresh` | vertical | trusted |
| `vertical-manufacturing-qc` | vertical | trusted |
| `vertical-real-estate-listing` | vertical | trusted |


## Next Collection Waves

Recommended next waves:

- `batch-031-domain-depth`: split cluster-covered claude-skills candidates into dedicated local skills only when repeated demand proves a cluster is too broad
- `batch-022-connectors`: connector-aware skills after host adapter verification
- `batch-023-bundle-tuning`: scenario bundle and overlap-group refinements after the converted catalog settles
