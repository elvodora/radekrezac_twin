# Change 2026-11-16 17:08 - Vercel CI/CD documentation

## Summary

Documented how to deploy the Gradio AI Twin from GitHub to Vercel automatically, including the Vercel environment variables.

## Files

- `doc/cicd.md` (new): deployment guide.
- `AGENTS.md` (new): agent guidance for the repository, including the deployment and change-log conventions.
- `changes/change-2026-11-16-17-08-vercel-cicd-doc.md` (new): this entry.

## Decisions

- **Deploy as a Vercel container image (`Dockerfile.vercel`).** Gradio runs its own server, and the container installs only `src/requirements.txt` instead of the large root `pyproject.toml`. No application code changes are needed; `GRADIO_SERVER_NAME` and `GRADIO_SERVER_PORT` make it listen on `0.0.0.0:80`.
- **Primary path: Vercel Git integration** (`main` goes to production, other branches and PRs to preview). GitHub Actions with `VERCEL_TOKEN` / `VERCEL_ORG_ID` / `VERCEL_PROJECT_ID` is documented as an alternative.
- **Runtime secrets** (`OPENAI_API_KEY`, `PUSHOVER_USER`, `PUSHOVER_TOKEN`) live in Vercel project environment variables for Production and Preview.

## Follow-ups (not done in this change)

- Create `Dockerfile.vercel` and `.vercelignore` from the templates in `doc/cicd.md`.
- Add `.env` and `.vercel` to `.gitignore`. `.env` is currently not ignored.
- Gradio queue state is in-memory, so parallel requests may fail across instances. This is acceptable for low traffic.
