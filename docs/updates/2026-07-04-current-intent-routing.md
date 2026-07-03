# Current Intent Routing

Date: 2026-07-04

## Summary

Improved smart skill selection for chat-style follow-up tasks that include old
history plus a new current request.

The router now detects explicit history/current separators and scores the
current request as the primary routing intent. Historical context is retained
as weak context only when the current request already has a distinctive signal.
This prevents stale website, browser, publish, or test signals from forcing an
unrelated scenario for a vague current continuation.

## What Changed

- Added `split_current_intent_text` support for English and Chinese markers:
  - `History: ... Current request: ...`
  - `Earlier context: ... Current request: ...`
  - `历史上下文：... 当前请求：...`
  - `之前：... 现在：...`
- Added profile metadata:
  - `current_intent_detected`
  - `current_intent_text`
  - `history_context_text`
  - `current_intent_weight`
  - `history_context_weight`
- Added deterministic low-confidence explanation fields:
  - `reason_codes`
  - `explanations`
  - `recommended_actions`
- Added `low_confidence_reasons`, explanations, and recommended actions to
  general fallback pipeline plans.
- Made runtime approval-gate task-signal checks use the current request when a
  history/current split is detected, while still preserving selected skill and
  bundle safety boundaries.
- Rendered low-confidence reasons and recommended actions in Markdown task
  packs.
- Added a router-eval regression case:
  `stale-history-vague-current-intent`.

## Routing Impact

The regression task:

```text
历史上下文：构建产品官网并准备上线发布检查。当前请求：继续优化任务
```

now remains a low-confidence `general` route instead of selecting
`website-build-launch`, and it avoids publish/browser execution skills.

## Verification

```text
bash scripts/verify.sh: 154 tests OK
tests.test_router: 54 tests OK
tests.test_registry_cli: 78 tests OK
router-eval: 40 / 40 cases OK
schema-check --registry catalog: OK, 172 manifests
maintain-check: OK, 23 bundles, 19 references, 336 / 336 claude-skills candidates covered
verify --registry catalog: 172 skills, 166 trusted, 0 tampered, 0 unknown provenance
git diff --check: OK
```

## Boundary

This is deterministic routing metadata only. It does not add runtime
permissions, network calls, source imports, external memory, or host gateway
integration.
