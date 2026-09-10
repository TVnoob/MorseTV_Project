# VRChat モールス信号 ブラウン管TV プロジェクト

このファイルは別セッションからの引き継ぎ書です。作業を始める前に全体を読んでください。
特に「確定済みの設計判断」は理由付きで結論が出ている項目です。蒸し返さないでください。

---

## 1. 何を作っているか

VRChat 上でモールス信号を音声送信しつつ、アバターが持つブラウン管テレビの画面に
**変換前の文字を1文字ずつ表示する**仕組み。

モールス音声だけでは相手が解読できず意思疎通にならない、というのが出発点。
画面に文字が出れば、モールスが読めない相手にも伝わる。

### データフロー

```
[HTML サウンドボード]  送信中の文字がハイライトされる
        |  sendCurrentChar(index)   ハイライトの変化を検知
        v
[JS: sendToVRChat(ch)]  pywebview / Eel / fetch を自動判別
        |
        v
[Python: vrc_morse_osc.py]  文字 -> グリフindex -> float
        |  UDP 127.0.0.1:9000  /avatar/parameters/MorseChar
        v
[VRChat]  アバターの float パラメータ
        |  Animator の Motion Time
        v
[TV画面のマテリアル]  _MainTex_ST をずらしてアトラスから1文字表示
```

---

## 2. 成果物一覧

| ファイル | 中身 | 状態 |
|---|---|---|
| `app.py` | pywebview ランチャ。**OSCブリッジ組み込み済み** | 完成・ループバック検証済み |
| `morse_code_soundboard.html` | OSC送信フックを追加済みのUI本体 | 完成・未実機テスト |
| `vrc_morse_osc.py` | OSC送信ブリッジ。標準ライブラリのみ | 完成・ループバック検証済み |
| `verify_setup.py` | 全体の整合性を一括チェック | 全9項目 PASS |
| `unity_assets/crt_tv.obj` / `.mtl` | ブラウン管TVの3Dモデル | 完成・目視検証済み |
| `unity_assets/crt_tv_generator.py` | 上記の生成スクリプト。寸法変更用 | 完成 |
| `unity_assets/crt_tv_preview.png` | レンダープレビュー | 参考用 |
| `unity_assets/morse_glyph_atlas.png` | 8x8 グリフアトラス 512x512 | 完成 |
| `unity_assets/glyph_uv_table.json` | 全文字のUVオフセットとパラメータ値 | 完成 |

`importSource/` は引き継ぎ元の素材置き場で、`.gitignore` 済み。
上記はそこからリポジトリ本体へ配置し直したもの。**編集するのは本体側**。

**最初にやること: `python verify_setup.py` を実行して全項目 PASS を確認する。**

---

## 3. 確定済みの設計判断（理由付き。再検討不要）

### 3-1. 1文字ずつ表示する。文字列は送らない

VRChat のアバターパラメータは float / int / bool のみで、任意の文字列を
外部から送る経路がない。文字列を送ろうとするとテキストバッファ・折り返し・
スクロールが全部 Animator 側の負担になる。

1文字だけなら「今どのグリフか」という状態が1個あるだけで済む。
HTML 側は既に送信中の文字を知っているので、実質インデックスを投げるだけ。

### 3-2. ハイライトのDOM監視はしない

`processPlaybackQueue` の中に `currentItem.index` が既にある。DOMを読む必要はない。
`highlightNode()` の直後に1行足すだけでフックできる。

### 3-3. float パラメータ + Motion Time 方式

int で「値ごとに別ステート」をやると 55 ステート並んで管理不能になる。
代わりに:

- float パラメータ `MorseChar` を 1 個だけ用意
- 55 フレームのアニメーションクリップを 1 本作る。各フレームで
  `_MainTex_ST` の z/w（UVオフセット）を該当グリフの位置に設定
- **全キーフレームを Stepped（定数補間）にする**
- ステートの Motion Time に `MorseChar` を接続

Stepped にしないと隣のグリフと補間されて中間フレームで壊れた表示になる。ここは必須。

### 3-4. 送信値は `index / 54`

グリフ 55 個なので分母は `len(CHARSET) - 1 = 54`。

### 3-5. 最低保持時間 0.40 秒（Python側）

**VRChat のパラメータ同期はイベントではなく状態のスナップショット。**
ある値が短時間しか保持されないと、他人のクライアントではその文字が丸ごと飛ぶ。
人が多いインスタンスでは帯域制限でさらに間隔が開く。

`vrc_morse_osc.py` のワーカースレッドが各文字を最低 `MIN_HOLD_SEC = 0.40` 秒保持する。
音声が速いと表示が遅れていくので、キューが 6 件を超えたら stderr に警告が出る。
警告が出るなら WPM を下げる。目安として 15 WPM 以下なら問題ない。

### 3-6. ブラウザから直接 UDP は送れない

VRChat の OSC は UDP。JS の fetch / WebSocket では届かない。
今回は exe が Python ラッパーなので Python 側で UDP を送る。中継プロセスは不要。

---

## 4. 検証済みの事項（再確認不要だが、壊したら気づけるように）

- **OSC パケット形式**: ダミー受信サーバを 9000 番に立てて実送信し、アドレス・
  4バイトアライメント・float デコードすべて正常を確認。
- **8bit 同期の耐性**: VRChat はリモート向けに float を 8bit へ量子化する。
  55 グリフだと 1 ステップ 0.0185 に対し分解能 0.0039。
  全 55 インデックスが量子化を通しても正しく復元されることを総当たりで確認済み。
  余裕は約 4.7 倍あるので記号を数個足しても安全。
  **ただしこれは丸め（round）で復元した場合の話。** Motion Time + Stepped は
  切り捨てで効くので、キーフレームの置き方を間違えると壊れる。**5-2 を必ず読むこと。**
- **HTML パッチ**: 変更 4 箇所すべてが適用されていることを文字列検査で確認。
- **3Dモデル**: 前面・背面・斜めからレンダリングして形状破綻がないことを目視確認。
  ベゼル内壁の法線反転バグを1件修正済み。

---

## 4-2. Motion Time のキーフレーム配置（重大。ここを外すと他人にだけ壊れて見える）

**キー i をフレーム i に置いてはいけない。フレーム i - 0.5 に置くこと。**

理由。Motion Time はパラメータ値をそのままクリップの正規化時刻として使う。
Stepped 補間は「その時刻以前で最も近いキー」を保持するので、実質 floor で効く。
一方リモートに届く値は 8bit 量子化で ±0.002 ぶれる。**下振れするとキー境界を割り、
1つ前のグリフが表示される。**

素直にキー i をフレーム i へ置いた場合を総当たりした結果:

```
配置A（キー i = フレーム i）        55 文字中 26 文字がずれる
  index  2 'B' -> frame 1.9059 -> キー 1 'A' が出る
  index  3 'C' -> frame 2.9647 -> キー 2 'B' が出る
  ...
配置B（キー i = フレーム i - 0.5）  ずれ 0 件。境界まで最小 0.39 フレームの余裕
```

半フレームずらすと、量子化後の時刻がキー区間の**中央**に落ちる。
余裕は片側 0.5 フレームに対し誤差 0.106 フレームで約 4.7 倍。

**さらに厄介なのは、ローカル（自分の画面）では量子化が効かないので正常に見えること。**
自分でテストしても気づけない。他人に見てもらうか、最初から配置Bで作るしかない。

実装上の注意:

- Unity のアニメーションウィンドウは整数フレームにスナップするので、
  **クリップの fps を 120 にして キー i をフレーム `2i - 1` に置く**（i=0 はフレーム0）。
  60fps 換算で i - 0.5 になる。
- クリップ長は 60fps 換算で 54 フレーム（120fps なら 108）。最後のキーは 107 なので、
  **フレーム 108 に index 54 と同じ値のダミーキーを 1 個足して長さを確定させる。**
  これがないと `MorseChar = 1.0`（`@`）が下振れした時に 1 つ前へ落ちる。

検算コードは `verify_motion_time.py` にしてある。グリフを増減したら走らせ直すこと。

## 5. 3Dモデルの仕様

- 寸法 幅 0.44 x 高さ 0.38 x **奥行き 0.46** メートル（Unity 原寸のまま使える）
- 原点は接地面の中央。背面はブラウン管のファンネル形状に絞り込み
- 566 トライアングル
- マテリアル 4 グループ:
  - `TV_Screen` … 画面。**UV が 0〜1 でフル展開済み。ここにアトラスを貼る**
  - `TV_Body` … 筐体・ベゼル・脚
  - `TV_Knob` … つまみ 3 個
  - `TV_Antenna` … 兎耳アンテナ。不要ならこのグループごと削除可
- 画面は中央がわずかに膨らんだ曲面。法線計算済みで滑らかに見える
- 寸法変更は `crt_tv_generator.py` 冒頭の `W, H, D` / `SX0,SX1,SY0,SY1` / `BULGE` を編集して再実行

---

## 6. グリフアトラスの仕様

- `morse_glyph_atlas.png` 512x512、8列x8行、1セル 64px、白文字・透過
- 文字順（`vrc_morse_osc.py` の `CHARSET` と完全一致させること）:

```
 ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,?'!/()&:;=+-_"$@
```

- **index 0 は空白。** 単語区切りで画面が消えるので、読む側が単語の切れ目を認識できる
- 行 0 が画像の上端。Unity の UV 原点は左下なので
  `offset = (col/8, 1 - (row+1)/8)`、`tiling = (1/8, 1/8)`
- 全文字の数値は `glyph_uv_table.json` に入っている

**CHARSET とアトラスのセル順は必ず一致させること。**
片方だけ変えると全文字がずれる。`verify_setup.py` がこの整合性を検査する。

---

## 7. HTML への変更内容（元ファイルとの差分）

音声処理には一切触れていない。追加は以下だけ。

1. `MORSE_CODE_MAP` の直後に OSC ブリッジブロックを挿入
   （`REVERSE_MORSE`、`txItems`、`lastSentIndex`、`sendToVRChat`、`sendCurrentChar`）
2. `startTransmission` 内、`processPlaybackQueue` 呼び出しの直前に
   `txItems = items;` と `lastSentIndex = -1;`
3. `processPlaybackQueue` 内の `highlightNode(currentItem.index);` の直後に
   `sendCurrentChar(currentItem.index);`
4. `stopTransmission` 内に `sendCurrentChar(-1);`（送信終了で画面を消す）
5. DIRECT MORSE モードの `char: ''` を `REVERSE_MORSE[code]` で解決

`sendCurrentChar` はインデックスが変化した時だけ発火する。
同じ文字の中のドット・ダッシュでは呼ばれない。

なお文字間ギャップにもその文字の index が入ったままなので、
文字の切り替わりは次の文字の音が鳴り始める瞬間になる。余韻が自動的に付く。

---

## 8. 未解決 / 次にやること

### 8-1. Python ラッパーの特定と組み込み（解決済み）

ラッパーは **pywebview** だった（`requirements.txt` に `pywebview>=5.4,<6`、
`app.py` が `webview.create_window()` を呼んでいる）。`app.py` への組み込みは完了:

- `js_api=vrc_morse_osc.Api()` を `create_window()` に渡した（本経路）
- ローカルHTTPサーバ側に `/vrc_send` を実装した（保険の経路）
- 終了時に `vrc_morse_osc.clear()` を呼ぶようにした

**なぜ経路が2本あるか。** `app.py` はHTMLをファイル直読みではなく
`http://127.0.0.1:<ポート>/` 経由で配信している。`window.pywebview.api` は
ページ読み込みの後から注入されるので、注入前に送信を始めると1文字目を落とす。
その場合HTMLは `fetch('/vrc_send?c=...')` へフォールバックする作りになっており、
同じHTTPサーバがそれを受けて同じ `push_char()` に流す。どちらから来ても結果は同じ。

### 8-2. 実機テスト（次にやること・ユーザー担当）

1. VRChat 側で OSC を有効化（Action Menu → Options → OSC → Enabled）
   パラメータを後から追加した場合は同じメニューから OSC 設定をリセット
2. `.\.venv\Scripts\python.exe verify_setup.py` で全項目 PASS を確認
   （VRChat 起動中は 9000 番が埋まって OSC 項目だけ FAIL する。これは正常）
3. `.\.venv\Scripts\python.exe vrc_morse_osc.py --demo HELLO WORLD` で単体送信テスト
4. `.\.venv\Scripts\python.exe app.py` でアプリを起動し、実際に送信して画面を見る
5. 問題なければ `.uild_exe.ps1` で exe を作り直す

`vrc_morse_osc.py` は `app.py` が明示的に import しているので
PyInstaller が自動で同梱する。`.spec` に足すものはない。
`unity_assets/` は Unity 側でだけ使うので exe には不要。

### 8-3. Unity 側の作業（ユーザーが手作業で行う）

**A. TVモデルの取り込み**

1. `unity_assets/crt_tv.obj` と `crt_tv.mtl` を同じフォルダへドラッグ
2. インポート設定は Scale Factor 1（メートル原寸で作ってある）、Normals は Import
   （法線は生成済み。Calculate にすると画面の曲面が硬くなる）
3. Materials タブ → Extract Materials で `TV_Body` / `TV_Screen` / `TV_Knob` /
   `TV_Antenna` を取り出す
4. アバターの子に置く。原点は接地面の中央。手に持たせるなら縮小する
5. アンテナが要らなければ `TV_Antenna` のメッシュごと削ってよい

**B. グリフアトラスのインポート設定**

`unity_assets/morse_glyph_atlas.png` を入れて、

- Alpha Is Transparency … ON
- Wrap Mode … Clamp
- Filter Mode … Bilinear
- **Generate Mip Maps … OFF**（遠くで隣のセルが混ざって別の文字が滲む）
- Compression … None か High Quality（既定の圧縮だと細い線が潰れる）

**C. 画面のマテリアル（落とし穴あり）**

アトラスは**透過の白文字**。Unlit/Transparent にそのまま貼ると文字以外が透けて
筐体の内側が見えてしまう。Emission に載せるのが正解:

- `TV_Screen` のシェーダーは Standard
- Albedo … テクスチャなしの暗い色（`crt_tv.mtl` の Kd 0.06, 0.07, 0.07 が目安）
- Emission … ON、Emission Map にアトラス、色は白〜淡い緑
- **Tiling を (0.125, 0.125)**。Offset はアニメーションが上書きするので何でもよい

Standard の Emission Map は `_MainTex_ST` の UV に従う。だから Albedo に
テクスチャを入れさえしなければ、`_MainTex_ST.z/w` を動かすと文字だけがずれる。
Poiyomi などに差し替えると動かすプロパティ名が変わる（`_EmissionMap_ST` など）。
まず Standard で通してから置き換えること。

**D. Expression Parameters**

float `MorseChar` を追加。Synced ON、Default 0、**Saved は OFF**
（次回ログイン時に前回の文字が復元されると気味が悪い）。コストは 8 bit。

**E. アニメーションクリップ（ここが本体）**

- 動かすのは `TV_Screen` を持つ Renderer の
  `material._MainTex_ST.z`（= offset.x）と `material._MainTex_ST.w`（= offset.y）
- 値は `unity_assets/glyph_uv_table.json` の `offset` をそのまま使う
- **全キーを Stepped**（キーを右クリック → Both Tangents → Constant）
- **キーの時刻は 4-2 の配置B。クリップを 120fps にして、キー i をフレーム `2i - 1`
  に置く（i=0 だけフレーム 0）。さらにフレーム 108 に index 54 と同じ値の
  ダミーキーを 1 個足してクリップ長を確定させる**
- 合計 56 キー x 2 プロパティ = 112 キー。手打ちは現実的でないので `.anim` の生成を推奨

**F. Animator（FX レイヤー）**

1. Parameters に float `MorseChar` を追加
2. 新規レイヤーを作り Weight を 1 にする
3. ステートを 1 つだけ置き、Motion に E のクリップを入れる
4. **ステートの Motion Time にチェックを入れ、`MorseChar` を選ぶ**
5. トランジションは不要。Write Defaults はアバター内の他レイヤーと揃える

**G. アップロード後**

Action Menu → Options → OSC → Enabled。パラメータを後から足した場合は
同じメニューから OSC 設定をリセットする。あとは `app.py` を起動して送信するだけ。

**H. 動作確認のしかた**

**ローカルでは 8bit 量子化が効かないので、4-2 のキーずれは自分では絶対に見えない。**
Animator ウィンドウで `MorseChar` を手動で 0.0185 刻みに動かして全文字を目視するか、
他人に見てもらうこと。

### 8-4. 検討したが保留にしている案

**直近3文字を横に並べる構成。** 1文字表示だと一瞬見逃すとその文字を失う。
`MorseChar0/1/2` の 3 パラメータ（8bit x 3 = 24bit、予算的に誤差）で、
Animator のロジックは 1 文字版が 3 セット並ぶだけ。改行処理も不要のまま。
画面を 3 セルに分けたモデルが別途必要になる。ユーザーが希望したら着手。

### 8-5. リポジトリ衛生（未対応・ユーザー判断待ち）

`dist/` `build/` `__pycache__/` がビルド生成物ごと git にコミットされている
（追跡ファイル 212 個）。exe を作り直すたびに巨大な差分が出る。
`.gitignore` に足して `git rm -r --cached` するのが定石だが、
履歴に触れる操作なので手を付けていない。

## 9. 相手に対する接し方

ユーザーは自分で設計を組み立てられる人。実際、
「ハイライト位置を検知して1文字ずつ送る」という核心のアイデアはユーザー発案で、
これが折り返し処理を丸ごと不要にしている。

説明を省略する必要はないが、当たり前のことを長々と書く必要もない。
落とし穴（同期の欠落、Stepped 補間、UDP 制約など）は先回りして伝えると喜ばれる。
