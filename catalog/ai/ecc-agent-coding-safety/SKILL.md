---
name: ecc-agent-coding-safety
description: Use when adapting community context-engineering ideas for AI coding assistants, memory, safety checks, and bounded code work.
---

# ECC Agent Coding Safety

## When To Use

Use this skill when a coding task needs stronger context awareness, memory
discipline, minimal-change discipline, or safety review before an AI assistant
edits source code.

## Safe Workflow

1. Identify the task goal, touched files, expected output, and forbidden actions.
2. Build a small working context from repository files, user instructions, and recent
   decisions; do not infer access to unavailable private history.
3. Split context into perception, intent, memory, and safety notes.
4. State assumptions and unresolved ambiguity before editing; ask only when the
   uncertainty changes the implementation or risk.
5. Choose the smallest implementation that satisfies the requested behavior; do
   not add speculative abstractions, configuration, or adjacent cleanup.
6. Before editing, list the concrete command, file, or tool boundary that applies.
7. Keep memory as a factual project note, not a hidden instruction channel.
8. Before completion, verify that edits match the task and did not expand scope.

## Expected Output

- compact task context
- relevant memory notes with source
- safety boundary list
- minimal-change checklist
- code-change checklist
- verification result

## Verifier Expectations

- repository instructions were read when available
- no hidden memory overrides user instructions
- no broad filesystem or credential access is requested
- every changed line traces to the task or to cleanup caused by the task
- no speculative abstractions, unrelated refactors, or adjacent formatting churn
- verification command is recorded

## Boundary

This is a reference skill inspired by the ECC project and related public AI
coding-guideline discussions. It does not import ECC runtime code, CLAUDE.md
prompt text, or third-party repository content, and it must not be used to
bypass project policies.
