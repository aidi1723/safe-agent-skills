---
name: code-codebase-graph-index-boundary
description: Use when reviewing MCP code intelligence, codebase graph indexes, call graphs, symbol search, architecture queries, git diff impact analysis, ADR memory, or structural code exploration boundaries.
---

# Code Codebase Graph Index Boundary

## When To Use

Use this skill when an agent may use a structural code index, MCP code graph,
call graph, symbol graph, architecture query, impact analysis, or repository
ADR memory to explore a codebase.

This skill provides method and safety boundaries only. It does not install,
start, update, or configure an MCP server or code indexer.

## Safe Workflow

1. Decide whether a graph index is justified: large repository, unfamiliar
   architecture, cross-file call paths, route mapping, impact analysis, or
   repeated symbol lookup.
2. Confirm the project scope, ignored paths, generated directories, vendored
   code, private submodules, and cross-repository boundaries before indexing.
3. Treat graph answers as indexed evidence, not source of truth. Read the
   relevant source file before editing behavior.
4. Check index freshness against git state, watcher status, or explicit index
   timestamp before relying on call paths or impact results.
5. Keep graph queries read-only unless the user explicitly asks for ADR or
   project metadata changes.
6. Record any MCP setup, update, config edit, UI launch, or background service
   as approval-required runtime work.
7. When graph output conflicts with direct source reads, prefer the source and
   mark the index stale or incomplete.

## Expected Output

- graph-index suitability decision
- repository scope and ignore boundary
- read-only query plan
- freshness and staleness notes
- source-read confirmation targets
- MCP runtime approval boundary
- residual risks for generated or cross-repo code

## Verifier Expectations

- project scope check
- ignored and generated path check
- index freshness check
- source-read confirmation check
- read-only query boundary check
- approval record for MCP setup or config changes

## Failure Handling

If the index is missing, stale, or outside the allowed project scope, fall back
to normal repository exploration and record why graph-assisted discovery was
not trusted for the task.
