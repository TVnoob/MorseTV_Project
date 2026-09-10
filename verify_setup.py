#!/usr/bin/env python3
"""
verify_setup.py - checks that every piece of the Morse-to-VRChat setup
is present and mutually consistent.

    python verify_setup.py

Run this first in a new session. Everything it checks was passing when the
handoff was written, so a failure means something drifted since then.
Pillow is optional; the atlas checks are skipped without it.
"""

import json
import os
import socket
import struct
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
# Unity へ持っていくアセットはリポジトリ直下ではなく unity_assets/ に置いてある。
ASSETS = "unity_assets"
HTML_NAME = "morse_code_soundboard.html"
results = []


def check(name):
    def deco(fn):
        try:
            detail = fn()
            results.append((True, name, detail or ""))
        except AssertionError as e:
            results.append((False, name, str(e)))
        except Exception as e:
            results.append((False, name, f"{type(e).__name__}: {e}"))
        return fn
    return deco


def path(*p):
    return os.path.join(HERE, *p)


# ------------------------------------------------------------------ files
@check("expected files are present")
def _files():
    want = [f"{ASSETS}/crt_tv.obj", f"{ASSETS}/crt_tv.mtl", HTML_NAME,
            "vrc_morse_osc.py", f"{ASSETS}/morse_glyph_atlas.png",
            f"{ASSETS}/glyph_uv_table.json", "app.py"]
    missing = [f for f in want if not os.path.exists(path(f))]
    assert not missing, "missing: " + ", ".join(missing)
    return f"{len(want)} files"


sys.path.insert(0, HERE)
import vrc_morse_osc as V  # noqa: E402


# ------------------------------------------------------------------ html
@check("HTML patch is fully applied")
def _html():
    src = open(path(HTML_NAME), encoding="utf-8").read()
    probes = {
        "bridge block": "function sendToVRChat",
        "dedupe emitter": "function sendCurrentChar",
        "playback hook": "sendCurrentChar(currentItem.index)",
        "item capture": "txItems = items;",
        "stop blanks screen": "sendCurrentChar(-1)",
        "direct-morse reverse lookup": "REVERSE_MORSE[code]",
    }
    bad = [k for k, v in probes.items() if v not in src]
    assert not bad, "not found: " + ", ".join(bad)
    assert src.count("sendCurrentChar(currentItem.index)") == 1, "playback hook duplicated"
    return f"{len(probes)} hooks"


@check("audio path in HTML is untouched")
def _audio():
    src = open(path(HTML_NAME), encoding="utf-8").read()
    for marker in ["function playTone", "function getTimingUnits",
                   "createOscillator", "linearRampToValueAtTime"]:
        assert marker in src, f"{marker} is gone"
    return "intact"


@check("app.py wires the bridge into pywebview")
def _app():
    src = open(path("app.py"), encoding="utf-8").read()
    probes = {
        "bridge import": "import vrc_morse_osc",
        "js_api injection": "js_api=vrc_morse_osc.Api()",
        "http fallback route": '"/vrc_send"',
        "blank on exit": "vrc_morse_osc.clear()",
    }
    bad = [k for k, v in probes.items() if v not in src]
    assert not bad, "not found: " + ", ".join(bad)
    return f"{len(probes)} hooks"


# ------------------------------------------------------------------ atlas
@check("CHARSET matches the glyph atlas grid")
def _atlas():
    assert len(V.CHARSET) <= 64, f"{len(V.CHARSET)} glyphs will not fit an 8x8 atlas"
    assert V.CHARSET[0] == " ", "index 0 must be blank so word gaps clear the screen"
    assert len(set(V.CHARSET)) == len(V.CHARSET), "duplicate character in CHARSET"
    try:
        from PIL import Image
    except ImportError:
        return f"{len(V.CHARSET)} glyphs (image check skipped, no Pillow)"
    im = Image.open(path(ASSETS, "morse_glyph_atlas.png"))
    assert im.size == (512, 512), f"atlas is {im.size}, expected (512, 512)"
    px = im.convert("RGBA").load()
    cell = 64
    for i, ch in enumerate(V.CHARSET):
        col, row = i % 8, i // 8
        ink = any(px[col*cell + x, row*cell + y][3] > 0
                  for x in range(4, cell-4, 3) for y in range(4, cell-4, 3))
        if ch == " ":
            assert not ink, "cell 0 should be empty"
        else:
            assert ink, f"cell {i} for {ch!r} is empty"
    return f"{len(V.CHARSET)} glyphs verified"


@check("UV table agrees with CHARSET")
def _uv():
    t = json.load(open(path(ASSETS, "glyph_uv_table.json"), encoding="utf-8"))
    assert t["charset"] == V.CHARSET, "glyph_uv_table.json is out of sync with CHARSET"
    span = len(V.CHARSET) - 1
    for e in t["entries"]:
        i = e["index"]
        assert abs(e["param"] - i/span) < 1e-5, f"param wrong at index {i}"
        assert abs(e["offset"][0] - (i % 8)/8) < 1e-9, f"u offset wrong at index {i}"
        assert abs(e["offset"][1] - (1 - (i//8 + 1)/8)) < 1e-9, f"v offset wrong at index {i}"
    return f"{len(t['entries'])} entries"


# ------------------------------------------------------------------ sync
@check("every glyph survives VRChat's 8-bit parameter sync")
def _quant():
    span = len(V.CHARSET) - 1
    bad = [i for i in range(span + 1) if round(round(i/span * 255)/255 * span) != i]
    assert not bad, f"indices lost to quantisation: {bad}"
    return f"step {1/span:.4f} vs resolution {1/255:.4f} ({(1/span)/(1/255):.1f}x margin)"


@check("Motion Time のキー配置が全グリフを正しく拾う")
def _motion():
    import verify_motion_time as M
    bad_a = M.mismatches(0.0)
    bad_b = M.mismatches(0.5)
    assert not bad_b, (
        f"キー i-0.5 の配置でも {len(bad_b)} 文字ずれる。CLAUDE.md 4-2 を参照")
    return (f"i-0.5 配置で余裕 {M.worst_margin():.2f} フレーム "
            f"(素直な i 配置なら {len(bad_a)} 文字が壊れる)")


# ------------------------------------------------------------------ osc
@check("OSC packets reach the wire and decode correctly")
def _osc():
    srv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        srv.bind(("127.0.0.1", V.VRC_PORT))
    except OSError:
        srv.close()
        raise AssertionError(
            f"port {V.VRC_PORT} is busy. If VRChat is running this is expected - "
            "close it and rerun, or trust the live client instead.")
    srv.settimeout(3)
    got = []

    def rx():
        while True:
            try:
                got.append(srv.recvfrom(1024)[0])
            except (socket.timeout, OSError):
                # OSError はテスト終了時に srv を閉じたときに出るだけ。
                return

    threading.Thread(target=rx, daemon=True).start()

    hold, V.MIN_HOLD_SEC = V.MIN_HOLD_SEC, 0.02
    sample = "SOS 9!"
    for ch in sample:
        V.push_char(ch)
    time.sleep(0.02 * len(sample) + 0.5)
    V.MIN_HOLD_SEC = hold
    srv.close()

    assert len(got) >= len(sample), f"sent {len(sample)}, received {len(got)}"
    span = len(V.CHARSET) - 1
    decoded = ""
    for p in got[:len(sample)]:
        assert len(p) % 4 == 0, "OSC packet is not 4-byte aligned"
        addr = p[:p.index(b"\x00")].decode()
        assert addr == "/avatar/parameters/" + V.PARAM_NAME, f"wrong address {addr}"
        idx = round(struct.unpack(">f", p[-4:])[0] * span)
        decoded += V.CHARSET[idx]
    assert decoded == sample.upper(), f"round trip gave {decoded!r}, expected {sample.upper()!r}"
    return f"{len(sample)} chars round-tripped"


# ------------------------------------------------------------------ model
@check("TV model has the four material groups")
def _model():
    groups, tris = [], 0
    for ln in open(path(ASSETS, "crt_tv.obj")):
        if ln.startswith("usemtl "):
            groups.append(ln.split()[1])
        elif ln.startswith("f "):
            tris += len(ln.split()) - 3
    for g in ["TV_Body", "TV_Screen", "TV_Knob", "TV_Antenna"]:
        assert g in groups, f"material group {g} is missing"
    mtl = open(path(ASSETS, "crt_tv.mtl")).read()
    for g in groups:
        assert "newmtl " + g in mtl, f"{g} has no entry in crt_tv.mtl"
    return f"{tris} triangles, {len(groups)} groups"


# ------------------------------------------------------------------ report
if __name__ == "__main__":
    width = max(len(n) for _, n, _ in results)
    for ok, name, detail in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name.ljust(width)}  {detail}")
    failed = sum(1 for ok, _, _ in results if not ok)
    print()
    if failed:
        print(f"{failed} of {len(results)} checks failed.")
        sys.exit(1)
    print(f"All {len(results)} checks passed. See CLAUDE.md for what to do next.")
