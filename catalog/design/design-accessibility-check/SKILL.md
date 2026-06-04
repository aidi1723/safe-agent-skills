---
name: design-accessibility-check
description: Use when reviewing interface accessibility, labels, contrast, keyboard reachability, focus states, and responsive readability.
---

# Design Accessibility Check

## When To Use

Use this skill when a UI needs accessibility review before release or when a
screen may be hard to read, navigate, or operate.

## Safe Workflow

1. Identify the target screen, component, or flow.
2. Check semantic labels, focus order, keyboard access, contrast, touch targets,
   and error messaging.
3. Review responsive text fit and state visibility.
4. Separate critical blockers from polish issues.
5. Verify fixes with browser inspection or screenshots when available.

## Expected Output

- accessibility findings by severity
- affected components
- remediation targets
- remaining risk notes

## Verifier Expectations

- keyboard path check
- contrast check
- responsive viewport check
- visible focus check

## Failure Handling

If live rendering is unavailable, perform a source-level review and name the
checks that still need browser verification.
