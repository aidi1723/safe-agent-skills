---
name: ai-tool-schema-protocol-check
description: Use when reviewing tool calling schemas, JSON arguments, function contracts, MCP-style protocol boundaries, or cross-model tool compatibility.
---

# AI Tool Schema Protocol Check

## When To Use

Use this skill when an AI workflow must pass structured arguments to tools,
functions, services, or protocol adapters.

## Safe Workflow

1. Identify the tool contract, required fields, optional fields, enums, nested
   objects, defaults, validation rules, and error response shape.
2. Compare model-facing schema with implementation-facing schema and note any
   naming, type, nullability, or casing mismatch.
3. Define how malformed, partial, duplicated, or out-of-order arguments should
   be handled before tool execution.
4. Keep protocol translation rules explicit when different model formats or
   adapter formats are involved.
5. Verify with sample valid calls, invalid calls, and boundary-value examples.

## Expected Output

- schema contract map
- field mismatch list
- malformed argument handling
- protocol translation notes
- sample validation cases

## Verifier Expectations

- required field check
- type and enum check
- invalid argument check
- implementation contract check

## Failure Handling

If the implementation contract is unavailable, do not infer tool arguments from
prompt text alone. Request the source contract or mark the schema as unverified.
