---
name: execution-browser-use-web-task
description: Use when designing browser-based agent tasks, web navigation plans, form workflows, or online task automation boundaries.
---

# Execution Browser Use Web Task

## When To Use

Use this skill when an agent needs to interact with websites, inspect pages,
collect visible information, or complete bounded browser workflows.

## Safe Workflow

1. Identify target URLs, account context, allowed actions, and stop conditions.
2. Separate read-only browsing from form submission, payment, account, or
   destructive actions.
3. Prefer visible page evidence and screenshots for verification.
4. Avoid collecting private session data unless explicitly scoped.
5. Stop and request approval before account-sensitive or irreversible actions.

## Expected Output

- browser task plan
- allowed and forbidden actions
- navigation evidence
- screenshot or visible-state notes
- blocked action list

## Verifier Expectations

- URL scope check
- visible evidence check
- screenshot or DOM check
- approval check for sensitive actions

## Failure Handling

If a site requires sensitive login, payment, or destructive submission, stop
and report the required approval.

## Boundary

This is a reference skill inspired by browser-use. It documents safe browser
agent workflow patterns and does not bundle automation code.
