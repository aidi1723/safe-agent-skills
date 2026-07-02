---
name: content-onboarding-cro-review
description: Use when reviewing onboarding cro workflows, metadata-only skill candidates, upstream reference clusters, or local adoption drafts before catalog inclusion.
---

# Onboarding Cro Review

## When To Use

Use this draft when reviewing the `onboarding-cro` metadata-only
candidate from `claude-skills` before deciding whether to author a local
OneCode skill, merge it into an existing skill, or keep it reference-only.

## Safe Workflow

1. Identify the task, audience, owner, source domain, target catalog category,
   and expected artifact.
2. Compare the candidate with existing trusted Safe-Agent-Skills to avoid
   duplicate or overlapping guidance.
3. Draft local OneCode guidance from project requirements and operator review;
   do not copy upstream skill bodies.
4. Check provenance, license notes, runtime permissions, and connector
   assumptions before import.
5. Produce an adoption recommendation only; Do not execute upstream content or
   mark this draft trusted.

## Expected Output

- metadata-only candidate summary
- overlap and merge recommendation
- local authoring notes
- required verifier checklist
- adoption decision: convert, merge, keep reference-only, or reject

## Verifier Expectations

- metadata-only boundary check
- duplicate skill check
- provenance and license check
- import, serial approval, schema-check, maintain-check, and verify before trust

## Draft Metadata

- upstream candidate: `onboarding-cro`
- source domain: `marketing-skill`
- source path: `marketing-skill/skills/onboarding-cro`
- mapped category: `content`
- score: `50`
- priority: `P3`
- adoption before draft: `reference_only`
