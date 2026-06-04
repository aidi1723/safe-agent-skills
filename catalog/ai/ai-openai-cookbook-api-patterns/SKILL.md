---
name: ai-openai-cookbook-api-patterns
description: Use when reviewing OpenAI API implementation patterns, examples, evals, structured outputs, RAG, or application recipes.
---

# AI OpenAI Cookbook API Patterns

## When To Use

Use this skill when an application needs API usage patterns, structured output
contracts, eval examples, embeddings, retrieval, or practical LLM workflow
review.

## Safe Workflow

1. Identify the API feature, model, data source, cost boundary, and expected
   artifact.
2. Prefer minimal examples that prove the required behavior.
3. Record structured output, eval, and retry requirements before production use.
4. Keep API keys and private prompts out of skill content and reports.
5. Verify claims against current official docs when the API behavior may have
   changed.

## Expected Output

- API pattern summary
- minimal implementation checklist
- cost and retry notes
- eval or verification plan
- source freshness notes

## Verifier Expectations

- official documentation check when current behavior matters
- schema or format check
- cost and retry boundary check
- secret redaction check

## Failure Handling

If API behavior or model availability is uncertain, state the uncertainty and
verify against official docs before implementation.

## Boundary

This is a reference skill inspired by OpenAI Cookbook. It documents application
pattern review and does not include private API keys or runtime access.
