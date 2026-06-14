---
name: ai-context-compression-budget-plan
description: Use when planning context compression, long prompt trimming, memory summaries, retrieval snippets, or token-budget tradeoffs before AI execution.
---

# AI Context Compression Budget Plan

## When To Use

Use this skill when long documents, chat history, code context, tool outputs,
logs, retrieval results, or memory notes must fit inside a constrained model
context.

## Safe Workflow

1. Inventory source materials, task-critical facts, required citations,
   freshness constraints, input types, and sections that must not be
   summarized away.
2. Separate facts, instructions, decisions, open questions, code references,
   tool results, logs, retrieval chunks, and low-value repetition before
   compression.
3. Preserve identifiers, file paths, source dates, numeric values, constraints,
   error codes, line numbers, retrieval IDs, and user decisions exactly when
   they drive the task.
4. Define compression budget, excluded material, retained evidence, and when to
   fetch the original source again.
5. Set source recheck triggers for destructive actions, security claims,
   legal/compliance claims, numeric decisions, and exact code edits.
6. Verify the compressed context against representative source samples before
   downstream use.

## Expected Output

- context inventory
- input type inventory
- compression budget
- must-preserve facts
- excluded or summarized material
- source recheck triggers

## Verifier Expectations

- source inventory check
- must-preserve fact check
- citation and date check
- exact error, path, command, and retrieval ID check
- sample reconstruction check

## Failure Handling

If compression would remove task-critical evidence, reduce task scope or split
the work instead of relying on an unsupported summary.
