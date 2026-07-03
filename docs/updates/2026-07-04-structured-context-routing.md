# Structured Context Routing

Date: 2026-07-04

## Summary

Added a structured context summary contract for router task text.

Callers can now pass explicit `current_intent`, `history_summary`, and
`stale_context` fields inside the task string. The router uses the current
intent as the primary routing signal, keeps history as weak context, and
records stale context without letting it affect scenario selection, direct
skill matching, or runtime approval-gate task-signal checks.

## Supported Labels

English examples:

```text
current_intent: continue optimizing the router
history_summary: previously built a product website and prepared publish checks
stale_context: website, publish, browser automation
```

Chinese examples:

```text
当前意图：继续优化任务
历史摘要：之前构建产品官网并准备上线发布检查
过期上下文：发布、浏览器、官网
```

## What Changed

- Added structured context label parsing for:
  - current intent;
  - history summary;
  - stale context / do-not-inherit context.
- Exposed new task-profile metadata:
  - `structured_context_detected`;
  - `stale_context_text`;
  - `stale_context_policy`.
- Preserved the previous free-form `History: ... Current request: ...`
  behavior.
- Added regression coverage showing stale publish/browser/website context does
  not route vague current work into `website-build-launch`.
- Added a reusable router-eval case:
  `structured-context-stale-history-vague-current-intent`.

## Verification

```text
bash scripts/verify.sh: 157 tests OK
schema-check --registry catalog: OK, 172 manifests
tests.test_router: 57 tests OK
router-eval: 41 / 41 cases OK
by_confidence.high: 36 passed, 0 failed
by_confidence.low: 5 passed, 0 failed
maintain-check: OK
verify --registry catalog: 172 skills, 166 trusted, 0 tampered, 0 unknown provenance
```

## Boundary

This is a deterministic input-contract parser. It does not add persistent
memory, semantic summarization, networked context retrieval, external
connectors, or runtime permissions.
