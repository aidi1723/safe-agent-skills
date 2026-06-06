# Workspace Boundary

## Source Of Truth

`safe-agent-skills` is maintained as a standalone repository.

Local source of truth:

```text
<safe-agent-skills-checkout>
```

GitHub source of truth:

```text
https://github.com/aidi1723/safe-agent-skills
```

All future work for the skill catalog, router skill, scenario bundles,
sanitizer CLI, documentation, verification, releases, and publishing should
happen from the standalone folder above.

## Do Not Nest The Checkout

Do not place this checkout inside a host runtime or core agent repository. If a
future tool or agent tries to work from a nested copy, stop and switch to the
standalone checkout:

```bash
cd "<safe-agent-skills-checkout>"
```

## Why This Boundary Exists

The skill project is related to OneCode, but it has a different lifecycle:

- it publishes to `aidi1723/safe-agent-skills`
- it maintains the public skill catalog
- it owns `safe-agent-router`
- it owns `catalog/`, `bundles/`, and batch documentation
- it has its own tests and release checks
- it should not appear as an untracked directory inside the OneCode core repo

Keeping it separate prevents accidental commits, noisy Git status output, and
confusion between OneCode runtime code and the skill catalog.

## Required Maintenance Flow

Before making changes:

```bash
cd "<safe-agent-skills-checkout>"
git status --short
```

Before publishing:

```bash
bash scripts/verify.sh
PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry catalog
PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check --registry catalog --bundles bundles/index.json
git diff --check
```

After router or catalog changes, reinstall the router skill for local Codex:

```bash
integrations/skills/safe-agent-router/scripts/install.sh ~/.codex/skills
```

Confirm the wrapper points to the standalone folder:

```bash
sed -n '1,5p' ~/.local/bin/safe-agent-router-task-pack
```

Expected path:

```text
SAFE_AGENT_SKILLS_HOME="<safe-agent-skills-checkout>"
```

## Parent Workspace Ignore Rule

The parent workspace ignores this standalone repository with:

```text
/safe-agent-skills/
```

This prevents the parent or OneCode workspace from treating the independent
skill repository as an unrelated untracked folder.
