# Regression Test Evidence Guide

Use this guide to prove a behavior change and protect it from recurrence. Bind
the test to an externally meaningful contract rather than incidental internals.

## Choose The Test Boundary

- Use a unit test for isolated deterministic logic and an integration or
  contract test when the defect crosses modules, schemas, storage, processes,
  or service boundaries.
- Use end-to-end coverage only when the user-visible workflow or integration
  wiring is the behavior at risk.
- Prefer the lowest boundary that reproduces the failure without replacing
  real behavior with mocks.

## Red And Green Evidence

Record the failing assertion against the old behavior and the passing result
after the change. A test written after implementation must be proven by
temporarily reverting the fix or otherwise reproducing the original failure.
Distinguish assertion failure from setup, import, timeout, or environment error.

## Reliability

Minimize fixtures, time, randomness, shared state, network dependence, and
implementation-coupled mocks. Review snapshots line by line and update them
only when the entire output change is intended. Treat retries as evidence of
flakiness, not as proof of correctness.

## Verification Scope

Run the targeted test, then the nearest shared test group, and expand to the
full suite when the change touches shared contracts or broad workflows. Record
commands, counts, skipped tests, unavailable dependencies, flakes, and residual
risk.
