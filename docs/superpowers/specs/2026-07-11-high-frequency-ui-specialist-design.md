# High-Frequency UI Specialist Design

Date: 2026-07-11
Status: approved direction, pending implementation

## Goal

Promote the existing high-frequency `design-ui-review` catalog skill from a
routing card to a specialist playbook for UI creation, redesign, review, and
polish without introducing a duplicate skill or another overlapping scenario.

## Scope

The change will:

- keep `design-ui-review` as the primary UI skill in the overlap group;
- keep the existing `website-build-launch` and `design-md-system-governance`
  scenario structure;
- classify `design-ui-review` as `specialist` in the depth policy;
- add decision guidance, evidence minimums, escalation rules, and a focused
  on-demand UI design reference;
- protect the new reference with the existing auxiliary-content hash;
- reseal the skill and synchronize the catalog and batch lifecycle indexes;
- add regression coverage and update maintained project records.

The change will not create a new UI skill, replace `design-md-ui`, alter router
selection semantics, add a frontend application, or redesign repository UI.

## Skill Responsibilities

`design-ui-review` will cover the common end-to-end UI workflow:

1. Determine product type, audience, primary workflow, and viewport targets.
2. Locate or create the visual source of truth, using `DESIGN.md` when present.
3. Choose an implementation base appropriate to the existing stack and product
   type without replacing a working framework unnecessarily.
4. Define or map semantic tokens and shared primitives before page-level edits.
5. Cover navigation, forms, tables, dialogs, empty/loading/error states,
   focus/hover/disabled states, responsive behavior, and content fit.
6. Preserve routing, data flow, business logic, and information architecture
   unless product redesign is explicitly requested.
7. Verify important workflows at desktop and mobile widths, with accessibility
   and screenshot evidence when the UI can be rendered.

The skill will delegate narrower concerns rather than duplicate them:

- `design-design-md-system-contract` owns DESIGN.md governance;
- `design-system-consistency` owns cross-screen token/component drift;
- `design-visual-quality-review` owns senior visual-quality critique;
- responsive, accessibility, motion, and premium landing skills remain focused
  verifiers or optional specialists selected by existing bundles.

## Reference Design

Add `references/ui-design-playbook.md` with conditional guidance for:

- data-heavy React and Vue admin products;
- React component systems and SaaS applications;
- marketing, documentation, and GEO sites;
- premium landing-page accents and motion;
- source-of-truth, token, state, responsive, accessibility, and visual QA.

The reference will follow the existing `design-md-ui` framework combination
and premium visual maps while remaining concise and repository-safe. It will
describe selection criteria and verification expectations, not install or
execute third-party frameworks.

## Integrity And Compatibility

Resealing will update `sanitized_sha256`, `auxiliary_sha256`, and
`manifest_sha256` for `design-ui-review`. The catalog index will be rebuilt
without rewriting unrelated reports. The batch index will retain its historical
promotion record and record the evolved catalog hash with
`content_match: false`.

Public Schema v1 task-pack hash shape remains unchanged. Existing scenario,
bundle, overlap, and trusted-only selection behavior must continue to pass.

## Verification

Implementation is complete only when:

- the depth audit reports 168 routing cards and 4 specialists with no errors or
  warnings;
- registry verification reports 172 skills, 166 trusted, and 0 tampered;
- manifest schema and batch lifecycle checks pass;
- focused depth, registry, router, and documentation tests pass;
- `scripts/verify.sh` passes locally;
- the maintenance log and closure report record UI design as a high-frequency
  specialist capability.

## Residual Boundaries

This specialist provides design method and verification requirements. It does
not grant browser, network, package-installation, credential, publishing, or
production authority. Visual quality still requires rendered evidence when a
frontend is available, and the host project remains the authority for its
framework, brand, product behavior, and accessibility obligations.
