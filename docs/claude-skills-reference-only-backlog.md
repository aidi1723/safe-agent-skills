# Claude Skills Reference-Only Backlog Closure

Date: 2026-07-02

## Scope

This document summarizes the former `claude-skills` reference-only backlog and
the cluster coverage path used to include it in the Safe-Agent-Skills trusted
local catalog.

The backlog items were not copied from upstream. They are now covered by local
OneCode-authored trusted skills that passed scan, approval, manifest sealing,
and registry verification. Upstream content remains metadata-only reference
material.

## Current Counts

Current candidate-map state:

```text
canonical candidates: 336
converted or covered by trusted local skills: 336
remaining reference-only candidates: 0
```

Former reference-only candidates covered by the cluster pass:

| Category | Count | Main Next-Step Use |
| --- | ---: | --- |
| `business` | 76 | Product, SaaS, executive, and operating workflows |
| `engineering` | 71 | MCP, onboarding, observability, environment, and agent operations |
| `code` | 47 | Developer-role and cloud-architecture review patterns |
| `content` | 44 | Marketing, CRO, growth, and lifecycle content workflows |
| `compliance` | 26 | RA/QM, AI governance, privacy, ISO, and regulated-domain checks |
| `research` | 8 | Grants, literature review, patent, and deep-research workflows |
| `execution` | 6 | Productivity and inbox-style personal execution patterns |
| `office` | 4 | Markdown, HTML, document, slide, and review helpers |
| `ai` | 1 | Loop-library style meta workflow reference |

Former reference-only candidates by source domain:

| Source Domain | Count |
| --- | ---: |
| `engineering` | 71 |
| `c-level-advisor` | 61 |
| `engineering-team` | 47 |
| `marketing-skill` | 44 |
| `ra-qm-team` | 17 |
| `product-team` | 15 |
| `compliance-os` | 9 |
| `research` | 8 |
| `productivity` | 6 |
| `markdown-html` | 4 |
| `loop-library` | 1 |

Priority distribution:

| Priority | Count | Meaning |
| --- | ---: | --- |
| `P2` | 18 | Useful next-wave candidates after local rewrite and review |
| `P3` | 265 | Lower-priority, overlapping, broad, or demand-dependent references |

Kind distribution:

| Kind | Count |
| --- | ---: |
| `skill` | 277 |
| `router-index` | 6 |

## Cluster Coverage

The 283 former reference-only items are now mapped to nine trusted local
cluster skills:

| Former Category | Count | Trusted Local Cluster Skill |
| --- | ---: | --- |
| `business` | 76 | `business-claude-skills-backlog-orchestration` |
| `engineering` | 71 | `engineering-claude-skills-operations-review` |
| `code` | 47 | `code-claude-skills-engineering-role-review` |
| `content` | 44 | `content-claude-skills-growth-review` |
| `compliance` | 26 | `compliance-claude-skills-regulated-review` |
| `research` | 8 | `research-claude-skills-evidence-review` |
| `execution` | 6 | `execution-claude-skills-productivity-review` |
| `office` | 4 | `office-claude-skills-document-review` |
| `ai` | 1 | `ai-claude-skills-meta-workflow-review` |

## Are These Duplicates?

Not exactly. The 283 former reference-only items fell into several groups:

- Some overlap existing trusted skills and should stay as coverage references
  unless they add a materially better workflow.
- Some are broad personas or advisory roles. These are useful as inspiration
  but noisy if added as default runtime skills.
- Some are real gaps but need local authoring before promotion.
- Some depend on connectors, external tools, accounts, or runtime assumptions
  that the skill catalog should not grant by itself.
- Some are upstream router indexes or platform mirrors rather than standalone
  reusable method skills.

So the backlog was mixed: partially duplicate, partially low priority,
partially useful future depth, and partially blocked by governance or
runtime-boundary review. Cluster coverage keeps them available to the router
through trusted local skills without adding 283 noisy default entries.

## Why They Were Not Trusted Individually

The common non-promotion reasons were:

- `reference_only` provenance meant upstream content was inspiration only. It
  must not be copied, installed, executed, or trusted directly.
- Many candidates are P3 and would increase routing noise more than task
  quality if added by default.
- Persona templates such as broad executive, architect, or specialist roles
  need concrete inputs, outputs, gates, and failure conditions before they are
  useful catalog skills.
- Several candidates overlap trusted local skills already selected by scenario
  bundles.
- Connector-aware items need host-adapter review for permissions, account
  boundaries, data handling, and stop conditions.
- Compliance and regulated-domain items require careful scope language so the
  skill gives review guidance rather than legal, medical, or regulatory
  authority.

Individual future promotion remains:

```text
reference-only candidate
  -> local OneCode-authored rewrite
  -> static scan
  -> schema validation
  -> serial approval
  -> manifest hash sealing
  -> registry verify
  -> trusted catalog inclusion
```

## Category Backlog

### Business

Count: 76.

High-value examples:

- `saas-scaffolder`
- `competitive-teardown`
- `ux-researcher-designer`
- `product-manager-toolkit`
- `research-summarizer`
- `apple-hig-expert`
- `experiment-designer`
- `roadmap-communicator`

Cluster action: covered by `business-claude-skills-backlog-orchestration`.

Main reason not promoted individually: this group mixes concrete product workflows with many
broad advisor/persona templates. The next pass should promote only workflows
with clear artifacts such as PRDs, experiments, roadmaps, competitive teardown
tables, UX research plans, or SaaS launch checklists.

### Engineering

Count: 71.

High-value examples:

- `mcp-server-builder`
- `codebase-onboarding`
- `observability-designer`
- `agenthub`
- `env-secrets-manager`
- `llm-wiki`
- `api-test-suite-builder`
- `setup`
- `run`
- `status`

Cluster action: covered by `engineering-claude-skills-operations-review`.

Main reason not promoted individually: this group includes real operational gaps but many
items are runtime-adjacent. They need host permission boundaries, tool
contracts, and concrete verification gates before trusted routing.

### Code

Count: 47.

High-value examples:

- `senior-prompt-engineer`
- `senior-fullstack`
- `self-improving-agent`
- `senior-frontend`
- `senior-ml-engineer`
- `adversarial-reviewer`
- `aws-solution-architect`
- `azure-cloud-architect`
- `gcp-cloud-architect`
- `coverage`
- `fix`

Cluster action: covered by `code-claude-skills-engineering-role-review`.

Main reason not promoted individually: many entries are developer-role personas rather than
bounded skills. Promotion should convert them into narrow review or execution
workflows such as prompt eval, cloud architecture review, regression coverage,
or adversarial code review.

### Content

Count: 44.

High-value examples:

- `marketing-demand-acquisition`
- `marketing-ideas`
- `copywriting`
- `paywall-upgrade-cro`
- `churn-prevention`
- `app-store-optimization`
- `page-cro`
- `x-twitter-growth`

Cluster action: covered by `content-claude-skills-growth-review`.

Main reason not promoted individually: several are useful marketing workflows, but default
routing already has content and claims-compliance coverage. Promotion should
focus on measurable output formats: acquisition brief, CRO audit, lifecycle
message set, ASO checklist, or campaign analytics review.

### Compliance

Count: 26.

High-value examples:

- `mdr-745-specialist`
- `capa-officer`
- `eu-ai-act-specialist`
- `fda-consultant-specialist`
- `gdpr-dsgvo-expert`
- `iso42001-specialist`
- `information-security-manager-iso27001`
- `isms-audit-expert`
- `qms-audit-expert`
- `quality-manager-qms-iso13485`

Cluster action: covered by `compliance-claude-skills-regulated-review`.

Main reason not promoted individually: these are high-risk domains. They should be promoted
only as review and evidence-collection workflows with clear disclaimers,
jurisdiction limits, and artifact requirements. They must not imply legal,
medical, regulatory, or certification authority.

### Research

Count: 8.

High-value examples:

- `grants`
- `pulse`
- `dossier`
- `litreview`
- `notebooklm`
- `patent`
- `syllabus`
- `deep-research`

Cluster action: covered by `research-claude-skills-evidence-review`.

Main reason not promoted individually: existing research skills already cover citation and
evidence workflows. Promotion should focus on differentiated artifacts such as
grant fit matrices, literature-review extraction schemas, patent landscape
maps, and source freshness checks.

### Execution

Count: 6.

Examples:

- `inbox-setup`
- `capture`
- `inbox-triage`
- `andreessen`
- `reflect`
- `roast`

Cluster action: covered by `execution-claude-skills-productivity-review`.

Main reason not promoted individually: these are mostly personal productivity or style
templates. They may be useful as optional workflows but are not strong default
catalog candidates unless converted into bounded task-intake, triage, or
retrospective protocols.

### Office

Count: 4.

Examples:

- `markdown-html-orchestrator`
- `md-slides`
- `md-document`
- `md-review`

Cluster action: covered by `office-claude-skills-document-review`.

Main reason not promoted individually: these overlap existing office/document guidance and
need clearer file-type contracts, renderer expectations, and visual
verification gates before adding more runtime surface.

### AI

Count: 1.

Example:

- `loop-library`

Cluster action: covered by `ai-claude-skills-meta-workflow-review`.

Main reason not promoted individually: this is best treated as a meta-workflow reference.
It should become a trusted catalog skill only if it produces a concrete,
auditable agent workflow pattern that does not depend on hidden runtime
permissions.

## Recommended Individual Promotion Waves

### Wave 1: P2 Product, Content, And Business Gaps

Target candidates:

- `saas-scaffolder`
- `competitive-teardown`
- `ux-researcher-designer`
- `product-manager-toolkit`
- `marketing-demand-acquisition`
- `copywriting`
- `paywall-upgrade-cro`
- `app-store-optimization`
- `grants`

Reason: these are already cluster-covered, but they are good candidates for
future dedicated local skills if repeated demand appears.

### Wave 2: Engineering Operational Depth

Target candidates:

- `mcp-server-builder`
- `codebase-onboarding`
- `observability-designer`
- `env-secrets-manager`
- `api-test-suite-builder`
- `setup`
- `run`
- `status`

Reason: these improve real agent execution quality but need tight boundaries
around credentials, local command execution, environment mutation, and
verification.

### Wave 3: Compliance And RA/QM Review Depth

Target candidates:

- `mdr-745-specialist`
- `capa-officer`
- `eu-ai-act-specialist`
- `gdpr-dsgvo-expert`
- `iso42001-specialist`
- `information-security-manager-iso27001`

Reason: these are valuable but high-risk. Promote only as evidence-collection
and checklist review skills with explicit non-authority language.

### Wave 4: Research And Office Conversion

Target candidates:

- `litreview`
- `patent`
- `deep-research`
- `dossier`
- `md-document`
- `md-slides`
- `md-review`

Reason: these can strengthen document and evidence workflows once output
schemas, citation checks, and rendering verification are explicit.

### Wave 5: Defer Persona-Heavy Advisor Templates

Target candidates:

- broad C-level advisor templates
- broad senior-engineer personas
- style-only personal productivity prompts
- upstream router indexes

Reason: these should remain reference-only until they are rewritten as bounded
methods with specific inputs, outputs, gates, and measurable acceptance
criteria.

## Promotion Criteria

A cluster-covered candidate should become a separate dedicated skill only when
all criteria are true:

- It fills a real catalog gap or materially improves an existing trusted skill.
- It can be rewritten locally without copying upstream bodies.
- It has a narrow trigger, clear output contract, and verifier expectations.
- It does not grant runtime permissions or assume external account access.
- It passes scanner, schema, maintain, and registry verification.
- It does not create duplicate routing noise with an existing trusted skill or
  scenario bundle.

## Maintenance Commands

Recompute the backlog from the candidate map:

```bash
python3 - <<'PY'
import json
from collections import Counter

with open("docs/claude-skills-candidate-map.json", encoding="utf-8") as f:
    data = json.load(f)

items = [
    c for c in data["candidates"]
    if c.get("adoption") == "reference_only"
]

print("count", len(items))
print("by_category", Counter(c.get("mapped_category", "") for c in items))
print("by_domain", Counter(c.get("source_domain", "") for c in items))
print("by_priority", Counter(c.get("priority", "") for c in items))
print("by_kind", Counter(c.get("kind", "") for c in items))
PY
```

Run the governance assessment:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer claude-skills-bulk-assess \
  --candidate-map docs/claude-skills-candidate-map.json \
  --draft-root batches \
  --registry catalog
```

Run the release maintenance gate:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check \
  --registry catalog \
  --bundles bundles/index.json \
  --references external-references/index.json \
  --claude-skills-candidate-map docs/claude-skills-candidate-map.json
```

## Residual Risks

- This backlog is based on the current local candidate map, not a live upstream
  sync.
- Upstream content remains metadata-only and must not be copied, executed, or
  trusted directly.
- Promotion work is intentionally slower than copying prompts because each
  trusted skill must preserve provenance, safety boundaries, and verification.
- Router quality can decrease if broad persona templates are later promoted as
  separate skills without narrow triggers and overlap controls.
