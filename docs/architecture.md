# Architecture

## Goal

Build a trusted skill supply-chain layer for OneCode.

The system imports external skills, extracts useful procedural knowledge, strips unsafe instructions, binds the result to OneCode policy, and records a verifiable evidence trail for every accepted skill.

## Non-Goals

- Do not run third-party skill scripts during import.
- Do not give skills direct execution authority.
- Do not allow a skill to override OneCode kernel rules.
- Do not treat community popularity as trust.
- Do not build a full marketplace in the MVP.

## System Boundary

The sanitizer owns skill intake and governance.

OneCode kernel owns execution:

```text
Skill Sanitizer:
  source capture
  parsing
  taxonomy classification
  scanning
  distillation
  manifest generation
  report generation
  registry status

OneCode Kernel:
  path guard
  permission matrix
  tool execution
  verifier execution
  WAL / ledger / checkpoint evidence
  resume and inspect
```

The sanitizer can recommend allowed tools and required verifiers, but the kernel makes the final decision.

See [Source Baseline](source-baseline.md) for the distinction between the local
OneCode kernel baseline and the public AgentCore OS product baseline. Connector,
Knowledge Vault, and publishing integrations are adapter targets, not required
assumptions of this sanitizer core.

## Components

### Host Adapter

Detects the target runtime and records the capability boundary.

The adapter should verify:

- host repository or product identity
- version or commit hash
- supported permission APIs
- supported evidence APIs
- supported verifier APIs
- optional sandbox support
- optional connector support
- optional vault or publishing support

Missing capabilities fail closed. For example, a skill that requires sandboxed
verifier execution cannot become `trusted` on a host that cannot prove sandbox
availability.

### Source Capturer

Accepts a skill source from:

- local folder
- local archive
- Git URL
- future curated community index

It records:

- source type
- source usage relationship
- source URL or local path
- source author or owner
- source license
- source reference URL
- collector identity
- source commit when available
- file list
- content hashes
- import timestamp

Missing provenance values are recorded as `unknown`; they are never omitted.
The source usage relationship is explicit: `source_import` means content was
imported from the cited source, `reference_only` means the source is a
reference or inspiration only, and `local_authoring` means the skill was
locally authored or seeded from local material.

### Skill Parser

Recognizes common skill formats:

- `SKILL.md`
- Markdown prompt packs
- YAML/JSON skill manifests
- README-like workflow docs
- bundled scripts and references

The parser produces a normalized source inventory.

### Taxonomy Classifier

Maps each source into the shared skill directory:

- `design`
- `code`
- `engineering`
- `security`
- `office`
- `execution`
- `research`
- `data`
- `business`
- `content`
- `commerce`
- `media`
- `compliance`
- `ai`
- `vertical`

Classification uses explicit manifest fields first, then source path and text
signals. Unknown skills become `review_required`; they do not become trusted by
guessing.

### Risk Scanner

Runs deterministic preflight checks before any rewrite or approval decision.
The scanner is intentionally conservative and auditable; it is a review
guardrail, not a complete malware detector.

It flags:

- destructive shell commands
- inline shell or interpreter execution
- encoded payload execution
- `curl | bash` and remote execution
- secret-looking strings
- instructions to bypass policies
- unrestricted filesystem access
- environment or credential exfiltration guidance

Scanner output is evidence, not just a warning.

### Skill Distiller

Extracts useful instructions from the source and rewrites them into a concise OneCode skill.

The distiller keeps:

- what the skill is for
- when to use it
- safe workflow steps
- required inputs
- expected outputs
- validation guidance
- reference-loading guidance

The distiller removes:

- unsafe execution instructions
- tool invocation commands that should be handled by OneCode
- policy overrides
- irrelevant prose

### Policy Binder

Creates `skill.json` for OneCode governance:

- `allowed_tools`
- `required_verifiers`
- `risk_level`
- `network_policy`
- `filesystem_policy`
- `approval_policy`
- `status`

The policy binder must fail closed. Unknown capabilities become denied or review-required.

### Report Generator

Writes a machine-readable sanitization report:

- source hashes
- sanitized hashes
- taxonomy classification
- removed fragments
- risk findings
- unresolved warnings
- required human review items
- final recommendation

### Audit And Approval

The local workflow supports:

- `audit`: verifies that a skill is `trusted` and that the current `SKILL.md`
  still matches `hashes.sanitized_sha256`
- `approve`: records local operator approval and moves a reviewed skill to
  `trusted`

Approval does not disable runtime policy. It only allows the sanitized skill to
be selected by normal OneCode runs.

### Registry

Stores sanitized skills in states:

- `quarantined`
- `review_required`
- `trusted`
- `rejected`
- `disabled`

Only `trusted` skills can be selected by normal OneCode runs.

The registry also stores `index.json`, generated from actual skill manifests.
It is an index, not the authority. Commands that need current trust state should
re-read each skill manifest.

### Registry Commands

The local MVP exposes:

- `import`: batch-sanitize child folders from an incoming directory
- `list`: print `registry/index.json`
- `inspect`: print one skill manifest
- `select`: choose matching skills for a task; defaults to `trusted` only
- `task-pack`: verify the registry and emit selected skill instructions for any
  host agent as JSON or Markdown; can include matching trusted scenario bundles
- `verify`: check sanitized hashes and provenance across the registry
- `maintain-check`: verify the registry and ensure trusted bundles reference
  only existing trusted skills; also validates trusted-only overlap groups
  when `overlap-groups.json` exists under the registry
- `reindex`: rebuild `index.json` from manifests
- `approve`, `reject`, `disable`: update review state and refresh the index

## Runtime Flow

When a trusted skill is used:

```text
user task
  -> task-pack verifies registry
  -> matching trusted skills selected
  -> sanitized SKILL.md guidance loaded into model context
  -> model emits plan
  -> OneCode validates plan
  -> kernel intersects permissions
  -> execution runs
  -> verifiers run
  -> evidence records skill identity and hash
```

Before runtime selection, `select` intersects task taxonomy with registry
entries and filters out non-`trusted` skills unless review mode is explicitly
requested.

For cross-agent use, `task-pack` performs the same trusted selection after
registry verification, then serializes the cleaned skill guidance,
provenance, hashes, verifier expectations, optional trusted scenario bundles,
and safety boundary into a single instruction pack. The pack can be consumed by
OneCode or by another agent runtime. It remains advisory and cannot widen the
host runtime's permissions.

The effective permission set is:

```text
user authorization
  intersection workspace policy
  intersection skill allowed_tools
  intersection OneCode kernel policy
```

Skills can narrow permissions. They cannot widen permissions.

## Evidence Contract

Every sanitized skill stores:

- source identity
- source author or owner
- source URL or local path
- source license
- collector identity
- source hash
- sanitizer version
- policy version
- sanitized skill hash
- removed-fragment hashes
- risk findings
- final status

Every OneCode run using skills records:

- selected skills
- skill versions
- skill manifest hashes
- required verifiers
- verifier results

This makes skill influence auditable.

## Failure Modes

### Unsafe Content Detected

The skill remains `quarantined` or becomes `rejected`.

### Ambiguous Capability

The skill becomes `review_required`.

### Missing Verifier

The skill can be stored, but it cannot become `trusted` until a verifier policy is attached or an explicit waiver is recorded.

### Source Changes

Any source hash change invalidates prior approval and returns the skill to `quarantined`.
