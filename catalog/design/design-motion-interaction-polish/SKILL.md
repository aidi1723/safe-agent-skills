---
name: design-motion-interaction-polish
description: Use when adding or reviewing UI micro-interactions, CSS animations, Motion for React transitions, hover and focus feedback, scroll reveals, loading states, or reduced-motion behavior in a web interface.
---

# Design Motion Interaction Polish

## When To Use

Use this skill when a web UI needs higher-quality interaction motion: hover
feedback, press states, focus transitions, menu/dialog animation, layout
continuity, skeleton/loading motion, scroll reveal, or Motion for React
choreography.

Use it after the static layout, hierarchy, and component system are already
coherent. Do not use it to compensate for weak content structure or unclear UI.

## Safe Workflow

1. Identify the interaction purpose: orientation, feedback, continuity,
   disclosure, loading progress, or brand expression.
2. Define a small motion vocabulary: durations, easing, distance, opacity,
   scale, delay, and stagger. Keep the vocabulary consistent across components.
3. Prefer lightweight CSS transitions for simple state changes. Use Motion for
   React or framework motion tools only when layout transitions, gestures, or
   sequencing need them.
4. Add motion to meaningful states: hover, active, focus-visible, selected,
   opening, closing, loading, success, error, and route or layout changes.
5. Respect reduced-motion preferences and ensure animations do not hide focus,
   block input, cause text overlap, or degrade mobile readability.
6. Keep motion restrained in dense dashboards and operational tools; reserve
   expressive choreography for landing pages, product storytelling, or brand
   moments.
7. Verify that animations support the task, remain performant, and do not create
   jank, flicker, unexpected scroll jumps, or inaccessible state changes.

## Expected Output

- interaction goals and affected components
- motion vocabulary or token recommendations
- implementation targets for CSS or motion library usage
- reduced-motion and accessibility notes
- viewport or screenshot evidence when rendering is available

## Verifier Expectations

- build check for frontend code
- reduced-motion behavior check when animations are added
- desktop and mobile viewport check for overlap, clipping, and layout stability
- focus-visible and keyboard interaction check for animated controls
- performance spot check for scroll, hover, and transition jank on key screens

## Failure Handling

If the UI is visually inconsistent before motion work, recommend fixing static
tokens, layout, and components first. If animation cannot be rendered, perform a
source-level review and name the browser checks still required.
