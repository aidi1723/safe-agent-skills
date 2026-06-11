---
name: design-tailwind-radix-system
description: Use when building, reviewing, or refactoring a React UI design system based on Tailwind CSS, Radix UI primitives, shadcn/ui-style components, tokens, variants, and accessible interaction states.
---

# Design Tailwind Radix System

## When To Use

Use this skill when a React project needs a source-owned component system using
Tailwind CSS, Radix UI, shadcn/ui-style components, CSS variables, reusable
variants, or consistent app-wide UI primitives.

Use it with `design-ui-review` for page-level polish and
`design-accessibility-check` when keyboard, focus, labels, dialogs, menus, or
forms are release-critical.

## Safe Workflow

1. Identify the existing source of truth: `DESIGN.md`, Tailwind config, CSS
   variables, component primitives, Radix wrappers, and shared layout shells.
2. Map the visual language into semantic tokens before changing individual
   pages: background, surface, border, text, muted text, accent, danger,
   success, radius, shadow, spacing, and motion duration.
3. Use Radix for interaction behavior and accessibility semantics; use Tailwind
   and component variants for presentation. Do not bypass existing primitives
   with unrelated page-local styling.
4. Standardize core components first: button, input, select, textarea, checkbox,
   radio, switch, tabs, dialog, popover, dropdown menu, tooltip, badge, card,
   table, toast, navigation, and empty/error states.
5. Define variants for size, tone, emphasis, density, loading, disabled, focus,
   selected, destructive, and icon-only states. Keep variants discoverable and
   reusable.
6. Preserve routing, data flow, business logic, and form behavior unless the
   user explicitly requests product-level redesign.
7. Verify representative screens at desktop and narrow viewport sizes, including
   keyboard focus paths for Radix-backed controls.

## Expected Output

- token and theme source summary
- component inventory and gap list
- proposed shared primitive or variant changes
- affected screens or flows
- verification notes for build, viewport, and accessibility checks

## Verifier Expectations

- build or type check for frontend code
- screenshot check for at least one representative screen when rendering is available
- responsive viewport check for narrow and desktop layouts
- keyboard and focus check for Radix dialogs, menus, popovers, tabs, and forms
- contrast and disabled/loading/empty/error state spot check

## Failure Handling

If the project has no clear design-system source, mark the assumed source of
truth before recommending changes. If Radix or Tailwind is not actually present,
fall back to `design-system-consistency` and report that this skill only applies
as an implementation target, not as existing project evidence.
