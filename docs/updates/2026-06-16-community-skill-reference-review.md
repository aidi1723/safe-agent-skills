# Community Skill Reference Review

Date: 2026-06-16

This update reviews whether stronger, verifiable community skill sources should
be included in the Safe-Agent-Skills system.

## Decision

Do not directly import or trust-run any external community skill as part of this
review.

Add three metadata-only external references instead:

- OpenAI Skills Catalog for Codex: official public Codex skill catalog and
  curated examples, kept as `reference_only` because the repository-level
  license is not declared.
- Agent Skills Specification: Apache-2.0 specification and documentation for
  skill structure, progressive disclosure, and evaluation guidance.
- Snyk Agent Scan: Apache-2.0 agent, MCP, and skill security scanner reference
  for future supply-chain and prompt-injection scanner hardening.

These entries are evidence and design references only. They do not affect normal
task-pack selection, do not add runtime tools, and do not change the trusted
catalog.

## Review Findings

The current project already has the right adoption model:

- external material starts outside trusted execution
- references are metadata-only
- trusted selection is limited to local sanitized catalog entries
- scenario bundles must reference trusted skills only
- registry, bundle, overlap, schema, and reference checks are automated

The main improvement opportunity is not more raw skills. It is a stricter
conversion queue for official and high-signal sources.

## Candidate Priority

Priority 1: specification and evaluation alignment.

- Use Agent Skills Specification to compare local `SKILL.md` structure,
  metadata expectations, progressive-disclosure boundaries, and skill eval
  practices.

Priority 2: security scanner rule hardening.

- Use Snyk Agent Scan as a threat-model and scanner-rule reference for agent
  skill supply-chain review. Do not add it as a runtime verifier until its
  command behavior and CI permissions are reviewed.

Priority 3: per-skill official catalog conversion.

- Review OpenAI curated Codex skills one by one. Good first candidates are
  security and engineering method skills such as CI fixing, threat modeling,
  security best practices, and ownership mapping. Each candidate still needs
  license confirmation, provenance recording, sanitization, hash recording, and
  manual approval before becoming trusted.

## Non-Adoption Rationale

High GitHub traction, official ownership, or community popularity is not enough
for trusted adoption. External skills can contain runtime assumptions, connector
permissions, mutable install behavior, hidden prompt instructions, or license
ambiguity. The safe path is metadata-only reference first, then local
sanitization and explicit promotion.

## Verification

Run:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer reference-check --references external-references/index.json
PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check --registry catalog --bundles bundles/index.json --references external-references/index.json
PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval --eval evals/router-quality.json --registry catalog --bundles bundles/index.json
```

