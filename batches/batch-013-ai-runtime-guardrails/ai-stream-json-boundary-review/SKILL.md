---
name: ai-stream-json-boundary-review
description: Use when reviewing streamed AI output, partial JSON parsing, incremental tool arguments, SSE output, or structured response boundaries.
---

# AI Stream JSON Boundary Review

## When To Use

Use this skill when AI output arrives incrementally and downstream code may act
before the full structured response is available.

## Safe Workflow

1. Identify the stream source, expected message format, parser behavior,
   completion marker, timeout, and consumer side effects.
2. Separate display-only streaming from structured data that can trigger a
   tool, write, publish, or workflow step.
3. Define when partial objects are allowed, when they are only previews, and
   what must wait for final validation.
4. Check handling for truncated output, invalid JSON, duplicate keys, arrays
   split across chunks, and schema drift.
5. Verify with complete, partial, malformed, slow, and interrupted stream
   examples.

## Expected Output

- stream boundary map
- final-validation rule
- partial-object handling
- malformed stream cases
- verification examples

## Verifier Expectations

- completion marker check
- final schema validation check
- interrupted stream check
- side-effect boundary check

## Failure Handling

If final validation cannot be proven, keep streamed data advisory and prevent
side effects until a complete validated object exists.
