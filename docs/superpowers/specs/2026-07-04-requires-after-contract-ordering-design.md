# Requires After Contract Ordering Design

Date: 2026-07-04

## Goal

Add first-class `contract.requires_after` metadata so trusted skills can
declare explicit ordering dependencies when artifact dependencies are not
enough.

## Scope

This milestone extends the local deterministic router and schema checker only.
It does not execute skills, grant runtime permissions, fetch external content,
or integrate a host semantic gateway.

## Behavior

- Skill manifests may declare `contract.requires_after` as a string array of
  skill names.
- The contract graph treats each selected `requires_after` relationship as an
  ordering edge from the required predecessor skill to the dependent skill.
- The router uses the contract graph topology to order selected skills when the
  graph is complete and acyclic.
- Contract diagnostics report `requires_after` references that are not present
  in the selected skill pack.
- Existing artifact-based dependencies, precondition diagnostics, collision
  diagnostics, and graph fallback diagnostics remain unchanged.

## Validation

- `schema-check` accepts valid `contract.requires_after` arrays.
- `schema-check` rejects non-string, duplicate, or self-referential
  `requires_after` values.
- Router tests cover ordering edges and missing ordering dependencies.
- Full verification remains:
  - `bash scripts/verify.sh`
  - `git diff --check`
  - `router-eval`
  - `schema-check`
  - `maintain-check`
  - `verify`

## Follow-Up Boundary

This does not prune incompatible ordering packs automatically. It surfaces
ordering intent and diagnostics so future host gateways or scheduler policy can
decide whether to stop, repair, or ask for operator input.
