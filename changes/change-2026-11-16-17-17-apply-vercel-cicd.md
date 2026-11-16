# Change 2026-11-16 17:17 - Apply Vercel CI/CD setup

## Summary

Added the deployment files described in `doc/cicd.md`.

## Files

- `Dockerfile.vercel` (new): Python 3.12 slim image. It installs `src/requirements.txt` with uv 0.13.0 and runs `python -m src.app` on `0.0.0.0:80` via `GRADIO_SERVER_NAME` / `GRADIO_SERVER_PORT`.
- `.vercelignore` (new): excludes `.env`, `.venv/`, `__pycache__/`, `prompts/`, `changes/` and `doc/` from CLI uploads.
- `.gitignore`: now ignores `.env` and `.vercel`. `.env` was never committed.
- `doc/cicd.md`: section 2 now describes the files as present.

## Verification

- Docker engine not running locally, so the image itself was **not built**.
- Simulated the image: a clean Python 3.12 venv with only `src/requirements.txt`, a copy of `src/`, and the Dockerfile's env vars. `python -m src.app` served on `0.0.0.0`; the page and `aiclone.jpeg` both returned 200.
- Not verified: a chat turn (OpenAI call) and an actual Vercel deployment.

## Remaining manual steps

- Import the GitHub repository in Vercel and set `OPENAI_API_KEY`, `PUSHOVER_USER`, `PUSHOVER_TOKEN` for Production and Preview (`doc/cicd.md` sections 3-4).
