---
name: ai-qwen-agent-tool-workflow
description: Use when reviewing function calling, MCP tools, code interpreter flows, RAG, or browser-extension agent workflows.
---

# AI Qwen Agent Tool Workflow

## When To Use

Use this skill when an agent workflow combines model reasoning with function
calling, tools, code execution, retrieval, or browser extension actions.

## Safe Workflow

1. Identify each tool, function schema, data source, and execution boundary.
2. Validate tool arguments before execution.
3. Keep code execution, browser actions, and external connectors under explicit
   host approval.
4. Separate retrieved evidence from model inference.
5. Record tool results and verification checks in the final report.

## Expected Output

- tool workflow plan
- function schema notes
- execution boundary
- retrieval and evidence notes
- verifier checklist

## Verifier Expectations

- function argument check
- connector permission check
- code execution boundary check
- evidence and output check

## Failure Handling

If a tool schema or permission boundary is missing, keep that tool disabled and
continue with advisory planning only.

## Boundary

This is a reference skill inspired by Qwen-Agent. It documents tool workflow
patterns and does not bundle models, extensions, or code interpreter runtimes.
