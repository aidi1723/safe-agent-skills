---
name: code-simplify-refactor-plan
description: Use when simplifying code, reducing unnecessary abstraction, clarifying control flow, shrinking duplicate logic, or planning a low-risk refactor after behavior is understood.
---

# Code Simplify Refactor Plan

## When To Use

Use this skill when code works but is harder than necessary to understand,
test, or maintain. It focuses on behavior-preserving simplification rather than
feature changes.

## Safe Workflow

1. State the behavior that must remain unchanged and the tests or checks that
   protect it.
2. Identify the complexity source: duplication, excessive abstraction,
   unclear naming, tangled branching, dead path, oversized function, or
   misplaced responsibility.
3. Prefer the smallest behavior-preserving change: inline speculative helpers,
   split one clear unit, remove redundant state, or narrow a public surface.
4. Keep refactors separate from feature changes unless the simplification is
   required to safely implement the feature.
5. Preserve public APIs, data contracts, migrations, and user-facing behavior
   unless an explicit migration plan exists.
6. Verify with focused tests first, then relevant broader checks.

## Expected Output

- simplification target and invariant behavior
- proposed minimal refactor steps
- affected files and public contracts
- regression verification plan
- rollback or review notes for risky cleanup

## Verifier Expectations

- existing behavior or regression test check
- public contract check
- focused test run
- broader relevant test or build check

## Failure Handling

If behavior is not sufficiently covered, write or request a focused regression
test before simplifying. If dynamic or external consumers may rely on the code,
mark the refactor as review-required.
