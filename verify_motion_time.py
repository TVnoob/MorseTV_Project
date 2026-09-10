#!/usr/bin/env python3
"""
verify_motion_time.py - Animator の Motion Time に流したとき、
55 グリフが全部ねらい通りのキーフレームに着地するかを総当たりで確かめる。

    python verify_motion_time.py

なぜ要るか。Motion Time はパラメータ値をそのままクリップの正規化時刻として使い、
Stepped 補間は「その時刻以前で最も近いキー」を保持する。つまり実質 floor。
一方リモートに届く値は 8bit 量子化でぶれる。下振れするとキー境界を割って
1 つ前のグリフが出る。ローカルでは量子化されないので自分では気づけない。

対策はキー i をフレーム i ではなく i - 0.5 に置くこと。詳細は CLAUDE.md 4-2。
"""

import math
import sys

import vrc_morse_osc as V

SPAN = len(V.CHARSET) - 1


def quantise(p: float) -> float:
    """VRChat がリモート向けに float パラメータを 8bit へ落とす。"""
    return round(p * 255) / 255


def landed_key(index: int, key_offset: float) -> int:
    """index を送ったとき Stepped 補間が実際に拾うキー番号。

    key_offset=0.0 はキー i をフレーム i に置いた配置、
    key_offset=0.5 はキー i をフレーム i-0.5 に置いた配置。
    """
    frame = quantise(index / SPAN) * SPAN
    return min(int(math.floor(frame + key_offset + 1e-9)), SPAN)


def mismatches(key_offset: float):
    return [(i, quantise(i / SPAN) * SPAN, landed_key(i, key_offset))
            for i in range(SPAN + 1) if landed_key(i, key_offset) != i]


def worst_margin() -> float:
    """配置B で、量子化後の時刻がキー境界へどれだけ近づくか（フレーム単位）。"""
    return min(min(abs(quantise(i / SPAN) * SPAN - (i - 0.5)),
                   abs(quantise(i / SPAN) * SPAN - (i + 0.5)))
               for i in range(1, SPAN + 1))


def main() -> int:
    bad_a = mismatches(0.0)
    bad_b = mismatches(0.5)

    print(f"グリフ数 {SPAN + 1}、クリップ長 {SPAN} フレーム相当\n")

    print("配置A  キー i をフレーム i に置く（素直な作り。使ってはいけない）")
    print(f"  ずれ {len(bad_a)} / {SPAN + 1} 文字")
    for i, f, c in bad_a[:6]:
        print(f"    index {i:2} {V.CHARSET[i]!r} -> frame {f:.4f} -> "
              f"キー {c} {V.CHARSET[c]!r} が出る")
    if len(bad_a) > 6:
        print(f"    ... 他 {len(bad_a) - 6} 件")

    print("\n配置B  キー i をフレーム i-0.5 に置く（120fps なら 2i-1。これを使う）")
    print(f"  ずれ {len(bad_b)} / {SPAN + 1} 文字")
    for i, f, c in bad_b:
        print(f"    index {i:2} {V.CHARSET[i]!r} -> frame {f:.4f} -> キー {c}")
    print(f"  キー境界までの最小余裕 {worst_margin():.4f} フレーム（片側 0.5 が上限）")

    if bad_b:
        print("\n配置Bでもずれている。グリフ数を変えたなら配置を見直すこと。")
        return 1
    print("\n配置Bなら全グリフが正しいキーに着地する。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
