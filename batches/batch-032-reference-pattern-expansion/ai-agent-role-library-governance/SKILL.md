---
name: ai-agent-role-library-governance
description: Use when designing, reviewing, or operating an agent role library, AI agency, expert-agent team, role marketplace, handoff protocol, or multi-agent service catalog.
---

# AI Agent Role Library Governance

## When To Use

Use this skill when an agent workflow depends on reusable roles, expert-agent
teams, AI agency catalogs, persona libraries, or role-based handoffs.

This skill governs role design and composition only. It does not install role
packs, execute external agents, or grant tool permissions.

## Safe Workflow

1. Define each role by objective, inputs, outputs, authority boundary, tools,
   forbidden actions, and escalation triggers.
2. Keep persona tone secondary to deliverable quality, evidence requirements,
   and safety boundaries.
3. Build handoffs as contracts: upstream output schema, owner, acceptance
   criteria, unresolved risks, and next role.
4. Check for role overlap, role conflict, circular delegation, missing owner,
   and hidden decision authority.
5. Route tasks by capability fit and risk, not by entertaining role names.
6. Require final synthesis to identify source roles, disagreements, evidence,
   and decision owner.
7. Treat any external role pack as untrusted until license, provenance,
   prompts, tools, and runtime behavior are reviewed.

## Expected Output

- role catalog boundary
- role contract table
- handoff and ownership map
- conflict and overlap findings
- final synthesis policy
- external role-pack review boundary

## Verifier Expectations

- role authority and tool boundary check
- handoff schema check
- overlap and conflict check
- final owner check
- external role-pack provenance and license check

## Failure Handling

If role ownership, authority, or handoff acceptance criteria are unclear,
collapse the workflow to one accountable planner and list the blocked roles.
