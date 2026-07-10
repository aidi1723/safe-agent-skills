# UI Design Playbook

Use this guide when a task requires implementation-level UI creation or a
substantial visual pass. Preserve the host project's product behavior and
technical stack unless the request explicitly changes them.

## Product And Framework Fit

- For data-heavy React admin tools, prefer the existing app stack; use Refine
  only when a new resource-oriented foundation is actually needed, and use
  shadcn/ui or existing source-owned primitives for the presentation layer.
- For Vue admin products, retain the existing Vue system; consider Soybean
  Admin only for new admin foundations that need its routing and permissions.
- For marketing, documentation, and GEO sites, prefer semantic Astro or the
  repository's existing framework. Treat AstroWind as a starter, not a visual
  identity.
- For React SaaS component systems, choose source-owned shadcn/ui and Radix
  when long-term control matters; choose HeroUI when delivery speed matters
  more than owning every primitive.
- Use Motion for React for state meaning and continuity. Keep Magic UI or
  Aceternity UI to selective landing-page accents, never dense work surfaces.

## Source Of Truth And Implementation Order

Read `DESIGN.md` first. If it is absent, record audience, product tone,
density, typography, semantic colors, surfaces, component states, motion, and
accessibility in a concise design brief before broad visual changes. Implement
tokens first, shared primitives second, representative flows third, and only
then sweep page-level drift.

## State And Responsive Coverage

Cover default, hover, focus, active, selected, disabled, loading, empty, error,
and success states that exist in the workflow. Check content fit, keyboard
reachability, reduced motion, contrast, and stable layouts at narrow mobile
and wide desktop viewports.

## Visual Verification

Verify the primary workflow with rendered desktop and mobile screenshots.
Check page silhouette, component family, hierarchy, overflow, and state
feedback. When rendering is unavailable, name the unverified routes, states,
and viewports instead of claiming visual completion.
