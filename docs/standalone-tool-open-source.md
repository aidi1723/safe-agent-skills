# Standalone Tool Open Source Statement

## What This Tool Is

`onecode-skill-sanitizer` is an open source CLI for building a safer skill
catalog for AI agents.

It can be used with the public `safe-agent-skills` catalog, but it is not
limited to that catalog. Any user, team, or agent platform can use the tool to
collect their own skills, record provenance, clean unsafe instructions, review
trust status, verify hashes, and generate task-specific agent instruction
packs.

In simple terms:

```text
your skills
  -> scan
  -> sanitize
  -> registry
  -> approve
  -> verify
  -> select
  -> task-pack for your agent
```

## Why It Exists

Agent skills are useful, but unmanaged skills create recurring problems:

- unclear source and ownership
- copied prompts with no license record
- hidden unsafe instructions
- broad filesystem or network assumptions
- shell snippets that should not run automatically
- prompt-injection text that tries to override higher-priority rules
- no way to know whether a skill changed after approval
- no shared format for agent runtimes to choose the right skill

This tool turns skills into maintainable records. A skill is no longer just a
text file copied from the internet. It becomes a versioned, sourced, hashed,
reviewed, and selectable asset.

## Who Can Use It

This tool is designed for:

- individual agent builders maintaining personal skills
- teams building private internal skill catalogs
- open source communities curating public skill collections
- coding agents that need task-specific instructions
- local-first AI systems that want deterministic safety checks
- MCP or workflow hosts that need a standard skill-selection layer

You do not need to use OneCode to benefit from the tool. OneCode is the original
safety philosophy behind this project, but the CLI output is plain JSON and
Markdown so other systems can consume it.

## What Users Can Bring

Users can bring their own skill folders:

```text
incoming/
  my-pdf-workflow/
    SKILL.md
  my-code-review-checklist/
    SKILL.md
  my-dashboard-polish-guide/
    SKILL.md
```

Then import them into a local registry:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer import ./incoming \
  --registry ./registry \
  --source-url https://github.com/example/my-skills \
  --author example-team \
  --license MIT \
  --reference https://github.com/example/my-skills \
  --collected-by local-operator
```

Each imported skill receives:

- sanitized `SKILL.md`
- `skill.json` manifest
- `SANITIZATION_REPORT.json`
- taxonomy record
- source record
- source hash
- sanitized hash
- trust status
- policy boundary

## What The Tool Does

### 1. Scan

Detects deterministic risky text patterns such as secrets, dangerous shell
instructions, inline interpreter execution, encoded payload execution, policy
override language, broad filesystem assumptions, and unsafe execution phrasing.

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer scan ./incoming/my-skill
```

### 2. Sanitize

Writes a sanitized skill folder and removes unsafe fragments that match current
scanner rules. Human review is still required before trusting unvetted third
party material.

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer sanitize ./incoming/my-skill \
  --out ./registry/custom/my-skill \
  --source-url https://github.com/example/my-skill \
  --author example-team \
  --license MIT \
  --reference https://github.com/example/my-skill \
  --collected-by local-operator
```

### 3. Review

Lets the operator approve, reject, or disable a skill after inspection.

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer approve ./registry/custom/my-skill
PYTHONPATH=src python3 -m onecode_skill_sanitizer reject ./registry/custom/bad-skill
PYTHONPATH=src python3 -m onecode_skill_sanitizer disable ./registry/custom/old-skill
```

### 4. Verify

Checks that approved skill files still match their recorded sanitized hashes and
that source records are complete.

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry ./registry
```

### 5. Select

Chooses matching skills for a task. Normal selection only returns `trusted`
skills.

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer select \
  "review security risk in this dependency" \
  --registry ./registry
```

### 6. Generate Agent Task Pack

Builds a task-specific instruction pack that a host agent can use directly.

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer task-pack \
  "review security risk in this dependency" \
  --registry ./registry \
  --top 3 \
  --format json
```

Markdown output is also supported:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer task-pack \
  "polish this dashboard interface" \
  --registry ./registry \
  --top 2 \
  --format markdown
```

The task pack includes:

- selected skill names
- optional trusted scenario bundles
- match scores
- capability descriptions
- source and license records
- sanitized hashes
- safe workflow
- expected output
- verifier expectations
- failure handling
- final agent instructions

### 7. Run Maintenance Check

Before publishing a registry and bundle set, verify both skill integrity and
trusted bundle references:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check \
  --registry ./registry \
  --bundles ./bundles/index.json
```

This command fails if the registry has tampered or unknown-provenance skills,
or if a trusted bundle references a missing or non-trusted skill.

## What The Tool Does Not Do

This tool does not automatically make an agent safe.

It does not:

- grant shell permissions
- grant filesystem permissions
- grant network permissions
- execute third-party code
- replace human review for high-risk skills
- guarantee that a skill is legally reusable
- bypass the host agent's own safety policy
- make financial, medical, legal, or production actions safe by default

The tool provides a safer skill catalog and instruction-pack layer. Runtime
permission control still belongs to the host agent, operating system, sandbox,
or workflow platform.

## Trust Model

The core trust rule is:

```text
method guidance is not execution authority
```

A skill can explain how to approach a task. It cannot expand what an agent is
allowed to do.

Default runtime use should only load `trusted` skills. `review_required` skills
can be inspected in review workflows. `quarantined`, `rejected`, and `disabled`
skills should not be used for normal execution.

## Suggested Standalone Workflow

1. Create your own `incoming/` folder.
2. Place one skill per subfolder.
3. Run `import` with full source metadata.
4. Inspect each generated `skill.json` and `SANITIZATION_REPORT.json`.
5. Approve only the skills you understand and accept.
6. Run `verify --registry ./registry`.
7. Run `maintain-check --registry ./registry --bundles ./bundles/index.json`
   when using scenario bundles.
8. Use `task-pack` before agent execution.
9. Record selected skill names and hashes in the agent's final report.

## Open Source Position

This project is open source so that skill safety can become a shared
engineering practice instead of a private prompt collection habit.

Users are encouraged to:

- build private skill catalogs
- publish sanitized public catalogs
- contribute new risk rules
- improve taxonomy coverage
- add verifier integrations
- adapt the JSON and Markdown output to their own agent runtimes

The goal is not to force every agent into one framework. The goal is to give
different agents a common, safer way to discover and consume useful skills.
