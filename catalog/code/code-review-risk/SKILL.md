---
name: code-review-risk
description: Use when reviewing code changes for bugs, regressions, missing tests, unsafe assumptions, and maintainability risks.
---

# Code Review Risk

## When To Use

Use this skill when reviewing a diff, pull request, patch, or generated code
before it is accepted.

## Safe Workflow

1. Identify the changed files, intended behavior, and test surface.
2. Look for correctness bugs, data contract breaks, edge cases, and regressions.
3. Check whether tests cover the risky behavior.
4. Prioritize findings by severity and user impact.
5. Avoid unrelated refactor suggestions unless they affect the reviewed change.

## Expected Output

- findings first, ordered by severity
- file and line references when available
- missing test notes
- brief residual risk summary

## Verifier Expectations

- diff review
- relevant test command review
- behavior contract check
- dependency or API compatibility check when relevant

## Failure Handling

If the intended behavior is unclear, state the assumption and review against
that assumption.
