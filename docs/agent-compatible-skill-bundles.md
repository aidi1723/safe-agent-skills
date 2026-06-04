# Agent-Compatible Skill Bundles

## Purpose

Safe Agent Skills is designed as a cross-agent skill layer.

The catalog does not depend on one specific runtime. Claude, Codex, OpenClaw,
Cursor, local agents, MCP hosts, CI workers, and custom agent systems can all
consume the same cleaned skill instructions as long as they can read Markdown
or JSON.

## Two Ways Agents Can Use Skills

### 1. Read Skills Directly

Every catalog entry has a cleaned `SKILL.md` file. A host agent can read that
file as a normal instruction document.

Each skill explains:

- when to use it
- what capability it provides
- safe workflow
- expected output
- verifier expectations
- failure handling
- source, author, license, and hash records

This is useful for agents that already have their own skill-loading mechanism.

### 2. Use Task Packs

`task-pack` is the universal agent-facing interface.

It receives a natural-language task, verifies the registry, selects matching
`trusted` skills, and emits a JSON or Markdown instruction pack that any host
agent can place in its planning context.

Example:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer task-pack \
  "build a product website and prepare launch checks" \
  --registry catalog \
  --top 5 \
  --include-bundles \
  --bundles bundles/index.json \
  --format markdown
```

The generated pack contains selected skill names, matching trusted scenario
bundles, capability descriptions, safe workflows, expected outputs, verifier
expectations, provenance records, and sanitized hashes.

For task-aware composition, use the deterministic scenario router:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer task-pack \
  "build a product website and prepare launch checks" \
  --registry catalog \
  --include-bundles \
  --bundles bundles/index.json \
  --router scenario \
  --max-skills 8 \
  --format markdown
```

This adds a task profile, selected scenario, capability coverage, ordered
execution plan, and selection explanations.

## Scenario Bundles

A single skill is a focused capability. A scenario bundle is a proven
combination of trusted skills for a larger real-world task.

Current default bundles:

| Bundle | Scenario |
| --- | --- |
| `website-build-launch` | Build or polish a website, add content and SEO checks, verify in browser, and prepare release. |
| `code-review-hardening` | Review generated code, tests, schema contracts, dependency risk, sandbox boundaries, and CI readiness. |
| `security-agent-guardrails` | Review an agent, connector, prompt, or workflow for prompt injection, I/O scanning, and safety boundaries. |
| `document-to-knowledge-base` | Convert PDFs, office files, and mixed documents into Markdown, chunks, summaries, and retrieval-ready notes. |
| `rag-agent-knowledge-app` | Design a source-grounded RAG or knowledge-base agent with retrieval, citations, structured outputs, and safety checks. |
| `data-analysis-report` | Clean data, analyze tables, plan visuals, and write a decision report. |
| `open-source-release` | Prepare a public repository, docs, safety statement, and release handoff. |
| `content-seo-publication` | Draft, fact-check, optimize, and publish public content. |
| `commerce-listing-growth` | Prepare marketplace listings, keyword plans, buyer replies, and trade communication. |

Bundle definitions live in:

- `bundles/README.md`
- `bundles/index.json`

Default bundles only reference `trusted` skills. `review_required`,
`quarantined`, `rejected`, and `disabled` skills are excluded.

Scenario bundles can include optional router metadata:

- `task_signals`: words or phrases that identify the scenario
- `required_capabilities`: capabilities that should be covered by selected skills
- `execution_order`: recommended skill order for host-agent planning

When `task-pack --router scenario` is used, the router chooses the closest
trusted bundle, maps capabilities to trusted skills, and emits an execution
plan. This keeps the agent's task flow more consistent than selecting skills
by keyword overlap alone.

## Cross-Agent Safety Boundary

Safe Agent Skills gives agents method, not authority.

A skill or bundle can tell an agent how to approach a task. It cannot grant:

- filesystem permissions
- shell permissions
- network permissions
- browser permissions
- connector permissions
- account access
- production write access

Those permissions must remain controlled by the host runtime: Claude, Codex,
OpenClaw, Cursor, OneCode, an MCP host, a CI runner, or a custom sandbox.

The fixed rule is:

```text
skill guidance is not execution authority
```

## Recommended Integration Pattern

1. Receive the user task.
2. Run `maintain-check --registry catalog --bundles bundles/index.json`.
3. Run `task-pack --include-bundles --router scenario` or load a matching
   scenario bundle.
4. Inject the generated instructions into the agent planning context.
5. Let the host runtime enforce filesystem, network, shell, connector, and
   production permissions.
6. Run the verifier expectations listed by the selected skills.
7. Record selected skill names, source URLs, and sanitized hashes in the final
   task report.

## Example Agent Usage

### Claude or Claude Code

Use Markdown output from `task-pack --include-bundles`, then place the
generated instructions in the task context or project instructions.

### Codex

Use Markdown or JSON output from `task-pack --include-bundles`, then let Codex
execute under its normal workspace, approval, and verification policy.

### OpenClaw or Custom Agents

Load `bundles/index.json` or call `task-pack` before planning. Treat selected
skills as planning guidance only. Tool execution still requires the host
runtime's own permission checks.

### MCP Hosts

Expose `task-pack` as a read-only planning helper. Do not let selected skills
expand tool scopes. MCP server permissions must be reviewed and approved
separately.

## Public Release Position

This repository can be published as a shared safe skill layer for the agent
ecosystem:

```text
community project skills
  -> OneCode safety validation and cleaning
  -> trusted catalog
  -> task-pack or scenario bundle
  -> Claude / Codex / OpenClaw / Cursor / custom agent
  -> host runtime permission control
```

The value is not that every agent becomes identical. The value is that
different agents can share the same cleaned, sourced, hash-verifiable task
methods while keeping their own safety controls.
