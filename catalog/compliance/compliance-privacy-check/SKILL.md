---
name: compliance-privacy-check
description: Use when checking whether a workflow, document, or dataset has privacy and data-handling risks that need review.
---

# Privacy Compliance Check

## When To Use

Use this skill when a task involves personal data, customer records, internal
policy, audit preparation, or data sharing decisions.

## Safe Workflow

1. Identify the data type, data subject, purpose, recipient, and retention need.
2. Distinguish public, internal, confidential, personal, and sensitive data.
3. Check whether the task needs consent, minimization, redaction, or human approval.
4. Avoid legal conclusions; provide operational risk notes and escalation points.
5. Recommend safer handling such as local processing, redaction, or scoped access.
6. Record unknown jurisdiction or policy dependencies.

## Expected Output

- data handling risk summary
- required approval or escalation notes
- redaction or minimization checklist
- unresolved policy questions

## Verifier Expectations

- policy scope check
- source citation or policy reference check
- approval requirement check
- disclaimer and escalation check

## Decision Guidance

Separate operational handling advice from legal interpretation. First decide
whether the workflow can proceed with ordinary controls, requires minimization
or redaction, requires an approved restricted environment, or must stop for a
privacy owner. Escalate whenever purpose, jurisdiction, data-subject category,
retention authority, transfer destination, or policy owner is unknown and the
task would disclose or transform personal or sensitive data.

Prefer the least-data path that still satisfies the stated purpose. A claimed
business need is not evidence of consent, lawful authority, retention rights,
or cross-border transfer approval. Never treat anonymization as complete when
records can still be linked through identifiers, free text, timestamps, small
cohorts, or external datasets.

## Evidence Minimum

- data categories and sensitivity classification
- purpose, recipient, processing location, and retention period
- applicable internal policy and accountable owner
- minimization, redaction, access, and deletion controls
- unresolved jurisdiction, consent, contract, or transfer questions
- approval or escalation record when required

## References

Load [the privacy evidence guide](references/privacy-evidence-guide.md) for
dataset transfers, customer-record analysis, retention decisions, or workflows
that combine multiple sources of personal data.

## Failure Handling

If jurisdiction, policy, or data classification is unknown, keep the result
advisory and request human review.
