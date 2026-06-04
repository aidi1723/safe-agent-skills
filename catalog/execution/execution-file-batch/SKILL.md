---
name: execution-file-batch
description: Use when running bounded batch work over workspace files, generated artifacts, exports, or repeated local file operations.
---

# Execution File Batch

## When To Use

Use this skill when a task requires repeated file processing inside a declared
workspace scope.

## Safe Workflow

1. Identify the input folder, output folder, file patterns, and expected result.
2. Perform a dry listing before any write operation.
3. Keep generated artifacts separate from source files unless the user requests
   in-place changes.
4. Record counts, skipped files, and failures.
5. Verify representative outputs before reporting completion.

## Expected Output

- batch scope
- file counts
- output paths
- skipped or failed items
- verification notes

## Verifier Expectations

- input listing check
- output artifact check
- filesystem diff check when applicable
- sample content check

## Failure Handling

If the file scope is ambiguous, stop and ask for the target folder before
writing outputs.
