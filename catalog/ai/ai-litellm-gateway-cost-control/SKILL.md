---
name: ai-litellm-gateway-cost-control
description: Use when reviewing model gateway routing, provider fallback, budget limits, rate limits, or agent cost controls.
---

# AI LiteLLM Gateway Cost Control

## When To Use

Use this skill when an agent or product routes requests across multiple model
providers and needs cost, latency, logging, rate, or fallback policy review.

## Safe Workflow

1. Identify providers, model names, routing rules, budget owner, and fallback
   order.
2. Separate reliability fallback from cost optimization and compliance routing.
3. Define per-task, per-user, and per-workspace limits before production use.
4. Record what happens when a provider fails, slows down, or exceeds budget.

## Expected Output

- routing policy summary
- budget and rate limit plan
- provider fallback matrix
- logging and privacy notes
- residual risk list

## Verifier Expectations

- provider list check
- budget limit check
- private data logging check
- fallback behavior check

## Failure Handling

If license or provider policy is unclear, keep the skill in review state and
avoid recommending default production use.

## Boundary

This is a reference skill inspired by LiteLLM. It documents gateway review
