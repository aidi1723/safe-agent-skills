# Community Skill Reference Closure Report

Date: 2026-06-16

Repository:

```text
https://github.com/aidi1723/safe-agent-skills
```

## Status

The community skill reference review is closed for the current scope.

This work checked whether higher-quality, verifiable community or official
skill sources should be added to the Safe-Agent-Skills system. The decision is
to expand the metadata-only reference library, not the trusted runtime catalog.

## Closure Baseline

Current verified baseline:

```text
total skills: 109
trusted skills: 103
quarantined skills: 3
review_required skills: 3
scenario bundles: 10
overlap groups: 7
external references: 9
top-level categories: 15 / 15
tampered skills: 0
unknown provenance records: 0
schema-check: ok
maintain-check: ok
reference-check: ok
router-eval: ok
full verification: 69 tests passing
```

## What Was Added

Three external references were added to:

```text
external-references/index.json
```

The entries are:

- OpenAI Skills Catalog for Codex
- Agent Skills Specification
- Snyk Agent Scan

All three are `metadata_only: true`. None is selected by default task packs,
none grants runtime permission, and none changes trusted catalog counts.

## Adoption Decision

The allowed use is reference-only:

- use OpenAI Skills Catalog for Codex for official ecosystem comparison and
  per-skill candidate discovery
- use Agent Skills Specification for skill structure, metadata, progressive
  disclosure, and evaluation alignment
- use Snyk Agent Scan as a scanner-rule and threat-model reference

The blocked use is runtime adoption:

- do not bulk-import external skill directories
- do not auto-install community skills
- do not execute external scanner code as a verifier without separate review
- do not promote a reference to trusted status without sanitization, hashes,
  provenance, and operator approval

## Supply-Chain Findings

Source and license records:

- `https://github.com/openai/skills`: official public OpenAI repository, but
  repository-level license was not declared by the GitHub API check on
  2026-06-16. Keep as `reference_only` until per-skill license and reuse rights
  are confirmed.
- `https://github.com/agentskills/agentskills`: Apache-2.0 specification
  repository. Suitable for process and schema alignment.
- `https://github.com/snyk/agent-scan`: Apache-2.0 scanner repository. Suitable
  for threat-model reference, but runtime execution requires a separate command
  and permission review.

Residual risk remains for all external ecosystems: upstream content can change,
README claims can be stale, runtime connectors can require accounts or network
permissions, and skill text can carry prompt-injection or policy-bypass
instructions. The current control is to keep these records metadata-only.

## Follow-Up Queue

Recommended next work:

1. Add a per-skill candidate review workflow for official catalog entries.
2. Compare local `SKILL.md` frontmatter and verifier expectations against the
   Agent Skills Specification.
3. Derive deterministic scanner fixtures from agent skill supply-chain attack
   patterns before considering any external scanner runtime.
4. Keep `reference-check` and `maintain-check --references` as release gates.

## Verification Evidence

Commands run:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer reference-check --references external-references/index.json
PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check \
  --registry catalog \
  --bundles bundles/index.json \
  --references external-references/index.json
PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval \
  --eval evals/router-quality.json \
  --registry catalog \
  --bundles bundles/index.json
bash scripts/verify.sh
```

Verified result:

```text
reference_count: 9
maintain-check: ok
router-eval: ok
tests: 69 passed
```

## Closure Decision

This review is complete.

The system now has a stronger, verifiable reference base for community and
official skill ecosystems while preserving the existing trusted-only execution
boundary.
