# Scenario Skill Bundles

Scenario bundles are curated groups of trusted skills for common real-world
tasks.

A single skill is a focused capability. A bundle is a task playbook: it lists
which skills to combine, the recommended order, the expected output, and the
verification checks. Bundles do not grant runtime permissions. They only help a
host agent choose a stronger starting plan.

## Bundle Rule

- Use only `trusted` skills for default bundles.
- Keep each bundle tied to a concrete scenario.
- Record the execution order and why each skill is included.
- Keep runtime actions under the host agent's normal approval policy.
- Verify the catalog before using a bundle in automation.

## Current Bundles

| Bundle | Scenario | Primary Skills |
| --- | --- | --- |
| `website-build-launch` | Build or polish a website and prepare it for release | architecture, UI, content, SEO, browser check, publish check |
| `code-review-hardening` | Review code, tests, schema contracts, and security risk | code review, regression tests, structured output, supply-chain review |
| `codebase-change-lifecycle` | Explore a codebase, implement or debug changes, simplify, test, and review | context, debugging, refactor safety, tests, review, release |
| `codebase-graph-intelligence` | Review code graph index, MCP code intelligence, architecture query, and impact-analysis boundaries | graph boundary, project context, schema, source confirmation, supply-chain review |
| `security-agent-guardrails` | Review an agent workflow for prompt injection, guardrails, and I/O scanning | prompt injection, output validation, I/O scanning, supply-chain review |
| `agent-planning-orchestration` | Clarify fuzzy requirements, decompose a plan, and coordinate multi-agent execution | requirements, metaskill workflow, orchestration, role workflow, multi-agent review |
| `document-to-knowledge-base` | Convert documents into Markdown, chunks, summaries, and source-backed notes | PDF review, Markdown conversion, document partitioning, source check |
| `data-analysis-report` | Clean data, analyze tables, plan visuals, and write a decision report | table analysis, data quality, visualization, office brief |
| `open-source-release` | Prepare a public repository, docs, safety statement, and release handoff | publish check, supply-chain review, editorial review, social post |
| `content-seo-publication` | Draft and review SEO/GEO content for publication | SEO brief, editorial review, source check, prompt patterns |
| `content-video-production` | Plan copy, content matrix, video script, and media handoff for short-form or programmatic video production | content strategy, brand voice, claims review, video script, Remotion boundary, media asset review |
| `agentic-media-production` | Plan reference-video analysis, media pipeline selection, provider routing, cost estimates, and render QA | agentic video pipeline, source check, Remotion boundary, asset review, schema review |
| `rag-agent-knowledge-app` | Design a source-grounded RAG or knowledge-base agent | orchestration, RAG workflow, retrieval, schema, source check, prompt-injection review |
| `agent-long-term-memory-governance` | Design durable agent memory contracts, recall disclosure, deletion paths, and tenant boundaries | memory contract, namespace boundary, privacy, source check, schema eval |
| `commerce-listing-growth` | Prepare marketplace product listings and buyer communication | listing, keyword plan, inquiry reply, content review |

## Website Build Launch

Use when creating, polishing, or preparing a website, landing page, dashboard,
or product page for release.

Recommended skills:

1. `business-requirements-brief`
2. `engineering-build-release`
3. `design-ui-review`
4. `design-system-consistency`
5. `content-seo-brief`
6. `content-social-post`
7. `execution-browser-check`
8. `execution-browser-use-web-task`
9. `execution-playwright-browser-automation`
10. `execution-publish-check`

Expected output:

- requirements and acceptance criteria
- architecture or build readiness notes
- UI and responsive review
- page copy and SEO notes
- browser verification evidence
- publish readiness checklist

## Code Review Hardening

Use when reviewing generated code, pull requests, bug fixes, or automation
changes before acceptance.

Recommended skills:

1. `code-review-risk`
2. `code-test-regression`
3. `ai-pydantic-schema-contract`
4. `ai-output-schema-eval`
5. `security-supply-chain-review`
6. `execution-e2b-sandbox-boundary`
7. `engineering-ci-troubleshoot`

Expected output:

- findings ordered by severity
- missing test notes
- schema or contract risks
- dependency and supply-chain risks
- sandbox and execution boundary notes
- verification commands and results

## Codebase Change Lifecycle

Use when a coding task needs project exploration, debugging or implementation,
simplification, regression testing, review, and engineering handoff.

Recommended skills:

1. `ecc-agent-coding-safety`
2. `code-python-debug`
3. `code-ast-refactor-safety`
4. `code-dead-path-cleanup-review`
5. `code-test-regression`
6. `code-review-risk`
7. `engineering-build-release`
8. `engineering-ci-troubleshoot`

Expected output:

- project context map
- debugging or implementation notes
- simplification and refactor-safety notes
- regression test evidence
- review findings
- build or CI readiness notes

## Security Agent Guardrails

Use when reviewing an AI agent, connector, prompt, or workflow for safety
boundaries.

Recommended skills:

1. `security-prompt-injection-review`
2. `security-guardrails-output-validation`
3. `security-llm-guard-io-scanning`
4. `ai-outlines-structured-generation`
5. `security-supply-chain-review`
6. `compliance-privacy-check`

Expected output:

- prompt-injection findings
- input and output scanning boundaries
- validation contract
- supply-chain notes
- privacy and escalation notes

## Agent Planning Orchestration

Use when a vague or multi-agent task needs requirements clarification,
workflow decomposition, role boundaries, handoff rules, and output validation
before execution.

Recommended skills:

1. `business-requirements-brief`
2. `ai-opensquilla-metaskill-workflow`
3. `ai-langchain-agent-orchestration`
4. `ai-crewai-role-workflow`
5. `ai-autogen-multi-agent-review`
6. `ai-tool-schema-protocol-check`
7. `ai-output-schema-eval`

Expected output:

- requirements and ambiguity summary
- workflow decomposition
- agent orchestration map
- role and authority boundaries
- handoff and termination criteria
- schema and output validation notes

## Document To Knowledge Base

Use when turning PDFs, office files, or mixed documents into Markdown,
retrieval-ready chunks, summaries, or knowledge-base entries.

Recommended skills:

1. `office-pdf-report`
2. `data-markitdown-file-to-markdown`
3. `data-marker-pdf-markdown-review`
4. `data-unstructured-document-partition`
5. `ai-llamaindex-rag-knowledge-workflow`
6. `data-haystack-rag-pipeline`
7. `data-qdrant-vector-retrieval`
8. `research-source-check`
9. `office-docx-brief`

Expected output:

- source file inventory
- extracted Markdown paths or notes
- conversion quality review
- chunking and metadata plan
- RAG and vector retrieval plan
- source-backed summary
- extraction uncertainty list

## Data Analysis Report

Use when cleaning a dataset, analyzing tables, planning charts, and preparing a
business or research report.

Recommended skills:

1. `data-quality-audit`
2. `data-table-analysis`
3. `data-visualization-plan`
4. `office-spreadsheet-cleanup`
5. `research-source-check`
6. `office-docx-brief`

Expected output:

- data quality findings
- analysis summary
- chart and dashboard plan
- spreadsheet cleanup notes
- source and assumption notes
- final report outline

## Open Source Release

Use when preparing a repository, package, catalog, or public artifact for open
source publication.

Recommended skills:

1. `execution-publish-check`
2. `security-supply-chain-review`
3. `compliance-terms-review`
4. `content-editorial-review`
5. `content-social-post`
6. `research-source-check`

Expected output:

- release readiness checklist
- source and license review
- public docs review
- social launch copy
- blockers and residual risks

## Content SEO Publication

Use when drafting, fact-checking, optimizing, and publishing public content.

Recommended skills:

1. `content-seo-brief`
2. `content-editorial-review`
3. `content-prompt-engineering-patterns`
4. `research-source-check`
5. `content-social-post`

Expected output:

- audience and search intent
- article or page outline
- source-backed claims
- edited copy
- social distribution copy

## Content Video Production

Use when a workflow combines copywriting, content
matrix planning, video scripts, media assets, and programmatic video production
ideas such as Remotion.

Recommended skills:

1. `content-strategy-matrix`
2. `content-seo-brief`
3. `content-brand-voice-boundary`
4. `content-editorial-review`
5. `content-claims-compliance-filter`
6. `media-video-script-review`
7. `media-remotion-video-production-boundary`
8. `media-asset-review`
9. `execution-publish-check`

Expected output:

- audience and content matrix notes
- copy and brand voice review
- claims compliance notes
- video script or edit brief
- programmatic video boundary notes
- asset readiness notes
- publication readiness boundary

Programmatic video execution, dependency install, rendering, cloud render,
upload, or publication still requires separate runtime, asset-rights, account,
and license review.

## RAG Agent Knowledge App

Use when designing a source-grounded RAG or knowledge-base agent with
retrieval, citations, structured outputs, and safety checks.

Recommended skills:

1. `business-requirements-brief`
2. `ai-langchain-agent-orchestration`
3. `ai-llamaindex-rag-knowledge-workflow`
4. `data-haystack-rag-pipeline`
5. `data-qdrant-vector-retrieval`
6. `ai-pydantic-schema-contract`
7. `ai-output-schema-eval`
8. `research-source-check`
9. `security-prompt-injection-review`

Expected output:

- requirements and source boundaries
- agent orchestration and retrieval plan
- indexing and chunking design
- vector retrieval quality checks
- structured answer contract
- citation and prompt-injection review

## Commerce Listing Growth

Use when preparing marketplace listings, search keywords, inquiry replies, and
trade communication.

Recommended skills:

1. `commerce-icbu-listing`
2. `commerce-product-keyword-plan`
3. `commerce-inquiry-reply`
4. `content-editorial-review`
5. `business-requirements-brief`

Expected output:

- product listing structure
- keyword plan
- buyer-facing copy
- inquiry response templates
- assumptions and next actions
