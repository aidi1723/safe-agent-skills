# Update Statement: Scenario Skill Router

Date: 2026-06-04

Repository:

```text
https://github.com/aidi1723/safe-agent-skills
```

## Summary

This update adds the deterministic Scenario Skill Router to
`Safe-Agent-Skills`.

The project can now do more than select individual skills by keyword score.
With `task-pack --router scenario`, an agent can describe a task and receive a
scenario-aware skill composition:

- task profile
- selected trusted scenario bundle
- capability coverage
- ordered execution plan
- selection explanations
- trusted skill instructions
- unchanged safety boundary

This is the first practical version of the repository's core product promise:
agents can automatically choose and combine useful community-derived skills
that have been recorded, verified, and cleaned under OneCode safety rules.

## New Command

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

## What The Router Adds

Scenario router output includes:

```text
router
task_profile
selected_scenario
coverage
execution_plan
selection_explanations
```

Example: a website launch task selects `website-build-launch` and composes:

```text
business-requirements-brief
engineering-build-release
design-ui-review
design-system-consistency
content-seo-brief
execution-browser-check
execution-playwright-browser-automation
execution-publish-check
```

Example: a RAG document agent task selects `rag-agent-knowledge-app` and
composes:

```text
business-requirements-brief
ai-langchain-agent-orchestration
ai-llamaindex-rag-knowledge-workflow
data-haystack-rag-pipeline
data-qdrant-vector-retrieval
ai-pydantic-schema-contract
ai-output-schema-eval
research-source-check
```

## Why This Matters

The repository is no longer only a cleaned skill catalog.

It now has a universal, deterministic routing capability that any host agent
can call before planning a task. Claude, Codex, OpenClaw, Cursor, local
agents, MCP hosts, CI workers, and custom agents can consume the same task
pack output while keeping their own runtime permission controls.

The practical value is:

- less manual searching for prompts or skills
- better task-specific skill combinations
- clearer execution order
- visible coverage gaps
- explainable selection reasons
- stable safety boundaries across host agents

## Safety Boundary

The security rule remains unchanged:

```text
skill guidance is method, not execution authority
```

The router chooses skills and orders them. It does not execute them.

It does not grant:

- filesystem permissions
- shell permissions
- network permissions
- browser permissions
- connector permissions
- account access
- credential access
- production write access

Those permissions remain controlled by the host runtime.

## Verification Evidence

Release gate:

```bash
bash scripts/verify.sh
PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry catalog
PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check --registry catalog --bundles bundles/index.json
git diff --check HEAD
```

Latest verified result:

```text
tests: 34 passed
skill_count: 75
trusted_count: 70
tampered_count: 0
unknown_provenance_count: 0
trusted_bundle_count: 9
bundle issues: 0
```

Scenario samples verified:

```text
website task -> website-build-launch
RAG task -> rag-agent-knowledge-app
```

## Files Added Or Updated

Core implementation:

- `src/onecode_skill_sanitizer/router.py`
- `src/onecode_skill_sanitizer/cli.py`
- `tests/test_router.py`
- `tests/test_registry_cli.py`

Routing metadata:

- `bundles/index.json`

Docs:

- `docs/agent-task-pack.md`
- `docs/agent-compatible-skill-bundles.md`
- `README.md`
- `docs/superpowers/specs/2026-06-04-skill-router-design.md`
- `docs/superpowers/plans/2026-06-04-skill-router.md`

## Maintenance Notes

Future bundle changes should preserve these rules:

- trusted bundles must reference only trusted skills
- every scenario bundle should define task signals when routing precision
  matters
- every scenario bundle should define capability coverage when the task has a
  known workflow
- `review_required` and `quarantined` skills must stay out of default routing
- router output must remain deterministic unless an explicit future mode adds
  model-assisted ranking

Recommended next phase:

```text
batch-009-community-depth
batch-010-domain-depth
router evaluation fixtures
optional host-agent integration examples
```
