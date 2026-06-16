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
them.
