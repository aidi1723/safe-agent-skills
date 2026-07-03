---
name: compliance-private-communication-boundary
description: Use when designing or reviewing private messaging, secure communication, E2EE workflows, identifier minimization, metadata protection, contact discovery, or privacy-preserving collaboration.
---

# Compliance Private Communication Boundary

## When To Use

Use this skill when a project includes private messaging, team communication,
agent-to-user notifications, secure collaboration, contact discovery, or
privacy-sensitive communication workflows.

This skill provides threat-model and privacy-review guidance only. It does not
implement encryption or certify security.

## Safe Workflow

1. Define communication actors, message types, retention needs, abuse cases,
   legal hold needs, and recovery expectations.
2. Minimize identifiers. Record which stable IDs, phone numbers, emails,
   usernames, device IDs, IPs, and account links are required, optional, or
   prohibited.
3. Separate message confidentiality from metadata privacy. Review routing,
   contact discovery, timing, presence, delivery receipts, attachments, and
   server logs.
4. State whether end-to-end encryption is required, where keys live, how key
   changes are shown, and what backups expose.
5. Check consent, blocking, reporting, audit logging, retention, deletion, and
   export paths.
6. Mark cryptography, authentication, abuse prevention, and compliance claims
   for specialist review before public release.

## Expected Output

- actor and data-flow map
- identifier minimization table
- metadata and retention risk register
- E2EE and key-management boundary
- consent, deletion, and abuse handling notes
- specialist-review requirements

## Verifier Expectations

- data minimization check
- metadata exposure check
- retention and deletion check
- encryption claim boundary check
- abuse and compliance review check

## Failure Handling

If identifier needs, metadata exposure, or key-management responsibilities are
unclear, block implementation claims and produce a privacy threat-model draft.
