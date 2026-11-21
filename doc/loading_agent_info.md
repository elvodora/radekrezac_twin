# Show "AI Twin is loading" during container start

## Problem

On Vercel the app runs from `Dockerfile.vercel` with `CMD ["python", "-m", "src.app"]`. Nothing listens on port 80 until `src.app` has imported gradio, openai and pypdf, parsed `profile.pdf` and started the Gradio server. On a cold start the visitor's browser waits on a blank page with no feedback.

## Approach

Bind port 80 within milliseconds with a tiny stdlib HTTP server that returns an "AI Twin is loading" page. Import the real app in the meantime. When it is ready, stop the loading server and launch Gradio on the same port. The loading page reloads itself every 2 seconds, so the visitor lands on the chat as soon as Gradio is up.

```
container start -> boot.py binds :80 -> serves loading page (auto refresh)
                -> imports src.app (slow)
                -> stops loading server -> demo launches on :80 -> next refresh shows chat
```

Only the Python standard library is used for the loading server, so it starts before any heavy import.

## Steps

### 1. Make `src/app.py` importable without launching

Move the `gr.ChatInterface(...).launch(...)` block that sat under `if __name__ == "__main__":` into a function, with its arguments unchanged:

```python
def launch():
    """Build the chat UI and start the Gradio server."""
    gr.ChatInterface(chat, ...).launch(css=CSS, js=JS, ...)


if __name__ == "__main__":
    launch()
```

`uv run python -m src.app` keeps working locally.

### 2. Add `src/boot.py`

```python
"""Container entrypoint: serve a loading page while the Gradio app starts."""

import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LOADING_HTML = b"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="2">
<title>AI Twin is loading</title>
<style>
  body { margin: 0; height: 100vh; display: grid; place-items: center;
         font-family: system-ui, sans-serif; background: #f7f7f8; color: #222; }
  @media (prefers-color-scheme: dark) { body { background: #111; color: #eee; } }
  .box { text-align: center; }
  .spinner { width: 40px; height: 40px; margin: 0 auto 16px; border-radius: 50%;
             border: 4px solid #ccc; border-top-color: #4f46e5;
             animation: spin 1s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body>
  <div class="box">
    <div class="spinner"></div>
    <h2>AI Twin is loading...</h2>
    <p>This takes a few seconds. The page refreshes automatically.</p>
  </div>
</body>
</html>"""


class LoadingHandler(BaseHTTPRequestHandler):
    """Answer every GET with the loading page."""

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(LOADING_HTML)

    def log_message(self, *args):
        pass


def main():
    """Serve the loading page, import the app, then hand the port to Gradio."""
    port = int(os.environ.get("GRADIO_SERVER_PORT", "7860"))
    loader = ThreadingHTTPServer(("0.0.0.0", port), LoadingHandler)
    threading.Thread(target=loader.serve_forever, daemon=True).start()
    print(f"Loading page on port {port}, importing app")

    from src.app import launch  # slow part: gradio, openai, pypdf, profile parsing

    loader.shutdown()
    loader.server_close()
    launch()


if __name__ == "__main__":
    main()
```

Notes:
- `Cache-Control: no-store` keeps browsers and the Vercel CDN from caching the loading page.
- Status 200 (not 503) so a platform health check or error page does not replace the loading page.
- Between `server_close()` and Gradio binding the port there is a gap of well under a second; a refresh that hits it simply retries 2 seconds later.

### 3. Update `Dockerfile.vercel`

Use the new entrypoint and precompile bytecode so imports are faster on cold start:

```dockerfile
RUN uv pip install --system --no-cache --compile-bytecode -r src/requirements.txt

COPY src/ src/
RUN python -m compileall -q src

CMD ["python", "-m", "src.boot"]
```

No change is needed in `.github/workflows/deploy.yml`; the next push deploys the new image.

## Status

Implemented on 2026-11-21. Local test with `GRADIO_SERVER_PORT=7899 uv run python -m src.boot`: the loading page was served for about 10 seconds, then the same port served the Gradio app.

## Verify

1. Locally: `docker build -f Dockerfile.vercel -t twin .` then `docker run --rm -p 8080:80 --env-file .env twin`. Open `http://localhost:8080` immediately: the loading page shows, then the chat appears after the app imports.
2. On Vercel: push to a branch, open the preview URL after a period of inactivity (cold start) and confirm the loading page appears before the chat.

## Limits

The loading page appears once the container process runs. Time Vercel spends pulling and starting the image happens before that, and no code in the container can show a message during it. Keep the image small (slim base, only `src/requirements.txt`) to keep that part short.
