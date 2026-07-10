---
name: design-ui-review
description: Use when creating, redesigning, reviewing, or polishing UI screens, dashboards, frontend views, design systems, responsive layouts, interaction states, or accessibility-sensitive interfaces.
---

# Design UI Review

## When To Use

Use this skill when the task asks to create or improve a user interface, review
a page, polish a dashboard, align a design system, or verify frontend visual
quality across desktop and mobile.

## Safe Workflow

1. Identify the product type, audience, primary workflow, target screens, and viewport range.
2. Read `DESIGN.md` or the established theme and component system before choosing a visual direction. If no source of truth exists, record a concise design brief before broad changes.
3. Preserve business logic, routing, data contracts, information architecture, and user workflows unless the user explicitly requests product-level redesign.
4. Map semantic color, typography, spacing, surface, motion, and state tokens before editing individual pages.
5. Implement or review shared primitives before page-specific styling. Cover navigation, controls, forms, tables, dialogs, loading, empty, error, success, focus, hover, selected, and disabled states that exist in the workflow.
6. Check hierarchy, density, content fit, contrast, keyboard reachability, reduced motion, and stable responsive behavior.
7. When rendering is available, verify the primary workflow with desktop and mobile screenshots and record any untested routes, states, or viewports.

## Expected Output

- concise findings or focused implementation changes
- screenshot or viewport verification when available
- clear notes for any remaining visual risk

## Decision Guidance

Classify the task before changing the interface:

- `focused_review`: inspect or repair a bounded screen or component without
  changing the product structure.
- `system_restyle`: change shared tokens, primitives, or component families
  while preserving workflows and information architecture.
- `new_interface`: create a new screen or flow within established product and
  technical constraints.
- `product_redesign`: change navigation, information architecture, workflow,
  or product behavior; require explicit user scope before proceeding.

Prefer the existing framework and design system when they can satisfy the
request. Select a new implementation base only for a new foundation or a
documented capability gap. Use expressive effects for marketing moments, not
dense operational surfaces, and never trade readability, performance, or
accessibility for novelty.

## Evidence Minimum

- product type, audience, primary task, and affected workflow
- visual source of truth or explicit design brief and assumptions
- existing framework, theme, tokens, shared primitives, and constraints
- target screens, content extremes, viewport range, and required states
- desktop and mobile render evidence when the UI can run
- build, interaction, accessibility, overflow, and responsive results
- unresolved visual risks, untested states, and approvals still required

## References

Load [the UI design playbook](references/ui-design-playbook.md) for new
interfaces, system-wide restyles, framework or component-base decisions,
premium visual work, or a complete responsive and state-quality pass.

## Verifier Expectations

- build check for frontend code
- screenshot check for important screens
- responsive viewport check for mobile and desktop
- accessibility check for contrast, labels, and keyboard reachability

## Failure Handling

If the UI cannot be rendered or inspected, report the blocker and the exact
verification that could not be completed. Do not claim visual completion from
source inspection alone. Package installation, network access, credentials,
publishing, and production changes remain subject to host approval.
