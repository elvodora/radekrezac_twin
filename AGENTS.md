# AGENTS.md

Guidance for AI coding agents working in this repository.

## Project

A Gradio chat app acting as Radek Rezac's "digital twin": an OpenAI chat model answers visitor questions about his career, grounded in his profile, and uses tools to notify him via Pushover. All application code lives in `src/`.

## Run locally

Dependencies are managed by the root `pyproject.toml` / `uv.lock`, a broad shared "agents" environment. The app itself only needs `src/requirements.txt` (gradio, openai, pypdf, requests, python-dotenv). Run from the repo root:

```
uv run python -m src.app
```

Required env vars, loaded from `.env` via python-dotenv: `OPENAI_API_KEY`, `PUSHOVER_USER`, `PUSHOVER_TOKEN`.

There are no tests or linters configured.

## Architecture

- `src/context.py`: builds `TWIN_SYSTEM_PROMPT` at import time from `profile.pdf` (text via pypdf) and `summary.txt`. Changing the twin's knowledge means editing these data files, not code.
- `src/app.py`: `chat()` runs a manual OpenAI Chat Completions tool loop that re-calls the model while `finish_reason == "tool_calls"`. The model is set in `MODEL_NAME`. It launches `gr.ChatInterface` with the CSS/JS from `styles.py`.
- `src/tools.py`: tool functions, their JSON schemas and `tool_map`. Adding a tool takes all three: the function, a schema appended to `tools`, and an entry in `tool_map`.
- `src/styles.py`: `CSS`, `JS`, `EXAMPLES` and `BANNER_IMAGE`. Light/dark theming keys off Gradio's `.dark` class on `<body>`. Layout width is set by `max-width` on `.gradio-container`; it is currently `100%` (full width). The chat area's height is set on the component in `app.py` (`gr.Chatbot(height="70vh", min_height=460)`), not in CSS. Gradio 6 has no `.chatbot` class, so `.chatbot` rules in `styles.py` have no effect.

## Conventions

- Imports use the `src.*` package prefix. Data files are resolved with `Path(__file__).parent`, never relative to the cwd.
- Any static file served through `/gradio_api/file=...` must be listed in `allowed_paths` in `app.py`.
- Use `uv` for Python and `pnpm` for Node tooling.

## Deployment

Deploys to Vercel as a container image (`Dockerfile.vercel` at the repo root). `vercel.json` must keep `"framework": "container"`; otherwise Vercel detects `src/app.py` as FastAPI and the build fails. It is triggered by GitHub pushes: `main` goes to production and other branches to preview. Runtime secrets are set as Vercel project environment variables. Full setup: `doc/cicd.md`.

Cold starts: the container entrypoint is `src/boot.py`, not `src/app.py`. A stdlib HTTP server binds the port at once, serves a self-refreshing "AI Twin is loading" page on `/` only, and holds every other path until ready, then redirects it (307) to itself. When `src.app.build_app()` is ready, the same listening socket is handed to uvicorn, so there is never a moment with no listener. Vercel spreads one page load over several instances, so never answer asset or API paths with the loading page, and never close the port during the switch. Keep `boot.py` imports stdlib-only before the port is bound, and keep `src/app.py` free of import-time launching. See `doc/loading_agent_info.md`.

## Change log

Record every change set in `changes/change-YYYY-MM-DD-HH-mm-<short-description>.md` (what changed, why, files touched).
