# Delivery Checklist

## MVP Scope

The local MVP is complete when the project can:

- scan one local skill folder
- sanitize one local skill folder
- batch import multiple skill folders
- classify skills into the shared taxonomy
- record required provenance for every skill
- write sanitized `SKILL.md`, `skill.json`, and `SANITIZATION_REPORT.json`
- maintain `registry/index.json`
- list and inspect registry entries
- approve, reject, and disable reviewed skills
- select only `trusted` skills by default
- emit a verified Agent task pack from selected skills
- verify registry integrity before runtime use
- rebuild stale registry indexes

## Current Status

- [x] Phase 001 closure report
- [x] Single-folder scan
- [x] Single-folder sanitize
- [x] Batch import
- [x] Taxonomy classification
- [x] Required provenance fields
- [x] Sanitized skill manifest
- [x] Sanitization report
- [x] Registry index
- [x] List and inspect
- [x] Approve, reject, disable
- [x] Trusted-only selection
- [x] Review-mode selection
- [x] Agent task pack output
- [x] Bundle-aware task pack output
- [x] Scenario router task-pack output
- [x] Scenario router capability coverage
- [x] Scenario router execution plan
- [x] Scenario router selection explanations
- [x] Maintenance check for registry and trusted bundle references
- [x] Registry verification
- [x] Reindex
- [x] Module entrypoint
- [x] Project verify script
- [x] Tests for scan, workflow, registry, verification, and tamper detection
- [x] Public-safe seed catalog
- [x] Batch records
- [x] Catalog status record
- [x] Public maintenance guide
- [x] Universal Agent task-pack guide
- [x] Cross-agent skill bundle guide
- [x] Scenario bundles
- [x] Public open-source statement
- [x] Standalone tool open-source statement
- [x] At least 3 trusted skills in every top-level category

## Current Public Baseline

- total skills: 164
- trusted skills: 158
- quarantined skills: 3
- review-required skills: 3
- top-level category coverage: 15 / 15
- scenario bundles: 15 trusted
- registry verification: ok

Closure report:

- [Phase 001 Closure Report](phase-001-closure-report.md)
- [Phase 002 Scenario Router Closure Report](phase-002-scenario-router-closure-report.md)
- [Scenario Capability Expansion Closure Report](scenario-capability-expansion-closure-report.md)

## Not In MVP

- network crawling
- Git clone intake
- LLM-based distillation
- JSON Schema runtime validation dependency
- OneCode kernel command integration
- review UI
- remote publishing

These remain future phases because the local trust chain should be stable
before external collection or runtime integration expands the blast radius.
