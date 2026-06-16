# Scenario System Expansion

Date: 2026-06-16

This update records the evaluation of four external skill-group ideas against
the maintained Safe-Agent-Skills scenario system:

- frontend design: design system, visual review, and CSS animation polish
- engineering development: exploration, review, debugging, tests, and
  simplification
- content creation: copywriting, content strategy, and Remotion-style video
  production
- planning and orchestration: deep interview, plan decomposition, and
  multi-agent teamwork

## Decision

Do not directly import or trust external skill names without source,
license, provenance, and runtime boundary records.

Promote the high-confidence parts as scenario-system maintenance instead:

- add `codebase-change-lifecycle` as a trusted bundle
- add `agent-planning-orchestration` as a trusted bundle
- keep frontend design inside the existing `website-build-launch` bundle and
  route signals
- add `content-video-production` as a trusted method-only bundle after adding a
  programmatic-video boundary skill

## Added Skills

Five locally authored, sanitized, and approved skills were added to convert the
reference abilities into maintainable catalog assets:

- `design-visual-quality-review`
- `codebase-explore-map`
- `code-simplify-refactor-plan`
- `content-strategy-matrix`
- `media-remotion-video-production-boundary`

## Rationale

The existing catalog already has trusted skills for UI review, design-system
consistency, motion polish, code review, debugging, regression testing,
requirements briefs, and multi-agent orchestration. The gap was mainly routing
and scenario composition, not raw skill count.

The content video workflow is useful as a method bundle, but programmatic video
execution remains outside default authority. Rendering, dependency install,
cloud render, upload, publication, asset rights, and Remotion license review
still require separate approval.

## Verification Targets

Router regression cases now cover:

- AI interface design polish routes to `website-build-launch`
- engineering lifecycle tasks route to `codebase-change-lifecycle`
- planning and multi-agent tasks route to `agent-planning-orchestration`
- content video production tasks route to `content-video-production`

Remotion is recorded as a metadata-only external reference. The local
`media-remotion-video-production-boundary` skill is a OneCode-authored method
rewrite and does not copy or execute Remotion runtime code.

## Closure

The implementation and verification summary is recorded in
[Scenario Capability Expansion Closure Report](../scenario-capability-expansion-closure-report.md).
