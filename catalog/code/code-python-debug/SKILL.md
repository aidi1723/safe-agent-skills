---
name: code-python-debug
description: Use when diagnosing and fixing Python bugs with focused tests, minimal changes, and explicit verification.
---

# Python Debug Workflow

## When To Use

Use this skill when a Python program, test, CLI, API path, or data-processing
script fails and the user wants a concrete fix.

## Safe Workflow

1. Reproduce the failure with the narrowest available command or input.
2. Identify the failing behavior and the expected behavior.
3. Write or update a focused test that fails for the observed problem.
4. Implement the smallest change that makes the test pass.
5. Re-run the focused test, then run the relevant broader test suite.
6. Report the exact verification commands and results.

## Expected Output

- root cause summary
- scoped code change
- regression test when appropriate
- verification evidence

## Verifier Expectations

- Python compile check
- focused unit test
- relevant test discovery or package-level test command

## Failure Handling

If the failure cannot be reproduced, report the reproduction gap and avoid
claiming the bug is fixed.
