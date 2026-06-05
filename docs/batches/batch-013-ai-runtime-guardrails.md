# Batch 013 AI Runtime Guardrails

## Purpose

Add local seed skills for AI runtime guardrails around model routing, tool
schemas, streamed structured output, RAG namespace boundaries, and context
compression budgets.

These entries are OneCode-authored method skills. They were inspired by
multi-model and runtime-boundary themes from community discussions, but they do
not claim provenance from unverified community repositories, plugin names, or
Star counts.

## Provenance

| Skill | Source | Author | License | Status Decision |
| --- | --- | --- | --- | --- |
| `ai-model-route-fallback-review` | local seed | OneCode Project | Apache-2.0 | trusted |
| `ai-tool-schema-protocol-check` | local seed | OneCode Project | Apache-2.0 | trusted |
| `ai-stream-json-boundary-review` | local seed | OneCode Project | Apache-2.0 | trusted |
| `data-rag-namespace-boundary-check` | local seed | OneCode Project | Apache-2.0 | trusted |
| `ai-context-compression-budget-plan` | local seed | OneCode Project | Apache-2.0 | trusted |

## License Boundary

This batch contains locally written workflow guidance. It does not copy
third-party code, prompt packs, runtime plugins, package manifests, examples,
provider configuration, connector definitions, model weights, or service
configuration.

## Batch Status

- imported skills: 5
- trusted skills in this batch: 5
- review-required skills in this batch: 0
- catalog total skills after batch: 100
- catalog trusted skills after batch: 95
- catalog review-required skills after batch: 2
- tampered skills: 0
- unknown provenance records: 0
- registry verification: ok

All five entries are trusted method guidance only. They do not grant runtime
authority or bind model endpoints, vector databases, filesystem access, network
access, account access, tool connectors, or production systems outside the host
runtime's policy layer.
