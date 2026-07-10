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

## Decision Guidance

Classify the check as `static_inspection`, `smoke_flow`, `responsive_visual`,
or `stateful_flow`. Static inspection confirms a bounded page and visible
state. A smoke flow verifies a short navigation or interaction path with clear
assertions. Responsive visual work compares stable layouts and content fit at
named viewports. Stateful flows cross forms, sessions, stored data, or account
boundaries and require explicit scope plus approval for any mutation.

Prefer visible text, semantic DOM state, URL, focus, and enabled/disabled state
assertions over timing alone. Use screenshots to prove rendered composition,
not as the only assertion for behavior. Record console and failed network
signals when they explain the observed state, while avoiding private payloads.

## Evidence Minimum

- approved URL or local server, environment, and starting state
- browser, viewport, route, and exact flow steps
- visible text, DOM, URL, focus, form, or state assertions
- desktop/mobile screenshots for visual or responsive claims
- console, request, media, canvas, loading, and error observations when relevant
- last confirmed state, reproduction steps, artifacts, and untested states
- approval record for authentication, payment, account, upload, or mutation risk

## References

Load [the browser verification evidence guide](references/browser-verification-evidence.md)
for multi-step flows, responsive review, forms, dynamic state, console/network
diagnosis, canvas or media, screenshots, and reproducible failure capture.

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
observed error, and last confirmed state. Stop before authentication, payment,
destructive submission, uploads, downloads, account mutation, private session
inspection, or non-approved hosts unless separately authorized.
