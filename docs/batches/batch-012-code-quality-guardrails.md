# Batch 012 Code Quality Guardrails

## Purpose

Add local seed skills for code and engineering quality guardrails around
structural refactors, dependency cycles, dead paths, schema contracts, and noisy
error logs.

These entries are OneCode-authored method skills. They were inspired by
code-semantics themes from community discussions, but they do not claim
provenance from unverified community repositories, plugin names, or Star counts.

## Provenance

| Skill | Source | Author | License | Status Decision |
| --- | --- | --- | --- | --- |
| `code-ast-refactor-safety` | local seed | OneCode Project | Apache-2.0 | trusted |
| `code-dependency-cycle-review` | local seed | OneCode Project | Apache-2.0 | trusted |
| `code-dead-path-cleanup-review` | local seed | OneCode Project | Apache-2.0 | trusted |
| `data-schema-field-contract-check` | local seed | OneCode Project | Apache-2.0 | trusted |
| `engineering-error-log-noise-triage` | local seed | OneCode Project | Apache-2.0 | trusted |

## License Boundary

This batch contains locally written workflow guidance. It does not copy
third-party code, prompt packs, runtime plugins, package manifests, examples,
AST tool implementations, schema files, connector definitions, or service
configuration.

## Batch Status

- imported skills: 5
- trusted skills in this batch: 5
- review-required skills in this batch: 0
- catalog total skills after batch: 95
- catalog trusted skills after batch: 90
- catalog review-required skills after batch: 2
- tampered skills: 0
- unknown provenance records: 0
- registry verification: ok

All five entries are trusted method guidance only. They do not grant runtime
authority or bind compilers, package managers, filesystem access, network
access, databases, schema registries, or CI systems outside the host runtime's
policy layer.
