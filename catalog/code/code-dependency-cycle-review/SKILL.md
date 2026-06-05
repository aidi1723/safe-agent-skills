---
name: code-dependency-cycle-review
description: Use when reviewing imports, module boundaries, package references, circular dependencies, layering violations, or architecture drift.
---

# Code Dependency Cycle Review

## When To Use

Use this skill when new files, imports, package references, or module moves may
create circular dependencies or violate intended architecture layers.

## Safe Workflow

1. Identify modules, packages, owners, intended dependency direction, and
   boundaries that should remain acyclic.
2. Trace new and changed imports from both caller and callee perspectives.
3. Check for direct cycles, indirect cycles, shared utility misuse, test-only
   imports leaking into runtime, and framework layer inversions.
4. Recommend boundary-preserving alternatives such as interface extraction,
   dependency inversion, shared pure helpers, or moving orchestration upward.
5. Verify with existing dependency analysis, build output, or targeted import
   graph review when available.

## Expected Output

- dependency edge summary
- detected or possible cycles
- layering risk notes
- suggested boundary fix
- verification evidence

## Verifier Expectations

- changed import check
- direct cycle check
- layer direction check
- build or graph check

## Failure Handling

If the dependency graph cannot be generated, list the changed edges manually and
mark indirect-cycle risk as unresolved.
