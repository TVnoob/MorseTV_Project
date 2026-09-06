from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import webview


PROJECT_DIR = Path(__file__).resolve().parent
HTML_FILE = PROJECT_DIR / "morse_code_soundboard.html"


class QuietRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


def main() -> None:
    if not HTML_FILE.is_file():
        raise FileNotFoundError(f"HTML file was not found: {HTML_FILE}")

    handler = lambda *args, **kwargs: QuietRequestHandler(
        *args, directory=str(PROJECT_DIR), **kwargs
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    Thread(target=server.serve_forever, daemon=True).start()

    webview.create_window(
        "CW Morse Virtual Soundboard",
        f"http://127.0.0.1:{server.server_port}/{HTML_FILE.name}",
        width=1280,
        height=900,
        min_size=(960, 640),
        resizable=True,
    )
    try:
        webview.start()
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
