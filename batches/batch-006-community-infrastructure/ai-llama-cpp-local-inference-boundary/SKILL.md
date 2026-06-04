---
name: ai-llama-cpp-local-inference-boundary
description: Use when reviewing local LLM inference, offline model use, context limits, quantization tradeoffs, or local privacy boundaries.
---

# AI Llama CPP Local Inference Boundary

## When To Use

Use this skill when an agent or product plans to use local inference and needs
privacy, context window, performance, model file, or deployment boundary review.

## Safe Workflow

1. Identify model file source, license, quantization, context window, and host
   hardware constraints.
2. Separate offline privacy benefits from remaining local data-handling risks.
3. Define allowed input data, logging behavior, and model storage path.
4. Check latency, memory, and output quality against the task requirement.
5. Record when local inference is advisory and when cloud fallback is allowed.

## Expected Output

- local inference boundary
- model source and license record
- performance and context notes
- privacy and logging policy
- fallback decision

## Verifier Expectations

- model provenance check
- license check
- local data handling check
- performance smoke check

## Failure Handling

If model provenance or license is unclear, keep the model out of trusted
runtime use until the missing record is resolved.

## Boundary

This is a reference skill inspired by llama.cpp. It documents local inference
review patterns and does not bundle model files or inference binaries.
