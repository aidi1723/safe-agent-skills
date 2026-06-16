---
name: media-remotion-video-production-boundary
description: Use when planning or reviewing Remotion-style programmatic video production, React-based video composition, render boundaries, asset inputs, captions, timing, and approval gates before generating video.
---

# Media Remotion Video Production Boundary

## When To Use

Use this skill when a task should turn an idea, script, or content matrix into a
programmatic video production plan using Remotion-style React composition,
timelines, captions, assets, and render checks.

This skill provides method and safety boundaries only. It does not install,
run, render, publish, or grant access to Remotion, media assets, cloud render
services, accounts, or production pipelines.

## Safe Workflow

1. Identify the video goal, duration, aspect ratio, platform, audience, script,
   brand constraints, and required source assets.
2. Convert the idea into scenes with timing, narration or captions, visual
   components, transitions, data overlays, and CTA.
3. Define inputs explicitly: images, clips, fonts, audio, data, subtitles,
   logos, product screenshots, and rights or license status.
4. Separate creative planning from rendering. Rendering, dependency install,
   cloud functions, uploads, and publication require separate host approval.
5. Plan technical checks: composition dimensions, frame range, asset loading,
   audio sync, subtitle readability, motion safety, and deterministic output.
6. Review claims, rights, brand voice, accessibility, and platform compliance
   before rendering or publishing.

## Expected Output

- scene-by-scene production plan
- asset and rights inventory
- Remotion-style composition boundary notes
- render and QA checklist
- approval gates for install, render, upload, and publish actions

## Verifier Expectations

- script and scene coverage check
- asset provenance and rights check
- dimensions, timing, captions, and audio sync review
- reduced-motion or flashing-risk check when relevant
- explicit approval record before any rendering or publishing workflow

## Failure Handling

If assets, rights, or platform requirements are missing, produce a shot and
asset requirement list instead of assuming visuals. If runtime permissions are
unclear, keep the workflow as planning-only.
