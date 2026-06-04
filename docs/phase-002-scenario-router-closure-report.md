# Phase 002 Scenario Router Closure Report

Date: 2026-06-04

## Status

Phase 002 is closed for today's delivery.

This phase upgraded `Safe-Agent-Skills` from a verified catalog and
bundle-aware task-pack generator into a deterministic scenario routing system.
The repository can now select a trusted scenario bundle, map task capabilities
to trusted skills, produce an ordered execution plan, and explain why each
skill was selected.

Repository:

```text
https://github.com/aidi1723/safe-agent-skills
```

## Public Baseline

Current catalog baseline:

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
scenario router: available
```

## What Was Delivered

### 1. Deterministic Skill Router

New module:

```text
src/onecode_skill_sanitizer/router.py
```

The router provides:

- task normalization
- deterministic task profiling
- scenario bundle scoring
- capability coverage generation
- execution plan generation
- selection explanations
- scenario task routing

It does not call external models and does not require network access.

### 2. Scenario Router CLI Mode

`task-pack` now supports:

```bash
--router scenario
--max-skills N
```

Example:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer task-pack \
  "build a product website and prepare launch checks" \
  --registry catalog \
  --include-bundles \
  --bundles bundles/index.json \
  --router scenario \
  --max-skills 8 \
  --format json
```

The existing simple mode remains available and backward compatible:

```bash
--router simple
```

### 3. Router Metadata For Scenario Bundles

All 9 trusted scenario bundles now include routing metadata:

- `task_signals`
- `required_capabilities`
- `execution_order`

This lets the router choose a scenario first, then compose the skills needed
for that scenario rather than relying only on keyword overlap.

### 4. Cross-Agent Documentation

Updated docs explain how agents can use the router safely:

- `README.md`
- `docs/agent-task-pack.md`
- `docs/agent-compatible-skill-bundles.md`

The docs state clearly that router output is method guidance only and does not
grant runtime permissions.

### 5. Design And Implementation Records

Design and execution records were added:

- `docs/superpowers/specs/2026-06-04-skill-router-design.md`
- `docs/superpowers/plans/2026-06-04-skill-router.md`

These files preserve the reasoning, implementation boundary, testing plan, and
future maintenance direction.

## Verification Evidence

Commands run:

```bash
bash scripts/verify.sh
PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry catalog
PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check --registry catalog --bundles bundles/index.json
git diff --check HEAD
```

Verified result:

```text
tests: 34 passed
registry status: ok
skill_count: 75
trusted_count: 70
tampered_count: 0
unknown_provenance_count: 0
bundle_count: 9
trusted_bundle_count: 9
bundle issues: 0
```

Scenario sample checks:

```text
build a product website and prepare launch checks
  -> website-build-launch

design a RAG document agent with vector retrieval and citation checks
  -> rag-agent-knowledge-app
```

## What Is Not Claimed

This phase does not claim:

- automatic execution of selected skills
- automatic filesystem, shell, network, browser, connector, account, or
  production permissions
- LLM-based routing
- autonomous community crawling
- legal approval of every upstream project beyond recorded source/license
  metadata
- safety for financial, medical, legal, or production actions without host
  approval

The router supplies deterministic method selection. The host runtime still
controls execution.

## Safety Boundary

The fixed rule remains:

```text
skill guidance is method, not execution authority
```

This applies to:

- individual skills
- scenario bundles
- task packs
- scenario router output
- host-agent integration

## Maintenance Rules After This Phase

Future maintainers should preserve these rules:

- Do not add a trusted bundle that references non-trusted skills.
- Do not route `quarantined`, `rejected`, or `disabled` skills.
- Use `--include-review-required` only for review work.
- Keep router selection deterministic unless a future mode explicitly states
  that model-assisted ranking is being used.
- Keep source, author, license, reference, collector, and hash records for
  every skill.
- Run `maintain-check` after changing bundles.
- Run both website and RAG scenario samples before publishing router changes.

## Next Phase

Recommended next phase:

1. Add `batch-009-community-depth` with more high-value community skill
   references that have clear source and license records.
2. Add `batch-010-domain-depth` for deeper design, code, security, office,
   research, and commerce workflows.
3. Add router evaluation fixtures for more scenarios.
4. Add optional host-agent integration examples for Codex, Claude, OpenClaw,
   MCP hosts, and custom local agents.

## Closure Decision

Phase 002 scenario routing is complete for today's delivery.

The repository is ready to continue as a public safe skill catalog, sanitizer,
scenario bundle library, and deterministic cross-agent skill router.
