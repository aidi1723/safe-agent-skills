# Headroom Agent I/O Compression Update

## Summary

Reviewed the current `chopratejas/headroom` public project as a reference for
agent-facing context compression across tool outputs, logs, retrieval chunks,
files, and chat history.

The repository was already represented by `headroom-context-compression` as a
trusted reference-style workflow. This update keeps that status and refines the
local skill guidance without importing or executing Headroom runtime code.

## Safety Decision

- Headroom remains a `reference_only` source for the local trusted workflow.
- No proxy, wrapper, MCP server, cross-agent memory, OAuth, or installer
  behavior is added to default task packs.
- Public compression percentages are treated as upstream claims unless locally
  reproduced.
- Runtime integration, if considered later, should be a separate
  review-required execution skill or connector review.

## Local Catalog Impact

`headroom-context-compression` now makes agent I/O compression explicit:

- classify inputs as `tool_result`, `log`, `rag_chunk`, `file_excerpt`,
  `chat_history`, or `note`
- retain error codes, stack anchors, line numbers, commands, paths, links, and
  retrieval source IDs
- record when the original source must be retrieved again
- verify compressed claims against representative source samples

`ai-context-compression-budget-plan` now includes the same agent I/O source
types in its planning and verifier expectations.

## Follow-Up Candidate

Future work can add a review-required skill such as
`execution-context-compression-proxy-review` for assessing proxy, MCP, wrapper,
and local-memory runtime integrations. That should remain separate from the
trusted method-only compression skills.

## Verification

- registry verification required
- schema check required
- maintain check required
- full verification script required
