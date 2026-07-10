# Supply-Chain Review Checklist

Use this checklist after the initial skill workflow identifies a concrete
dependency, plugin, connector, model asset, or community skill.

## Identity And Provenance

- Record the canonical source, immutable version or commit, publisher, license,
  release date, and retrieval method.
- Distinguish a source repository from mirrors, package indexes, forks, and
  republished archives.
- Confirm that the reviewed bytes correspond to the proposed installation or
  adoption artifact.

## Execution Surface

- Inspect install, build, post-install, startup, update, and uninstall hooks.
- Identify native binaries, generated code, downloaded payloads, subprocesses,
  filesystem writes, network destinations, environment reads, and credential
  access.
- Compare requested permissions with the narrowest permissions needed for the
  stated use.

## Maintenance Risk

- Record release cadence, ownership concentration, abandoned or transferred
  projects, compromised-release history, and the update mechanism.
- Prefer immutable pins and reviewed upgrade changes for high-impact assets.
- Identify transitive dependencies or external services that can change
  behavior without modifying the direct dependency.

## Decision Record

Document the decision, evidence, reviewer, date, allowed use, version scope,
required controls, prohibited uses, monitoring expectations, and review
trigger. A scanner result is supporting evidence, not the complete decision.

Stop and quarantine when the artifact identity cannot be established, the
license is incompatible or unknown, executable behavior cannot be inspected,
or required permissions exceed the approved boundary.
