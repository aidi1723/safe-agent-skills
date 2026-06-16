# Batch 015 Scenario Capability Expansion

Date: 2026-06-16

This batch converts four high-value capability groups into local,
provenance-recorded Safe-Agent-Skills assets.

## Added Trusted Skills

| Skill | Category | Purpose |
| --- | --- | --- |
| `design-visual-quality-review` | design | Review visual hierarchy, polish, and AI-generated UI quality. |
| `codebase-explore-map` | code | Map an unfamiliar repository before implementation or review. |
| `code-simplify-refactor-plan` | code | Plan behavior-preserving simplification and refactors. |
| `content-strategy-matrix` | content | Plan multi-format content matrices and production queues. |
| `media-remotion-video-production-boundary` | media | Plan Remotion-style video production while keeping rendering and publishing outside default authority. |

## Scenario Updates

- `website-build-launch` now includes `design-visual-quality-review`.
- `codebase-change-lifecycle` now includes `codebase-explore-map` and
  `code-simplify-refactor-plan`.
- `content-video-production` is promoted to a trusted method-only bundle using
  `content-strategy-matrix` and
  `media-remotion-video-production-boundary`.

## Safety Boundary

These skills provide method only. They do not grant runtime permission for
filesystem writes, dependency installation, browser access, rendering, cloud
rendering, account access, uploads, or publication.

Remotion remains a metadata-only external reference. Runtime use requires
separate license, asset-rights, dependency, account, and host approval review.
