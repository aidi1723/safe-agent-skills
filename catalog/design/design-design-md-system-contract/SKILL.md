---
name: design-design-md-system-contract
description: Use when creating, reviewing, or enforcing DESIGN.md files, design-system source-of-truth docs, token maps, component states, accessibility notes, or implementation design contracts.
---

# Design DESIGN.md System Contract

## When To Use

Use this skill when a project uses or needs a `DESIGN.md` file as the source of
truth for visual direction, design tokens, components, accessibility, and
implementation constraints.

This skill reviews design documentation and implementation alignment only. It
does not import external design systems or override product requirements.

## Safe Workflow

1. Confirm whether `DESIGN.md` exists. If it exists, treat it as the visual
   source of truth unless the user explicitly changes direction.
2. If missing and the work is design-oriented, draft a concise brief covering
   audience, product tone, layout density, typography, colors, surfaces,
   motion, components, and accessibility.
3. Map design tokens to implementation locations before patching individual
   pages.
4. Require component states for navigation, buttons, forms, cards, tables,
   dialogs, empty states, loading, errors, focus, hover, and disabled states.
5. Check responsive behavior, content fit, contrast, keyboard reachability,
   and reduced-motion expectations.
6. Record deviations between implementation and `DESIGN.md` as explicit
   decisions, not silent drift.

## Expected Output

- DESIGN.md presence and authority decision
- design brief or gap list
- token and component-state map
- accessibility and responsiveness checks
- implementation alignment notes
- unresolved design decisions

## Verifier Expectations

- source-of-truth check
- token and component state coverage check
- responsive and content-fit check
- accessibility state check
- implementation drift check

## Failure Handling

If design authority is unclear, pause visual changes and produce a short
decision brief instead of making broad styling changes.
