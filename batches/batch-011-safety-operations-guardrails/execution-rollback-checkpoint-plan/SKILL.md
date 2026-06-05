---
name: execution-rollback-checkpoint-plan
description: Use when planning reversible changes, repository checkpoints, migration safety, release rollback, or recovery notes before risky work.
---

# Execution Rollback Checkpoint Plan

## When To Use

Use this skill when a task may change many files, update dependencies, alter
schemas, publish artifacts, migrate data, or modify release state.

## Safe Workflow

1. Identify the current state, intended changes, affected files or systems, and
   whether the work is local-only or externally visible.
2. Choose a checkpoint method that fits the task: clean commit, branch,
   worktree, backup artifact, migration snapshot, or release tag.
3. Define the rollback trigger, rollback owner, and verification needed after
   returning to the checkpoint.
4. Keep generated files, dependency lockfiles, migrations, and release notes in
   the rollback scope when they are affected.
5. Record recovery limits, data-loss risks, and actions that cannot be undone
   locally.

## Expected Output

- affected-scope summary
- checkpoint method
- rollback trigger
- recovery steps
- non-reversible risk notes

## Verifier Expectations

- clean starting state check
- affected scope check
- checkpoint existence check
- rollback verification check

## Failure Handling

If no reliable checkpoint exists, pause risky changes and create or request an
appropriate checkpoint before proceeding.
