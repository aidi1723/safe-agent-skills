---
name: security-llm-guard-io-scanning
description: Use when reviewing LLM input and output scanning, sensitive-data filtering, or prompt security gates.
---

# Security LLM Guard IO Scanning

## When To Use

Use this skill when prompts, retrieved context, tool outputs, or model responses
need scanning before they enter or leave an agent workflow.

## Safe Workflow

1. Identify each input and output boundary in the agent flow.
2. Classify scan concerns: sensitive data, prompt injection, toxicity,
   prohibited content, insecure URLs, or unsafe tool guidance.
3. Prefer redaction or quarantine before the content reaches a higher-privilege
   tool.
4. Keep scanner findings separate from final user-facing text.
5. Record what was blocked, redacted, allowed, or escalated.

## Expected Output

- scanned boundary list
- finding categories
- redaction or block decisions
- residual risk notes
- escalation recommendation

## Verifier Expectations

- input boundary check
- output boundary check
- sensitive data redaction check
- prompt injection review

## Failure Handling

If a scanner cannot determine whether content is safe, preserve the content in
review state and avoid passing it to privileged tools.

## Boundary

This is a reference skill inspired by Protect AI LLM Guard. It documents safe
I/O scanning patterns and does not include scanner packages or rulesets.
