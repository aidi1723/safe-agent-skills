# Structural Maintainability Redesign

Date: 2026-07-11

Project: `Safe-Agent-Skills`

## Goal

Reduce the repository's maintenance and onboarding cost without changing its
public CLI contract, trusted-catalog semantics, routing behavior, or
method-only safety boundary.

The redesign addresses four verified pressure points:

- core behavior is concentrated in `cli.py`, `router.py`, and one registry test
  module
- `batches/` mixes active drafts, source snapshots, and already promoted skill
  bodies
- historical reports compete with current documentation for attention
- every catalog skill uses a concise routing-card shape, including domains that
  need deeper operational guidance

## Success Criteria

The work is complete when:

1. `cli.py` contains parser wiring, compatibility exports, and thin command
   dispatch rather than bulk workflows, rendering, validation, and registry
   implementation.
2. `router.py` remains the compatibility facade while focused routing modules
   own profiles, selection, and execution-graph logic.
3. The largest registry test module is split along the same ownership
   boundaries as production code.
4. Every batch has a machine-readable lifecycle state and a documented
   canonical location. Promoted duplicate bodies are replaced by traceable
   promotion records only when the catalog body is byte-identical and the
   original Git commit and content hash are retained.
5. `docs/index.md` is the single documentation entry point. README links to
   current truth first, while updates, closure reports, batch notes, and design
   records are explicitly presented as history.
6. A documented skill-depth policy distinguishes routing cards from playbooks
   and specialist skills. Selected high-risk representative skills include
   useful on-demand references, and an automated audit reports future depth
   regressions without imposing arbitrary padding.
7. Catalog trust status, sanitized hashes, bundle behavior, Schema v1/v2 output,
   and existing CLI commands remain compatible except for intentionally
   resealed skills whose bodies are deepened in this change.
8. The repository verification suite passes, the completion report records
   before-and-after measurements, and the result is committed and pushed to the
   configured GitHub remote.

## Scope

### Included

- extraction of cohesive code from the current large Python modules
- compatibility re-exports for callers and tests
- test-module decomposition without reducing behavioral coverage
- batch lifecycle inventory, validation, and duplicate-promotion compaction
- current-versus-history documentation navigation
- skill-depth policy, audit metrics, and a small representative depth upgrade
- architecture, maintenance, and completion-report updates
- local verification, Git commit, and push to `origin`

### Excluded

- changing routing algorithms or selection weights
- changing the host execution or permission model
- adding a semantic model dependency
- changing trusted status merely to satisfy structural targets
- rewriting all 172 skills to a fixed word count
- deleting provenance or historical release evidence
- physically relocating every historical document in this cycle

Historical documents keep stable paths to avoid widespread broken links. The
new index supplies the archive boundary semantically; physical relocation can
happen in a later compatibility-breaking documentation release.

## Considered Approaches

### Documentation-Only Cleanup

Add indexes and warnings but leave code and batch duplication unchanged.

This has low implementation risk, but it does not reduce the core change
hotspots or prevent draft/catalog confusion in tools and searches. It is
insufficient.

### Full Repository Rewrite

Create a new package hierarchy, move all history, and regenerate every catalog
asset in one release.

This produces a clean tree quickly, but it creates unnecessary risk for public
imports, catalog hashes, provenance links, and router regression behavior. It
is rejected.

### Incremental Compatibility-Preserving Extraction

Extract one cohesive responsibility at a time, keep facades and stable paths,
add lifecycle metadata before compacting duplicates, and deepen only skills
whose risk and task complexity justify it.

This is the selected approach. It reduces verified maintenance costs while
keeping each migration step independently testable and reversible through Git.

## Target Code Architecture

The package keeps a flat module layout for this cycle. This matches the current
repository and avoids introducing nested packages before ownership boundaries
have stabilized.

```text
src/onecode_skill_sanitizer/
  cli.py                 argparse wiring and compatibility exports
  commands.py            thin command handlers and output dispatch
  registry.py            registry IO, indexing, status, and verification
  rendering.py           JSON-to-Markdown task-pack rendering
  bulk.py                candidate planning, draft generation, assessment
  router.py              public routing compatibility facade
  routing_profiles.py    signals, normalization, profiles, bundle scoring
  routing_execution.py   stages, approval gates, and graph compilation
  batch_lifecycle.py     batch inventory and promotion-record validation
  skill_depth.py         deterministic depth metrics and policy findings
```

Existing modules such as `validation.py`, `references.py`, `intent.py`,
`composer.py`, `compiler.py`, and `contracts.py` retain their current roles.

### Compatibility Strategy

Public functions currently imported from `onecode_skill_sanitizer.cli` or
`onecode_skill_sanitizer.router` remain importable from those modules. During
the migration, the facade imports and re-exports implementations from the new
owner module. The console entry point remains
`onecode_skill_sanitizer.cli:main`.

Extraction must be behavior-preserving. Each move begins with a focused import
or output contract test, observes the expected failure, then moves the minimal
implementation and runs both focused and full regression tests.

### Boundary Order

1. Extract pure task-pack rendering from `cli.py`.
2. Extract bulk candidate and draft workflows from `cli.py`.
3. Extract registry operations and thin command dispatch from `cli.py`.
4. Extract routing profile data and scoring from `router.py`.
5. Extract execution graph and approval-gate construction from `router.py`.
6. Split tests after each production boundary is stable.

This order starts with pure functions and keeps parser and compatibility
surfaces stable until the end.

## Batch Lifecycle Design

`catalog/` remains the only runtime-selectable registry. `batches/` becomes an
explicit intake and provenance workspace with four lifecycle states:

- `active_draft`: editable material not eligible for runtime selection
- `review_ready`: complete enough for sanitizer and human review
- `promoted`: canonical body exists in `catalog/`
- `superseded`: retained only as historical provenance

`batches/index.json` records each batch, its lifecycle, item counts, canonical
catalog targets, source commit, and content hashes. A validator rejects unknown
states, missing targets, or a `promoted` record whose expected catalog content
does not match.

For byte-identical promoted bodies, the batch copy may be replaced with a
`PROMOTED.md` record containing:

- original relative path
- canonical catalog path
- original SHA-256
- promotion commit
- lifecycle status

The batch `skill.json` remains as provenance metadata and gains a promotion
record where its schema permits. If existing verification treats the body as a
required source artifact, that item is left intact and reported as an
uncompacted exception. No source evidence is silently deleted.

Repository search, documentation, and maintenance commands identify
`catalog/` as production and `batches/` as non-runtime material.

## Documentation Information Architecture

`docs/index.md` becomes the human source of truth with five sections:

1. Start here
2. Current architecture and behavior
3. Operator and maintainer guides
4. Catalog and skill authoring
5. Historical records

README keeps product positioning, installation, the verified baseline, and a
small set of current links. The chronological list of updates and closure
reports moves out of the main narrative and is reachable through the history
section of `docs/index.md`.

The documentation contract distinguishes:

- **current**: normative behavior and maintained workflows
- **reference**: supporting design and domain material
- **history**: dated plans, updates, batch notes, acceptance records, and
  closure reports

No historical file is described as current merely because it was most recently
written.

## Skill Depth Design

Line count is a signal, not a quality target. Skills are classified by intended
instruction depth:

- `routing_card`: bounded workflow, expected output, and verifier contract
- `playbook`: decisions, failure modes, examples, and reusable checklists
- `specialist`: concise entry instructions plus on-demand references or assets

The initial policy audit reports:

- words and workflow-step count
- required structural sections
- presence of examples, decision guidance, and failure handling
- on-demand reference and script counts
- risk-level and depth-class mismatch

The audit fails only on structural or policy contradictions. Word-count and
reference thresholds begin as warnings so maintainers can calibrate them from
real routing and task outcomes.

This cycle deepens a small representative set from security, compliance, and
engineering. Their manifests are resealed through the existing governance
workflow, and catalog verification must prove the resulting hashes and trust
states are coherent.

## Data and Error Handling

All new inventory and audit formats are deterministic JSON with stable ordering.
Malformed lifecycle records, invalid canonical paths, and catalog hash
mismatches fail closed with actionable findings. Read-only audit commands never
rewrite catalog or batch content.

Compaction is a separate explicit maintenance operation. It processes only
byte-identical promoted copies, emits a report of changed and skipped items,
and never changes catalog content.

Module extraction must not change emitted task-pack JSON or Markdown. Golden
and schema-based tests compare outputs before and after the move.

## Testing Strategy

Testing follows red-green-refactor for every production boundary:

- focused import-compatibility tests for facade exports
- golden output tests for Markdown and JSON rendering
- unit tests for registry, lifecycle, and depth-policy functions
- fixture-based batch promotion validation tests
- unchanged router evaluation and Schema v1/v2 regression tests
- catalog maintain, reference, schema, contract, and hash verification
- full repository verification through `scripts/verify.sh`

Documentation checks verify that `docs/index.md` exists, README points to it,
all current links resolve, and historical documents are reachable without
dominating the primary entry path.

## Delivery and Reporting

The final report records:

- before-and-after line distribution for core and test modules
- batch counts by lifecycle and number of duplicate bodies compacted or skipped
- documentation counts by current/reference/history class
- catalog depth distribution and the skills deepened in this cycle
- verification commands and exact results
- compatibility guarantees, known residual risks, and recommended next steps

Changes are committed in coherent stages so code extraction, lifecycle data,
documentation, skill depth, and final reporting remain independently auditable.
After the final clean verification, the branch is pushed to the configured
GitHub `origin` remote.

## Risks and Mitigations

- **Import regressions:** keep facade re-exports and focused compatibility
  tests.
- **Output drift:** compare deterministic task-pack fixtures and router evals.
- **Broken provenance:** compact only byte-identical promoted bodies and retain
  commit/hash records.
- **Catalog trust drift:** reseal only intentionally deepened skills and run all
  catalog verification gates.
- **Documentation link breakage:** retain existing historical paths and add an
  index before considering moves.
- **Artificial skill inflation:** use risk and task complexity rather than a
  universal minimum length.
- **Oversized migration:** stop extraction at the defined ownership boundaries;
  routing algorithm changes remain out of scope.

