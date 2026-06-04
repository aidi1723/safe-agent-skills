# Source Baseline

## Purpose

This document keeps the OneCode Skill Sanitizer grounded in verified project
facts instead of marketing shorthand or similarly named projects.

The sanitizer can target more than one host runtime, but each host capability
must be treated as an adapter contract, not an assumed fact.

## Verified Local OneCode Baseline

The local repository at `/Users/aidi/大字典/one code` currently describes
OneCode as a local-first agent kernel prototype.

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
- unsafe fragments are detected and removed or rewritten
- every sanitized skill has a manifest and report
- every trusted skill has a recorded source hash and sanitized hash
- runtime use is constrained by the host kernel permission model

The sanitizer must not claim:

- that community skills are 100% clean
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
