---
name: business-jira-workflow-review
description: Use when reviewing Jira workflows, issue taxonomies, project boards, status transitions, backlog hygiene, or delivery reporting setup.
---

# Business Jira Workflow Review

## When To Use

Use this skill when a team needs to review Jira workflows, issue types, boards,
status transitions, backlog hygiene, or delivery reporting.

## Safe Workflow

1. Identify project scope, teams, issue types, workflow states, reports, and
   governance owner.
2. Separate planning workflow, delivery workflow, incident or defect workflow,
   and reporting needs.
3. Check whether statuses, transitions, required fields, and boards match actual
   team behavior.
4. Flag permission, automation, compliance, and reporting changes for admin
   review before implementation.
5. Produce a workflow findings list and migration-safe improvement plan.

## Expected Output

- Jira workflow summary
- issue taxonomy findings
- backlog and board hygiene notes
- reporting gaps
- admin review checklist

## Verifier Expectations

- workflow-state consistency check
- required-field check
- permission boundary check
- migration risk check

## Failure Handling

If Jira configuration cannot be inspected, provide a review checklist and avoid
asserting current configuration behavior.
