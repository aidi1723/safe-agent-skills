---
name: ai-opensquilla-metaskill-workflow
description: Use when turning repeated multi-step agent work into reusable scenario skills, workflows, or bundle candidates.
---

# AI OpenSquilla MetaSkill Workflow

## When To Use

Use this skill when a repeated agent task should be captured as a reusable
workflow, scenario bundle, or higher-level meta skill.

## Safe Workflow

1. Identify the repeated task, expected artifact, and required verification.
2. Split the workflow into stable steps with clear stop conditions.
3. Record which existing trusted skills belong in the workflow.
4. Keep runtime tools and connectors outside the skill definition.
5. Promote the workflow to a bundle only after provenance and trusted status are
   verified for every referenced skill.

## Expected Output

- repeated task summary
- candidate meta skill or bundle name
- ordered skill list
- verification gates
- runtime permission boundary

## Verifier Expectations

- trusted-only bundle check
- provenance check
- duplicate workflow check
- operator review before publication

## Failure Handling

If the repeated task depends on untrusted skills or unclear permissions, keep
the workflow as a draft and do not add it to default bundles.

## Boundary

This is a reference skill inspired by OpenSquilla MetaSkills. It documents a
workflow capture pattern and does not copy OpenSquilla runtime code.
