# Update Statement: Smart Skill Router

Date: 2026-06-06

Repository:

```text
https://github.com/aidi1723/safe-agent-skills
```

## Summary

This update adds `smart`, a simpler skill-selection entry that automatically
builds a verified task pack from the trusted catalog, scenario bundles,
natural-language invariants, overlap groups, and a deterministic mesh execution
graph.

The goal is to let operators describe the task and hard boundaries without
manually selecting, sorting, or de-duplicating skills.

## What Changed

- Added `onecode-skill-sanitizer smart "<task>"`.
- Added `task-pack --router mesh` for advanced users who need the same router
  through the existing task-pack interface.
- Added deterministic invariant capability mapping for secrets, public claims,
  responsive UI checks, source checks, and browser verification.
- Added overlap-group pruning to reduce redundant skill selection.
- Added a mesh execution graph with ordered stages.
- Added tests for invariant mapping, mesh routing, overlap pruning, and the
  `smart` CLI command.
- Added `docs/smart-skill-router.md`.

## Follow-up Hardening

The router now treats `general` or zero-signal tasks as low confidence and does
not force a scenario bundle. This prevents meta-review and repository
maintenance tasks from being incorrectly routed through unrelated workflows
such as `website-build-launch`.

The catalog also adds a dedicated `skill-router-quality-review` trusted bundle
for tasks that explicitly ask to evaluate Safe-Agent-Skills, smart routing,
automatic skill selection, or bundle composition quality.

When no trusted scenario is selected, CLI task packs now keep `bundle_count` at
`0` even if some selected skills overlap with existing bundles. The selected
skills remain available, but the output no longer claims a full scenario
playbook unless the scenario router actually matched one.

## Design References

This update borrows two real open-source ecosystem patterns:

- AnyTool-style pre-selection: trim a large tool universe to a compact task
  pack before the agent sees it (`https://github.com/HKUDS/AnyTool`).
- MCP aggregator-style entry simplicity: expose one operator-facing interface
  over many underlying tools (`https://github.com/punkpeye/awesome-mcp-servers`,
  `https://github.com/1mcp-app/agent`,
  `https://github.com/askbudi/roundtable`).

The implementation remains catalog-bound: only existing `trusted` skills can
be selected. External MCP servers or community tools still require provenance,
sanitization, approval, and registry verification before use.

## Safety Boundary

`smart` selects method guidance only. It does not execute tools, install skills,
grant network access, grant filesystem access, route models, or bypass the host
runtime approval policy.

## Verification Evidence

Release gate:

```bash
PYTHONPATH=src python3 -m unittest tests.test_router.RouterTest.test_parse_invariant_capabilities_maps_hard_boundaries tests.test_router.RouterTest.test_route_mesh_task_adds_invariant_skills_and_prunes_overlap
PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_smart_command_outputs_mesh_router_pack_with_invariant_skills
PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_scenario_router_does_not_force_bundle_for_general_meta_review_task tests.test_registry_cli.RegistryCliTest.test_smart_router_does_not_force_bundle_for_general_meta_review_task
PYTHONPATH=src python3 -m onecode_skill_sanitizer smart "build a landing page and prepare launch checks" --invariants "不能泄露密钥；公开文案必须合规；必须响应式验证"
PYTHONPATH=src python3 -m onecode_skill_sanitizer smart "复查 safe-agent-skills 项目是否达到智能选择和自动搭配 skill 的目标"
bash scripts/verify.sh
```

Expected baseline:

```text
skill_count: 105
trusted_count: 100
trusted_bundle_count: 10
overlap_group_count: 7
smart router: deterministic_mesh_router
```
