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
