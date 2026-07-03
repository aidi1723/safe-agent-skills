# Feature Log

Date: 2026-07-03

## User-Facing Entry

Install one skill, `safe-agent-router`, and let it select trusted skills and
scenario bundles from this repository. The router emits a task pack with:

- task profile
- selected scenario bundle
- capability coverage
- ordered execution plan
- selected trusted skills
- provenance and hash records
- verifier expectations
- fixed safety boundary

## Current Catalog Size

```text
167 catalog skills
161 trusted skills
18 trusted scenario bundles
15 top-level categories
7 trusted overlap groups
29 router eval cases
336 / 336 tracked claude-skills candidates covered
```

## Trusted Category Capability Map

| Category | Trusted Count | Capabilities |
| --- | ---: | --- |
| `ai` | 24 | agent orchestration, RAG workflows, long-term memory contracts, structured generation, schema contracts, output evaluation, model routing, context compression |
| `business` | 28 | requirements, SaaS metrics, customer success, finance operations, procurement, project operations, internal communication, product management |
| `code` | 10 | code review, debugging, regression testing, refactor safety, dependency and dead-path checks, code graph index boundaries |
| `commerce` | 12 | ICBU listings, keywords, RFP responses, inquiry replies, pricing, deal desk, partnerships, commercial forecasting |
| `compliance` | 7 | privacy, terms, licensing, accessibility, public claims, regulated-industry review boundaries |
| `content` | 11 | SEO, editorial quality, brand voice, social content, content strategy, freshness and claims review |
| `data` | 11 | data quality, table analysis, visualization, RAG data boundaries, document partitioning and conversion |
| `design` | 8 | UI review, responsive checks, accessibility, visual quality, design systems, premium landing pages, motion polish |
| `engineering` | 5 | CI troubleshooting, build and release checks, performance profiling, operations review, log triage |
| `execution` | 8 | browser automation guidance, publish checks, sandbox boundaries, rollback planning, file batch workflows |
| `media` | 5 | video scripts, asset review, Remotion production boundaries, agentic media pipeline planning, brand asset packs |
| `office` | 7 | PDF reports, DOCX briefs, spreadsheets, markdown structure, links, tables, document review |
| `research` | 11 | source verification, citation maps, paper synthesis, clinical study design, finance and market research |
| `security` | 8 | prompt injection review, supply-chain review, command risk preflight, secret redaction, output guardrails |
| `vertical` | 6 | education plans, manufacturing QC, real-estate listings, learning memory, industry intake and solution packaging |

## Trusted Scenario Bundles

| Bundle | Purpose |
| --- | --- |
| `website-build-launch` | Build and verify product websites and launch checks |
| `code-review-hardening` | Review generated code and harden tests before accepting changes |
| `codebase-change-lifecycle` | Explore, modify, test, review, and release codebase changes |
| `codebase-graph-intelligence` | Plan code graph index, MCP code intelligence, source confirmation, and impact-analysis boundaries |
| `security-agent-guardrails` | Review prompt injection, connector permissions, and agent guardrails |
| `agent-planning-orchestration` | Plan multi-agent and tool-routing workflows |
| `document-to-knowledge-base` | Convert documents into knowledge-base-ready chunks with evidence checks |
| `content-video-production` | Plan and review content, scripts, assets, video boundaries, and publishing |
| `agentic-media-production` | Plan reference-video analysis, media pipeline routing, cost estimates, and render QA gates |
| `data-analysis-report` | Clean data, analyze tables, plan charts, and prepare reports |
| `open-source-release` | Prepare public-safe release, docs, provenance, and verification |
| `content-seo-publication` | Draft, fact-check, edit, and publish SEO content |
| `rag-agent-knowledge-app` | Design RAG document agents with retrieval and citation checks |
| `agent-long-term-memory-governance` | Design durable agent memory contracts, recall disclosure, deletion paths, and tenant boundaries |
| `claude-skills-backlog-coverage` | Cover tracked `claude-skills` backlog candidates through trusted local clusters |
| `skill-router-quality-review` | Review router quality, task-pack contracts, bundle composition, and tests |
| `industry-application-orchestration` | Profile multi-industry users, select trusted domain skills, check regulated boundaries, and package solution plans |
| `commerce-listing-growth` | Improve marketplace listings, keywords, inquiries, and commerce growth workflows |

## Newest Capability Expansion

The latest expansion adds three agentic reference-pattern bundles and three
trusted local skills:

- `media-agentic-video-pipeline-plan`
- `ai-graph-memory-contract`
- `code-codebase-graph-index-boundary`

This lets the single router support agentic media production, durable memory
governance, and code graph intelligence while preserving method-only runtime
boundaries.
