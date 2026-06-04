---
name: trivy-container-security-scan
description: Use when reviewing container images, filesystems, dependencies, IaC, secrets, or SBOM security findings with Trivy-style scanners.
---

# Trivy Container Security Scan

## When To Use

Use this skill when a project needs container, dependency, configuration, secret,
or SBOM security review before release or deployment.

## Safe Workflow

1. Identify the target type: image, filesystem, repository, IaC directory, SBOM,
   or container registry metadata.
2. Confirm the scanner is already installed or approved by the operator.
3. Run only bounded scans against the declared target.
4. Group findings by vulnerability, misconfiguration, secret exposure, and license
   risk.
5. Prioritize exploitable critical and high findings that affect deployed paths.
6. Produce remediation steps and record residual risk.

## Expected Output

- scan target and scanner version
- severity summary
- critical and high findings
- remediation plan
- ignored or accepted risk list

## Verifier Expectations

- target path or image is explicit
- no unapproved installation occurs
- secrets are redacted in reports
- remediation is tied to package, image layer, or config path

## Boundary

This is a reference skill inspired by Aqua Security Trivy. It documents a safe
review workflow and does not bundle scanner binaries or vulnerability databases.
