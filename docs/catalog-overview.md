# Catalog Overview

Safe-Agent-Skills is organized around trusted, method-only skills selected by
the router. The recommended user entry remains the single `safe-agent-router`
skill, not manual installation of every catalog skill.

## Current Baseline

- 152 catalog skills
- 146 trusted skills
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
and records 53 upstream candidate conversion or coverage mappings. These are
represented by 38 distinct local safe catalog skills across SaaS metrics, RFP responses,
procurement, pricing, customer success, clinical study design, vendor
management, commercial forecasting, revenue operations, deal desk, finance
analysis, Scrum project review, knowledge operations, process mapping,
commercial policy, partnerships, channel economics, product management,
Jira workflow review, Confluence knowledge review, internal communications,
capacity planning, meeting analysis, team communications, contract proposal
review, sales engineering, market research, product research, research finance,
investment memo review, Atlassian administration governance, Atlassian template
governance, marketing pricing strategy review, commercial operations, finance
operations, growth operations, project management operations, and research
operations governance. The ranked candidate queue
now has no remaining `candidate` entries; future expansion should mine
reference-only clusters for deeper engineering, product, marketing, compliance,
RA/QM, and connector-aware workflows.

For faster expansion planning, use the bulk planner to group all remaining
metadata-only items into large review waves:

```bash
onecode-skill-sanitizer claude-skills-bulk-plan \
  --candidate-map docs/claude-skills-candidate-map.json \
  --batch-size 50
```

Then materialize a selected wave as local drafts:

```bash
onecode-skill-sanitizer claude-skills-bulk-draft \
  --candidate-map docs/claude-skills-candidate-map.json \
  --out batches/batch-XXX-claude-skills-bulk-draft \
  --batch-size 50 \
  --batch-index 1
```

After draft materialization, assess the whole draft pool before local authoring or import:

```bash
onecode-skill-sanitizer claude-skills-bulk-assess \
  --candidate-map docs/claude-skills-candidate-map.json \
  --draft-root batches \
  --registry catalog
```

Include the candidate map in the release maintenance gate so converted
coverage mappings continue to point at existing trusted catalog skills:

```bash
onecode-skill-sanitizer maintain-check \
  --registry catalog \
  --bundles bundles/index.json \
  --references external-references/index.json \
  --claude-skills-candidate-map docs/claude-skills-candidate-map.json
```

The current assessment classifies 283 candidates to keep reference-only and
53 as already converted or covered by existing trusted skills. There are no
remaining `author_local_skill` or `merge_existing` candidates after the
coverage pass.
See [Claude Skills Reference-Only Backlog](claude-skills-reference-only-backlog.md)
for the detailed category breakdown, non-promotion reasons, and next promotion
waves.
The assessment command does not approve or trust drafts. Converted candidates
must still map to existing trusted local catalog skills or they are reported as
`invalid_converted_mapping`.

External libraries such as `claude-skills` are reference-only. Do not install,
copy, execute, or trust upstream skills without per-skill review.
