# CLAUDE.md Reference Review

## Summary

Added `multica-ai/andrej-karpathy-skills` as a metadata-only external
reference after reviewing its compact `CLAUDE.md` coding-behavior rules and
current public traction.

The reference is useful as market evidence: developers are actively looking for
small, memorable rules that make coding agents think first, avoid speculative
work, change code narrowly, and verify outcomes. That demand supports this
project's positioning, but it does not change the trust boundary.

## Safety Decision

- The project is recorded as `reference_only`, not copied into the catalog.
- The source license is currently recorded as `unknown`.
- Star counts and public popularity are not treated as trust evidence.
- The useful behavior pattern was represented as a local rule refinement in
  `ecc-agent-coding-safety`, not as a verbatim import.
- Default task packs must not auto-install, execute, or privilege the external
  repository.

## Local Catalog Impact

`ecc-agent-coding-safety` now makes minimal-change discipline explicit:

- state implementation-changing assumptions before editing
- choose the smallest implementation that satisfies the request
- avoid speculative abstractions and unrelated cleanup
- verify that changed lines trace to the user task or to cleanup caused by the
  task

## Public Copy Draft

Title: Why a single CLAUDE.md file can earn developer attention

The signal is not the file. The signal is the pain.

Developers are tired of coding agents that jump into edits, rewrite too much,
add abstractions nobody asked for, and then leave humans to debug the blast
radius. That is why compact rules like "think before coding", "simplicity
first", "surgical changes", and "goal-driven execution" spread so quickly.

For one repository, a `CLAUDE.md` can help. For a team, a product, or a shared
agent platform, the harder problem is governance: which rules are trusted, what
source they came from, whether they were rewritten safely, which tasks should
load them, and how the result is verified.

That is the gap `safe-agent-skills` is built for. It turns useful community
workflow ideas into provenance-recorded, policy-bounded, hash-verifiable skill
packs that agents can route to task by task.

Prompt files are a starting point. Trusted, verifiable skill routing is the
next layer.

## Verification

- reference metadata check required
- registry verification required
- maintain check required
- schema check required
