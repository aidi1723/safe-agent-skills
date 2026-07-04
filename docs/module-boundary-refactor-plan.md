# Module Boundary Refactor Plan

This plan keeps the current CLI behavior stable while reducing the maintenance
cost of the large `cli.py`, `router.py`, and registry test modules.

## Current Pressure Points

- `src/onecode_skill_sanitizer/cli.py` mixes command parsing, registry IO,
  schema validation, router eval, bulk draft generation, and status mutation.
- `src/onecode_skill_sanitizer/router.py` mixes scenario profiles, scoring,
  contract graph planning, pipeline planning, approval gate detection, and
  output quality scoring.
- `tests/test_registry_cli.py` combines real catalog regression tests,
  command-level tests, schema checks, bulk candidate workflows, and CI-like
  maintenance checks.

## Target Boundaries

- `commands/`: thin argparse command handlers and output rendering.
- `registry/`: manifest loading, registry indexing, status mutation, and
  provenance checks.
- `validation/`: schema checks, reference checks, bundle checks, and overlap
  group checks.
- `routing/`: task profiles, scenario scoring, mesh routing, contract graphs,
  pipeline plans, and selection quality.
- `bulk/`: claude-skills candidate planning, draft generation, and assessment.
- `tests/`: split by the same boundaries, with a small real-catalog regression
  suite kept separate from focused unit tests.

## Migration Sequence

1. Extract pure validation functions first because they have narrow inputs and
   strong existing tests.
2. Move router profile data and scoring helpers into `routing/` while keeping
   public imports re-exported from `router.py`.
3. Move CLI command bodies into `commands/`, leaving `cli.py` as parser wiring
   plus compatibility wrappers.
4. Split `test_registry_cli.py` after each extraction so failures stay local to
   the moved behavior.
5. Keep `scripts/verify.sh`, `router-eval`, `maintain-check`, and
   `schema-check` green after every step.

## Progress

- 2026-07-04: Extracted repository asset path resolution into
  `onecode_skill_sanitizer.paths` with focused regression coverage. This is a
  low-risk boundary split used by CLI read-only commands and router checks.
- 2026-07-04: Extracted manifest hashing, sealing, and pure schema validation
  into `onecode_skill_sanitizer.validation` with focused import-level coverage.
  `cli.py` now keeps command orchestration while reusing validation helpers.
- 2026-07-04: Extracted external reference metadata validation into
  `onecode_skill_sanitizer.references` with focused regression coverage.
  `reference-check` and `maintain-check` now share the same module boundary.

## Compatibility Rules

- Preserve the existing `onecode-skill-sanitizer` console entry point.
- Preserve public imports used by the current tests during the transition.
- Do not change catalog hashes, skill trust status, or bundle semantics as part
  of pure module moves.
- Add focused regression tests before each extraction when behavior is not
  already covered.
