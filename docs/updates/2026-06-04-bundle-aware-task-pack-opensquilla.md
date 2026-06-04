# Update Statement: Bundle-Aware Task Packs and OpenSquilla Reference Batch

Date: 2026-06-04

Repository:

```text
https://github.com/aidi1723/safe-agent-skills
```

## Summary

This update moves `Safe-Agent-Skills` from a verified skill catalog into a
more practical cross-agent skill routing system.

The repository now supports:

- automatic task-to-skill selection through `task-pack`
- trusted scenario bundle matching through `task-pack --include-bundles`
- catalog and bundle integrity checks through `maintain-check`
- a new OpenSquilla-inspired reference batch
- a clearer safety boundary for Claude, Codex, OpenClaw, Cursor, MCP hosts,
  local agents, and custom agents

Current public baseline:

```text
total skills: 75
trusted skills: 70
quarantined skills: 3
review_required skills: 2
scenario bundles: 9
top-level categories: 15 / 15
minimum trusted coverage: 3 trusted skills per category
tampered skills: 0
unknown provenance records: 0
registry verification: ok
bundle maintenance check: ok
```

## What Changed

### 1. Task packs can now include trusted scenario bundles

Agents can already ask the sanitizer to choose useful skills for a task:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer task-pack \
  "design a RAG document agent with vector retrieval and citation checks" \
  --registry catalog \
  --top 5 \
  --format json
```

This release adds scenario-aware output:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer task-pack \
  "design a RAG document agent with vector retrieval and citation checks" \
  --registry catalog \
  --top 5 \
  --include-bundles \
  --bundles bundles/index.json \
  --format json
```

The agent receives both:

- the best matching trusted individual skills
- the best matching trusted scenario bundles

Example result for a RAG knowledge task:

```text
selected skills:
- ai-llamaindex-rag-knowledge-workflow
- ai-qwen-agent-tool-workflow
- ai-langchain-agent-orchestration
- ai-autogen-multi-agent-review
- ai-crewai-role-workflow

selected bundles:
- rag-agent-knowledge-app
- document-to-knowledge-base
```

This is the core capability of the tool: an agent can describe a task, then
receive a cleaned, provenance-recorded, OneCode-verified skill pack instead of
manually searching community prompts.

### 2. Scenario bundles are now protected by maintenance checks

The new `maintain-check` command verifies that trusted bundles do not silently
reference unsafe catalog entries.

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check \
  --registry catalog \
  --bundles bundles/index.json
```

The check fails if a trusted bundle references:

- a missing skill
- a non-trusted skill
- a tampered skill
- a catalog with missing provenance

This keeps scenario bundles from becoming a backdoor into unreviewed skill
instructions.

### 3. OpenSquilla reference skills were added

This release added `batch-008-opensquilla-reference` with three trusted,
reference-style skills:

| Skill | Category | Status | What it preserves |
| --- | --- | --- | --- |
| `ai-opensquilla-metaskill-workflow` | ai | trusted | Reusable MetaSkill workflow planning pattern |
| `ai-opensquilla-token-routing-pattern` | ai | trusted | On-demand skill loading and token routing pattern |
| `security-opensquilla-sandbox-policy` | security | trusted | Sandbox-first execution and refusal boundary pattern |

Source record:

```text
source: https://opensquilla.ai/
author: OpenSquilla community
license: Apache-2.0
```

Important boundary: these entries are reference-style rewrites. They preserve
useful workflow ideas, but do not copy OpenSquilla runtime code, do not bundle
third-party connectors, and do not grant runtime permissions.

## Safety Statement

The skills in this repository come from community projects, engineering
practice, and curated workflow references. They are not published as raw,
unverified prompts.

Published `trusted` skills have passed the current OneCode safety validation
and cleaning workflow:

- source and author recording
- license and reference recording
- static risk scanning
- dangerous instruction cleanup
- status review
- sanitized hash recording
- registry verification
- bundle maintenance checks where applicable

The result is safer and more reliable than copying unknown prompts or agent
instructions directly from the internet.

The security boundary remains explicit:

```text
skill guidance is method, not execution authority
```

A skill can tell an agent how to perform a task. It cannot automatically grant
filesystem, shell, network, browser, connector, account, credential, trading,
deployment, or production write permissions. Those permissions remain
controlled by the host runtime, such as OneCode, Claude, Codex, OpenClaw,
Cursor, MCP hosts, local sandboxes, or custom agent systems.

## Cross-Agent Usage

This repository is designed as a universal skill source. It is not tied to a
single agent product.

Supported consumption patterns:

- Claude can read `SKILL.md` files or Markdown task packs.
- Codex can read `SKILL.md` files or generated task packs.
- OpenClaw and other local agents can load the JSON output.
- Cursor and coding agents can use selected skills as task context.
- MCP hosts can expose `task-pack` as a read-only skill selection tool.
- Custom agents can call the CLI and enforce their own runtime permissions.

The common rule is that the catalog supplies cleaned method guidance; the host
supplies execution policy.

## Published Documents

Main public docs:

- [README](../../README.md)
- [Open Source Statement](../open-source-statement.md)
- [Agent Task Pack](../agent-task-pack.md)
- [Agent-Compatible Skill Bundles](../agent-compatible-skill-bundles.md)
- [Skill Bundles](../skill-bundles.md)
- [Catalog Status](../catalog-status.md)
- [Batch 008: OpenSquilla Reference](../batches/batch-008-opensquilla-reference.md)

## Verification Evidence

Release gate:

```bash
bash scripts/verify.sh
PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry catalog
PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check --registry catalog --bundles bundles/index.json
git diff --check
```

Expected release result:

```text
tests: pass
registry verification: ok
bundle maintenance check: ok
diff whitespace check: ok
```

## Maintenance Direction

Next collection waves should continue using the same rule:

- every skill must record source, author, license, reference, and collector
- every community project entry should be rewritten as safe method guidance
- no third-party runtime code should be copied into the trusted catalog
- no skill should receive runtime permissions by being listed
- `review_required` and `quarantined` entries must stay out of default
  selection and trusted bundles

The next practical milestone is to grow `batch-009-community-depth` and
`batch-010-domain-depth` while preserving the same verification standard.
