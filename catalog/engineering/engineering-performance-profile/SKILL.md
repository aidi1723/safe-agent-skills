---
name: engineering-performance-profile
description: Use when reviewing performance, latency, memory growth, slow builds, bottlenecks, and reliability under load.
---

# Engineering Performance Profile

## When To Use

Use this skill when software feels slow, resource-heavy, unreliable under load,
or expensive to build and run.

## Safe Workflow

1. Define the performance symptom, target metric, and affected workflow.
2. Measure before changing code when a benchmark or log is available.
3. Separate CPU, memory, IO, network wait, build time, and rendering costs.
4. Prefer focused improvements with measurable before and after evidence.
5. Record tradeoffs, especially caching, concurrency, and data freshness.

## Expected Output

- metric and baseline
- bottleneck hypothesis
- improvement target
- verification result
- residual risk

## Verifier Expectations

- benchmark or timing check
- resource observation when available
- regression test for behavior
- comparison against baseline

## Failure Handling

If no measurement is available, propose a minimal benchmark before recommending
large changes.
