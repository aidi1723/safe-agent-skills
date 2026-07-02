# Catalog Overview

Safe-Agent-Skills is organized around trusted, method-only skills selected by
the router. The recommended user entry remains the single `safe-agent-router`
skill, not manual installation of every catalog skill.

## Current Baseline

- 136 catalog skills
- 130 trusted skills
- 13 trusted scenario bundles
- 15 top-level categories
- trusted-only default routing
- provenance, hash, schema, and maintain checks before publication

## Domain Map

| Domain | Use For | Example Command |
| --- | --- | --- |
| `ai` | agent planning, routing, schemas, RAG, output validation | `onecode-skill-sanitizer task-pack "design a RAG document agent" --registry catalog --include-bundles --bundles bundles/index.json --router scenario` |
| `code` | code review, debugging, regression tests, refactor safety | `onecode-skill-sanitizer task-pack "review generated code and harden tests" --registry catalog --include-bundles --bundles bundles/index.json --router scenario` |
| `design` | UI review, design-system consistency, responsive checks | `onecode-skill-sanitizer task-pack "polish a product dashboard UI" --registry catalog --include-bundles --bundles bundles/index.json --router scenario` |
| `security` | prompt injection, supply chain, guardrails, secret redaction | `onecode-skill-sanitizer task-pack "review an agent workflow for connector permissions" --registry catalog --include-bundles --bundles bundles/index.json --router scenario` |
| `content` | SEO briefs, editorial checks, claims compliance, social posts | `onecode-skill-sanitizer task-pack "draft and fact check an SEO blog post" --registry catalog --include-bundles --bundles bundles/index.json --router scenario` |
| `data` | data quality, table analysis, document-to-knowledge workflows | `onecode-skill-sanitizer task-pack "clean spreadsheet data and prepare chart notes" --registry catalog --include-bundles --bundles bundles/index.json --router scenario` |
| `commerce` | marketplace listings, keyword plans, buyer replies, RFP responses, pricing strategy | `onecode-skill-sanitizer task-pack "review this RFP response and pricing assumptions" --registry catalog --include-bundles --bundles bundles/index.json --router scenario` |
| `research` | source checks, citation maps, paper synthesis, freshness review, clinical study design review | `onecode-skill-sanitizer task-pack "review a clinical study protocol design" --registry catalog --include-bundles --bundles bundles/index.json --router scenario` |

## Maintenance Priorities

The `claude-skills` expansion audit evaluated 336 canonical upstream candidates
and converted 22 local safe skills across SaaS metrics, RFP responses,
procurement, pricing, customer success, clinical study design, vendor
management, commercial forecasting, revenue operations, deal desk, finance
analysis, Scrum project review, knowledge operations, process mapping,
commercial policy, partnerships, channel economics, product management,
Jira workflow review, Confluence knowledge review, internal communications,
and capacity planning. Remaining priority gaps include research operations,
meeting and team communication review, sales engineering, contract and proposal
writing, and deeper market, product, research, and finance analysis.

External libraries such as `claude-skills` are reference-only. Do not install,
copy, execute, or trust upstream skills without per-skill review.
