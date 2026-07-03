# Requires After Contract Ordering

Date: 2026-07-04

## Summary

Added first-class `contract.requires_after` ordering metadata to routed task
packs.

Skills can now declare explicit predecessor skills when artifact dependencies
alone cannot describe the correct execution order. The router turns selected
`requires_after` relationships into contract graph edges and surfaces missing
predecessors as diagnostics before execution.

## What Changed

- Added schema support for `contract.requires_after`.
- Added self-reference validation for `contract.requires_after`.
- Added contract graph edges with type `contract_requires_after`.
- Added missing ordering diagnostics:
  - `missing_ordering_count`
  - `missing_ordering`
- Rendered missing ordering diagnostics in Markdown task packs and agent
  instructions.
- Preserved artifact-based dependency edges, missing precondition diagnostics,
  collision diagnostics, and graph fallback diagnostics.

## Output Shape

```json
{
  "missing_ordering_count": 1,
  "missing_ordering": [
    {
      "skill": "design-ui-review",
      "requires_after": "business-requirements-brief",
      "source": "contract.requires_after"
    }
  ]
}
```

## Verification Targets

- `PYTHONPATH=src python3 -m unittest tests.test_router.RouterTest.test_build_contract_graph_uses_requires_after_ordering_edges tests.test_router.RouterTest.test_build_contract_diagnostics_reports_missing_requires_after`
- `PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_schema_check_validates_optional_contract_shape tests.test_registry_cli.RegistryCliTest.test_schema_check_rejects_invalid_contract_values`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval --eval evals/router-quality.json --registry catalog --bundles bundles/index.json`
- `bash scripts/verify.sh`
- `git diff --check`

## Boundary

This update changes local routing metadata, schema validation, diagnostics, and
task-pack rendering only. It does not grant runtime permissions, execute
skills, import external content, invoke connectors, run browser automation, or
change trust status.

Remaining non-blocking work now focuses on host semantic gateway integration,
networked source-import automation, and documentation consolidation.
