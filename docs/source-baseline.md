# Source Baseline

## Purpose

This document keeps the OneCode Skill Sanitizer grounded in verified project
facts instead of marketing shorthand or similarly named projects.

The sanitizer can target more than one host runtime, but each host capability
must be treated as an adapter contract, not an assumed fact.

## Verified Host Runtime Baseline

A local host runtime review described OneCode as a local-first agent kernel
prototype. Public documentation should record capabilities without exposing
operator-specific checkout paths.

The verified local README emphasizes:

- scoped file writes
- append-only run evidence
- stateful resumption
- deterministic status profiles
- guarded write and patch surfaces
- verifier policy allowlists
- Docker sandbox support for smoke checks and optional verifier execution
- run evidence under `<workspace>/.onecode/runs/<run-id>/`

This makes local OneCode a good execution boundary for sanitized skills because
the skill can remain advisory while the kernel owns path checks, permissions,
evidence, checkpointing, and verifier execution.

## Public AgentCore OS Baseline

Public search results for the domestic CNB mirror identify the AgentCore OS
main GitHub repository as:

```text
https://github.com/aidi1723/agentcore-os
```

The CNB mirror describes AgentCore OS as a local-first AI work platform with:

- BYOK / API-key driven usage
- browser shell and desktop shell entry points
- Knowledge Vault
- connectors
- task manager / console / settings control surface
- publishing queue or publishing flow
- business workflows for sales, support, research, and content

Reference:

```text
https://cnb.cool/aidiyangyu/agentcore-os
```

Those are useful host capabilities for a future integration, but they should
not be assumed to exist in the local OneCode kernel unless the runtime adapter
verifies them.

## Naming Risk

There are multiple public projects named OneCode, 1Code, AgentCore, and
AgentCore-like systems. The sanitizer must avoid relying on product names
alone.

Every integration should record:

- repository URL
- commit hash or release version
- detected capability manifest
- available connector APIs
- available vault APIs
- available sandbox APIs
- available approval and evidence APIs

## Security Claims Boundary

The sanitizer may claim these properties when implemented and verified:

- untrusted skills are not executed during import
- deterministic risk patterns are detected and removed or rewritten when covered by scanner rules
- every sanitized skill has a manifest and report
- every trusted skill has a recorded source hash and sanitized hash
- every skill records `source.usage` so external references are not confused
  with verbatim upstream imports
- runtime use is constrained by the host kernel permission model

The sanitizer must not claim:

- that community skills are 100% clean
- that deterministic regex scanning catches every obfuscated unsafe instruction
- that `github_reference` means upstream project content was copied or sanitized
- that `reference_only` provenance means the referenced project endorsed,
  reviewed, or supplied the local skill text
- that local-first alone prevents all exfiltration
- that popularity or repository stars imply trust
- that connector or vault support exists without adapter verification
- that sandboxing is active unless the run evidence proves it

## Integration Rule

Host integration should use capability detection:

```text
detect host
  -> read host capability manifest
  -> bind sanitizer policy to supported APIs
  -> fail closed when a required capability is missing
```

For local OneCode, the first adapter should bind to evidence, path guard,
verifier, checkpoint, and optional Docker sandbox behavior.

For AgentCore OS, a later adapter can bind to connectors, Knowledge Vault,
publishing flow, and desktop/browser shell surfaces after those APIs are
verified from the target repository.
