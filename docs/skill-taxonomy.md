# Skill Taxonomy

## Purpose

This catalog gives OneCode Skill Sanitizer a user-facing directory for
collecting, cleaning, reviewing, and selecting skills.

The top-level categories should be understandable to operators and users. The
subcategory and verifier fields give the kernel enough structure to choose a
skill safely.

The category is classification metadata only. It never grants permissions.
OneCode kernel policy still owns runtime authority.

## Classification Fields

Every collected skill should be tagged with:

- `category`: one top-level directory name
- `subcategory`: narrower workflow type
- `task_intent`: what the user is trying to accomplish
- `artifact_type`: code, document, image, report, deployment, dataset, etc.
- `risk_level`: low, medium, high, or critical
- `tool_needs`: expected tools or connectors
- `required_verifiers`: checks needed before completion
- `collection_priority`: P0, P1, P2, or P3

## Top-Level Directories

```text
skills/
  design/
  code/
  engineering/
  security/
  office/
  execution/
  research/
  data/
  business/
  content/
  commerce/
  media/
  compliance/
  ai/
  vertical/
```

## Priority Rule

- `P0`: collect first; immediately useful to OneCode core tasks
- `P1`: high value, but needs clearer verifier or adapter support
- `P2`: useful after the registry and review flow exists
- `P3`: vertical or advanced skills; collect later

## P0 Categories

### design

Purpose: UI, visual systems, frontend polish, dashboards, landing pages,
motion, layout, and product-facing experience.

Subcategories:

- `design.ui`: screen and component design
- `design.system`: tokens, reusable components, and consistency
- `design.frontend`: implemented frontend pages and app views
- `design.dashboard`: dense operational tools and admin panels
- `design.review`: visual QA, responsiveness, accessibility, and polish

Typical verifiers:

- build check
- screenshot check
- responsive viewport check
- accessibility check
- visual consistency checklist

Risk notes: preserve business logic, routing, data contracts, and product
behavior unless the user explicitly requests product-level redesign.

### code

Purpose: write, edit, debug, test, review, refactor, and explain source code.

Subcategories:

- `code.edit`: targeted file edits and patches
- `code.debug`: bug isolation and fix workflow
- `code.review`: code review and risk finding
- `code.test`: unit, integration, and regression test workflow
- `code.refactor`: scoped structural improvement
- `code.docs`: developer documentation and API docs

Typical verifiers:

- compile check
- unit test
- type check
- lint check
- diff review

Risk notes: code skills may request writes, tests, package commands, or git
operations. Sanitize them aggressively and require scoped workspaces.

### engineering

Purpose: project structure, build systems, deployment, CI/CD, containers,
performance, release flow, and operations hardening.

Subcategories:

- `engineering.build`: build and packaging workflow
- `engineering.deploy`: deployment planning and execution
- `engineering.ci`: CI/CD configuration and repair
- `engineering.container`: Docker and container workflow
- `engineering.performance`: speed, memory, and reliability work
- `engineering.observability`: logs, metrics, and incident triage

Typical verifiers:

- build check
- smoke test
- health check
- deployment diff
- rollback plan check

Risk notes: deployment and infrastructure actions are high risk. Require
explicit approval for network, credentials, infrastructure writes, and
production changes.

### security

Purpose: audit, harden, threat-model, detect prompt injection, protect secrets,
review sandbox policy, and inspect supply-chain risk.

Subcategories:

- `security.review`: source and dependency security review
- `security.prompt`: prompt injection and agent safety review
- `security.secrets`: secret detection and handling
- `security.policy`: permission and sandbox policy review
- `security.supply_chain`: package, skill, and connector supply-chain review
- `security.incident`: incident triage and evidence collection

Typical verifiers:

- secret scan
- dependency advisory check
- permission diff
- policy conformance check
- evidence completeness check

Risk notes: security skills must not exfiltrate secrets, exploit systems, or
perform active attacks unless a separately approved testing scope exists.

### office

Purpose: documents, spreadsheets, slides, reports, email drafts, meeting notes,
file conversion, and everyday office workflows.

Subcategories:

- `office.pdf`: PDF extraction, rendering, repair, and conversion
- `office.docx`: Word document creation and editing
- `office.sheet`: spreadsheet analysis and formatting
- `office.slides`: presentation creation and review
- `office.email`: email drafting and reply preparation
- `office.report`: structured reports and summaries

Typical verifiers:

- render check
- text extraction check
- schema check
- file hash check
- visual layout check

Risk notes: office skills often ask for broad filesystem access. Rewrite to
workspace-only inspection unless the user explicitly provides scoped inputs.

### execution

Purpose: run actual workflows through browser automation, file operations,
task queues, batch processing, publishing flows, and repeatable local actions.

Subcategories:

- `execution.browser`: browser inspection, form filling, and UI flow checks
- `execution.files`: bounded file scanning, copying, and batch processing
- `execution.pipeline`: multi-step task flow orchestration
- `execution.publish`: controlled publishing and release steps
- `execution.verify`: repeatable verification and evidence collection

Typical verifiers:

- action trace
- screenshot check
- filesystem diff
- output artifact check
- approval record check

Risk notes: execution skills carry the highest operational risk because they
try to make things happen. They must declare allowed tools, approved paths,
approved hosts, approval requirements, and verifier requirements.

## P1 Categories

### research

Purpose: gather, compare, summarize, and cite external information.

Subcategories:

- `research.web`: general web research
- `research.source`: primary-source verification
- `research.market`: market, competitor, and product research
- `research.academic`: papers, datasets, and technical literature
- `research.news`: time-sensitive news and event tracking

Typical verifiers:

- citation check
- source freshness check
- source type check
- claim-to-source mapping

Risk notes: research skills need network boundaries, source attribution, and
freshness rules. They should not scrape private systems or bypass robots,
paywalls, or authentication.

### data

Purpose: transform, validate, analyze, and report on structured data.

Subcategories:

- `data.clean`: data cleaning and normalization
- `data.sql`: SQL query and schema work
- `data.analysis`: statistical or business analysis
- `data.report`: dashboard, chart, and narrative report generation
- `data.pipeline`: local ETL and import/export workflow

Typical verifiers:

- schema validation
- row count check
- aggregate consistency check
- query dry run
- output diff

Risk notes: data skills may encounter private or regulated information. They
should minimize retention and avoid uploading data to external services.

### content

Purpose: create, edit, localize, and optimize written content.

Subcategories:

- `content.write`: articles, scripts, posts, and emails
- `content.edit`: rewrite, shorten, expand, and style match
- `content.seo`: keyword, GEO, and search optimization
- `content.localize`: translation and localization
- `content.brand`: brand voice and message consistency

Typical verifiers:

- format check
- style checklist
- source citation check
- originality check where available

Risk notes: content skills should avoid unsupported claims, hidden advertising,
copyright leakage, and source-free factual assertions.

### commerce

Purpose: product listing, catalog, marketplace, SKU, inquiry, and publishing
workflows.

Subcategories:

- `commerce.catalog`: product attributes and SKU structure
- `commerce.listing`: marketplace listing generation
- `commerce.icbu`: Alibaba International Station workflows
- `commerce.amazon`: Amazon marketplace workflows
- `commerce.publish`: multi-channel publishing checks

Typical verifiers:

- category rule check
- attribute completeness check
- forbidden-word check
- image and asset checklist
- marketplace policy checklist

Risk notes: marketplace skills need platform-specific policy references and
should not automate account-sensitive actions without approval.

### ai

Purpose: prompt design, model evaluation, agent behavior shaping, RAG, and
dataset preparation.

Subcategories:

- `ai.prompt`: prompt and system instruction design
- `ai.eval`: evaluation and benchmark workflow
- `ai.dataset`: dataset cleaning and labeling
- `ai.agent`: agent tool-use and planning patterns
- `ai.rag`: retrieval and knowledge-base workflow
- `ai.modelops`: model selection, cost, and routing guidance

Typical verifiers:

- eval run
- prompt injection check
- output schema check
- cost or token budget check
- benchmark report check

Risk notes: prompt skills are especially prone to policy override language.
Strip any instruction that tries to outrank system, developer, or kernel rules.

## P2 Categories

### business

Purpose: repeatable business workflows and internal operations.

Subcategories:

- `business.sales`: sales research, outreach, and CRM preparation
- `business.support`: customer support triage and reply drafting
- `business.ops`: SOP, checklist, and process automation
- `business.hr`: hiring, onboarding, and internal documents
- `business.procurement`: supplier, quote, and contract comparison

Typical verifiers:

- policy checklist
- source citation check
- tone and format check
- approval routing check

Risk notes: business skills often touch customer data and company policy. They
should avoid sending private data outside approved systems.

### media

Purpose: image, audio, video, game, and interactive media workflows.

Subcategories:

- `media.image`: image generation, editing, and asset preparation
- `media.video`: video generation, editing, and storyboard workflow
- `media.audio`: speech, music, and audio processing
- `media.game`: game logic, assets, and playtest workflow
- `media.presentation`: visual storytelling and media-heavy slides

Typical verifiers:

- asset existence check
- visual inspection
- format check
- render check
- rights and source checklist

Risk notes: media skills need copyright, likeness, and source-material rules.

### compliance

Purpose: controlled legal, finance, privacy, audit, and policy assistance.

Subcategories:

- `compliance.legal`: legal document review assistance
- `compliance.finance`: financial analysis and reporting support
- `compliance.privacy`: privacy and data handling checks
- `compliance.audit`: audit trail and control evidence
- `compliance.policy`: internal policy mapping

Typical verifiers:

- jurisdiction or policy scope check
- source citation check
- approval requirement check
- disclaimer and escalation check

Risk notes: these skills are advisory only. They must not present themselves as
legal, tax, accounting, medical, or compliance authority.

## P3 Categories

### vertical

Purpose: specialized workflows for industries or knowledge domains.

Subcategories:

- `vertical.education`
- `vertical.healthcare`
- `vertical.manufacturing`
- `vertical.energy`
- `vertical.realestate`
- `vertical.construction`
- `vertical.logistics`
- `vertical.government`

Typical verifiers:

- domain checklist
- source citation check
- safety escalation check
- human review requirement

Risk notes: vertical skills should be collected only after the general
sanitizer pipeline is stable, because many domains carry high-stakes decisions.

## Collection Order

The first collection wave should focus on:

1. `design`
2. `code`
3. `engineering`
4. `security`
5. `office`
6. `execution`
7. `research`
8. `ai`
9. `content`
10. `commerce`

This order matches OneCode's current strength: local file work, evidence,
verification, guarded execution, and practical engineering workflows.

## Selection Rule

At task time, choose skills by intersection:

```text
user task intent
  intersection category and subcategory
  intersection artifact type
  intersection allowed tools
  intersection required verifier availability
  intersection risk policy
  intersection workspace and host capability
```

If multiple skills match, prefer:

- lower risk
- narrower scope
- stronger verifier coverage
- newer sanitized version
- clearer source provenance

If no trusted skill matches, OneCode should run without a skill or ask for
review instead of loading an untrusted one.

## Directory Naming

Sanitized skills should use stable category directories:

```text
skills/
  design/react-dashboard/
  code/python-debug/
  engineering/docker-build/
  security/prompt-injection-review/
  office/pdf-render-check/
  execution/browser-form-flow/
  research/primary-source/
  ai/output-schema-eval/
  commerce/icbu-listing/
```

The directory name is classification metadata, not a permission grant.
