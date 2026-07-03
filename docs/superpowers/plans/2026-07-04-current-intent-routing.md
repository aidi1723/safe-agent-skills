# Current Intent Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add current-intent weighting and deterministic low-confidence explanations to the Safe-Agent-Skills router.

**Architecture:** Keep routing deterministic and local. Add a small task-text splitter in `router.py`, feed weighted profile scoring through existing scenario selection, and expose stable explanation fields through existing task-pack JSON and Markdown rendering.

**Tech Stack:** Python standard library, `unittest`, existing CLI and router evaluation commands.

---

### Task 1: Router Unit Tests

**Files:**
- Modify: `tests/test_router.py`

- [ ] Add a test proving `build_task_profile("历史上下文：构建产品官网并准备发布检查。当前请求：继续优化任务")` returns `task_type == "general"`, `matched_signal_score == 0`, and `current_intent_detected is True`.
- [ ] Add a test proving an English stale-history/current-request string does not select `website-build-launch` in `route_scenario_task`.
- [ ] Add a test proving `build_selection_quality` returns `reason_codes`, `explanations`, and `recommended_actions` for low-confidence general fallback.
- [ ] Add a test proving `build_pipeline_plan` copies low-confidence reason codes into `low_confidence_reasons`.

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_router.RouterTest.test_build_task_profile_prioritizes_chinese_current_intent_over_history tests.test_router.RouterTest.test_route_scenario_task_ignores_stale_history_for_vague_current_intent tests.test_router.RouterTest.test_build_selection_quality_explains_low_confidence_general_fallback tests.test_router.RouterTest.test_build_pipeline_plan_includes_low_confidence_reason_codes -v
```

Expected first run: FAIL before implementation.

### Task 2: CLI And Eval Tests

**Files:**
- Modify: `tests/test_registry_cli.py`
- Modify: `evals/router-quality.json`

- [ ] Add a CLI Markdown rendering test or extend an existing task-pack test so `## Selection Quality` includes reason codes and recommended actions when low confidence.
- [ ] Add a stale-history eval case with expected empty scenario, `general` task type, max three skills, and forbidden browser/publish execution skills.

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest -v
PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval --eval evals/router-quality.json --registry catalog --bundles bundles/index.json
```

Expected first focused run: FAIL before implementation for new expectations.

### Task 3: Minimal Router Implementation

**Files:**
- Modify: `src/onecode_skill_sanitizer/router.py`
- Modify: `src/onecode_skill_sanitizer/cli.py`

- [ ] Add `split_current_intent_text(task)` returning normalized current/history text plus detection metadata.
- [ ] Update `build_task_profile` to use weighted profile scoring when current intent is detected.
- [ ] Keep history from forcing a scenario when the current request has no distinctive profile signal.
- [ ] Update `build_selection_quality` with stable `reason_codes`, `explanations`, and `recommended_actions`.
- [ ] Update `build_pipeline_plan` and Markdown rendering to expose the new explanation fields.

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_router -v
PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest -v
```

Expected: PASS after implementation.

### Task 4: Docs, Verification, And Release Notes

**Files:**
- Create: `docs/updates/2026-07-04-current-intent-routing.md`
- Modify: `docs/maintenance-log.md`
- Modify: `docs/github-update-summary-2026-07-03.md`
- Modify: `README.md`
- Modify: `/private/tmp/safe-agent-release-notes-20260703.md`

- [ ] Record what changed, verification evidence, selected scenario, selected skills, assumptions, and residual risks.
- [ ] Run the full verification suite and diff check.
- [ ] Commit, push, and update GitHub release notes.

Run:

```bash
bash scripts/verify.sh
git diff --check
PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval --eval evals/router-quality.json --registry catalog --bundles bundles/index.json
PYTHONPATH=src python3 -m onecode_skill_sanitizer schema-check --registry catalog
PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check --registry catalog --bundles bundles/index.json --references external-references/index.json --claude-skills-candidate-map docs/claude-skills-candidate-map.json
PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry catalog
```
