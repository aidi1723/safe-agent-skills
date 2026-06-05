---
name: code-ast-refactor-safety
description: Use when planning structural refactors, symbol renames, import rewrites, large edits, AST-aware changes, or regex replacement risk reviews.
---

# Code AST Refactor Safety

## When To Use

Use this skill when code changes affect symbols, imports, call sites, file
structure, or repeated patterns where plain text replacement may be unsafe.

## Safe Workflow

1. Identify language, parser availability, target symbols, call sites, tests,
   and generated files that must be excluded.
2. Prefer compiler, language server, or AST-aware tooling for symbol changes
   when the project supports it.
3. Map impacted imports, exports, references, overloads, type declarations, and
   public API boundaries before editing.
4. Keep textual replacement limited to simple literals with narrow file scope
   and reviewable diffs.
5. Verify with formatting, type checks, tests, or focused compile checks after
   the refactor.

## Expected Output

- refactor scope map
- parser or tooling recommendation
- impacted symbol list
- excluded generated files
- verification commands

## Verifier Expectations

- symbol reference check
- generated file exclusion check
- compile or type check
- focused regression test check

## Failure Handling

If parser or type-check support is unavailable, reduce scope and require manual
diff review before treating the refactor as complete.
