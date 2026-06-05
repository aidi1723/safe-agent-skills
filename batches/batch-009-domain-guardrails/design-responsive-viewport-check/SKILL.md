---
name: design-responsive-viewport-check
description: Use when reviewing responsive UI layouts, viewport breakpoints, text overflow, mobile readability, or screenshot-based layout regressions.
---

# Design Responsive Viewport Check

## When To Use

Use this skill when a UI, page, dashboard, or component must work across
mobile, tablet, desktop, and wide viewports.

## Safe Workflow

1. Identify target routes, key components, supported viewport widths, and
   content that may expand or wrap.
2. Check layout at narrow, default desktop, and wide desktop sizes before
   judging the design complete.
3. Look for horizontal scroll, clipped text, overlapping controls, broken
   grids, unstable fixed-format elements, and unreadable density.
4. Prefer shared layout tokens, constraints, and component fixes before
   one-off page overrides.
5. Record viewport evidence and unresolved responsive risks.

## Expected Output

- viewport checklist
- layout findings
- affected routes or components
- screenshot or DOM evidence when available
- fix targets or residual risk notes

## Verifier Expectations

- narrow viewport check
- desktop viewport check
- wide viewport check when relevant
- text overflow and overlap check

## Failure Handling

If the UI cannot be rendered, report the route, missing runtime, and the
viewport checks that could not be completed.
