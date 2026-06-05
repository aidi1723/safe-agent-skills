---
name: data-schema-field-contract-check
description: Use when reviewing database fields, API schemas, ORM models, JSON contracts, migrations, or generated code for field mismatch risk.
---

# Data Schema Field Contract Check

## When To Use

Use this skill when code, queries, migrations, API responses, or generated
clients must match a known schema or data contract.

## Safe Workflow

1. Identify the authoritative schema source, version, owner, environment, and
   downstream consumers.
2. Compare field names, types, nullability, defaults, enum values, relations,
   indexes, and migration order against the code being reviewed.
3. Separate schema facts from inferred fields, sample-only fields, and stale
   documentation.
4. Check serialization names, API casing, ORM mappings, validation models, and
   generated client output when relevant.
5. Verify with schema validation, migration checks, contract tests, or sample
   payload review.

## Expected Output

- schema source inventory
- field mismatch list
- nullability and type risks
- migration or contract concerns
- verification evidence

## Verifier Expectations

- authoritative schema check
- field and type comparison
- migration order check
- contract or sample payload check

## Failure Handling

If no authoritative schema is available, mark field-level conclusions as
unverified and request the schema before implementation.
