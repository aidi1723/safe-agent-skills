---
name: engineering-claude-skills-operations-review
description: Use when reviewing MCP, codebase onboarding, observability, runbook, environment, setup, run, status, secrets, API testing, or engineering-operations references from the claude-skills backlog.
---

# Engineering Claude Skills Operations Review

## When To Use

Use this skill when a backlog candidate concerns engineering operations, MCP
server design, codebase onboarding, observability, runbooks, environment setup,
status workflows, secrets handling, API testing, migration, or release gates.

## Safe Workflow

1. Identify repository scope, environment, command surface, data boundary,
   owner, and expected operational artifact.
2. Separate read-only analysis from workspace writes, environment mutation,
   account access, external services, and production activity.
3. Map operational tasks to existing engineering, code, security, execution,
   and CI skills before creating new catalog entries.
4. Convert candidates into bounded runbooks, onboarding maps, SLO reviews,
   test plans, or environment checklists with explicit verification commands.
5. Stop before credential use, deployment, production writes, or unapproved
   network actions.

## Expected Output

- operational scope and permission boundary
- artifact and verification contract
- trusted-skill coverage map
- runbook or checklist outline
- adoption decision and blocked runtime assumptions

## Verifier Expectations

- command and environment boundary check
- credential and account boundary check
- CI or local verification check
- candidate-map coverage check

## Failure Handling

If runtime permissions are unclear, keep the task in review mode and produce a
bounded plan instead of attempting operational execution.
