# CLAUDE.md Reference Closure Report

Date: 2026-06-14

Repository:

```text
https://github.com/aidi1723/safe-agent-skills
```

## Status

The CLAUDE.md reference review is closed for the current scope.

This work evaluated the public `multica-ai/andrej-karpathy-skills` project and
the supplied social-post draft, then converted the useful parts into bounded
project updates without copying third-party prompt text or weakening the trust
model.

## Closure Baseline

Current verified baseline:

```text
total skills: 109
trusted skills: 103
quarantined skills: 3
review_required skills: 3
scenario bundles: 10
overlap groups: 7
external references: 6
top-level categories: 15 / 15
tampered skills: 0
unknown provenance records: 0
schema-check: ok
maintain-check: ok
reference-check: ok
full verification: 69 tests passing
```

## What Was Closed

### 1. External Reference Intake

`multica-ai/andrej-karpathy-skills` was added to
`external-references/index.json` as:

```text
adoption_status: reference_only
metadata_only: true
license: unknown
```

The reference records the project's useful behavioral-rule signal:

- think before coding
- simplicity first
- surgical changes
- goal-driven execution

It does not create a trusted skill, import repository content, execute code, or
grant runtime permission.

### 2. Claim Boundary

The social-post draft contained useful framing, but several claims were not
safe to publish as written:

- time-bound star count claims can become stale quickly
- "industry standard" is not established by popularity alone
- code-reduction percentages need source evidence
- "100% robustness" style claims are too absolute for public use

The local update preserves the market signal while avoiding unsupported public
claims.

### 3. Local Skill Refinement

`ecc-agent-coding-safety` was refined to make minimal-change discipline
explicit:

- state implementation-changing assumptions before editing
- choose the smallest implementation that satisfies the request
- avoid speculative abstractions, configuration, and adjacent cleanup
- verify that changed lines trace to the task or cleanup caused by the task

The catalog and batch copies were kept in sync, and the sanitized hash was
updated in `skill.json`, `SANITIZATION_REPORT.json`, and `catalog/index.json`.

### 4. Public Positioning Draft

A safe publication draft was added in
`docs/updates/2026-06-14-claude-md-reference.md`.

The core message is:

```text
Prompt files are a starting point. Trusted, verifiable skill routing is the
next layer.
```

This positions `safe-agent-skills` as a governance and routing layer above
single-project instruction files.

### 5. Maintenance Documentation

The maintenance and status docs now include the external-reference check path:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer reference-check \
  --references external-references/index.json
```

`maintain-check` examples now include:

```bash
--references external-references/index.json
```

## What Is Not Claimed

This closure does not claim:

- endorsement from Andrej Karpathy or the referenced repository owner
- legal clearance to copy third-party prompt text
- that GitHub stars prove safety, correctness, or trust
- that the referenced `CLAUDE.md` is an industry standard
- that local coding-agent outcomes will improve by a fixed percentage
- that external references can be selected by default task packs

External references remain metadata and context only.

## Verification Evidence

Commands run:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry catalog
PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check \
  --registry catalog \
  --bundles bundles/index.json \
  --references external-references/index.json
PYTHONPATH=src python3 -m onecode_skill_sanitizer schema-check --registry catalog
PYTHONPATH=src python3 -m onecode_skill_sanitizer reference-check \
  --references external-references/index.json
bash scripts/verify.sh
```

Verified result:

```text
registry status: ok
skill_count: 109
trusted_count: 103
tampered_count: 0
unknown_provenance_count: 0
reference_count: 6
reference-check: ok
schema-check: ok
maintain-check: ok
tests: 69 passed
```

## Remaining Risk

Remaining risks are bounded and recorded:

- the external repository license is unknown
- star counts and social traction may change after capture
- the public draft still needs platform-specific editing before publication
- no automated mechanism yet converts external references into local candidate
  skills

These are acceptable for a metadata-only reference closure.

## Closure Decision

The CLAUDE.md reference review is complete.

Future work should treat this project as a market-signal and behavior-pattern
reference, not as trusted source material.
