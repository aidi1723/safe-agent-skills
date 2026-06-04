# Skill Index

This index lists every catalog skill with its category, review status, and
one-line capability description.

Each individual `SKILL.md` also contains:

- frontmatter `description`
- `When To Use`
- `Safe Workflow`
- `Expected Output`
- `Verifier Expectations`
- `Failure Handling`

## Catalog Skills

| Category | Skill | Status | Capability |
| --- | --- | --- | --- |
| ai | `ai-guidance-constrained-generation` | trusted | Use when an LLM task needs constrained generation, token-level control, or explicit output structure. |
| ai | `ai-litellm-gateway-cost-control` | review_required | Use when reviewing model gateway routing, provider fallback, budget limits, rate limits, or agent cost controls. |
| ai | `ai-llama-cpp-local-inference-boundary` | trusted | Use when reviewing local LLM inference, offline model use, context limits, quantization tradeoffs, or local privacy boundaries. |
| ai | `ai-outlines-structured-generation` | trusted | Use when an AI workflow needs strict structured output, regex-like constraints, or schema-shaped generation. |
| ai | `ai-output-schema-eval` | trusted | Use when evaluating AI outputs against schema, format, task requirements, safety constraints, and regression examples. |
| ai | `ai-pydantic-schema-contract` | trusted | Use when defining typed contracts, JSON Schema outputs, validation models, or parser-safe AI response formats. |
| ai | `ai-vllm-serving-capacity-plan` | trusted | Use when reviewing high-throughput LLM serving, batching, memory planning, latency targets, or inference capacity. |
| ai | `ecc-agent-coding-safety` | trusted | Use when adapting community context-engineering ideas for AI coding assistants, memory, safety checks, and bounded code work. |
| ai | `headroom-context-compression` | trusted | Use when compressing long task context, chat history, notes, or documents before an AI workflow while preserving key facts. |
| ai | `hermes-agent-memory-assistant` | quarantined | Use when evaluating agent memory, preference learning, task continuity, and assistant personalization boundaries. |
| ai | `supermemory-memory-engine-reference` | quarantined | Use when designing, evaluating, or integrating persistent AI memory retrieval without exposing private data or secrets. |
| business | `business-process-sop` | trusted | Use when documenting repeatable business operations, handoffs, checklists, roles, and standard operating procedures. |
| business | `business-requirements-brief` | trusted | Use when turning business goals, stakeholder notes, user needs, and constraints into clear requirements. |
| business | `business-support-triage` | trusted | Use when triaging customer support requests, drafting safe replies, and identifying escalation needs. |
| code | `code-python-debug` | trusted | Use when diagnosing and fixing Python bugs with focused tests, minimal changes, and explicit verification. |
| code | `code-review-risk` | trusted | Use when reviewing code changes for bugs, regressions, missing tests, unsafe assumptions, and maintainability risks. |
| code | `code-test-regression` | trusted | Use when adding or reviewing regression tests, failure cases, fixtures, and verification commands for code changes. |
| commerce | `commerce-icbu-listing` | trusted | Use when preparing Alibaba International Station product listing structure, attributes, keywords, and inquiry-oriented copy. |
| commerce | `commerce-inquiry-reply` | trusted | Use when drafting buyer inquiry replies, quotation responses, product clarification, and trade follow-up messages. |
| commerce | `commerce-product-keyword-plan` | trusted | Use when planning product keywords, category terms, listing search intent, and marketplace discovery structure. |
| compliance | `compliance-accessibility-policy` | trusted | Use when reviewing accessibility commitments, product conformance notes, support process, and public accessibility statements. |
| compliance | `compliance-privacy-check` | trusted | Use when checking whether a workflow, document, or dataset has privacy and data-handling risks that need review. |
| compliance | `compliance-terms-review` | trusted | Use when reviewing terms, policies, disclaimers, user-facing rules, and operational commitments for risk. |
| compliance | `vibe-trading-research-assistant` | quarantined | Use when evaluating AI-assisted trading research workflows, quantitative analysis notes, and financial decision safety boundaries. |
| content | `content-editorial-review` | trusted | Use when reviewing drafts for clarity, structure, tone, factual consistency, audience fit, and publication readiness. |
| content | `content-prompt-engineering-patterns` | trusted | Use when designing prompts, context instructions, RAG workflows, agent behavior specs, or prompt review checklists. |
| content | `content-seo-brief` | trusted | Use when preparing an SEO, GEO, article, or product content brief with factual claims and source boundaries. |
| content | `content-social-post` | trusted | Use when preparing social posts, short announcements, community updates, launch notes, and channel-specific copy. |
| data | `data-marker-pdf-markdown-review` | trusted | Use when reviewing PDF-to-Markdown extraction quality, layout preservation, table handling, or OCR uncertainty. |
| data | `data-markitdown-file-to-markdown` | trusted | Use when converting mixed office files, documents, or local assets into clean Markdown for agent workflows. |
| data | `data-quality-audit` | trusted | Use when checking datasets for missing values, duplicates, schema drift, outliers, freshness, and readiness for analysis. |
| data | `data-table-analysis` | trusted | Use when cleaning, summarizing, validating, or explaining tabular datasets inside an approved workspace. |
| data | `data-unstructured-document-partition` | trusted | Use when transforming complex documents into clean chunks, structured records, or retrieval-ready text. |
| data | `data-visualization-plan` | trusted | Use when choosing charts, dashboard views, metric summaries, visual encodings, and data storytelling structure. |
| design | `design-accessibility-check` | trusted | Use when reviewing interface accessibility, labels, contrast, keyboard reachability, focus states, and responsive readability. |
| design | `design-system-consistency` | trusted | Use when checking UI tokens, components, spacing, typography, states, and visual consistency across screens. |
| design | `design-ui-review` | trusted | Use when reviewing or polishing a UI screen, dashboard, or frontend view for layout, visual hierarchy, responsiveness, and accessibility. |
| engineering | `engineering-build-release` | trusted | Use when preparing a local build, release readiness check, or engineering handoff with explicit smoke tests and rollback notes. |
| engineering | `engineering-ci-troubleshoot` | trusted | Use when diagnosing CI failures, build jobs, test matrix problems, cache issues, and release pipeline breakage. |
| engineering | `engineering-performance-profile` | trusted | Use when reviewing performance, latency, memory growth, slow builds, bottlenecks, and reliability under load. |
| execution | `execution-browser-check` | trusted | Use when running bounded browser inspection, form-flow checks, screenshots, or UI smoke verification. |
| execution | `execution-file-batch` | trusted | Use when running bounded batch work over workspace files, generated artifacts, exports, or repeated local file operations. |
| execution | `execution-publish-check` | trusted | Use when preparing controlled publishing, release handoff, artifact upload, or public repository readiness checks. |
| media | `media-asset-review` | trusted | Use when checking image, video, audio, or presentation assets for readiness, format, rights, and output quality. |
| media | `media-brand-asset-pack` | trusted | Use when organizing brand assets, image sets, logo files, usage notes, and publication-ready media packs. |
| media | `media-video-script-review` | trusted | Use when reviewing short video scripts, narration, shot plans, product demos, and edit briefs for clarity and risk. |
| office | `office-docx-brief` | trusted | Use when drafting, editing, structuring, or reviewing Word-style documents, briefs, memos, and formatted reports. |
| office | `office-pdf-report` | trusted | Use when extracting, reviewing, summarizing, or checking PDF reports inside an approved workspace. |
| office | `office-spreadsheet-cleanup` | trusted | Use when cleaning, reviewing, formatting, or summarizing spreadsheets, CSV files, tables, and business data sheets. |
| research | `research-competitor-brief` | trusted | Use when comparing competitors, products, pricing pages, positioning, features, and public market signals. |
| research | `research-paper-synthesis` | trusted | Use when summarizing papers, technical reports, datasets, methods, limitations, and evidence across research sources. |
| research | `research-source-check` | trusted | Use when verifying factual claims against primary or high-quality sources with explicit citations. |
| security | `security-guardrails-output-validation` | trusted | Use when designing output validation, structured compliance checks, or guardrail review for LLM and agent responses. |
| security | `security-llm-guard-io-scanning` | trusted | Use when reviewing LLM input and output scanning, sensitive-data filtering, or prompt security gates. |
| security | `security-prompt-injection-review` | trusted | Use when reviewing prompts, skills, connector instructions, or agent workflows for prompt-injection and unsafe authority risks. |
| security | `security-supply-chain-review` | trusted | Use when reviewing package, plugin, connector, dependency, or skill supply-chain risk before adoption. |
| security | `trivy-container-security-scan` | trusted | Use when reviewing container images, filesystems, dependencies, IaC, secrets, or SBOM security findings with Trivy-style scanners. |
| vertical | `vertical-education-plan` | trusted | Use when preparing education plans, lesson outlines, study workflows, or learning assessments with age and context awareness. |
| vertical | `vertical-manufacturing-qc` | trusted | Use when preparing manufacturing quality-control checklists, inspection notes, defect summaries, and production handoff records. |
| vertical | `vertical-real-estate-listing` | trusted | Use when preparing real-estate listing copy, property fact checks, feature summaries, and buyer-facing notes. |
