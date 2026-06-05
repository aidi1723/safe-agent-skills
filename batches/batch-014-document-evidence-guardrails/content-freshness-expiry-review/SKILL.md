---
name: content-freshness-expiry-review
description: Use when reviewing stale content, time-sensitive claims, dated screenshots, outdated docs, pricing mentions, policy dates, or freshness risk.
---

# Content Freshness Expiry Review

## When To Use

Use this skill when content includes time-sensitive claims, dated evidence,
pricing, product availability, legal or operational dates, screenshots, or
market statements.

## Safe Workflow

1. Identify every date, relative-time phrase, version, price, availability
   statement, and time-sensitive comparison.
2. Convert relative dates into explicit dates when the publication context is
   known.
3. Check whether sources, screenshots, tables, and linked references have an
   acceptable freshness window for the content purpose.
4. Flag stale claims, missing access dates, version drift, expired offers, and
   language that implies current certainty without current evidence.
5. Recommend expiry notes, review dates, or wording that makes freshness limits
   clear.

## Expected Output

- freshness-sensitive claim list
- explicit date conversions
- stale or missing-source warnings
- review-by date recommendations
- revised wording targets

## Verifier Expectations

- date and version check
- source freshness check
- relative-time conversion check
- expiry or review-date check

## Failure Handling

If freshness cannot be verified, label the claim as time-sensitive and avoid
presenting it as current.
