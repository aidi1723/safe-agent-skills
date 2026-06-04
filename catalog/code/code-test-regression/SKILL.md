---
name: code-test-regression
description: Use when adding or reviewing regression tests, failure cases, fixtures, and verification commands for code changes.
---

# Code Test Regression

## When To Use

Use this skill when a bug fix or feature needs tests that prove behavior and
guard against future breakage.

## Safe Workflow

1. Identify the behavior being protected and the smallest reliable test surface.
2. Write or review a test that fails on the old behavior when possible.
3. Keep fixtures minimal and focused on the behavior.
4. Verify the test command and record the result.
5. Avoid broad snapshot updates unless the changed output is intentional.

## Expected Output

- test intent
- test file and case name
- failure mode covered
- verification command and result

## Verifier Expectations

- targeted test run
- full relevant test group when risk is shared
- failure-case coverage
- fixture review

## Failure Handling

If a true regression test is not practical, explain the blocker and provide the
strongest available verification.
