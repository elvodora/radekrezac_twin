"""Container entrypoint: serve a loading page while the Gradio app starts.

Vercel can spread one page load over several container instances, so an
instance that is still starting may receive asset or API requests for a page
served by a ready instance. Only "/" gets the loading page; any other request
is held until this instance is ready and then redirected to the same URL.

The listening socket is never closed: it is handed from the loading server to
uvicorn, so requests arriving during the switch wait in the backlog instead of
being refused.
"""

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

ready = threading.Event()


class LoadingHandler(BaseHTTPRequestHandler):
    """Loading page for "/", hold-and-redirect for everything else."""

    def do_GET(self):
        if self.path.split("?")[0] == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(LOADING_HTML)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(LOADING_HTML)
        else:
            self.redirect_when_ready()

    def do_HEAD(self):
        self.redirect_when_ready()

    def do_POST(self):
        self.redirect_when_ready()

    def redirect_when_ready(self):
        """Wait until the app is ready, then send the client back to the same URL."""
        ready.wait(timeout=120)
        self.send_response(307)
        self.send_header("Location", self.path)
        self.send_header("Content-Length", "0")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def log_message(self, *args):
        pass


def main():
    """Serve the loading page, build the app, then hand the socket to uvicorn."""
    host = os.environ.get("GRADIO_SERVER_NAME", "0.0.0.0")
    port = int(os.environ.get("GRADIO_SERVER_PORT", "7860"))
    loader = ThreadingHTTPServer((host, port), LoadingHandler)
    threading.Thread(target=loader.serve_forever, daemon=True).start()
    print(f"Loading page on {host}:{port}, importing app")

    import uvicorn
    from src.app import build_app  # slow part: gradio, openai, pypdf, profile parsing

    app = build_app()
    loader.shutdown()  # stop accepting; the socket stays open and queues connections
    ready.set()  # held requests now get their redirect
    print("App ready, handing socket to uvicorn")
    uvicorn.Server(uvicorn.Config(app, log_level="warning")).run(sockets=[loader.socket])


if __name__ == "__main__":
    main()
