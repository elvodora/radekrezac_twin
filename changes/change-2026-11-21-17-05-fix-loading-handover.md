# Change 2026-11-21 17:05 - Fix loading page handover on Vercel

## Summary

After the loading page, Vercel showed either a blank page or `500 FUNCTION_INVOCATION_FAILED`, and the chat appeared only after manual refreshes. Fixed in `src/boot.py`.

## Root cause

Reproduced with a cold start of production (`https://radekrezac-twin.vercel.app/`, idle for more than 6 minutes, then opened in a browser):

- The loading page showed, then the refresh returned the Gradio HTML.
- Every `/assets/*.js` request returned 200 with `text/html`. The browser rejected each one with "Expected a JavaScript module script but the server responded with a MIME type of text/html", so Gradio never rendered.
- The Gradio HTML came from a ready instance, while its assets went to another instance that was still starting. The old `boot.py` answered every path with the loading page.
- Second flaw: the old `boot.py` closed the socket and let `demo.launch()` bind the port again. A request routed to the instance in that gap is refused, which Vercel reports as `500 FUNCTION_INVOCATION_FAILED`.

## Fix

- `src/boot.py`: the loading page is served only on `/`. Other GET, HEAD and POST requests are held until the app is ready, then answered with `307` to the same URL. The listening socket is never closed: the loading server stops and uvicorn runs on the same socket (`Server.run(sockets=[...])`).
- `src/app.py`: `launch()` is replaced by `build_demo()`, `build_app()` (via `gr.mount_gradio_app`) and `UI_OPTIONS`. Local `python -m src.app` still uses `demo.launch()`.
- `doc/loading_agent_info.md`: rewritten for the new design, with the Vercel findings.
- `AGENTS.md`: cold-start rules updated.

## Verification

- Local `src.boot` on port 7899: an asset requested during loading was held about 8 s, then served as `text/javascript` after one redirect. Polling `/` every 0.1 s went from the loading page (23 polls) to Gradio, with no refused connection.
- Browser: the UI rendered with its styles and banner. A chat message got a model reply, which shows the queue works through uvicorn.
- `python -m src.app` still serves the app.
- Not yet verified: a Vercel cold start with this version. It needs a push and deploy.
