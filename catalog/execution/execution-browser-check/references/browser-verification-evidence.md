# Browser Verification Evidence

Use this guide to produce reproducible browser evidence for a bounded workflow.

## Setup

Record the approved target, server readiness, browser, viewport, starting URL,
authentication state, test data, and actions that are prohibited. Confirm that
the page is not a stale error or blank render before testing deeper behavior.

## Assertions

Tie each step to visible text, semantic DOM state, URL, focus, control state,
or a stable screenshot. Check loading, empty, error, success, disabled, and
validation states that belong to the flow. Use desktop and mobile viewports for
responsive claims and inspect content overflow or occlusion.

## Diagnostics

Capture relevant console errors, failed requests, media or canvas output, and
the last confirmed state without exposing private payloads. Distinguish page
failure from server, browser automation, asset, and test-data failures.

## Handoff

Record exact reproduction steps, expected and observed results, screenshots or
traces, untested states, and any action stopped for approval.
