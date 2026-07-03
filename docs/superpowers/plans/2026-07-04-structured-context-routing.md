# Structured Context Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a structured context summary contract to task-text routing.

**Architecture:** Extend the existing task parser in `router.py` so structured labels are normalized into the same current-intent fields added in the previous milestone. Preserve existing CLI shape and task-pack schema compatibility by adding optional metadata fields only.

**Tech Stack:** Python standard library, existing `unittest` suite, existing router-eval JSON fixtures.

---

### Task 1: RED Router Tests

**Files:**
- Modify: `tests/test_router.py`

- [ ] Add a profile test for Chinese structured context:

```python
profile = build_task_profile("当前意图：继续优化任务\n历史摘要：构建产品官网并准备发布检查\n过期上下文：发布、浏览器、官网")
self.assertEqual(profile["task_type"], "general")
self.assertTrue(profile["structured_context_detected"])
self.assertIn("发布", profile["stale_context_text"])
```

- [ ] Add a routing test proving stale context does not select `website-build-launch`.
- [ ] Add an approval-gate test proving stale publish/browser labels do not create approval gates.
- [ ] Add a positive current-intent test proving `current_intent: review safe-agent-skills router quality` selects `skill-router-quality-review` despite website history.

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_router -v
```

Expected first run: new tests fail before implementation.

### Task 2: GREEN Parser Implementation

**Files:**
- Modify: `src/onecode_skill_sanitizer/router.py`

- [ ] Add a helper to parse multiline structured fields with English and Chinese labels.
- [ ] Prefer structured `current_intent` over free-form full text.
- [ ] Map `history_summary` into weak historical context.
- [ ] Record `stale_context` but exclude it from scoring and approval-gate task text.
- [ ] Keep existing `History: ... Current request: ...` behavior unchanged.

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_router -v
```

Expected after implementation: PASS.

### Task 3: Eval And Documentation

**Files:**
- Modify: `evals/router-quality.json`
- Create: `docs/updates/2026-07-04-structured-context-routing.md`
- Modify: `docs/maintenance-log.md`
- Modify: `docs/github-update-summary-2026-07-03.md`
- Modify: `/private/tmp/safe-agent-release-notes-20260703.md`

- [ ] Add one structured-context router-eval case.
- [ ] Record the behavior, verification, and method-only boundary.
- [ ] Update current verification counts after final verification.

Run:

```bash
bash scripts/verify.sh
git diff --check
PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval --eval evals/router-quality.json --registry catalog --bundles bundles/index.json
PYTHONPATH=src python3 -m onecode_skill_sanitizer schema-check --registry catalog
PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check --registry catalog --bundles bundles/index.json --references external-references/index.json --claude-skills-candidate-map docs/claude-skills-candidate-map.json
PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry catalog
```
