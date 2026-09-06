from pathlib import Path

import webview


PROJECT_DIR = Path(__file__).resolve().parent
HTML_FILE = PROJECT_DIR / "morse_code_soundboard.html"


def main() -> None:
    if not HTML_FILE.is_file():
        raise FileNotFoundError(f"HTML file was not found: {HTML_FILE}")

    webview.create_window(
        "CW Morse Virtual Soundboard",
        HTML_FILE.as_uri(),
        width=1280,
        height=900,
        min_size=(960, 640),
        resizable=True,
    )
    webview.start()


if __name__ == "__main__":
    main()
