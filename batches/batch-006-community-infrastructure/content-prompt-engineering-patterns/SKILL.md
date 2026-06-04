---
name: content-prompt-engineering-patterns
description: Use when designing prompts, context instructions, RAG workflows, agent behavior specs, or prompt review checklists.
---

# Content Prompt Engineering Patterns

## When To Use

Use this skill when a prompt, system note, RAG instruction, or agent workflow
needs clearer task framing, context control, examples, or evaluation criteria.

## Safe Workflow

1. Define the task, audience, allowed context, and expected artifact.
2. Separate instructions, examples, constraints, and evaluation criteria.
3. Keep safety hierarchy explicit and avoid ambiguous authority language.
4. Include only examples that reduce ambiguity.
5. Add verification criteria so output can be reviewed without changing the
   prompt after the fact.

## Expected Output

- prompt structure
- context and constraint notes
- example policy
- evaluation checklist
- safety hierarchy notes

## Verifier Expectations

- instruction clarity check
- context boundary check
- example relevance check
- prompt injection review

## Failure Handling

If the target behavior cannot be measured, define a small evaluation checklist
before expanding the prompt.

## Boundary

This is a reference skill inspired by the Prompt Engineering Guide. It
documents prompt design patterns and does not copy prompt libraries or course
content.
