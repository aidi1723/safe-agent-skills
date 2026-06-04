# OneCode Skill Sanitizer

OneCode Skill Sanitizer is a standalone project for turning external or community skills into OneCode-governed skill instructions.

Its purpose is not to execute third-party skills directly. Its purpose is to preserve useful domain workflows while removing unsafe commands, privilege-escalation instructions, hidden dependencies, secret leakage, and content that conflicts with OneCode's execution rules.

The CLI can also be used independently of OneCode. Users can bring their own
`incoming/` skill folders, build a private or public `registry/`, approve their
own trusted skills, and generate JSON or Markdown task packs for any host
agent. See [Standalone Tool Open Source Statement](docs/standalone-tool-open-source.md).

## Open Source Statement

This project is a public-safe skill catalog and sanitizer for AI agents. It is
designed to turn scattered community skills into provenance-recorded,
policy-bounded, hash-verifiable, and maintainable `trusted` skill assets.

All published catalog skills have passed the OneCode safety validation and
cleaning workflow: provenance recording, static risk scanning,
unsafe-instruction cleanup, status review, sanitized hash recording, and
registry verification. This makes the project safer and more reliable than
copying unverified prompts or agent instructions directly from the open
internet.

Current public baseline:

- 72 total skills
- 67 trusted skills
- 15 / 15 top-level categories covered
- at least 3 trusted skills in every top-level category
- 0 tampered skills
- 0 unknown provenance records

See [Open Source Statement](docs/open-source-statement.md) for the full project
positioning and contribution stance.

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
  -> static risk scan
  -> instruction distillation
  -> policy rewrite
  -> verifier binding
  -> evidence manifest
  -> quarantined registry entry
  -> approval
  -> trusted OneCode skill
```

## First Principle

No imported skill is trusted by default.

Every external skill starts in `quarantined` state. It can become `trusted` only after the sanitizer produces a manifest, a sanitization report, and a clean risk scan under OneCode policy.

`trusted` means the skill has passed the current OneCode safety validation and
cleaning process. It does not grant unrestricted runtime permissions:
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
  --author example-team \
  --license MIT \
  --reference https://github.com/example/skills \
  --collected-by onecode-local
onecode-skill-sanitizer audit ./registry/pdf
onecode-skill-sanitizer approve ./registry/pdf
```

Every scan and sanitize report records provenance. Missing values are written
as `unknown`, not omitted.

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
selects matching trusted skills, loads their cleaned `SKILL.md` instructions,
and emits a JSON or Markdown instruction pack that any host Agent can place in
its planning context. The pack provides method, verifier expectations, and
provenance. It does not grant filesystem, network, connector, shell, or
production permissions; those remain controlled by the host runtime.

Scenario bundles in `bundles/` combine multiple trusted skills for common
workflows such as website launch, code review hardening, document-to-knowledge
base, data analysis, open source release, and commerce listing growth.

The first MVP can also be exposed through OneCode:

```bash
onecode skills sanitize --source ./incoming/pdf-skill --out ./skills/pdf
onecode skills audit ./skills/pdf
onecode skills approve pdf
```

## Project Docs

- [Source Baseline](docs/source-baseline.md)
- [Agent Task Pack](docs/agent-task-pack.md)
- [Standalone Tool Open Source Statement](docs/standalone-tool-open-source.md)
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
