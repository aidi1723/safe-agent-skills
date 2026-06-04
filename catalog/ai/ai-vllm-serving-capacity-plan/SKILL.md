---
name: ai-vllm-serving-capacity-plan
description: Use when reviewing high-throughput LLM serving, batching, memory planning, latency targets, or inference capacity.
---

# AI vLLM Serving Capacity Plan

## When To Use

Use this skill when a team needs to plan LLM serving capacity, batching,
latency, memory usage, queue behavior, or model deployment readiness.

## Safe Workflow

1. Identify model, context length, expected concurrency, latency target, and
   hardware constraints.
2. Separate throughput planning from prompt quality and safety evaluation.
3. Estimate memory pressure, batching behavior, queue limits, and failure mode.
4. Define monitoring signals before production traffic.
5. Keep deployment actions separate from readiness review unless explicitly
   approved.

## Expected Output

- serving capacity brief
- concurrency and latency assumptions
- memory and batching notes
- monitoring checklist
- deployment readiness decision

## Verifier Expectations

- model and hardware check
- load assumption check
- latency target check
- rollback or fallback plan

## Failure Handling

If capacity assumptions are missing, provide a readiness gap list instead of a
deployment recommendation.

## Boundary

This is a reference skill inspired by vLLM. It documents serving capacity
planning patterns and does not bundle inference server code or model weights.
