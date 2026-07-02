---
name: code-claude-skills-engineering-role-review
description: Use when reviewing senior-engineer, fullstack, frontend, backend, ML, cloud architect, QA, prompt engineering, security, or code-role references from the claude-skills backlog.
---

# Code Claude Skills Engineering Role Review

## When To Use

Use this skill when a backlog candidate is framed as a developer, architect,
reviewer, QA, prompt engineer, ML engineer, cloud architect, or security role
and must be converted into bounded code-review or implementation guidance.

## Safe Workflow

1. Identify the engineering surface, repository context, target artifact,
   test surface, risk level, and owner.
2. Convert role language into concrete tasks: review, design, migrate, test,
   debug, harden, evaluate, or document.
3. Route implementation work through existing code, security, CI, and testing
   skills before adding new catalog entries.
4. Require explicit verification for code changes: targeted tests, build or
   type checks, schema checks, and review notes.
5. Keep cloud, account, deployment, and production actions outside the skill
   unless the host runtime separately approves them.

## Expected Output

- role-to-task conversion
- code surface and risk map
- required verification commands
- existing trusted skill coverage
- adoption decision and missing capability notes

## Verifier Expectations

- regression-test plan check
- cloud or account boundary check
- duplicate code-skill check
- candidate-map coverage check

## Failure Handling

If the candidate remains a broad senior-role persona, keep it cluster-mapped
and do not create a separate trusted skill until a repeatable task contract is
clear.
