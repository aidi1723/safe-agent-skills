# Router Skill Primary Entry

## Decision

`safe-agent-router` should remain in the main `safe-agent-skills` repository as
the preferred user entry point.

Users should install this one skill first:

```text
integrations/skills/safe-agent-router/
```

They do not need to manually install, choose, or combine every other catalog
skill. The router reads the verified registry and returns the trusted task pack
needed for the current task.

## Why Not Split It Into A Separate Repository Now

The router's value depends on the main repository state:

- `catalog/` skill registry
- `bundles/` scenario bundles
- source and author records
- sanitized hashes
- trusted, quarantined, and review-required status
- OneCode safety rules
- registry and bundle verification commands

If the router is split too early, the router package can drift away from the
catalog, bundles, and verification rules it depends on. That would make task
selection less reliable and harder to audit.

## Recommended Public Positioning

Use this message in the project README, release notes, and social posts:

```text
Install one skill: safe-agent-router.
It automatically selects and combines OneCode-verified trusted skills from the
Safe-Agent-Skills catalog for each task. You do not need to manually install or
match every skill yourself.
```

## User Installation

Codex:

```bash
integrations/skills/safe-agent-router/scripts/install.sh ~/.codex/skills
```

Claude Code:

```bash
integrations/skills/safe-agent-router/scripts/install.sh ~/.claude/skills
```

Custom agents:

```text
copy integrations/skills/safe-agent-router/ into the agent skill directory
expose safe-agent-router-task-pack as a read-only task routing command
```

## Runtime Model

```text
user task
  -> safe-agent-router
  -> verified catalog and trusted scenario bundles
  -> selected task pack
  -> host agent executes within its own permissions
```

The router provides method guidance only. It does not grant filesystem, shell,
network, browser, connector, account, credential, deployment, or production
permissions.

## Future Split Option

A separate repository can be created later, but it should be a lightweight
installer or distribution wrapper, not a disconnected copy of the full skill
catalog.

Future shape:

```text
safe-agent-router-installer
  -> install scripts
  -> version lock
  -> host-agent templates
  -> pointer to safe-agent-skills
```

The source of truth should remain the main `safe-agent-skills` repository until
the router has stable version locking, release channels, and compatibility
tests across host agents.
