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
| ai | `ai-autogen-multi-agent-review` | trusted | Use when reviewing multi-agent collaboration, role boundaries, conversation loops, or agent handoff workflows. |
| ai | `ai-context-compression-budget-plan` | trusted | Use when planning context compression, long prompt trimming, memory summaries, retrieval snippets, or token-budget tradeoffs before AI execution. |
| ai | `ai-crewai-role-workflow` | trusted | Use when designing role-based agent teams, task delegation, process sequencing, or collaborative agent workflows. |
| ai | `ai-guidance-constrained-generation` | trusted | Use when an LLM task needs constrained generation, token-level control, or explicit output structure. |
| ai | `ai-hermes-tweet-workflow` | trusted | Use when reviewing Hermes Agent workflows that need X social signal, read-first exploration, or approval-gated account actions through Hermes Tweet. |
| ai | `ai-langchain-agent-orchestration` | trusted | Use when designing agent orchestration, tool routing, prompt chains, memory boundaries, or production LLM workflow structure. |
| ai | `ai-litellm-gateway-cost-control` | review_required | Use when reviewing model gateway routing, provider fallback, budget limits, rate limits, or agent cost controls. |
| ai | `ai-llama-cpp-local-inference-boundary` | trusted | Use when reviewing local LLM inference, offline model use, context limits, quantization tradeoffs, or local privacy boundaries. |
| ai | `ai-llamaindex-rag-knowledge-workflow` | trusted | Use when designing RAG, document agents, knowledge indexing, citation retrieval, or OCR-backed knowledge workflows. |
| ai | `ai-model-route-fallback-review` | trusted | Use when reviewing model routing, fallback choices, escalation rules, provider selection, cost tradeoffs, or AI workflow reliability boundaries. |
| ai | `ai-openai-cookbook-api-patterns` | trusted | Use when reviewing OpenAI API implementation patterns, examples, evals, structured outputs, RAG, or application recipes. |
| ai | `ai-opensquilla-metaskill-workflow` | trusted | Use when turning repeated multi-step agent work into reusable scenario skills, workflows, or bundle candidates. |
| ai | `ai-opensquilla-token-routing-pattern` | trusted | Use when reviewing token-aware skill loading, model routing, task-pack compression, or cost-sensitive agent planning. |
| ai | `ai-outlines-structured-generation` | trusted | Use when an AI workflow needs strict structured output, regex-like constraints, or schema-shaped generation. |
| ai | `ai-output-schema-eval` | trusted | Use when evaluating AI outputs against schema, format, task requirements, safety constraints, and regression examples. |
| ai | `ai-pydantic-schema-contract` | trusted | Use when defining typed contracts, JSON Schema outputs, validation models, or parser-safe AI response formats. |
| ai | `ai-qwen-agent-tool-workflow` | trusted | Use when reviewing function calling, MCP tools, code interpreter flows, RAG, or browser-extension agent workflows. |
| ai | `ai-rule-failure-log-synthesis` | trusted | Use when reviewing agent failures, policy blocks, verifier failures, repeated mistakes, or logs that should become safer future rules. |
| ai | `ai-stream-json-boundary-review` | trusted | Use when reviewing streamed AI output, partial JSON parsing, incremental tool arguments, SSE output, or structured response boundaries. |
| ai | `ai-token-rate-budget-guard` | trusted | Use when planning model calls, agent loops, context size, budget limits, rate limits, or fallback behavior for AI workflows. |
| ai | `ai-tool-schema-protocol-check` | trusted | Use when reviewing tool calling schemas, JSON arguments, function contracts, MCP-style protocol boundaries, or cross-model tool compatibility. |
| ai | `ai-vllm-serving-capacity-plan` | trusted | Use when reviewing high-throughput LLM serving, batching, memory planning, latency targets, or inference capacity. |
| ai | `ecc-agent-coding-safety` | trusted | Use when adapting community context-engineering ideas for AI coding assistants, memory, safety checks, and bounded code work. |
| ai | `headroom-context-compression` | trusted | Use when compressing long task context, tool outputs, logs, retrieval chunks, chat history, notes, or documents before an AI workflow while preserving key facts. |
| ai | `hermes-agent-memory-assistant` | quarantined | Use when evaluating agent memory, preference learning, task continuity, and assistant personalization boundaries. |
| ai | `supermemory-memory-engine-reference` | quarantined | Use when designing, evaluating, or integrating persistent AI memory retrieval without exposing private data or secrets. |
| business | `business-process-sop` | trusted | Use when documenting repeatable business operations, handoffs, checklists, roles, and standard operating procedures. |
| business | `business-requirements-brief` | trusted | Use when turning business goals, stakeholder notes, user needs, and constraints into clear requirements. |
| business | `business-support-triage` | trusted | Use when triaging customer support requests, drafting safe replies, and identifying escalation needs. |
| code | `code-ast-refactor-safety` | trusted | Use when planning structural refactors, symbol renames, import rewrites, large edits, AST-aware changes, or regex replacement risk reviews. |
| code | `code-dead-path-cleanup-review` | trusted | Use when reviewing unused code, stale branches, dead feature paths, unreachable logic, cleanup diffs, or tree-shaking candidates. |
| code | `code-dependency-cycle-review` | trusted | Use when reviewing imports, module boundaries, package references, circular dependencies, layering violations, or architecture drift. |
| code | `code-python-debug` | trusted | Use when diagnosing and fixing Python bugs with focused tests, minimal changes, and explicit verification. |
| code | `code-review-risk` | trusted | Use when reviewing code changes for bugs, regressions, missing tests, unsafe assumptions, and maintainability risks. |
| code | `code-simplify-refactor-plan` | trusted | Use when simplifying code, reducing unnecessary abstraction, clarifying control flow, shrinking duplicate logic, or planning a low-risk refactor after behavior is understood. |
| code | `code-test-regression` | trusted | Use when adding or reviewing regression tests, failure cases, fixtures, and verification commands for code changes. |
| code | `codebase-explore-map` | trusted | Use when first exploring an unfamiliar repository, mapping architecture, finding entry points, identifying ownership boundaries, or preparing a codebase context brief before implementation or review. |
| commerce | `commerce-icbu-listing` | trusted | Use when preparing Alibaba International Station product listing structure, attributes, keywords, and inquiry-oriented copy. |
| commerce | `commerce-inquiry-reply` | trusted | Use when drafting buyer inquiry replies, quotation responses, product clarification, and trade follow-up messages. |
| commerce | `commerce-link-tracking-audit` | trusted | Use when checking campaign links, UTM parameters, commerce landing pages, inquiry funnels, tracking events, or marketing handoff URLs. |
| commerce | `commerce-product-keyword-plan` | trusted | Use when planning product keywords, category terms, listing search intent, and marketplace discovery structure. |
| compliance | `compliance-accessibility-policy` | trusted | Use when reviewing accessibility commitments, product conformance notes, support process, and public accessibility statements. |
| compliance | `compliance-license-policy-gate` | trusted | Use when reviewing third-party packages, copied snippets, assets, datasets, model files, or community skills for license and reuse risk. |
| compliance | `compliance-privacy-check` | trusted | Use when checking whether a workflow, document, or dataset has privacy and data-handling risks that need review. |
| compliance | `compliance-public-claim-risk-register` | trusted | Use when reviewing public statements, marketing claims, compliance-sensitive assertions, risk registers, disclaimers, or approval notes. |
| compliance | `compliance-terms-review` | trusted | Use when reviewing terms, policies, disclaimers, user-facing rules, and operational commitments for risk. |
| compliance | `vibe-trading-research-assistant` | quarantined | Use when evaluating AI-assisted trading research workflows, quantitative analysis notes, and financial decision safety boundaries. |
| content | `content-brand-voice-boundary` | trusted | Use when reviewing brand voice, tone drift, style consistency, content polish, or whether generated copy matches a defined editorial voice. |
| content | `content-claims-compliance-filter` | trusted | Use when reviewing marketing, SEO, listing, ad, landing-page, or sales copy for risky claims, absolute language, unsupported promises, or compliance-sensitive wording. |
| content | `content-editorial-review` | trusted | Use when reviewing drafts for clarity, structure, tone, factual consistency, audience fit, and publication readiness. |
| content | `content-fact-contradiction-review` | trusted | Use when reviewing long-form content, reports, documentation, or generated copy for internal contradictions, conflicting facts, timeline errors, or source gaps. |
| content | `content-freshness-expiry-review` | trusted | Use when reviewing stale content, time-sensitive claims, dated screenshots, outdated docs, pricing mentions, policy dates, or freshness risk. |
| content | `content-prompt-engineering-patterns` | trusted | Use when designing prompts, context instructions, RAG workflows, agent behavior specs, or prompt review checklists. |
| content | `content-seo-brief` | trusted | Use when preparing an SEO, GEO, article, or product content brief with factual claims and source boundaries. |
| content | `content-social-post` | trusted | Use when preparing social posts, short announcements, community updates, launch notes, and channel-specific copy. |
| content | `content-strategy-matrix` | trusted | Use when planning a content matrix, campaign content system, topic pillars, channel mapping, audience stages, editorial cadence, or multi-format content strategy before writing. |
| data | `data-haystack-rag-pipeline` | trusted | Use when reviewing modular RAG pipelines, retrieval routing, semantic search, memory, or production LLM application flows. |
| data | `data-marker-pdf-markdown-review` | trusted | Use when reviewing PDF-to-Markdown extraction quality, layout preservation, table handling, or OCR uncertainty. |
| data | `data-markitdown-file-to-markdown` | trusted | Use when converting mixed office files, documents, or local assets into clean Markdown for agent workflows. |
| data | `data-qdrant-vector-retrieval` | trusted | Use when reviewing vector search, embedding indexes, retrieval filters, similarity results, or RAG database boundaries. |
| data | `data-quality-audit` | trusted | Use when checking datasets for missing values, duplicates, schema drift, outliers, freshness, and readiness for analysis. |
| data | `data-rag-namespace-boundary-check` | trusted | Use when reviewing RAG namespaces, vector index filters, retrieval scopes, metadata boundaries, tenant isolation, or grounded answer source limits. |
| data | `data-schema-field-contract-check` | trusted | Use when reviewing database fields, API schemas, ORM models, JSON contracts, migrations, or generated code for field mismatch risk. |
| data | `data-table-analysis` | trusted | Use when cleaning, summarizing, validating, or explaining tabular datasets inside an approved workspace. |
| data | `data-table-calculation-verify` | trusted | Use when checking tables, spreadsheets, reports, financial summaries, percentages, totals, averages, or numeric claims for calculation consistency. |
| data | `data-unstructured-document-partition` | trusted | Use when transforming complex documents into clean chunks, structured records, or retrieval-ready text. |
| data | `data-visualization-plan` | trusted | Use when choosing charts, dashboard views, metric summaries, visual encodings, and data storytelling structure. |
| design | `design-accessibility-check` | trusted | Use when reviewing interface accessibility, labels, contrast, keyboard reachability, focus states, and responsive readability. |
| design | `design-motion-interaction-polish` | trusted | Use when adding or reviewing UI micro-interactions, CSS animations, Motion for React transitions, hover and focus feedback, scroll reveals, loading states, or reduced-motion behavior in a web interface. |
| design | `design-premium-landing-page` | trusted | Use when creating, polishing, or reviewing a premium marketing landing page, product launch page, SaaS homepage, brand showcase, or conversion page using modern visual references such as Awwwards, Godly, Lapa Ninja, Cruip, Magic UI, or Aceternity UI. |
| design | `design-responsive-viewport-check` | trusted | Use when reviewing responsive UI layouts, viewport breakpoints, text overflow, mobile readability, or screenshot-based layout regressions. |
| design | `design-system-consistency` | trusted | Use when checking UI tokens, components, spacing, typography, states, and visual consistency across screens. |
| design | `design-tailwind-radix-system` | trusted | Use when building, reviewing, or refactoring a React UI design system based on Tailwind CSS, Radix UI primitives, shadcn/ui-style components, tokens, variants, and accessible interaction states. |
| design | `design-ui-review` | trusted | Use when reviewing or polishing a UI screen, dashboard, or frontend view for layout, visual hierarchy, responsiveness, and accessibility. |
| design | `design-visual-quality-review` | trusted | Use when reviewing frontend visual quality, visual hierarchy, typography, spacing, color balance, density, polish, or whether an AI-generated interface looks generic or unfinished. |
| engineering | `engineering-build-release` | trusted | Use when preparing a local build, release readiness check, or engineering handoff with explicit smoke tests and rollback notes. |
| engineering | `engineering-ci-troubleshoot` | trusted | Use when diagnosing CI failures, build jobs, test matrix problems, cache issues, and release pipeline breakage. |
| engineering | `engineering-error-log-noise-triage` | trusted | Use when triaging stack traces, CI logs, runtime errors, noisy logs, repeated failures, or framework noise before debugging. |
| engineering | `engineering-performance-profile` | trusted | Use when reviewing performance, latency, memory growth, slow builds, bottlenecks, and reliability under load. |
| execution | `execution-browser-check` | trusted | Use when running bounded browser inspection, form-flow checks, screenshots, or UI smoke verification. |
| execution | `execution-browser-use-web-task` | trusted | Use when designing browser-based agent tasks, web navigation plans, form workflows, or online task automation boundaries. |
| execution | `execution-e2b-sandbox-boundary` | trusted | Use when reviewing code execution sandboxes, tool environments, ephemeral workspaces, or agent runtime isolation. |
| execution | `execution-file-batch` | trusted | Use when running bounded batch work over workspace files, generated artifacts, exports, or repeated local file operations. |
| execution | `execution-mcp-tool-connector-review` | review_required | Use when reviewing MCP servers, tool connectors, permission scopes, data access, or agent integration boundaries. |
| execution | `execution-playwright-browser-automation` | trusted | Use when planning deterministic browser checks, UI smoke tests, page assertions, screenshots, or web automation verification. |
| execution | `execution-publish-check` | trusted | Use when preparing controlled publishing, release handoff, artifact upload, or public repository readiness checks. |
| execution | `execution-rollback-checkpoint-plan` | trusted | Use when planning reversible changes, repository checkpoints, migration safety, release rollback, or recovery notes before risky work. |
| media | `media-asset-review` | trusted | Use when checking image, video, audio, or presentation assets for readiness, format, rights, and output quality. |
| media | `media-brand-asset-pack` | trusted | Use when organizing brand assets, image sets, logo files, usage notes, and publication-ready media packs. |
| media | `media-remotion-video-production-boundary` | trusted | Use when planning or reviewing Remotion-style programmatic video production, React-based video composition, render boundaries, asset inputs, captions, timing, and approval gates before generating video. |
| media | `media-video-script-review` | trusted | Use when reviewing short video scripts, narration, shot plans, product demos, and edit briefs for clarity and risk. |
| office | `office-docx-brief` | trusted | Use when drafting, editing, structuring, or reviewing Word-style documents, briefs, memos, and formatted reports. |
| office | `office-link-reference-integrity` | trusted | Use when reviewing document links, Markdown references, footnotes, anchors, cross-references, bibliography entries, or broken reference risk. |
| office | `office-markdown-structure-lint` | trusted | Use when reviewing Markdown, documentation, briefs, generated reports, or knowledge-base pages for heading structure, broken tables, links, frontmatter, or format consistency. |
| office | `office-pdf-report` | trusted | Use when extracting, reviewing, summarizing, or checking PDF reports inside an approved workspace. |
| office | `office-spreadsheet-cleanup` | trusted | Use when cleaning, reviewing, formatting, or summarizing spreadsheets, CSV files, tables, and business data sheets. |
| office | `office-table-source-reconciliation` | trusted | Use when reconciling report tables, spreadsheet excerpts, copied figures, source datasets, table captions, or numeric document evidence. |
| research | `research-citation-evidence-map` | trusted | Use when mapping claims to citations, reviewing evidence coverage, checking source-backed summaries, or preparing citation-heavy research output. |
| research | `research-competitor-brief` | trusted | Use when comparing competitors, products, pricing pages, positioning, features, and public market signals. |
| research | `research-paper-synthesis` | trusted | Use when summarizing papers, technical reports, datasets, methods, limitations, and evidence across research sources. |
| research | `research-recent-social-signal-brief` | review_required | Use when researching recent social, community, market, or creator signals from the last 30 days and turning noisy multi-source evidence into a cited brief. |
| research | `research-source-check` | trusted | Use when verifying factual claims against primary or high-quality sources with explicit citations. |
| research | `research-source-lineage-trace` | trusted | Use when tracing claims back to sources, checking citation lineage, reviewing summaries, or preventing unsupported research assertions. |
| security | `security-command-risk-preflight` | trusted | Use when reviewing proposed terminal commands, file operations, scripts, dependency actions, or operational steps before execution. |
| security | `security-guardrails-output-validation` | trusted | Use when designing output validation, structured compliance checks, or guardrail review for LLM and agent responses. |
| security | `security-llm-guard-io-scanning` | trusted | Use when reviewing LLM input and output scanning, sensitive-data filtering, or prompt security gates. |
| security | `security-opensquilla-sandbox-policy` | trusted | Use when reviewing agent sandbox boundaries, refusal logs, approval gates, or repeated unsafe action attempts. |
| security | `security-prompt-injection-review` | trusted | Use when reviewing prompts, skills, connector instructions, or agent workflows for prompt-injection and unsafe authority risks. |
| security | `security-secret-context-redaction` | trusted | Use when reviewing logs, configs, prompts, screenshots, environment notes, or context packs for secrets and sensitive data before sharing. |
| security | `security-supply-chain-review` | trusted | Use when reviewing package, plugin, connector, dependency, or skill supply-chain risk before adoption. |
| security | `trivy-container-security-scan` | trusted | Use when reviewing container images, filesystems, dependencies, IaC, secrets, or SBOM security findings with Trivy-style scanners. |
| vertical | `vertical-education-plan` | trusted | Use when preparing education plans, lesson outlines, study workflows, or learning assessments with age and context awareness. |
| vertical | `vertical-learning-memory-refresh` | trusted | Use when planning learning reinforcement, spaced review, knowledge retention, study workflows, or refresh schedules for long-running knowledge work. |
| vertical | `vertical-manufacturing-qc` | trusted | Use when preparing manufacturing quality-control checklists, inspection notes, defect summaries, and production handoff records. |
| vertical | `vertical-real-estate-listing` | trusted | Use when preparing real-estate listing copy, property fact checks, feature summaries, and buyer-facing notes. |
