---
name: ai-token-rate-budget-guard
description: Use when planning model calls, agent loops, context size, budget limits, rate limits, or fallback behavior for AI workflows.
---

# AI Token Rate Budget Guard

## When To Use

Use this skill when an AI workflow may consume significant model tokens,
request volume, context window capacity, or paid API budget.

## Safe Workflow

1. Identify the task goal, expected model calls, context inputs, output size,
   retry policy, and budget or rate limit.
2. Split work into required calls, optional calls, verification calls, and
   expensive escalation paths.
3. Prefer smaller source inventories, cached context, sampled verification, and
   bounded retry counts before using higher-cost paths.
4. Define stop conditions for repeated failures, low confidence, empty
   retrieval, quota pressure, or unchanged outputs.
5. Record estimated cost drivers, rate-limit risks, fallback plan, and what
   work should wait for operator approval.

## Expected Output

- model-call inventory
- token and rate budget estimate
- retry and stop-condition plan
- fallback or escalation boundary
- residual cost risks

## Verifier Expectations

- input scope check
- retry bound check
- stop condition check
- budget and rate-limit check

## Failure Handling

If budget or rate limits are unknown, use conservative assumptions and mark
high-volume work as requiring operator approval.
