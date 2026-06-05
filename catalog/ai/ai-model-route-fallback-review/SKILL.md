---
name: ai-model-route-fallback-review
description: Use when reviewing model routing, fallback choices, escalation rules, provider selection, cost tradeoffs, or AI workflow reliability boundaries.
---

# AI Model Route Fallback Review

## When To Use

Use this skill when an AI workflow must choose between local, hosted,
specialized, or fallback models while preserving quality, budget, and safety
requirements.

## Safe Workflow

1. Identify task type, required capabilities, latency target, budget limit,
   privacy boundary, and acceptable fallback behavior.
2. Separate routing conditions for routine work, hard reasoning, tool use,
   long context, low confidence, and repeated failure.
3. Define escalation and fallback rules with clear stop conditions and operator
   review points for costly or sensitive work.
4. Keep provider-specific assumptions separate from task requirements.
5. Record model limits, quality risks, retry bounds, and verification evidence.

## Expected Output

- routing decision table
- fallback and escalation rules
- budget and latency risks
- quality verification plan
- unresolved provider assumptions

## Verifier Expectations

- task capability check
- fallback rule check
- retry and stop-condition check
- budget and privacy boundary check

## Failure Handling

If model limits or provider behavior are unknown, choose the conservative route
and mark the decision as requiring operator review.
