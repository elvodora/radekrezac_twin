# Change 2026-11-21 14:53 - Loading agent info

## Summary

Documented how to show visitors an "AI Twin is loading" page while the Vercel container starts. Documentation only; no code changed yet.

## Why

`Dockerfile.vercel` runs `python -m src.app` directly. Nothing listens on port 80 until gradio, openai and pypdf are imported and the profile is parsed, so on a cold start the visitor sees a blank page with no feedback.

## Proposed solution

A new entrypoint `src/boot.py` binds port 80 immediately with a stdlib HTTP server that serves a self-refreshing loading page, imports `src.app`, then stops the loading server and launches Gradio on the same port. `Dockerfile.vercel` switches `CMD` to `src.boot` and precompiles bytecode. The GitHub workflow needs no change.

## Files

- `doc/loading_agent_info.md`: new, step-by-step instructions.
- `AGENTS.md`: Deployment section points to the new doc.

## Inputs read

- `Dockerfile.vercel`
- `.github/workflows/deploy.yml`
