# Batch 006 Community Infrastructure Skills

## Purpose

Add a second community-reference wave focused on high-value AI infrastructure
projects: guardrails, structured generation, cost routing, document
structuring, PDF-to-Markdown review, prompt engineering, local inference, and
LLM serving capacity.

These entries are reference-style skills. They preserve useful engineering
patterns, safe workflows, verifier expectations, and source records. They do
not copy third-party source code, package third-party runtimes, or grant
execution permissions.

## Provenance

Source metadata was checked with GitHub repository metadata before intake.

| Skill | Source | Author | License | Status Decision |
| --- | --- | --- | --- | --- |
| `security-guardrails-output-validation` | https://github.com/guardrails-ai/guardrails | guardrails-ai | Apache-2.0 | trusted reference |
| `security-llm-guard-io-scanning` | https://github.com/protectai/llm-guard | Protect AI | MIT | trusted reference |
| `ai-guidance-constrained-generation` | https://github.com/guidance-ai/guidance | guidance-ai | MIT | trusted reference |
| `ai-outlines-structured-generation` | https://github.com/dottxt-ai/outlines | dottxt-ai | Apache-2.0 | trusted reference |
| `ai-litellm-gateway-cost-control` | https://github.com/BerriAI/litellm | BerriAI | Other | review-required reference |
| `ai-pydantic-schema-contract` | https://github.com/pydantic/pydantic | Pydantic | MIT | trusted reference |
| `data-unstructured-document-partition` | https://github.com/Unstructured-IO/unstructured | Unstructured-IO | Apache-2.0 | trusted reference |
| `data-markitdown-file-to-markdown` | https://github.com/microsoft/markitdown | Microsoft | MIT | trusted reference |
| `data-marker-pdf-markdown-review` | https://github.com/datalab-to/marker | datalab-to | GPL-3.0 | trusted reference, no code copied |
| `content-prompt-engineering-patterns` | https://github.com/dair-ai/Prompt-Engineering-Guide | DAIR.AI | MIT | trusted reference |
| `ai-llama-cpp-local-inference-boundary` | https://github.com/ggml-org/llama.cpp | ggml-org | MIT | trusted reference |
| `ai-vllm-serving-capacity-plan` | https://github.com/vllm-project/vllm | vllm-project | Apache-2.0 | trusted reference |

## License Boundary

This batch does not import third-party code or prompt bodies. It only records
source identity and rewrites publicly observable engineering patterns into
OneCode-safe skill instructions.

`data-marker-pdf-markdown-review` references a GPL-3.0 project and is limited
to workflow review guidance. No GPL source code is copied.

`ai-litellm-gateway-cost-control` is collected with license value `Other`
because GitHub repository metadata reports `Other`. It should remain outside
default trusted selection until license and operational policy are reviewed.

## Batch Status

Completed.

Result:

- imported skills: 12
- trusted skills in this batch: 11
- review-required skills in this batch: 1
- catalog total skills after batch: 60
- catalog trusted skills after batch: 56
- catalog review-required skills after batch: 1
- tampered skills: 0
- unknown provenance records: 0
- registry verification: `ok`

`ai-litellm-gateway-cost-control` remains `review_required` because the GitHub
license metadata reports `Other` and the sanitizer found unresolved
broad-filesystem or credential-access wording in the source skill draft. It is
recorded for future review, but excluded from normal trusted selection.
