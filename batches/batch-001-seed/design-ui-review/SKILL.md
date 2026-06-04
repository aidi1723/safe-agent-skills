---
name: design-ui-review
description: Use when reviewing or polishing a UI screen, dashboard, or frontend view for layout, visual hierarchy, responsiveness, and accessibility.
---

# Design UI Review

## When To Use

Use this skill when the task asks to improve a user interface, review a page,
polish a dashboard, or check frontend visual quality.

## Safe Workflow

1. Identify the target screen, route, component, or screenshot.
2. Preserve business logic, routing, data contracts, and user workflows unless the user explicitly requests product-level redesign.
3. Review typography, spacing, alignment, color contrast, density, empty states, loading states, and responsive behavior.
4. Prefer shared tokens, reusable components, and existing design patterns before editing one-off page styles.
5. If visual verification is available, capture desktop and mobile screenshots and compare them against the requested outcome.

## Expected Output

- concise findings or focused implementation changes
- screenshot or viewport verification when available
- clear notes for any remaining visual risk

## Verifier Expectations

- build check for frontend code
- screenshot check for important screens
- responsive viewport check for mobile and desktop
- accessibility check for contrast, labels, and keyboard reachability

## Failure Handling

If the UI cannot be rendered or inspected, report the blocker and the exact
verification that could not be completed.
