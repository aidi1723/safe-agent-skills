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
PYTHONPATH=src python3 -m onecode_skill_sanitizer smart "build a landing page and prepare launch checks" --invariants "不能泄露密钥；公开文案必须合规；必须响应式验证"
bash scripts/verify.sh
```

Expected baseline:

```text
skill_count: 105
trusted_count: 100
trusted_bundle_count: 9
overlap_group_count: 7
smart router: deterministic_mesh_router
```
