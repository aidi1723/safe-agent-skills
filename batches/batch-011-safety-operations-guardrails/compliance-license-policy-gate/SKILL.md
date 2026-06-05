---
name: compliance-license-policy-gate
description: Use when reviewing third-party packages, copied snippets, assets, datasets, model files, or community skills for license and reuse risk.
---

# Compliance License Policy Gate

## When To Use

Use this skill when a project may adopt external code, prompts, docs, assets,
datasets, models, plugins, or reference workflows from third-party sources.

## Safe Workflow

1. Inventory each external source, owner, URL or local path, version, license,
   and intended reuse type.
2. Separate reference-only learning from copied content, runtime dependency,
   bundled asset, connector configuration, and generated derivative work.
3. Check compatibility with the project license, distribution model, attribution
   needs, notice files, and internal policy.
4. Flag unclear licenses, missing provenance, reciprocal-license risk,
   proprietary material, and unapproved model or dataset reuse.
5. Record whether the source can be trusted, needs review, must remain
   reference-only, or should be excluded.

## Expected Output

- source inventory
- license and reuse classification
- attribution or notice needs
- blocked or review-required items
- approved use boundary

## Verifier Expectations

- source provenance check
- license field check
- reuse type check
- policy decision check

## Failure Handling

If license or ownership cannot be verified, keep the material out of trusted
catalog or release output until review is complete.
