---
name: design-visual-quality-review
description: Use when reviewing frontend visual quality, visual hierarchy, typography, spacing, color balance, density, polish, or whether an AI-generated interface looks generic or unfinished.
---

# Design Visual Quality Review

## When To Use

Use this skill when a UI needs a senior visual-design pass beyond basic layout
correctness: hierarchy, composition, density, typography, color, contrast,
spacing rhythm, surface treatment, icon use, and whether generated UI feels
credible for the product domain.

Use it with `design-system-consistency` when tokens and components need
alignment, and with `design-motion-interaction-polish` when static visuals are
solid but interaction feedback still feels weak.

## Safe Workflow

1. Identify the product domain, audience, primary workflow, viewport targets,
   and existing design source of truth.
2. Review hierarchy first: primary task, scan path, information density,
   grouping, and whether important actions are visually discoverable.
3. Review visual system quality: type scale, line height, spacing rhythm,
   color roles, borders, shadows, radius, icons, and empty/loading/error states.
4. Flag AI-looking artifacts: generic gradients, random decorative elements,
   inconsistent cards, weak contrast, oversized hero type inside tools,
   repeated same-hue palettes, and decorative motion without state meaning.
5. Prefer token, theme, or reusable component fixes before page-level patches.
6. Preserve routing, data contracts, business behavior, and accessibility
   boundaries unless the user explicitly requests product redesign.
7. Verify with screenshots or viewport checks when rendering is available.

## Expected Output

- visual quality findings ordered by user impact
- token, component, or layout change targets
- domain-fit notes for density, tone, and polish
- accessibility or responsive visual risks
- screenshot or viewport verification notes when available

## Verifier Expectations

- design source-of-truth check
- desktop and mobile visual review
- contrast and text-overflow spot check
- component and token consistency check
- screenshot evidence when UI rendering is available

## Failure Handling

If the product domain, audience, or visual source of truth is unclear, state the
assumption before recommending visual changes. If no rendered UI is available,
perform a source-level review and name the browser checks still required.
