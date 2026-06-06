# External Reference Roadmap

Date: 2026-06-06

This document defines the future development direction for learning from
external tool-routing and MCP aggregation projects without weakening the
Safe-Agent-Skills trust model.

## Goal

Improve `smart` routing so it can learn from high-quality external ecosystems
while keeping execution bounded to this repository's verified catalog.

The immediate direction is not to run external tools automatically. The safer
first step is to build a metadata-only external reference library that can
inform future skill collection, capability mapping, and bundle design.

## Reference Projects

These projects are useful as architecture references, not trusted runtime
dependencies:

- `https://github.com/HKUDS/AnyTool`
- `https://github.com/punkpeye/awesome-mcp-servers`
- `https://github.com/askbudi/roundtable`

Additional MCP aggregators, registries, and tool-routing projects can be added
only after source, license, provenance, and maintenance status are recorded.

## Non-Goals

- Do not auto-install external MCP servers.
- Do not execute unreviewed community tools.
- Do not expose external tool schemas to an agent before review.
- Do not treat GitHub stars, popularity, or README claims as trust.
- Do not bypass the existing `trusted` / `review_required` / `quarantined`
  registry states.

## Direction

### Phase 1: Metadata-Only Reference Library

Create a small curated reference index for external projects.

Suggested path:

```text
external-references/index.json
```

Each reference should include:

- name
- source URL
- source type
- author or organization
- license
- captured date
- project category
- claimed capabilities
- relevant local taxonomy categories
- runtime permission notes
- adoption status: `reference_only`, `candidate`, `rejected`, or `converted`
- review notes

Acceptance criteria:

- References are data only.
- No external code is downloaded or executed.
- Every entry has provenance and license fields.
- The index can be checked by `maintain-check`.

### Phase 2: Capability Mapping

Map external project capabilities into the existing skill taxonomy.

Examples:

- AnyTool-style hierarchical retrieval maps to `ai.routing`,
  `ai.orchestration`, and `ai.tool-schema`.
- MCP server directories map to candidate source discovery, not automatic
  execution.
- Unified MCP gateways map to future bundle and routing-contract design.

Acceptance criteria:

- `smart` can cite external references as design context.
- External references do not affect selected skills by default.
- A selected task pack must still contain only local trusted skills.

### Phase 3: Candidate Skill Drafting

Add a controlled workflow for turning an external reference into a local skill
candidate.

Draft workflow:

1. Record provenance and license.
2. Summarize capabilities without copying project text wholesale.
3. Assign taxonomy and risk level.
4. Generate a draft `SKILL.md` under an incoming or quarantine area.
5. Run sanitization, schema checks, and manual approval.
6. Promote only after registry verification passes.

Acceptance criteria:

- Drafts start as `review_required` or `quarantined`.
- Promotion to `trusted` remains explicit.
- Generated skills must have verifier expectations and safety boundaries.

### Phase 4: Router Evaluation Suite

Build an evaluation set that measures whether `smart` chooses the right local
skills and bundles.

Representative tasks:

- website launch
- code review hardening
- RAG app planning
- document-to-knowledge-base conversion
- data analysis
- commerce listing growth
- public content review
- agent safety review
- skill router quality review
- vague or unsupported tasks

Acceptance criteria:

- Known scenarios select the intended trusted bundle.
- Vague tasks leave `selected_scenario.id` empty.
- Required invariant skills are preserved even when `max-skills` is small.
- Overlap pruning never removes required safety or verification gates.

### Phase 5: Optional External Discovery

Only after Phases 1-4 are stable, consider optional discovery commands.

Possible command shape:

```bash
onecode-skill-sanitizer reference-import <source-url> --out external-references
onecode-skill-sanitizer reference-check --references external-references/index.json
```

This phase should remain metadata-first. Any runtime adapter, MCP connector, or
tool execution path must be a separate explicit approval flow.

## Routing Principles

- Prefer a small correct pack over a large impressive pack.
- Use external projects as evidence for design direction, not as authority.
- Select only trusted local skills in normal mode.
- Keep low-confidence routing conservative.
- Add scenario bundles only when repeated task patterns are stable.
- Record why each selected skill is needed.

## Risk Controls

External ecosystems introduce supply-chain, license, prompt-injection, privacy,
and execution-boundary risks. The following controls are mandatory:

- provenance capture
- license review
- no default execution
- no automatic trust promotion
- registry verification before selection
- source and hash records for converted skills
- explicit operator approval for any connector or network behavior

## Near-Term Recommendation

Implement Phase 1 and Phase 2 first.

This gives the project a practical way to learn from AnyTool-style retrieval
and MCP aggregator ecosystems without taking on the full complexity of an
external tool marketplace or runtime plugin host.
