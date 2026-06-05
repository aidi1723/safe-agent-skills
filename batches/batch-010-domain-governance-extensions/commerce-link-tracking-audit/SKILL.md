---
name: commerce-link-tracking-audit
description: Use when checking campaign links, UTM parameters, commerce landing pages, inquiry funnels, tracking events, or marketing handoff URLs.
---

# Commerce Link Tracking Audit

## When To Use

Use this skill when commerce pages, emails, ads, product listings, or campaign
materials must preserve link tracking and funnel measurement integrity.

## Safe Workflow

1. Inventory all outbound links, CTAs, forms, phone links, chat links, and
   tracking events in scope.
2. Check that required UTM fields, campaign IDs, source names, and event names
   match the local analytics or BI convention.
3. Verify that internal navigation, lead forms, and conversion links preserve
   attribution across the funnel.
4. Flag broken links, missing tracking parameters, duplicate event names,
   unsafe redirects, and unapproved destination domains.
5. Record any analytics-schema assumptions instead of inventing event names.

## Expected Output

- link and CTA inventory
- tracking parameter findings
- event naming issues
- destination domain concerns
- funnel attribution gaps

## Verifier Expectations

- link inventory check
- UTM or campaign parameter check
- tracking event schema check
- destination and redirect check

## Failure Handling

If the analytics schema is unavailable, report the missing schema and limit the
review to mechanical URL, redirect, and parameter consistency checks.
