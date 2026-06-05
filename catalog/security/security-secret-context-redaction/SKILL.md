---
name: security-secret-context-redaction
description: Use when reviewing logs, configs, prompts, screenshots, environment notes, or context packs for secrets and sensitive data before sharing.
---

# Security Secret Context Redaction

## When To Use

Use this skill when task context, logs, config snippets, prompts, or generated
reports may contain private access material, customer data, internal endpoints,
or other sensitive material.

## Safe Workflow

1. Identify the files, pasted text, screenshots, and generated artifacts that
   will be shared or retained.
2. Look for credential-like labels, private endpoints, customer identifiers,
   personal data, signing material, session values, and proprietary records.
3. Replace sensitive values with stable placeholders that preserve structure
   without preserving the secret.
4. Keep redaction notes separate from the sanitized artifact and avoid copying
   sensitive values into issue summaries.
5. Record unresolved uncertainty when a value looks sensitive but cannot be
   classified from local context.

## Expected Output

- context inventory
- redaction checklist
- sanitized placeholder policy
- unresolved sensitive-data questions
- safe sharing boundary

## Verifier Expectations

- sensitive label check
- placeholder consistency check
- artifact scope check
- sharing boundary check

## Failure Handling

If sensitive data is found, do not repeat the value in the response. Describe
the data class and location at a high level.
