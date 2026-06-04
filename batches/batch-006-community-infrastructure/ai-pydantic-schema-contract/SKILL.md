---
name: ai-pydantic-schema-contract
description: Use when defining typed contracts, JSON Schema outputs, validation models, or parser-safe AI response formats.
---

# AI Pydantic Schema Contract

## When To Use

Use this skill when an agent output should be validated as typed data before it
is used by code, automation, documents, or downstream workflows.

## Safe Workflow

1. Define required fields, optional fields, value ranges, and nested objects.
2. Write examples that pass and fail the intended contract.
3. Validate model output with a parser or schema check before downstream use.
4. Report field-level failures instead of rewriting the contract silently.
5. Keep schema validation separate from business approval and runtime access.

## Expected Output

- typed schema summary
- accepted and rejected examples
- validation result
- field-level error list
- downstream compatibility notes

## Verifier Expectations

- schema parser check
- required field check
- type and range check
- failure example check

## Failure Handling

If the desired schema is incomplete, create a minimal explicit schema and mark
missing requirements for operator review.

## Boundary

This is a reference skill inspired by Pydantic. It documents schema-contract
patterns and does not bundle runtime validation libraries.
