---
name: execution-mcp-tool-connector-review
description: Use when reviewing MCP servers, tool connectors, permission scopes, data access, or agent integration boundaries.
---

# Execution MCP Tool Connector Review

## When To Use

Use this skill when an agent will connect to tools, MCP servers, filesystems,
APIs, databases, browsers, or local services.

## Safe Workflow

1. Identify connector purpose, owner, data access, allowed tools, and host
   approval policy.
2. Separate read-only tools from write, account, production, and external
   network actions.
3. Check whether the connector exposes private files, secrets, credentials, or
   broad workspace access.
4. Require explicit approval for high-impact or irreversible operations.
5. Record connector limits, test evidence, and residual risk.

## Expected Output

- connector inventory
- permission boundary
- sensitive data risk notes
- approval checklist
- review decision

## Verifier Expectations

- tool list check
- permission scope check
- sensitive data access check
- host approval policy check

## Failure Handling

If license, tool scope, or data access is unclear, keep the connector in review
state and exclude it from default runtime use.

## Boundary

This is a reference skill inspired by Model Context Protocol server patterns.
It documents connector review only and does not bundle MCP servers or grant
tool access.
