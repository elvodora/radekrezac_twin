# Show "AI Twin is loading" during container start

## Problem

Nothing listens on port 80 until `src.app` has imported gradio, openai and pypdf and parsed `profile.pdf` (about 10 s). On a Vercel cold start the visitor would wait on a blank page.

## Design

`Dockerfile.vercel` runs `python -m src.boot`. `src/boot.py`:

1. Binds the port immediately with a stdlib `ThreadingHTTPServer`, before any heavy import.
2. Answers `/` with an "AI Twin is loading" page (200, `no-store`, `<meta http-equiv="refresh" content="2">`).
3. Holds every other request (assets, API, HEAD, POST) until the app is ready, then answers `307` to the same URL.
4. Builds the app with `src.app.build_app()` (Gradio mounted on FastAPI via `gr.mount_gradio_app`).
5. Stops the loading server but keeps its listening socket open, and runs uvicorn on that same socket: `uvicorn.Server(config).run(sockets=[loader.socket])`.

```
cold start -> boot.py binds :80
           -> "/"        : loading page, refresh every 2 s
           -> other paths: held, then 307 to same URL
           -> app built  -> same socket handed to uvicorn -> next refresh shows the chat
```

`src/app.py` exposes `build_demo()`, `build_app()` and `UI_OPTIONS` (css, js, theme, allowed_paths). `uv run python -m src.app` still runs `build_demo().launch(**UI_OPTIONS)` for local use.

## Why each part is needed (found on Vercel)

- **Several instances serve one page load.** A cold-start test on production showed the Gradio HTML coming from a ready instance while its `/assets/*.js` requests went to another instance still starting. The first version answered every path with the loading page, so the scripts came back as `text/html`, the browser rejected them ("Expected a JavaScript module script ... MIME type of text/html") and the page stayed blank. Hence: loading page only on `/`, hold-and-redirect for everything else.
- **No gap at the handover.** The first version closed the socket and let `demo.launch()` bind the port again. A request routed to the instance in between was refused, which Vercel reports as `500 FUNCTION_INVOCATION_FAILED`. Handing the open socket to uvicorn means connections wait in the backlog instead.

## Dockerfile

```dockerfile
RUN uv pip install --system --no-cache --compile-bytecode -r src/requirements.txt
COPY src/ src/
RUN python -m compileall -q src
CMD ["python", "-m", "src.boot"]
```

No change is needed in `.github/workflows/deploy.yml`.

## Verify

1. Locally: `GRADIO_SERVER_PORT=7899 uv run python -m src.boot`. During loading, `curl -L http://127.0.0.1:7899/assets/<file>.js` must wait, then return `text/javascript` after one redirect. `/` must go from the loading page to Gradio with no refused connection.
2. Docker: `docker build -f Dockerfile.vercel -t twin .` then `docker run --rm -p 8090:80 --env-file .env twin`, open `http://localhost:8090` immediately.
3. Vercel: leave production idle for more than 5 minutes (30 s for preview) so it scales to zero, then open the public URL. The loading page must turn into the chat with no blank page and no manual refresh.

## Limits

- Time Vercel spends pulling and starting the image happens before `boot.py` runs; nothing in the container can show a message then.
- Gradio's queue (send message, stream reply) assumes requests reach the same process. Vercel gives no instance affinity, so chat may still misbehave if Vercel spreads one session over several instances.
