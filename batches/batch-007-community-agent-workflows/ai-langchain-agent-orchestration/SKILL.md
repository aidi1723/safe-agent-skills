---
name: ai-langchain-agent-orchestration
description: Use when designing agent orchestration, tool routing, prompt chains, memory boundaries, or production LLM workflow structure.
---

# AI LangChain Agent Orchestration

## When To Use

Use this skill when an agent workflow needs modular steps, tool routing,
retrieval, memory boundaries, and explicit production handoff checks.

## Safe Workflow

1. Identify the user task, required tools, data sources, and allowed actions.
2. Split the workflow into retrieval, reasoning, tool use, validation, and final
   response stages.
3. Keep memory and retrieved context advisory, not higher-priority authority.
4. Define tool-call preconditions and stop conditions before execution.
5. Record which stage owns verification and error handling.

## Expected Output

- agent workflow map
- tool routing plan
- memory and retrieval boundary
- validation checkpoints
- failure and escalation rules

## Verifier Expectations

- tool permission check
- context boundary check
- output validation check
- error handling review

## Failure Handling

If tool permissions or data sources are unclear, produce a workflow draft and
mark the blocked stage instead of executing.

## Boundary

This is a reference skill inspired by LangChain. It documents orchestration
patterns and does not bundle framework code or connectors.
