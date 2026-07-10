---
name: code-test-regression
description: Use when adding or reviewing regression tests, failure cases, fixtures, and verification commands for code changes.
---

# Code Test Regression

## When To Use

Use this skill when a bug fix or feature needs tests that prove behavior and
guard against future breakage.

## Safe Workflow

1. Identify the behavior, user-visible or contract-level failure, original triggering conditions, and blast radius being protected.
2. Choose the lowest reliable boundary that reproduces the defect: unit, integration, contract, end-to-end, or system.
3. Demonstrate that the test fails against the old behavior for the expected assertion, not because of setup, import, timeout, or environment errors.
4. Implement or review behavioral assertions that survive internal refactoring. Keep fixtures, mocks, time, randomness, network access, and shared state minimal.
5. Run the test against the corrected behavior and record the exact command, result, and test identity.
6. Run the nearest shared test group, then expand verification when the change affects shared contracts, persistence, integrations, or broad workflows.
7. Review snapshots line by line, record skipped or flaky coverage, and avoid broad fixture or snapshot updates unless every changed value is intentional.

## Expected Output

- test intent
- test file and case name
- failure mode covered
- verification command and result

## Decision Guidance

Use a unit test for isolated deterministic logic. Use integration or contract
coverage when behavior crosses modules, schemas, storage, processes, or service
boundaries. Use end-to-end or system coverage only when the integration wiring
or user workflow is itself the behavior at risk. Prefer the lowest boundary
that reproduces the failure without mocking away the relevant behavior.

A regression test needs credible RED and GREEN evidence. When the test is
written after the implementation, temporarily revert the fix or reproduce the
old behavior through a controlled fixture so the test is observed failing for
the intended reason. A test that only ever passed documents current behavior
but does not prove it guards the regression.

Scale verification to blast radius. A narrow implementation with a stable
contract may need a targeted group; a shared parser, schema, state store, or
workflow boundary usually requires broader tests. Treat retries as evidence of
flakiness, not a substitute for a deterministic pass.

## Evidence Minimum

- behavior or contract protected and the original triggering conditions
- test file, case name, chosen boundary, and why that level is sufficient
- RED command and expected assertion failure against the old behavior
- GREEN command and result against the corrected behavior
- fixture, mock, snapshot, time, randomness, and external dependency choices
- nearest shared test-group result and broader-suite result when required
- skipped, flaky, unavailable, or non-reproducible checks and residual risk

## References

Load [the regression test evidence guide](references/regression-evidence-guide.md)
for shared boundaries, snapshots, timing, mocks, flaky tests, integration
failures, or changes with a broad verification surface.

## Verifier Expectations

- targeted test run
- full relevant test group when risk is shared
- failure-case coverage
- fixture review

## Failure Handling

If a true regression test is not practical, explain the blocker and provide the
strongest available verification without calling it equivalent. Shell
execution, dependency installation, CI reruns, network access, credentials,
and production tests remain subject to host approval.
