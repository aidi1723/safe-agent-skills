# Structured Context Routing Design

**Goal:** Let callers pass an explicit context summary contract inside task
text so the router can distinguish current intent, historical summary, and
stale context without new runtime dependencies or CLI flags.

## Scope

This milestone extends deterministic task-text parsing only. It does not add
external memory, network calls, host gateway integration, new skill execution,
or runtime permissions.

## Contract

Task text may include labeled fields:

```text
current_intent: continue optimizing the router
history_summary: previously built a product website and prepared publish checks
stale_context: website, publish, browser automation
```

Chinese labels are also accepted:

```text
当前意图：继续优化任务
历史摘要：之前构建产品官网并准备上线发布检查
过期上下文：发布、浏览器、官网
```

Supported labels:

- Current intent: `current_intent`, `current intent`, `current request`,
  `当前意图`, `当前请求`
- History summary: `history_summary`, `history summary`, `history`,
  `历史摘要`, `历史上下文`
- Stale context: `stale_context`, `stale context`, `do_not_inherit`,
  `不要继承`, `过期上下文`

## Behavior

If `current_intent` is present, it becomes the primary routing text. Historical
summary is weak context and only contributes when the current intent already
has a distinctive scenario signal. Stale context is recorded for auditability
but ignored for scenario scoring, direct skill matching, and runtime approval
task-signal checks.

Existing free-form `History: ... Current request: ...` behavior remains
compatible.

## Output Metadata

`task_profile` should expose:

- `structured_context_detected`
- `current_intent_text`
- `history_context_text`
- `stale_context_text`
- `stale_context_policy`
- `current_intent_weight`
- `history_context_weight`

## Testing

Regression tests cover:

- Structured Chinese context with stale website/publish/browser text remains
  low-confidence `general` when current intent is vague.
- Runtime approval gates do not inherit stale publish/browser signals.
- Structured current intent can route to `skill-router-quality-review` even if
  history mentions an unrelated website launch.
- Router-eval includes a reusable structured-context stale-history case.

## Boundary

This is an input contract for deterministic routing. It is not a long-term
memory store, semantic summarizer, or host-side context gateway.
