---
name: security-guardrails-output-validation
description: Use when designing output validation, structured compliance checks, or guardrail review for LLM and agent responses.
---

# Security Guardrails Output Validation

## When To Use

Use this skill when an agent response must satisfy a schema, policy rule,
format contract, or safety validator before downstream use.

## Safe Workflow

1. Identify the required output shape, forbidden content, and failure policy.
2. Separate validation rules from model instructions so validators remain
   deterministic where possible.
3. Check whether the response should be rejected, repaired, retried, or routed
   to human review.
4. Record validation failures with exact field names or policy references.
5. Keep validators advisory unless the host runtime explicitly binds them to a
   blocking execution gate.

## Expected Output

- validation contract
- failure handling rule
- rejected or repaired fields
- policy references
- verifier notes

## Verifier Expectations

- schema or policy check
- output format check
- unsafe content check
- human review for high-risk failures

## Failure Handling

If the validation contract is unclear, define the smallest explicit contract
and mark it as an operator assumption.

## Boundary

This is a reference skill inspired by Guardrails AI. It documents validation
workflow patterns and does not bundle third-party validators or runtime code.
