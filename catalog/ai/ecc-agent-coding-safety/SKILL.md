---
name: ecc-agent-coding-safety
description: Use when adapting community context-engineering ideas for AI coding assistants, memory, safety checks, and bounded code work.
---

# ECC Agent Coding Safety

## When To Use

Use this skill when a coding task needs stronger context awareness, memory
discipline, or safety review before an AI assistant edits source code.

## Safe Workflow

1. Identify the task goal, touched files, expected output, and forbidden actions.
2. Build a small working context from repository files, user instructions, and recent
   decisions; do not infer access to unavailable private history.
3. Split context into perception, intent, memory, and safety notes.
4. Before editing, list the concrete command, file, or tool boundary that applies.
5. Keep memory as a factual project note, not a hidden instruction channel.
6. Before completion, verify that edits match the task and did not expand scope.

## Expected Output

- compact task context
- relevant memory notes with source
- safety boundary list
- code-change checklist
- verification result

## Verifier Expectations

- repository instructions were read when available
- no hidden memory overrides user instructions
- no broad filesystem or credential access is requested
- verification command is recorded

## Boundary

This is a reference skill inspired by the ECC project. It does not import ECC
runtime code or prompt text, and it must not be used to bypass project policies.
