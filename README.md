# OneCode Skill Sanitizer

OneCode Skill Sanitizer is a standalone project for turning external or community skill material, local seed workflows, and reference-derived guidance into OneCode-governed skill instructions.

Its purpose is not to execute third-party skills directly. Its purpose is to preserve useful domain workflows while applying deterministic risk preflight checks, provenance records, review status, hash verification, and explicit execution boundaries. The scanner is a guardrail and review aid; it is not a complete malware detector or a substitute for host-runtime sandboxing.

The CLI can also be used independently of OneCode. Users can bring their own
`incoming/` skill folders, build a private or public `registry/`, approve their
own trusted skills, and generate JSON or Markdown task packs for any host
agent. See [Standalone Tool Open Source Statement](docs/standalone-tool-open-source.md).

## Maintenance Boundary

Maintain this repository as its own checkout, separate from any host runtime or
core agent repository. Future skill catalog, router, documentation,
verification, commit, and release work should happen from this standalone
repository checkout. See [Workspace Boundary](docs/workspace-boundary.md).

## Recommended Entry: Install One Router Skill

The recommended user-facing entry is `safe-agent-router`, published inside
this main repository:

```text
integrations/skills/safe-agent-router/
```

Users do not need to install or combine every catalog skill manually. Install
this one router skill, then let it select the right OneCode-verified trusted
skills and scenario bundle for each task.

```bash
integrations/skills/safe-agent-router/scripts/install.sh ~/.codex/skills
```

For Claude Code:

```bash
integrations/skills/safe-agent-router/scripts/install.sh ~/.claude/skills
```

After installation:

```bash
safe-agent-router-task-pack "build a product website and prepare launch checks"
```

Current publishing decision: keep the router skill in this main repository as
the primary entry point, because it depends on the same `catalog/`, `bundles/`,
provenance records, trusted status, hash checks, and OneCode safety rules. See
[Router Skill Primary Entry](docs/router-skill-primary-entry.md).

## Open Source Statement

This project is a public-safe skill catalog and sanitizer for AI agents. It is
designed to turn scattered community skills into provenance-recorded,
policy-bounded, hash-verifiable, and maintainable `trusted` skill assets.

All published catalog skills have passed the current OneCode governance
workflow: provenance recording, deterministic static risk scanning, status
review, sanitized hash recording, and registry verification. Many community
entries are locally authored reference skills inspired by public projects, not
verbatim imports from those repositories. This makes the project safer and more
auditable than copying unverified prompts or agent instructions directly from
the open internet, but it should not be treated as a standalone security
sandbox.

Current public baseline:

- 109 total skills
- 103 trusted skills
- 10 trusted scenario bundles
- 7 trusted-only skill overlap groups
- 15 / 15 top-level categories covered
- at least 3 trusted skills in every top-level category
- 0 tampered skills
- 0 unknown provenance records

See [Open Source Statement](docs/open-source-statement.md) for the full project
positioning and contribution stance.

Latest update statement:
[Structural Scanner Hardening](docs/updates/2026-06-12-structural-scanner-hardening.md).

Previous update:
[Consistency Rule Hardening](docs/updates/2026-06-12-consistency-rule-hardening.md).

Phase 001 is closed and ready for public maintenance. See
[Phase 001 Closure Report](docs/phase-001-closure-report.md).

Phase 002 scenario routing is closed for today's delivery. See
[Phase 002 Scenario Router Closure Report](docs/phase-002-scenario-router-closure-report.md).

The audit hardening cycle is closed. See
[Audit Hardening Closure Report](docs/audit-hardening-closure-report.md) and
[Next Development Plan](docs/next-development-plan.md).

## Core Position

Skills provide method.

OneCode provides boundary, execution control, verification, and evidence.

When used outside OneCode, the host agent or operating environment provides
that boundary. The sanitizer still records provenance, cleans risky
instructions, verifies hashes, and emits bounded task packs, but it does not
grant runtime permissions.

This project is designed to stay usable even when the host product changes.
It does not assume that every OneCode or AgentCore OS runtime already exposes
the same connector, vault, publishing, or sandbox APIs. Those integrations must
be bound through explicit adapters.

The sanitizer sits between untrusted skill sources and the OneCode skill registry:

```text
external skill
  -> source capture
  -> deterministic risk preflight scan
  -> instruction distillation
  -> policy rewrite or bounded local synthesis
  -> verifier binding
  -> evidence manifest
  -> quarantined registry entry
  -> approval
  -> trusted OneCode skill
```

## First Principle

No imported skill is trusted by default.

Every external skill starts in `quarantined` state. It can become `trusted` only after the sanitizer produces a manifest, a sanitization report, and a clean deterministic risk scan under OneCode policy.

`trusted` means the skill has passed the current OneCode safety validation and
review process. It does not mean the source is perfectly safe, and it does not
grant unrestricted runtime permissions:
connectors, filesystem access, network access, and production actions still
belong to the host runtime's approval and policy layer.

## What Is Preserved

- task scope
- useful domain workflow
- input and output expectations
- verification requirements
- failure handling guidance
- reference material
- safe tool suggestions
- concise examples

## What Is Removed

- direct destructive commands
- shell download-and-execute patterns
- requests to disable sandboxing, approval, or verification
- instructions to ignore higher-priority policies
- secrets, tokens, and private credentials
- broad filesystem access
- unbounded network access
- hidden persistence or self-modifying behavior
- long non-operational explanation
- conflicting or ambiguous execution instructions

## Local CLI

From this folder, use:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer --help
```

```bash
onecode-skill-sanitizer scan ./incoming/pdf-skill
onecode-skill-sanitizer sanitize ./incoming/pdf-skill --out ./registry/pdf \
  --source-url https://github.com/example/skills/pdf \
  --source-usage source_import \
  --author example-team \
  --license MIT \
  --reference https://github.com/example/skills \
  --collected-by onecode-local
onecode-skill-sanitizer audit ./registry/pdf
onecode-skill-sanitizer approve ./registry/pdf
```

Every scan and sanitize report records provenance. `source.usage` records the
relationship to the cited source: `source_import` for imported content,
`reference_only` for external projects used only as inspiration or comparison,
and `local_authoring` for local seed workflows. Missing provenance values are
written as `unknown`, not omitted.

Batch registry workflow:

```bash
onecode-skill-sanitizer import ./incoming --registry ./registry \
  --collected-by onecode-local
onecode-skill-sanitizer list --registry ./registry
onecode-skill-sanitizer inspect office-pdf --registry ./registry
onecode-skill-sanitizer select "process a pdf report" --registry ./registry
onecode-skill-sanitizer task-pack "process a pdf report" --registry ./registry \
  --top 3 \
  --format json
onecode-skill-sanitizer verify --registry ./registry
onecode-skill-sanitizer maintain-check --registry ./registry --bundles ./bundles/index.json
onecode-skill-sanitizer reindex --registry ./registry
```

Review workflow:

```bash
onecode-skill-sanitizer approve ./registry/office/office-pdf
onecode-skill-sanitizer reject ./registry/security/unsafe-skill
onecode-skill-sanitizer disable ./registry/office/old-skill
```

`select` returns only `trusted` skills by default. Use
`--include-review-required` only for review work, not normal execution.

`task-pack` is the universal Agent-facing interface. It verifies the registry,
selects matching trusted skills, loads their sanitized `SKILL.md` instructions,
and emits a JSON or Markdown instruction pack that any host Agent can place in
its planning context. The pack provides method, verifier expectations, and
provenance. It does not grant filesystem, network, connector, shell, or
production permissions; those remain controlled by the host runtime.

`task-pack --include-bundles` can also include matching trusted scenario
bundles, so a host Agent receives both individual skill guidance and a larger
task playbook when the task matches a known workflow.

For the simplest default entry, use `smart`. The name is a convenience label:
selection is deterministic, non-LLM routing over trusted catalog metadata,
scenario signals, overlap groups, and invariant hints:

```bash
onecode-skill-sanitizer smart \
  "build a landing page and prepare launch checks" \
  --invariants "不能泄露密钥；公开文案必须合规；必须响应式验证"
```

`smart` returns the same task-pack structure plus a mesh execution graph,
invariant capability coverage, and overlap-pruned skill list. See
[Smart Skill Router](docs/smart-skill-router.md).

For vague or unsupported repository-maintenance tasks, `smart` is conservative:
if the task does not match a trusted scenario signal, it leaves
`selected_scenario.id` empty and returns only directly matched trusted skills.

For more precise task-aware composition, use the deterministic scenario router:

```bash
onecode-skill-sanitizer task-pack "build a product website and prepare launch checks" \
  --registry ./registry \
  --include-bundles \
  --bundles ./bundles/index.json \
  --router scenario \
  --max-skills 8 \
  --format json
```

`--router scenario` adds a task profile, selected scenario, capability
coverage, ordered execution plan, and selection explanations. It still does
not grant filesystem, network, connector, shell, browser, or production
permissions.

Scenario bundles in `bundles/` combine multiple trusted skills for common
workflows such as website launch, code review hardening, document-to-knowledge
base, RAG agent design, data analysis, open source release, and commerce
listing growth.

Functional overlap between trusted skills is recorded in
[`catalog/overlap-groups.json`](catalog/overlap-groups.json) and explained in
[Skill Overlap Groups](docs/skill-overlap-groups.md). This is a selection hint
layer for routers and operators, not a deletion or merge list.

These skills and bundles are agent-compatible by design. Claude, Codex,
OpenClaw, Cursor, local agents, MCP hosts, CI workers, and custom agent
systems can consume the same sanitized Markdown or JSON task packs. The safety
rule stays the same across all hosts: skill guidance is method, not execution
authority. See [Agent-Compatible Skill Bundles](docs/agent-compatible-skill-bundles.md).

Agents can also install the single router skill:
[Safe Agent Router Skill Integration](docs/router-skill-integration.md).
After installing `safe-agent-router`, a host agent does not need the operator
to manually choose, combine, or install every other catalog skill. The router
selects the best trusted skills and scenario bundle for the task, then returns
a task pack with the execution order, verifier expectations, source records,
and safety boundary.

This is the recommended default integration model:

```text
install one skill -> route every non-trivial task -> use selected trusted skill pack
```

The first MVP can also be exposed through OneCode:

```bash
onecode skills sanitize --source ./incoming/pdf-skill --out ./skills/pdf
onecode skills audit ./skills/pdf
onecode skills approve pdf
```

## Project Docs

- [Workspace Boundary](docs/workspace-boundary.md)
- [Source Baseline](docs/source-baseline.md)
- [Smart Skill Router](docs/smart-skill-router.md)
- [Audit Hardening Closure Report](docs/audit-hardening-closure-report.md)
- [Next Development Plan](docs/next-development-plan.md)
- [External Reference Roadmap](docs/external-reference-roadmap.md)
- [Scheduler Hardening Roadmap](docs/scheduler-hardening-roadmap.md)
- [Latest Domain Guardrails Update](docs/updates/2026-06-05-domain-guardrails.md)
- [Latest Verification Hardening Update](docs/updates/2026-06-05-verification-hardening.md)
- [Latest Router Skill Update](docs/updates/2026-06-05-router-skill-single-entry.md)
- [Router Skill Primary Entry](docs/router-skill-primary-entry.md)
- [Scenario Skill Router Update](docs/updates/2026-06-04-scenario-skill-router.md)
- [Phase 002 Scenario Router Closure Report](docs/phase-002-scenario-router-closure-report.md)
- [Previous Update Statement](docs/updates/2026-06-04-bundle-aware-task-pack-opensquilla.md)
- [Agent Task Pack](docs/agent-task-pack.md)
- [Agent-Compatible Skill Bundles](docs/agent-compatible-skill-bundles.md)
- [Safe Agent Router Skill Integration](docs/router-skill-integration.md)
- [Standalone Tool Open Source Statement](docs/standalone-tool-open-source.md)
- [Phase 001 Closure Report](docs/phase-001-closure-report.md)
- [Architecture](docs/architecture.md)
- [Skill Taxonomy](docs/skill-taxonomy.md)
- [Skill Index](docs/skill-index.md)
- [Skill Bundles](docs/skill-bundles.md)
- [Sanitization Policy](docs/sanitization-policy.md)
- [MVP Roadmap](docs/mvp-roadmap.md)
- [Implementation Plan](docs/implementation-plan.md)
- [Operator Guide](docs/operator-guide.md)
- [Catalog Status](docs/catalog-status.md)
- [Maintenance Guide](docs/maintenance-guide.md)
- [Open Source Statement](docs/open-source-statement.md)
- [Skill Manifest Schema](schemas/skill-manifest.schema.json)
- [Registry Index Schema](schemas/registry-index.schema.json)
- [Verify Report Schema](schemas/verify-report.schema.json)
- [Example Sanitization Report](examples/sanitization-report.example.json)
- [Example Registry Index](examples/registry-index.example.json)
- [Example Verify Report](examples/verify-report.example.json)

## Verify

```bash
bash scripts/verify.sh
```
