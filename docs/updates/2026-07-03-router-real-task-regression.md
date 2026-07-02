# Router Real Task Regression

Date: 2026-07-03

This update adds a real-world scenario routing regression set for the trusted
Safe-Agent-Skills catalog.

## What Changed

- Added a 20-case real task matrix covering Chinese, English, mixed-language,
  Traditional Chinese, typo-prone, and generic tasks.
- Covered expected scenario selection for:
  - `claude-skills-backlog-coverage`
  - `skill-router-quality-review`
  - `website-build-launch`
  - `rag-agent-knowledge-app`
  - `document-to-knowledge-base`
  - `code-review-hardening`
  - `codebase-change-lifecycle`
  - `agent-planning-orchestration`
  - `commerce-listing-growth`
  - generic no-bundle routing
- Added regression protection so `claude-skills-backlog-coverage` does not
  steal router-quality tasks about skill selection and task orchestration.
- Expanded router normalization for Traditional Chinese and conversational
  routing-quality phrases such as skill selection, execution orchestration,
  wrong skill invocation, and unrelated skill selection.

## Verification Focus

The regression set checks the scenario id, selected bundle id, and pipeline
plan id for each matched task. Generic tasks must keep an empty scenario and no
selected bundles.

The first red run exposed two missing Traditional Chinese routing cases:

```text
優化技能庫的自動推薦和任務編排能力
完善 skill 選擇與執行編排，避免錯誤調用不相關技能
```

Both now route to `skill-router-quality-review` through deterministic
normalization instead of relying on broad fuzzy matching.
