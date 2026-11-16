# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Gradio chat app acting as Radek Rezac's "digital twin": an OpenAI chat model answers visitor questions about his career, grounded in his profile, and uses tools to notify him via Pushover.

## Running

Dependencies are managed by the root `pyproject.toml` / `uv.lock` (a broad shared "agents" environment; the app itself only needs gradio, openai, pypdf, requests, python-dotenv). Run from the repo root:

```
uv run python -m src.app
```

Required env vars (loaded from `.env` via python-dotenv): `OPENAI_API_KEY`, `PUSHOVER_USER`, `PUSHOVER_TOKEN`.

Imports use the `src.*` package prefix; data files (`profile.pdf`, `summary.txt`, `aiclone.jpeg`) are resolved via `Path(__file__).parent`, so keep new file references module-relative rather than cwd-relative.

There are no tests or linters configured.

## Architecture

- `context.py` - builds `TWIN_SYSTEM_PROMPT` at import time from `profile.pdf` (text via pypdf) and `summary.txt`. Changing the twin's knowledge means editing these data files, not code.
- `app.py` - `chat()` runs a manual OpenAI Chat Completions tool loop: re-calls the model while `finish_reason == "tool_calls"`. Model name is `MODEL_NAME`. Launches `gr.ChatInterface` with CSS/JS from `styles.py`; `allowed_paths` must include any static file served via `/gradio_api/file=...`.
- `tools.py` - tool functions, their JSON schemas, and `tool_map`. Adding a tool requires all three: the function, a schema appended to `tools`, and an entry in `tool_map`. Both current tools just send a Pushover notification.
- `styles.py` - `CSS`, `JS`, `EXAMPLES` constants. Light/dark theming keys off Gradio's `.dark` class on `<body>`; the banner uses `aiclone.jpeg` as background.
