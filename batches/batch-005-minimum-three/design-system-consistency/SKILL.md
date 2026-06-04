---
name: design-system-consistency
description: Use when checking UI tokens, components, spacing, typography, states, and visual consistency across screens.
---

# Design System Consistency

## When To Use

Use this skill when a product has repeated UI components, mixed styling, uneven
spacing, or inconsistent states across pages.

## Safe Workflow

1. Identify the shared tokens, component library, theme layer, and target screens.
2. Compare typography, spacing, radius, color, borders, shadows, and states.
3. Prefer shared token or component fixes before page-specific overrides.
4. Preserve routing, data contracts, and business behavior.
5. Verify at least one dense screen and one narrow viewport when possible.

## Expected Output

- consistency findings
- token or component change targets
- affected screens
- verification notes

## Verifier Expectations

- build check
- screenshot check when UI rendering is available
- responsive check for narrow and wide viewports
- accessibility spot check

## Failure Handling

If the design system source is unclear, mark the assumed source of truth before
making recommendations.
