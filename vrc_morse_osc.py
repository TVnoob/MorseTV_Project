"""
vrc_morse_osc.py - sends the character currently being keyed to a VRChat avatar.

Standard library only. No pip install needed.

VRChat receives OSC over UDP on 127.0.0.1:9000. A browser cannot send UDP,
so the HTML calls into this module and this module talks to VRChat.

--------------------------------------------------------------------------
HOOKING IT UP - pick the one that matches your wrapper
--------------------------------------------------------------------------

  Eel:
      import eel, vrc_morse_osc
      vrc_morse_osc.bind_eel(eel)          # exposes vrc_send_char to JS
      eel.init('web'); eel.start('index.html')

  pywebview:
      import webview, vrc_morse_osc
      webview.create_window('Morse', 'index.html', js_api=vrc_morse_osc.Api())
      webview.start()

  Flask / FastAPI (or any local HTTP server):
      from flask import Flask, request
      import vrc_morse_osc
      app = Flask(__name__)

      @app.route('/vrc_send')
      def vrc_send():
          vrc_morse_osc.push_char(request.args.get('c', ' '))
          return '', 204

The patched HTML tries all three in that order, so you only need one.

--------------------------------------------------------------------------
ON THE VRCHAT SIDE
--------------------------------------------------------------------------
  * Avatar needs a float parameter named MorseChar (see PARAM_NAME below),
    listed in the Expression Parameters asset.
  * Turn OSC on in game: Action Menu -> Options -> OSC -> Enabled.
  * If the parameter was added after VRChat cached the avatar's OSC config,
    reset the config from that same menu.

Run this file directly to test without the soundboard:
      python vrc_morse_osc.py --demo HELLO WORLD
"""

import socket
import struct
import sys
import threading
import time
import queue

# --------------------------------------------------------------- config
VRC_HOST = "127.0.0.1"
VRC_PORT = 9000
PARAM_NAME = "MorseChar"

# Index order. MUST match morse_glyph_atlas.png cell order (8 per row).
CHARSET = (" ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
           ".,?'!/()&:;=+-_\"$@")

# VRChat syncs avatar parameters to other players as periodic snapshots, not
# as events. A value that is held for less than roughly this long can be
# skipped entirely on someone else's client. Every character is held at least
# this long, even if the audio has already moved on.
MIN_HOLD_SEC = 0.40

# Above this backlog the display is lagging noticeably behind the tone.
WARN_QUEUE_LEN = 6

_ADDRESS = "/avatar/parameters/" + PARAM_NAME
_INDEX = {c: i for i, c in enumerate(CHARSET)}
_SPAN = len(CHARSET) - 1

_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
_queue = queue.Queue()
_worker = None
_lock = threading.Lock()


# --------------------------------------------------------------- osc wire
def _pad(b: bytes) -> bytes:
    """OSC strings are null terminated and padded to a multiple of 4 bytes."""
    b += b"\x00"
    return b + b"\x00" * (-len(b) % 4)


def _osc_float(address: str, value: float) -> bytes:
    return _pad(address.encode("ascii")) + _pad(b",f") + struct.pack(">f", value)


def send_index(index: int) -> None:
    """Send a glyph index straight away, no hold logic."""
    index = max(0, min(index, _SPAN))
    _sock.sendto(_osc_float(_ADDRESS, index / _SPAN), (VRC_HOST, VRC_PORT))


# --------------------------------------------------------------- queueing
def _run():
    while True:
        index = _queue.get()
        send_index(index)
        time.sleep(MIN_HOLD_SEC)


def _ensure_worker():
    global _worker
    with _lock:
        if _worker is None or not _worker.is_alive():
            _worker = threading.Thread(target=_run, daemon=True)
            _worker.start()


def push_char(ch) -> None:
    """Queue one character for display. Unknown characters show as blank."""
    ch = (ch or " ")
    if len(ch) > 1:
        ch = ch[0]
    index = _INDEX.get(ch.upper(), 0)
    _ensure_worker()
    _queue.put(index)
    n = _queue.qsize()
    if n > WARN_QUEUE_LEN:
        print(f"[vrc_morse_osc] display is {n} characters behind - "
              f"lower the WPM or reduce MIN_HOLD_SEC", file=sys.stderr)


def clear() -> None:
    """Blank the screen immediately and drop anything still queued."""
    try:
        while True:
            _queue.get_nowait()
    except queue.Empty:
        pass
    send_index(0)


# --------------------------------------------------------------- wrappers
class Api:
    """js_api object for pywebview."""

    def vrc_send_char(self, ch):
        push_char(ch)
        return True

    def vrc_clear(self):
        clear()
        return True


def bind_eel(eel_module):
    """Expose the bridge to JavaScript under Eel."""
    eel_module.expose(_eel_send_char)
    eel_module.expose(_eel_clear)


def _eel_send_char(ch):
    push_char(ch)


_eel_send_char.__name__ = "vrc_send_char"


def _eel_clear():
    clear()


_eel_clear.__name__ = "vrc_clear"


# --------------------------------------------------------------- demo
if __name__ == "__main__":
    if "--demo" in sys.argv:
        text = " ".join(sys.argv[sys.argv.index("--demo") + 1:]) or "CQ CQ"
        print(f"sending to {VRC_HOST}:{VRC_PORT} -> {_ADDRESS}")
        for ch in text:
            idx = _INDEX.get(ch.upper(), 0)
            print(f"  {ch!r:6} index {idx:2}  param {idx/_SPAN:.4f}")
            push_char(ch)
        time.sleep(len(text) * MIN_HOLD_SEC + 0.5)
        clear()
    else:
        print(__doc__)
