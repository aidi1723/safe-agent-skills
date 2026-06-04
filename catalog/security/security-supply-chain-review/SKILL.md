---
name: security-supply-chain-review
description: Use when reviewing package, plugin, connector, dependency, or skill supply-chain risk before adoption.
---

# Security Supply Chain Review

## When To Use

Use this skill when a project plans to add an external package, connector,
plugin, model asset, or community skill.

## Safe Workflow

1. Identify the source URL, author, license, release history, and intended use.
2. Review install path, runtime permissions, update behavior, and maintainer risk.
3. Check for unusual scripts, network behavior, hidden persistence, or unclear
   provenance.
4. Prefer read-only evaluation before enabling runtime use.
5. Record approval requirements and residual risk.

## Expected Output

- source and license record
- risk summary
- allowed use recommendation
- approval checklist
- evidence links

## Verifier Expectations

- provenance check
- license check
- package script review when applicable
- permission and connector boundary review

## Failure Handling

If provenance or license cannot be confirmed, recommend quarantine until the
missing record is resolved.
