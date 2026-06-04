---
name: ai-guidance-constrained-generation
description: Use when an LLM task needs constrained generation, token-level control, or explicit output structure.
---

# AI Guidance Constrained Generation

## When To Use

Use this skill when free-form model output is too risky and the task needs
controlled structure, slot filling, stop conditions, or grammar-like output
boundaries.

## Safe Workflow

1. Define the output slots, allowed values, and termination condition.
2. Keep constraints readable and minimal so failures are easy to diagnose.
3. Separate generation constraints from runtime permissions.
4. Use examples only when they narrow the desired output behavior.
5. Verify that the final output satisfies the declared structure before use.

## Expected Output

- constrained output plan
- required slots or grammar notes
- stop condition
- validation checklist
- unresolved ambiguity notes

## Verifier Expectations

- output structure check
- required field check
- stop condition check
- no hidden permission expansion

## Failure Handling

If constraints conflict, simplify to the smallest valid output contract and
report the discarded constraint.

## Boundary

This is a reference skill inspired by Guidance. It documents constrained
generation patterns and does not bundle third-party runtime code.
