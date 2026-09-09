from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import parse_qs, urlparse

import webview

import vrc_morse_osc


PROJECT_DIR = Path(__file__).resolve().parent
HTML_FILE = PROJECT_DIR / "morse_code_soundboard.html"


class QuietRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass

    def do_GET(self) -> None:
        # window.pywebview.api がまだ注入されていない間、HTML はこの経路に
        # フォールバックしてくる。取りこぼすと送信中の文字が画面に出ない。
        parsed = urlparse(self.path)
        if parsed.path == "/vrc_send":
            ch = parse_qs(parsed.query).get("c", [" "])[0]
            vrc_morse_osc.push_char(ch)
            self.send_response(204)
            self.end_headers()
            return
        super().do_GET()


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
        js_api=vrc_morse_osc.Api(),
    )
    try:
        webview.start()
    finally:
        # 閉じた瞬間に最後の1文字がTV画面へ焼き付いたままになるのを防ぐ。
        vrc_morse_osc.clear()
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
