---
name: execution-playwright-browser-automation
description: Use when planning deterministic browser checks, UI smoke tests, page assertions, screenshots, or web automation verification.
---

# Execution Playwright Browser Automation

## When To Use

Use this skill when a browser task needs repeatable navigation, visible text
checks, screenshots, form-flow smoke tests, or UI regression evidence.

## Safe Workflow

1. Define target URL, viewport, browser context, and allowed user actions.
2. Prefer assertions on URL, visible text, DOM state, and screenshot evidence.
3. Keep test data and account context separate from public reports.
4. Stop before payment, account mutation, destructive forms, or private data
   extraction unless explicitly approved.
5. Record the exact page state and failure reproduction steps.

## Expected Output

- browser verification plan
- assertions and screenshots
- reproduction steps
- observed failures
- approval notes for sensitive flows

## Verifier Expectations

- navigation trace
- visible assertion check
- screenshot check
- sensitive action boundary check

## Failure Handling

If a page cannot load or the state is unstable, report the last confirmed URL,
visible state, and blocker.

## Boundary

This is a reference skill inspired by Microsoft Playwright. It documents
browser verification patterns and does not bundle Playwright runtime code.
