---
name: ai-outlines-structured-generation
description: Use when an AI workflow needs strict structured output, regex-like constraints, or schema-shaped generation.
---

# AI Outlines Structured Generation

## When To Use

Use this skill when an agent must produce JSON, enums, typed fields, or
regex-constrained text that downstream parsers can rely on.

## Safe Workflow

1. Write the target schema or pattern before generating content.
2. Keep optional fields explicit and avoid vague natural-language requirements.
3. Validate generated output with a parser whenever possible.
4. Separate schema failure from factual or safety failure.
5. Retry only with the same contract unless the operator changes the task.

## Expected Output

- schema or pattern contract
- generated structured output
- validation result
- field-level failures
- retry or repair decision

## Verifier Expectations

- parser validation check
- required field check
- enum or regex check
- downstream compatibility check

## Failure Handling

If no stable schema exists, emit a minimal draft schema and request review
before using the result in automation.

## Boundary

This is a reference skill inspired by Outlines. It documents structured
generation patterns and does not bundle third-party runtime code.
