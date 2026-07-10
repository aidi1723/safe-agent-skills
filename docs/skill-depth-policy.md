# Skill Depth Policy

Skill quality is not measured by a universal line-count target. The catalog
uses three instruction-depth classes:

- `routing_card`: concise scope, bounded workflow, output, and verifier contract
- `playbook`: routing guidance plus decisions, failure modes, examples, and checklists
- `specialist`: concise entry guidance backed by on-demand references or assets

`catalog/depth-policy.json` is the machine-readable policy. Skills default to
`routing_card`; explicit overrides identify skills whose risk or task
complexity requires greater depth.

Repeated high-frequency use is also a valid promotion signal. A routing card
may become a specialist when real tasks repeatedly need decision criteria,
state coverage, evidence expectations, or an on-demand reference that would be
too heavy for every routing context. `design-ui-review` is the first specialist
promoted explicitly on this basis. The first high-frequency specialist batch
extends the same policy to code review, regression testing, and source
verification while retaining their established scenario and overlap roles.
The remaining high-frequency batches apply the same rule to repository
exploration, browser and CI verification, PDF and DOCX delivery, table
analysis, SEO briefing, and publication readiness. These promotions deepen
existing roles; they do not create duplicate skills or new scenario bundles.

The `depth-check` command treats missing required sections and invalid policy
classes as errors. Word count, missing examples, missing decision guidance,
and thin specialist references begin as warnings. This prevents mechanical
padding while still exposing likely depth gaps for review.

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer depth-check \
  --catalog catalog \
  --policy catalog/depth-policy.json
```

References and scripts under a catalog skill are protected by the optional
`hashes.auxiliary_sha256` manifest field. After an approved body or reference
change, reseal the skill explicitly and rebuild the registry index:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer reseal-content \
  catalog/security/security-supply-chain-review
PYTHONPATH=src python3 -m onecode_skill_sanitizer reseal-content \
  catalog/design/design-ui-review
PYTHONPATH=src python3 -m onecode_skill_sanitizer reseal-content \
  catalog/code/code-review-risk
PYTHONPATH=src python3 -m onecode_skill_sanitizer reseal-content \
  catalog/code/code-test-regression
PYTHONPATH=src python3 -m onecode_skill_sanitizer reseal-content \
  catalog/research/research-source-check
PYTHONPATH=src python3 -m onecode_skill_sanitizer reseal-content \
  catalog/code/codebase-explore-map
PYTHONPATH=src python3 -m onecode_skill_sanitizer reseal-content \
  catalog/execution/execution-browser-check
PYTHONPATH=src python3 -m onecode_skill_sanitizer reseal-content \
  catalog/engineering/engineering-ci-troubleshoot
PYTHONPATH=src python3 -m onecode_skill_sanitizer reindex --registry catalog
```

Resealing updates integrity evidence only. It does not grant trust, change
status, widen permissions, or authorize execution.
