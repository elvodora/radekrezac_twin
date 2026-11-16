# Change 2026-11-16 18:20 - Fix failed Vercel deployment

## Problem

The GitHub Actions run for commit `fbbfbc5` (run 43915609326) failed in the "Deploy production" step:

```
Error: Found src/app.py but it does not define a top-level "app" FastAPI instance.
```

The `Node.js 20 is deprecated` message in the same run is only a warning. It did not cause the failure.

## Root cause (verified)

- `vercel project inspect` showed **Framework Preset: FastAPI**, auto-detected from `src/app.py` at import, so `Dockerfile.vercel` was ignored.
- A preview with `"framework": null` ("Other") built in 54 ms, and `vercel inspect` listed no builds, so the image still wasn't built.
- Vercel Container Runtime docs: an existing project detected as another framework needs the `container` preset.

## Changes

- `vercel.json` (new): `"framework": "container"`.
- `.github/workflows/deploy.yml`: `actions/checkout@v7` and `pnpm/action-setup@v6`, both on the node24 runtime, and Vercel CLI pinned to `vercel@65.16.0`.
- `doc/cicd.md`: documents `vercel.json`, the updated workflow, preview verification and a troubleshooting table.

## Verification

- Preview `dpl_CejnRSNhZqSBEYiipzgDmNDNdacK`: the image built (9 Dockerfile steps, 60 packages) and `vercel inspect` shows `λ container (131.21MB)`.
- That preview returns **500**. The project has no environment variables (`vercel env ls` is empty). Running the app locally without `OPENAI_API_KEY` reproduces `openai.OpenAIError: Missing credentials` at import.

## Remaining manual step

Set `OPENAI_API_KEY`, `PUSHOVER_USER`, `PUSHOVER_TOKEN` for Production and Preview (`doc/cicd.md` section 4), then push or redeploy.
