# Manifest Integrity and Contract Router Hardening

Date: 2026-06-18

## Summary

This update closes the manifest integrity gap found during hands-on review and
adds the first contract-aware routing path for selected scenario chains.

The project remains a deterministic, method-only skill governance system. These
changes raise the verification floor; they do not turn scanner results or skill
selection into runtime permission grants.

## Security Changes

- `skill.json` now carries `hashes.manifest_sha256`.
- The manifest hash is computed from canonical JSON after removing only
  `hashes.manifest_sha256` itself.
- `verify` reports `manifest-hash-mismatch` when manifest content changes
  without resealing.
- `schema-check` validates policy scopes and rejects permission-like
  `allowed_tools` values such as `shell`, `network`, `filesystem`, and
  `browser`.
- `reindex` is the explicit maintenance path that can reseal manifests.
  Read-only commands must not silently repair manifest tampering.

## Scanner Changes

The deterministic scanner now covers the bypass samples from the review:

- variable-indirected destructive shell commands such as `$CMD -rf /`
- Python dynamic execution through `eval(compile(...))`
- Chinese-language secret exfiltration intent
- SSH key copying through `scp`
- netcat reverse shell execution through `nc -e`
- PowerShell encoded commands
- JavaScript `fetch(...)` followed by dynamic execution through `eval(...)`

This remains deterministic preflight scanning, not complete malware or prompt
injection detection. Human approval and host runtime permission controls remain
part of the safety boundary.

## Contract Routing Changes

`skill.json` can now include an optional `contract` block:

```json
{
  "contract": {
    "requires_context": ["requirements_brief"],
    "produces_artifacts": ["build_artifact"],
    "produces_evidence": ["browser_check"],
    "capability_vector": ["execution.browser_check"],
    "stage_hint": "verification",
    "conflicts_with": [],
    "cost_weight": 2
  }
}
```

Router behavior:

- if all final selected skills have contracts, the mesh router builds a
  contract dependency graph from produced artifacts/evidence to required
  context;
- acyclic graphs are topologically layered and expose `mode: contract`;
- missing contracts fall back to the existing stage-based graph;
- contract cycles return `fallback_reason: contract_cycle` and avoid silently
  trusting an invalid order.

The first contracts were added to the website build and release chain skills so
that launch-style tasks can exercise the new graph path while the rest of the
catalog remains backward compatible.

## Verification

Use the normal maintenance gate:

```bash
bash scripts/verify.sh
```

Targeted checks include:

- manifest tampering reports `manifest-hash-mismatch`;
- schema policy and tool validation rejects unbounded manifest permissions;
- scanner bypass payloads produce deterministic findings;
- router contract graph tests cover ordering, fallback, and cycle behavior;
- `router-eval` keeps the existing scenario regression set green.

## Operator Notes

- Add contracts incrementally. A partial chain falls back to stage routing until
  every selected skill in the final pack has a contract.
- Keep contract fields method-level: they describe expected context, artifacts,
  evidence, and selection cost. They do not authorize runtime tools.
- Use `reindex` after intentional manifest edits so the manifest hash, report
  hash record, and catalog index are regenerated together.
