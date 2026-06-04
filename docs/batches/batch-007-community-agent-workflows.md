# Batch 007 Community Agent Workflow Skills

## Purpose

Add community-reference skills for agent orchestration, RAG, browser execution,
tool connectors, sandboxes, API patterns, vector retrieval, and modular
production workflows.

These entries are reference-style rewrites. They preserve useful engineering
patterns and safety boundaries, but do not copy third-party code, package
third-party runtimes, or grant connector permissions.

## Provenance

Source metadata was checked with GitHub repository metadata before intake.

| Skill | Source | Author | License | Status Decision |
| --- | --- | --- | --- | --- |
| `ai-langchain-agent-orchestration` | https://github.com/langchain-ai/langchain | langchain-ai | MIT | trusted reference |
| `ai-llamaindex-rag-knowledge-workflow` | https://github.com/run-llama/llama_index | run-llama | MIT | trusted reference |
| `ai-autogen-multi-agent-review` | https://github.com/microsoft/autogen | Microsoft | CC-BY-4.0 | trusted reference |
| `ai-crewai-role-workflow` | https://github.com/crewAIInc/crewAI | crewAIInc | MIT | trusted reference |
| `execution-browser-use-web-task` | https://github.com/browser-use/browser-use | browser-use | MIT | trusted reference |
| `execution-playwright-browser-automation` | https://github.com/microsoft/playwright | Microsoft | Apache-2.0 | trusted reference |
| `execution-mcp-tool-connector-review` | https://github.com/modelcontextprotocol/servers | modelcontextprotocol | Other | review-required reference |
| `ai-qwen-agent-tool-workflow` | https://github.com/QwenLM/Qwen-Agent | QwenLM | Apache-2.0 | trusted reference |
| `ai-openai-cookbook-api-patterns` | https://github.com/openai/openai-cookbook | OpenAI | MIT | trusted reference |
| `execution-e2b-sandbox-boundary` | https://github.com/e2b-dev/E2B | e2b-dev | Apache-2.0 | trusted reference |
| `data-qdrant-vector-retrieval` | https://github.com/qdrant/qdrant | qdrant | Apache-2.0 | trusted reference |
| `data-haystack-rag-pipeline` | https://github.com/deepset-ai/haystack | deepset-ai | Apache-2.0 | trusted reference |

## License Boundary

This batch records source identity and rewrites public engineering patterns
into OneCode-safe skill instructions. It does not copy third-party code,
runtime assets, prompts, examples, or connector definitions.

`execution-mcp-tool-connector-review` is collected with license value `Other`
because GitHub repository metadata reports `Other`. It should remain outside
default trusted selection until license and connector policy are reviewed.

## Batch Status

- imported skills: 12
- trusted skills in this batch: 11
- review-required skills in this batch: 1
- catalog total skills after batch: 72
- catalog trusted skills after batch: 67
- catalog review-required skills after batch: 2
- tampered skills: 0
- unknown provenance records: 0
- registry verification: ok

`execution-mcp-tool-connector-review` remains `review_required` because GitHub
reports the source license as `Other` and the sanitizer found an unresolved
`broad-filesystem-access` risk. It is recorded for review but excluded from
normal task selection and default bundles.
