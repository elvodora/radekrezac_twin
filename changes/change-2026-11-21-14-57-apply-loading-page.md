# Change 2026-11-21 14:57 - Apply loading page

## Summary

Implemented the plan from `doc/loading_agent_info.md` (see `change-2026-11-21-14-53-loading-agent-info.md`). During a cold start visitors now see an "AI Twin is loading..." page instead of a blank page.

## Files

- `src/app.py`: the `gr.ChatInterface(...).launch(...)` block moved from `if __name__ == "__main__":` into `launch()`. Arguments are unchanged. `uv run python -m src.app` still works.
- `src/boot.py`: new container entrypoint. A stdlib `ThreadingHTTPServer` serves the loading page (200, `no-store`, refreshes every 2 s) while `src.app` imports. It then shuts down and `launch()` starts Gradio on the same port.
- `Dockerfile.vercel`: `CMD` is now `python -m src.boot`. Dependencies and `src` are precompiled to bytecode.
- `doc/loading_agent_info.md`: step 1 matches the real code; added a Status section.
- `AGENTS.md`: Deployment notes that the entrypoint is `src/boot.py`.

## Verification

- Ran `GRADIO_SERVER_PORT=7899 uv run python -m src.boot` and polled `/` every 0.5 s. Polls 1-20 (about 10 s) returned the loading page. Poll 21 returned the Gradio app on the same port. The port was free after the process was stopped.
- Not yet verified: the Docker image build, and a Vercel preview deploy on a cold start.
