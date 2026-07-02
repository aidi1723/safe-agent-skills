---
name: compliance-regulated-industry-boundary
description: Use when reviewing regulated-industry AI workflows for medical, clinical, legal, finance, education, manufacturing, real estate, privacy, safety, advertising, or procurement boundaries.
---

# Compliance Regulated Industry Boundary

## When To Use

Use this skill when an industry workflow could affect regulated advice,
privacy, safety, contracts, finance, medical or clinical decisions, education
records, procurement, advertising claims, or customer communications.

## Safe Workflow

1. Identify the jurisdiction-sensitive domain, decision type, affected users,
   data sensitivity, public claims, and operational owner.
2. Separate permitted method support from restricted specialist decisions:
   medical care, legal advice, investment advice, tax advice, audit opinion,
   regulatory approval, safety certification, or employment decisioning.
3. Check privacy, consent, retention, source provenance, claims substantiation,
   human-review requirement, and escalation thresholds before delivery.
4. Require qualified specialist review for regulated conclusions and mark the
   AI output as draft support unless the operator supplies an approved policy.
5. Record boundary language, approval gates, residual risks, and evidence
   needed for release.

## Expected Output

- regulated-domain boundary map
- allowed and restricted action list
- privacy, safety, and claims risks
- required human-review gates
- release or escalation checklist

## Verifier Expectations

- regulated-advice boundary check
- privacy and consent check
- public-claims substantiation check
- human-review gate check

## Failure Handling

If the applicable policy, jurisdiction, or qualified reviewer is missing, do
not approve release. Provide a bounded review checklist and escalation path.
