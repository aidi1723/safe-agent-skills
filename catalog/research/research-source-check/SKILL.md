---
name: research-source-check
description: Use when verifying factual claims against primary or high-quality sources with explicit citations.
---

# Research Source Check

## When To Use

Use this skill when a task needs current facts, source attribution, comparison
between sources, or verification of a claim before it is used in an answer.

## Safe Workflow

1. Decompose the request into exact material claims, definitions, dates, quantities, and decisions that require verification.
2. Match each claim to the strongest available evidence, preferring primary records, official documentation, standards, statutes, filings, datasets, and original research.
3. Assess source authority, directness, scope, date, version, methodology, independence, conflicts of interest, and whether the cited passage supports the complete claim.
4. Record title, publisher or author, publication or update date, stable URL or identifier, access limits, and the exact claim supported.
5. Compare independent sources when a claim is dynamic, disputed, high-impact, regulated, or dependent on definitions or methodology.
6. Separate source facts, calculations, inference, forecasts, and opinion. Do not turn plausible analysis into a sourced fact.
7. Resolve disagreements by comparing dates, scope, definitions, populations, versions, jurisdictions, methods, and incentives rather than silently averaging results.
8. Report claim status, uncertainty, freshness limits, inaccessible evidence, and the event that would require rechecking.

## Expected Output

- claim-by-claim verification
- concise source list
- dates and publisher names
- clear distinction between source facts and analysis

## Decision Guidance

Classify each material claim as `verified`, `qualified`, `disputed`, `stale`,
or `unverified`. Use `verified` only when accessible evidence directly supports
the full claim at the required date and scope. Use `qualified` when evidence
supports a narrower statement or depends on explicit conditions. Use
`disputed` when credible sources conflict, `stale` when the evidence no longer
meets the claim's time requirement, and `unverified` when reliable support is
absent or inaccessible.

Primary evidence is preferred but not automatically sufficient: confirm that
it is the applicable version and that its methods or definitions match the
claim. Strong secondary sources may interpret complex primary material, but
search snippets, aggregators, copied citations, and unsourced summaries are
discovery leads rather than final evidence.

For current or volatile claims, record an as-of date. For high-impact or
regulated claims, require stronger corroboration and keep operational research
separate from qualified legal, medical, financial, or regulatory judgment.

## Evidence Minimum

- exact claim, scope, relevant date, and required confidence
- source type, title, publisher or author, date or version, and stable locator
- passage, table, field, or result that directly supports the claim
- authority, directness, independence, methodology, and freshness assessment
- claim status and explicit qualification, disagreement, or uncertainty
- separation of sourced facts, calculations, inference, forecast, and opinion
- inaccessible evidence, citation drift, and the trigger for future rechecking

## References

Load [the source evidence assessment](references/source-evidence-assessment.md)
for dynamic, disputed, high-impact, regulated, multi-source, methodological,
paywalled, archived, or otherwise difficult evidence.

## Verifier Expectations

- citation check
- source freshness check
- source type check
- claim-to-source mapping

## Failure Handling

If a claim cannot be verified from reliable sources, state that it is
unverified instead of filling the gap. Never fabricate citations, treat a
search snippet as verification, silently resolve conflicting sources, or
bypass access controls. Network, account, subscription, and external retrieval
actions remain subject to host approval.
