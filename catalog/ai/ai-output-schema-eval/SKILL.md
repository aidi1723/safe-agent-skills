---
name: ai-output-schema-eval
description: Use when evaluating AI outputs against schema, format, task requirements, safety constraints, and regression examples.
---

# AI Output Schema Eval

## When To Use

Use this skill when checking whether an AI output satisfies a required schema,
format, benchmark, or task-specific contract.

## Safe Workflow

1. Identify the expected output schema, format, or checklist.
2. Compare the output against required fields, types, constraints, and examples.
3. Separate schema failure, factual failure, safety failure, and style failure.
4. Prefer deterministic validation when a parser or schema is available.
5. Record failures with exact field names or requirement references.
6. Avoid changing the scoring criteria after seeing the output unless the user asks for a revised eval.

## Expected Output

- pass or fail summary
- issue list by requirement
- exact schema or format failures
- suggested correction targets

## Verifier Expectations

- output schema check
- format check
- benchmark or example comparison
- prompt injection check when evaluating agent instructions

## Failure Handling

If the expected schema is unclear, ask for or infer a minimal explicit schema
and mark the inference.
