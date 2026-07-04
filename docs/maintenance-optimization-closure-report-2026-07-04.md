# Maintenance Optimization Closure Report

Date: 2026-07-04

## Summary

This report closes the 2026-07-04 maintenance optimization pass for
`safe-agent-skills`.

The pass focused on making the router and maintenance workflow easier to
operate safely after repeated project-wide review requests. Known issues from
the review thread were addressed, documented, verified locally, committed,
pushed, and confirmed in GitHub Actions.

## Closed Work

### Router And Scenario Coverage

- Chinese project-wide maintenance and follow-up requests route to the intended
  project lifecycle or skill-router quality scenarios instead of unrelated
  bundles.
- `skill-router-quality-review` now has real-catalog regression coverage for
  the required `supply_chain_review` capability.
- `security-supply-chain-review` is selected when the router quality bundle
  requires supply-chain review.
- Vague continuation tasks remain lightweight and do not overselect broad
  execution or browser skills.

### Script And Installed Skill Behavior

- `integrations/skills/safe-agent-router/scripts/task_pack.sh` now resolves the
  repository beside the script before falling back to `SAFE_AGENT_SKILLS_HOME`.
- This prevents a globally exported `SAFE_AGENT_SKILLS_HOME` from making a
  repository-local script run against a stale checkout.
- The installed `safe-agent-router` copy was refreshed after the fix.
- The installed wrapper command was verified against the supply-chain coverage
  regression.

### Module Boundaries

Reusable logic was split out of `cli.py`:

- `src/onecode_skill_sanitizer/paths.py` owns repository asset path resolution.
- `src/onecode_skill_sanitizer/validation.py` owns manifest hashing, sealing,
  schema checks, policy checks, and pure validation helpers.
- `src/onecode_skill_sanitizer/references.py` owns external reference index
  loading and metadata-only reference validation.
- `cli.py` remains the command orchestration and compatibility layer.

### Verification And CI

- CI now installs development checks and runs `ruff` before the verification
  script.
- `scripts/verify.sh` also runs `ruff` when available.
- Local and remote verification both cover the expanded 164-test baseline.

## Final State

```text
commit: 5f280b2 chore: harden router maintenance workflow
branch: main
remote: origin/main
catalog skills: 172
trusted skills: 166
trusted scenario bundles: 23
external references: 19
trusted overlap groups: 7
tracked claude-skills candidates: 336
covered claude-skills candidates: 336
router eval cases: 42
full verification tests: 164
```

## Verification Evidence

Local verification:

```text
ruff check .: OK
bash scripts/verify.sh: 164 tests OK
git diff --check: clean
installed safe-agent-router wrapper: selected skill-router-quality-review
installed safe-agent-router wrapper: supply_chain_review covered by security-supply-chain-review
```

Remote verification:

```text
GitHub Actions run: 28702849795
workflow: Verify
result: success
Python 3.11: passed
Python 3.12: passed
Python 3.13: passed
```

GitHub reported a non-blocking annotation that `actions/checkout@v4` and
`actions/setup-python@v5` are being forced onto Node.js 24 because Node.js 20 is
deprecated. This did not fail the run.

## Maintenance Entry Points

Use these files first when resuming maintenance:

- [Maintenance Guide](maintenance-guide.md)
- [Maintenance Log](maintenance-log.md)
- [Module Boundary Refactor Plan](module-boundary-refactor-plan.md)
- [Router Skill Integration](router-skill-integration.md)
- [Stage Acceptance Report](stage-acceptance-report-2026-07-04.md)
- [Delivery Readiness Report](delivery-readiness-report.md)

## Required Commands For Future Maintenance

Run these before claiming a maintenance pass is complete:

```bash
ruff check .
bash scripts/verify.sh
git diff --check
```

When router behavior changes, also run the relevant targeted tests and
`router-eval`:

```bash
PYTHONPATH=src python3 -m unittest tests.test_router tests.test_registry_cli -v
PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval \
  --eval evals/router-quality.json \
  --registry catalog \
  --bundles bundles/index.json
```

After changing `integrations/skills/safe-agent-router`, reinstall the router
skill and verify the installed wrapper:

```bash
integrations/skills/safe-agent-router/scripts/install.sh ~/.codex/skills
safe-agent-router-task-pack "复查 skill-router-quality-review 的 supply_chain_review coverage 缺口" --format json
```

The expected installed-wrapper behavior is:

- selected scenario: `skill-router-quality-review`
- selected skill includes: `security-supply-chain-review`
- `supply_chain_review` coverage status: `covered`

## Residual Risks And Follow-Up

No known code or routing blocker remains from this maintenance pass.

Non-blocking follow-up:

- Upgrade GitHub Actions versions when newer official action releases remove
  the Node.js 20 deprecation annotation.
- Continue reducing historical baseline duplication across older closure
  reports; treat old reports as dated evidence, not current truth.
- Keep `cli.py` thin. New reusable behavior should move to focused modules with
  direct tests.
- If a future installed router behaves differently from the repository CLI,
  check `SAFE_AGENT_SKILLS_HOME`, reinstall the router skill, and run the
  installed-wrapper regression above.

## Safety Boundary

This closure remains method-only. Skills do not grant filesystem, shell,
network, browser, account, connector, production, or publishing permissions.
Runtime authority remains with the host environment and operator approvals.
