---
name: codebase-explore-map
description: Use when first exploring an unfamiliar repository, mapping architecture, finding entry points, identifying ownership boundaries, or preparing a codebase context brief before implementation or review.
---

# Codebase Explore Map

## When To Use

Use this skill before non-trivial code changes in an unfamiliar or large
repository. It helps build a compact project map without reading unrelated
files or inventing architecture from guesses.

## Safe Workflow

1. Read repository instructions, package manifests, top-level docs, and test or
   build entry points.
2. Map runtime entry points, major modules, data flow, shared contracts, and
   generated or vendor directories to avoid.
3. Locate the smallest file set relevant to the requested task with fast search
   and targeted reads.
4. Identify local conventions: framework, naming, test style, formatting,
   state management, error handling, and release commands.
5. Record assumptions, unknowns, and the files that are likely safe to change.
6. Stop exploration when the implementation surface is clear enough; avoid
   broad inventory work that does not affect the task.

## Decision Guidance

Classify the exploration as `orientation`, `change_mapping`,
`incident_mapping`, or `architecture_review`. Orientation identifies how to
build, test, and navigate the project. Change mapping traces only the contracts
and consumers relevant to a requested modification. Incident mapping follows a
failure from its observed boundary toward the responsible owner. Architecture
review may examine broader ownership and dependency structure, but still needs
an explicit question and evidence limit.

Treat repository instructions and executable manifests as stronger evidence
than filenames or directory names. Confirm entry points through imports,
configuration, scripts, routes, registrations, or tests. Stop when the relevant
entry point, owner, data flow, contract, test surface, generated boundaries,
and unresolved risks are clear enough for the next task.

## Evidence Minimum

- repository instructions and their scope or precedence
- package, build, test, lint, formatting, and release entry points
- runtime entry points, major owners, relevant data flow, and shared contracts
- generated, vendor, cache, fixture, migration, and artifact directories
- targeted search terms and files that support the map
- likely change surface, downstream consumers, and verification commands
- assumptions, conflicting evidence, unresolved ownership, and stopping reason

## References

Load [the repository evidence map](references/repository-evidence-map.md) for
large repositories, unfamiliar frameworks, cross-module changes, incidents,
generated code, multiple runtimes, or unclear ownership boundaries.

## Expected Output

- compact repository map
- relevant files and entry points
- local conventions and commands
- likely change surface
- assumptions and unresolved questions

## Verifier Expectations

- repository instruction check
- manifest and test-command check
- targeted search evidence
- change-surface review before editing

## Failure Handling

If repository structure is ambiguous or generated code cannot be separated from
source code, mark the risky paths and ask for ownership guidance before editing
them. Do not edit files, install dependencies, execute unapproved commands, or
infer architecture from naming alone.
