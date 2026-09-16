#!/usr/bin/env python3
"""
vrc_osc_listen.py - VRChat が送り返してくる OSC を表示する診断ツール。標準ライブラリのみ。

    python vrc_osc_listen.py

VRChat は、いま着ているアバターに存在するパラメータの値が変わるたびに
127.0.0.1:9001 へ /avatar/parameters/<名前> を送り返す。着替えると /avatar/change に
アバター ID が流れる。これを見れば「VRChat がアバターのパラメータを実際に書き換えたか」が
OSC Debug 画面の見た目に頼らず確定する。

使い方:
  1. VRChat を起動し、OSC を Enabled にしてこのスクリプトを実行
  2. テレビのアバターに着替える -> /avatar/change が出る
  3. 別の PowerShell で python vrc_morse_osc.py --demo HELLO を実行
     -> /avatar/parameters/MorseChar が 0.148 / 0.093 / ... と返ってくれば
        アバター側のパラメータは書き換わっている

Ctrl+C で終了。
"""

import socket
import struct
import sys
import time

LISTEN = ("127.0.0.1", 9001)
# 関係ない大量のパラメータ（VelocityX 等）で画面が埋まらないよう、既定ではこれだけ通す
INTERESTING = ("/avatar/change", "/avatar/parameters/MorseChar")


def _read_string(data, pos):
    end = data.index(b"\x00", pos)
    s = data[pos:end].decode("utf-8", "replace")
    pos = end + 1
    pos += (-pos) % 4
    return s, pos


def parse(packet):
    """OSC メッセージを (address, [values]) に分解する。バンドルは中身を再帰的に展開する。"""
    if packet.startswith(b"#bundle"):
        out, pos = [], 16
        while pos < len(packet):
            (size,) = struct.unpack(">i", packet[pos:pos + 4]); pos += 4
            out.extend(parse(packet[pos:pos + size])); pos += size
        return out
    addr, pos = _read_string(packet, 0)
    tags, pos = _read_string(packet, pos)
    vals = []
    for t in tags.lstrip(","):
        if t == "f": (v,) = struct.unpack(">f", packet[pos:pos + 4]); pos += 4
        elif t == "i": (v,) = struct.unpack(">i", packet[pos:pos + 4]); pos += 4
        elif t == "s": v, pos = _read_string(packet, pos)
        elif t == "T": v = True
        elif t == "F": v = False
        else: v = f"<{t}>"
        vals.append(v)
    return [(addr, vals)]


def main():
    show_all = "--all" in sys.argv
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(LISTEN)
    except OSError as e:
        print(f"{LISTEN[1]} 番を開けない ({e})。他の OSC ツール（VRCFaceTracking 等）が使っていないか確認。")
        return 1
    print(f"{LISTEN[0]}:{LISTEN[1]} で待機中 … VRChat 側で OSC が Enabled になっていること。"
          f"{'全アドレスを表示' if show_all else 'MorseChar と avatar/change だけ表示 (--all で全部)'}")
    print("Ctrl+C で終了\n")
    sock.settimeout(0.5)   # Windows は recvfrom 中に Ctrl+C が効かないので定期的に抜ける
    last = {}
    try:
        while True:
            try:
                data, _ = sock.recvfrom(65535)
            except socket.timeout:
                continue
            for addr, vals in parse(data):
                if not show_all and addr not in INTERESTING:
                    continue
                key = (addr, tuple(vals))
                if last.get(addr) == key:
                    continue          # 同じ値の連打は省く
                last[addr] = key
                ts = time.strftime("%H:%M:%S")
                shown = ", ".join(f"{v:.4f}" if isinstance(v, float) else repr(v) for v in vals)
                print(f"{ts}  {addr}  {shown}")
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
