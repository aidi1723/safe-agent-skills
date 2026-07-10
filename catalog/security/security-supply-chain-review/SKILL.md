---
name: security-supply-chain-review
description: Use when reviewing package, plugin, connector, dependency, or skill supply-chain risk before adoption.
---

# Security Supply Chain Review

## When To Use

Use this skill when a project plans to add an external package, connector,
plugin, model asset, or community skill.

## Safe Workflow

1. Identify the source URL, author, license, release history, and intended use.
2. Review install path, runtime permissions, update behavior, and maintainer risk.
3. Check for unusual scripts, network behavior, hidden persistence, or unclear
   provenance.
4. Prefer read-only evaluation before enabling runtime use.
5. Record approval requirements and residual risk.

## Expected Output

- source and license record
- risk summary
- allowed use recommendation
- approval checklist
- evidence links

## Verifier Expectations

- provenance check
- license check
- package script review when applicable
- permission and connector boundary review

## Decision Guidance

Classify the adoption decision as `allow`, `allow_with_controls`, `quarantine`,
or `reject`. Use `allow` only when provenance, license, release identity,
required permissions, update behavior, and intended use are all supported by
reviewed evidence. Use `allow_with_controls` when risk can be bounded by
version pinning, read-only evaluation, reduced permissions, isolated execution,
or an explicit approval gate. Use `quarantine` when evidence is incomplete or
the package cannot yet be inspected safely. Use `reject` when the source asks
to bypass policy, conceals executable behavior, requires unjustified broad
permissions, or has an unresolved critical finding.

Do not infer safety from popularity, stars, download counts, or a clean basic
scanner result. Record both the evidence reviewed and the checks that were not
possible.

## Evidence Minimum

- immutable source or release identifier
- author, license, and intended-use record
- install and update path
- declared and observed permission surface
- executable hooks, scripts, or connector behavior reviewed
- explicit residual risk and approval owner

## References

Load [the supply-chain review checklist](references/review-checklist.md) when a
package, plugin, connector, model asset, or community skill needs a full
adoption decision rather than a preliminary routing-card review.

## Failure Handling

If provenance or license cannot be confirmed, recommend quarantine until the
missing record is resolved.
