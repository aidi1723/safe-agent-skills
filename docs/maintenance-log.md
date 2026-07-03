# Maintenance Log

Date: 2026-07-03

## Current Maintained Baseline

```text
branch: main
catalog skills: 172
trusted skills: 166
trusted scenario bundles: 23
external references: 19
trusted overlap groups: 7
tracked claude-skills candidates: 336
covered claude-skills candidates: 336
router eval cases: 34
verification command: bash scripts/verify.sh
```

## 2026-07-03 Reference Pattern Expansion

Added five trusted, locally authored method skills based on external reference
project review:

- `research-multi-platform-search-boundary`
- `business-value-investment-research-framework`
- `ai-agent-role-library-governance`
- `design-design-md-system-contract`
- `compliance-private-communication-boundary`

Added five trusted scenario bundles:

- `multi-platform-research-discovery`
- `investment-research-diligence`
- `agent-role-library-governance`
- `design-md-system-governance`
- `private-communication-governance`

Recorded metadata-only external references for Agent-Reach, ai-berkshire,
agency-agents, Google DESIGN.md ecosystem references, and SimpleX Chat.
OpenMontage and codebase-memory-mcp were reviewed again and remain covered by
batch 031 skills. No upstream code, prompts, installers, connectors, accounts,
scrapers, investment agents, role packs, design skills, messaging servers, or
cryptographic implementations were imported or enabled.

Updated router profiles and eval coverage so multi-platform research,
investment diligence, role-library governance, DESIGN.md governance, and
private communication tasks route to dedicated trusted bundles instead of
generic RAG, website, multi-agent, or general scenarios.

## 2026-07-03 Agentic Reference Patterns

Added three trusted, locally authored method skills based on external reference
project review:

- `media-agentic-video-pipeline-plan`
- `ai-graph-memory-contract`
- `code-codebase-graph-index-boundary`

Added three trusted scenario bundles:

- `agentic-media-production`
- `agent-long-term-memory-governance`
- `codebase-graph-intelligence`

Recorded metadata-only external references for OpenMontage, cognee, and
codebase-memory-mcp. The references remain non-runtime provenance records; no
upstream code, prompts, installers, renderers, memory services, MCP servers, or
background indexers were imported or enabled.

Updated router profiles and regression coverage so reference-video media
production, long-term graph memory governance, and MCP code graph intelligence
route to dedicated trusted bundles instead of older generic video, RAG, or code
review scenarios.

Current verified baseline after this update:

```text
branch: main
catalog skills: 172
trusted skills: 166
trusted scenario bundles: 23
external references: 19
trusted overlap groups: 7
tracked claude-skills candidates: 336
covered claude-skills candidates: 336
router eval cases: 34
verification command: bash scripts/verify.sh
```

## Maintenance Gates

Run these gates before publishing catalog, router, bundle, or documentation
changes:

```bash
bash scripts/verify.sh
env PYTHONPATH=src python3 -m onecode_skill_sanitizer.cli verify --registry catalog
env PYTHONPATH=src python3 -m onecode_skill_sanitizer.cli maintain-check --registry catalog --bundles bundles/index.json --references external-references/index.json --claude-skills-candidate-map docs/claude-skills-candidate-map.json
env PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval --eval evals/router-quality.json --registry catalog --bundles bundles/index.json
git diff --check
```

Expected current results:

```text
verify: ok, 172 skills, 166 trusted, 0 tampered, 0 unknown provenance
maintain-check: ok, 23 bundles, 336 / 336 candidates covered
router-eval: ok, 34 / 34 cases
full script: 127 tests OK
```

## Routine Maintenance Checklist

- Keep `README.md`, `catalog/README.md`, `docs/catalog-status.md`, and
  `docs/feature-log.md` in sync with `catalog/index.json` and
  `bundles/index.json`.
- Add or update router eval cases when a new scenario profile, bundle, or major
  signal family is added.
- Keep default task packs trusted-only. Use review-required or quarantined
  skills only for explicit review work.
- Do not copy or execute upstream community skills directly. Convert useful
  patterns through local authoring, scan, schema check, approval, manifest
  sealing, and registry verification.
- Update `docs/claude-skills-candidate-map.json` only when a candidate maps to
  an existing trusted local skill or is intentionally queued for future work.
- Reinstall `safe-agent-router` only when integration skill files or wrapper
  scripts change, or when the local repository path changes.

## Next Maintenance Backlog

- Watch upstream reference sources for new or changed skill candidates.
- Promote cluster-covered candidates into dedicated local skills only when
  repeated real tasks show that a cluster is too broad.
- Continue expanding multilingual routing signals for common Chinese, English,
  and mixed-language task phrasing.
- Add deeper parser-backed checks where deterministic regex scanning is too
  shallow for a recurring risk class.
