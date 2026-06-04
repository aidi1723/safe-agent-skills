---
name: execution-browser-check
description: Use when running bounded browser inspection, form-flow checks, screenshots, or UI smoke verification.
---

# Browser Execution Check

## When To Use

Use this skill when the task requires opening a page, checking a UI flow,
capturing a screenshot, or verifying that a browser-visible state works.

## Safe Workflow

1. Confirm the target URL or local dev server.
2. Use only approved hosts and user-provided pages.
3. Avoid collecting private session data unless the user explicitly scopes it for the task.
4. Capture navigation steps, screenshots, and final page state when useful.
5. Prefer assertions on visible text, URL, DOM state, or screenshot evidence.
6. Stop and report if authentication, payment, destructive submission, or account-sensitive actions are encountered.

## Expected Output

- browser action summary
- screenshot or assertion evidence
- observed failures and reproduction steps

## Verifier Expectations

- navigation trace
- screenshot check
- DOM or visible-text assertion
- approval record for account-sensitive actions

## Failure Handling

If the page cannot load or the browser action cannot complete, report the URL,
observed error, and last confirmed state.
