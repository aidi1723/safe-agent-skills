# Current Intent Routing Design

**Goal:** Improve smart skill selection when a task string contains stale history plus a newer request, and make low-confidence routes explain why they are low confidence.

## Scope

This milestone changes only deterministic routing metadata and tests. It does not add runtime tools, network calls, memory services, or host permissions.

## Behavior

When task text contains a clear history/current separator, the router treats the current request as the primary intent and the history block as weak context. Supported separators include English and Chinese forms such as `History: ... Current request: ...`, `Earlier context: ... Current request: ...`, `历史上下文：... 当前请求：...`, and `之前：... 现在：...`.

Normal one-shot tasks keep existing behavior. If no separator is found, profile scoring continues to use the full normalized task text.

## Data Contract

`build_task_profile` should include:

- `current_intent_detected`: boolean
- `current_intent_text`: normalized current request text when detected
- `history_context_text`: normalized historical context text when detected
- `current_intent_weight`: `1.0` for current intent scoring
- `history_context_weight`: `0.25` when history is detected, otherwise `0.0`

`selection_quality` should include:

- `reason_codes`: stable machine-readable low-confidence and warning IDs
- `explanations`: short human-readable explanations for the reason codes
- `recommended_actions`: deterministic next actions for low-confidence handoff

## Routing Rule

Scenario profile selection uses weighted score:

`current_score + int(history_score * history_context_weight)`

If current intent exists and has no distinctive scenario signal, history must not force a scenario match. This prevents old website, release, browser, or test signals from routing a vague current continuation into an unrelated scenario.

## Testing

Regression tests must cover:

- Chinese and English history/current separators.
- Vague current requests remaining `general` even when history mentions website launch.
- Low-confidence selection quality containing stable reason codes, explanations, and recommended actions.
- Markdown task packs rendering the new explanation fields.
- Router eval adding at least one stale-history case.

## Risks

Separator detection is intentionally conservative. A task without explicit history/current markers keeps the existing behavior, so ambiguous chat transcripts may still need caller-side summarization.
