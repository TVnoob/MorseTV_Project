# Unity 作業ガイド（初心者向け・画面操作レベル）

設計の理由や落とし穴は `CLAUDE.md` に書いてある。こちらは**手を動かす手順だけ**。
上から順にやれば、VRChat にアップロードしなくても Unity 内で動作確認まで到達する。

---

## 0. Unity の画面の見方（ここが分かれば大半は解決する）

Unity の画面は 4 つの領域でできている。

| ウィンドウ | 何が表示されるか |
|---|---|
| **Hierarchy** | いまシーンに「置いてある」モノの一覧 |
| **Scene** | それを 3D で見た図 |
| **Inspector** | 選択中のモノの中身。設定はここでいじる |
| **Project** | プロジェクト内の**ファイル**一覧（`Assets` フォルダの中身） |

### 最重要: Project の `crt_tv` と Hierarchy の `crt_tv` は別物

- **Project** にある `crt_tv` … 3Dモデルの**ファイル**（設計図）
- **Hierarchy** にある `crt_tv` … それをシーンに**置いた実体**

**Animator などのコンポーネントを追加できるのは Hierarchy 側だけ。**
Project のファイルを選ぶと Inspector にはインポート設定（Model / Rig / Animation /
Materials のタブ）が出て、**`Add Component` ボタンは表示されない**。
「Animator を追加できない」という場合、まずここを疑う。

---

## 1. Hierarchy ウィンドウを出す

Hierarchy が画面に見当たらない場合:

```
メニューバー → Window → General → Hierarchy
```

ショートカットは `Ctrl + 4`。

レイアウトがぐちゃぐちゃになっているなら、まるごと戻せる:

```
メニューバー → Window → Layouts → Default
```

Hierarchy は通常、画面の左端に縦長で表示される。

---

## 2. TV がシーンに置かれているか確認する

Hierarchy に `crt_tv` があるか見る。無ければ:

1. Project ウィンドウで `crt_tv`（**立方体のアイコン**が付いている方。
   白い紙アイコンの `crt_tv` は `.mtl` ファイルなので違う）を見つける
2. それを **Hierarchy へドラッグ&ドロップ**する

Hierarchy の `crt_tv` の左にある **▶ の三角** をクリックすると中身が開き、
`TV_Body` / `TV_Screen` / `TV_Knob` / `TV_Antenna` が子として並ぶ。

> Scene ビューで TV をクリックして選択した場合、選ばれるのは子の `TV_Screen` など。
> **親の `crt_tv` を選ぶには Hierarchy でクリックするのが確実。**

---

## 3. crt_tv に Animator を追加する

1. **Hierarchy で `crt_tv`** をクリック（子ではなく、一番上の親）
2. Inspector の**一番下までスクロール**する
3. 幅の広い **`Add Component`** ボタンを押す
4. 出てきた検索欄に `animator` と打つ
5. 一覧の **`Animator`** をクリック

> **`Animation` という似た名前の項目があるが別物。** 古い仕組みなので選ばないこと。

Inspector に `Animator` の欄が増える。中身は次の通り:

- **Controller** … 空欄。次の手順で入れる
- **Avatar** … `None` のままでよい
- **Apply Root Motion** … チェックなしでよい

---

## 4. Animator Controller を作って割り当てる

1. Project ウィンドウの `Assets` の何もない所で**右クリック**
2. `Create` → `Animator Controller`
3. 名前を `MorseFX` にする（好きな名前でよい）
4. できた `MorseFX` を、**Hierarchy の `crt_tv` を選んだ状態で**
   Inspector の `Animator` → `Controller` 欄へドラッグ&ドロップ

これで「TV が Animator を持っている」状態になる。
クリップ生成スクリプトはこの Animator を目印にパスを計算するので、
**この手順を飛ばすとスクリプトはエラーで止まる。**

---

## 5. 生成スクリプトをプロジェクトに入れる

1. Project ウィンドウの `Assets` で右クリック → `Create` → `Folder`
2. フォルダ名を **`Editor`** にする（この名前でないとエディタ拡張として読まれない）
3. エクスプローラで
   `PythonProject1\unity_assets\Editor\MorseCharClipGenerator.cs` を開き、
   Unity の `Assets/Editor` フォルダへコピーする

> Unity プロジェクトのフォルダが分からない場合は、Project ウィンドウの `Assets` を
> 右クリック → `Show in Explorer` で開ける。

Unity に戻ると右下にスピナーが回り、コンパイルが走る。終わると
**メニューバーに `Tools` が増えている**。増えていなければ Console にエラーが出ているので、
その内容を伝えてほしい。

---

## 5-b. アトラス画像のインポート設定

Project で `morse_glyph_atlas` をクリックし、Inspector で:

- **Alpha Is Transparency … OFF**（ON だと文字が白い円に潰れる。理由は `CLAUDE.md` 8-3 B）
- **Generate Mip Maps … OFF**
- Wrap Mode … Clamp
- Filter Mode … Bilinear
- Compression … None か High Quality

変えたら一番下の **`Apply`** を押す。押さないと反映されない。

---

## 6. 画面のマテリアルを仕上げる

Hierarchy で `crt_tv` → `TV_Screen` を選ぶ。Inspector の下の方にマテリアルが出る。

- **Shader** … `Standard`
- **Rendering Mode** … `Opaque`
- **Albedo** … テクスチャは入れない。色だけ暗いグレー（`0F1212` でよい）
- **Emission** … チェックを入れる
- **Emission のテクスチャスロット** … `Color` と書かれた行の**左端にある小さな四角**。
  ここに `morse_glyph_atlas` をドラッグする
  （「Emission Map」という名前の項目は存在しない。ラベルは `Color`）
- **Emission の色（HDRバー）** … **白か淡い緑**。黒のままだと何も光らない
- **Global Illumination** … `Baked` から **`None`** に変える
- **Main Maps の Tiling** … `X 0.125` `Y 0.125`

Offset はアニメーションが上書きするので触らなくてよい。

---

## 7. クリップを生成する

1. Hierarchy で **`TV_Screen`** をクリック（今度は子の方）
2. メニューバー → `Tools` → `Morse` → `MorseChar クリップを生成`
3. 保存先を聞かれるので `Assets` の下に `MorseChar` として保存

Console（Project ウィンドウの隣のタブ）に結果が出る:

```
MorseChar クリップを生成しました
  保存先: Assets/MorseChar.anim
  パス: "TV_Screen"  (MeshRenderer)
  グリフ 55 個 + 末尾ダミー 1 = キー 56 個 x 2 プロパティ
  クリップ長: 0.9000 秒 (108 フレーム @ 120fps)
  8bit 量子化の検算: 全 55 グリフ OK
```

**最後の行が `全 55 グリフ OK` になっていることを必ず確認する。**
赤いエラーで「◯文字がずれる」と出たらそのクリップは使わない。

---

## 8. Animator Controller に組み込む

1. Project で `MorseFX` を**ダブルクリック** → Animator ウィンドウが開く
2. ウィンドウ左側の **`Parameters` タブ**をクリック
3. **`+`** ボタン → `Float` を選ぶ
4. 名前を **`MorseChar`** にする（`vrc_morse_osc.py` と同じ綴り。大文字小文字も一致させる）
5. 右側のグリッドの何もない所で**右クリック** → `Create State` → `Empty`
6. できた四角（オレンジ色になる）をクリック
7. Inspector の **`Motion`** 欄に、Project の `MorseChar`（アニメーションクリップ）を
   ドラッグ&ドロップ
8. Inspector の **`Motion Time` にチェックを入れる**
9. チェックの下に出るドロップダウンで **`MorseChar`** を選ぶ

トランジション（矢印）は作らなくてよい。ステートは 1 個だけでよい。

---

## 9-0. アニメーション抜きで、マテリアルだけで文字を出す（最初にやる）

クリップも Animator も関係なく、**手で Offset を打つだけ**で文字が出るかを見る。
ここが通れば表示系は正しい。通らなければ以降は全部無駄なので、必ずここから。

1. Hierarchy で `TV_Screen` を選ぶ
2. Inspector のマテリアル → Main Maps の **Offset** に直接打ち込む:

| Offset X | Offset Y | 出る文字 |
|---|---|---|
| 0.125 | 0.875 | A |
| 0.25 | 0.875 | B |
| 0.375 | 0.5 | 0（数字のゼロ） |
| 0.75 | 0.125 | @ |

3. 打った瞬間に Game / Scene ビューの画面に文字が出れば OK。終わったら `0 / 0` に戻す

> 出ない場合は Emission 側の問題。Emission の `Color` 行の左の四角に
> `morse_glyph_atlas` が入っているか、Emission の色が黒でないかを見る。

> 文字が**白い円に潰れて**見える、Offset 0/0 なのに画面の**上端だけ緑の線**が出る、
> といった場合はアトラスの `Alpha Is Transparency` が ON になっている。5-b を見直す。

---

## 9. クリップ単体で確認する（Play モードなし）

Animator や Motion Time を介さず、**クリップ単体でテレビの文字が動くか**を先に見る。
ここが通らないと Play モードで何をしても動かない。

1. Hierarchy で **`crt_tv`** をクリック
2. メニューバー → `Window` → `Animation` → **`Animation`**（`Animator` ではない方。`Ctrl+6`）
3. 開いたウィンドウの**左上のドロップダウン**で `MorseChar` を選ぶ
   - ドロップダウンに出てこない → `MorseFX` のステートに `MorseChar` が入っていない。手順 8-7 を確認
4. 左側にプロパティが 2 行出る:
   ```
   TV_Screen : Mesh Renderer.Material._MainTex_ST.z
   TV_Screen : Mesh Renderer.Material._MainTex_ST.w
   ```
5. **この 2 行の文字色を見る。**
   - **黄色** → パスが合っていない（`TV_Screen` が見つからない）。手順 7 の Console に出た
     `パス:` の値と、Hierarchy の実際の階層を見比べる。階層を変えたなら手順 7 をやり直す
   - **白** → パスは正しい。次へ
6. ウィンドウ左上の **`Preview` ボタン**を押す（赤い録画ボタンの隣）。
   押すとタイムラインの背景が青みがかる。**これを押さないと、再生ヘッドを動かしても
   何も起きない**
7. 上のタイムラインにある**白い縦線（再生ヘッド）を左右にドラッグ**する。
   同時に Inspector の `TV_Screen` マテリアルの **Offset の数値が変わるか**も見る
   （変わらない → アニメーションが届いていない。Preview が入っているか再確認）
   - 画面の文字が切り替わる → **クリップは正しい。** 問題は Play モード側なので手順 9-b へ
   - 切り替わらない → マテリアル側。手順 6 を見直す。特に
     「Emission のテクスチャスロットにアトラスが入っているか」
     「Emission の色が黒のままになっていないか」

> 再生ヘッドを動かすと `TV_Screen` のマテリアルの Offset が書き換わる。
> 確認が終わったら Animation ウィンドウを閉じ、Offset を `0 / 0` に戻しておく。

---

## 9-b. Play モードで確認する

0. マテリアルの **Tiling が 0.125 / 0.125 に戻っているか**確認する。
   **Play 中に Tiling が 0 になる**なら、古いクリップを使っている。手順 7 でクリップを
   作り直す（生成スクリプトは Tiling も同梱するよう修正済み。理由は `CLAUDE.md` 4-3）
1. **Hierarchy で `crt_tv` を選んでおく。これを忘れると何も起きない**（下の注意 0）
2. 画面上部中央の **▶（再生）ボタン**を押す
3. Animator ウィンドウの `Parameters` タブに `MorseChar` の**数値入力欄**が出る
   （スライダーではない。数値をドラッグするか直接打つ）
4. 値を **0 → 1** へ少しずつ動かす

画面の文字が切り替われば成功。刻み幅は `1 ÷ 54 ≒ 0.0185`。

| 値 | 出る文字 |
|---|---|
| 0.0000 | （空白） |
| 0.0185 | A |
| 0.0370 | B |
| 0.4815 | Z |
| 0.5000 | 0 |
| 0.6667 | 9 |
| 1.0000 | @ |

確認できたら **▶ をもう一度押して Play モードを抜ける**。

> **注意 0（いちばん多い原因）**: Animator ウィンドウは「**Hierarchy で選択中の**
> オブジェクトの Animator」を表示する。`crt_tv` を選んでいないと、Controller
> アセットのプレビューを見ているだけで、値を変えても 3D モデルには届かない。
> Play 中に `crt_tv` を選ぶと、ステートの四角の下に**青いバー**が出る。
> これが動いている印。出なければ Animator が回っていない。
>
> **注意 1**: ステートの Inspector で **`Motion Time` にチェック**が入り、その下の
> ドロップダウンが **`MorseChar`** になっているか、もう一度見る。チェックだけ入れて
> パラメータを選んでいないと動かない。
>
> **注意 2**: Play モード中に変えた設定は保存されない。これは仕様。
>
> **注意 3**: アニメーションがマテリアルを触るため、Play を抜けた後に
> `TV_Screen` のマテリアルの Offset が変な値で残ることがある。
> 気になれば `Offset X 0 / Y 0` に戻す。表示には影響しない。
>
> **注意 4**: **Play モードでは 8bit 量子化が再現されない。**
> `CLAUDE.md` 4-2 のキーずれはここでは絶対に出ない。
> そちらは手順 7 の Console の検算結果で判断すること。

---

## 9-c. Animator ウィンドウを使わずに確認する（9-b で出ないとき）

`unity_assets/MorseCharTester.cs` を使う。Animator ウィンドウの「どのオブジェクトを
見ているか」問題を丸ごと回避し、**送った値と実際にマテリアルへ届いた値を並べて表示**する。

1. `MorseCharTester.cs` を Unity の `Assets` 直下へコピー（`Editor` の中ではない）
2. Hierarchy で `crt_tv` を選び、Add Component → `MorseCharTester`
3. ▶ で Play
4. Inspector の **Index スライダー**を動かす（1 = A、54 = @）

Game ビューの左上に 3 行出る:

```
送信: MorseChar = 0.0185 -> index 1 'A'  期待 offset (0.125, 0.875)
実際: TV_Screen の _MainTex_ST  tiling (0.125, 0.125)  offset (0.125, 0.875)
Animator: normalizedTime 0.0185
```

| 見え方 | 意味 |
|---|---|
| 「設定エラー」が出る | メッセージのとおり直す（Animator が無い、Controller が空、パラメータ名が違う等） |
| 実際の offset が期待と一致し、文字も出る | 全部正常。9-b で出なかったのは Animator ウィンドウの操作の問題 |
| 実際の offset が期待と一致するのに文字が出ない | マテリアル側。tiling が (0.125, 0.125) か、Emission にアトラスが入っているか |
| 実際の offset が動かない（0, 0 のまま等） | アニメーションが届いていない。ステートの Motion にクリップが入っているか、Motion Time にチェックが入りパラメータが選ばれているか |
| normalizedTime が MorseChar と違う | Motion Time が効いていない。ステートを選び直して Motion Time を設定し直す |

確認が終わったら `MorseCharTester` は Remove Component で外す。VRChat には不要。

---

## 10. VRChat にアップロードする

経路は 2 つ。**TV そのものをアバターにする（10-A）**か、**既存の人型アバターに持たせる
（10-B）**か。どちらも 10-6 以降は共通。

**前提: VRChat アカウントの Trust Rank が New User 以上**でないとアップロードできない
（Visitor のままだと Builder タブに「Not allowed」と出る）。

---

### 10-A. TV そのものをアバターにする（人型でない Generic アバター）

今 Unity で動いている `crt_tv` にそのまま VRC Avatar Descriptor を付ける。
**Animator も Controller もクリップも今のまま使える**ので、追加作業はこれだけ:

**A-1. 大きさを決める**

原寸は幅 44cm・高さ 38cm（アンテナ込み 75cm）。そのままだと視点が床から 22cm で
歩きづらい。`crt_tv` の Transform の **Scale を X/Y/Z すべて同じ値**にして拡大する。

| Scale | 本体の高さ | 視点の高さ | 感じ |
|---|---|---|---|
| 3 | 1.1 m | 0.7 m | 子供くらい |
| 4 | 1.5 m | 0.9 m | ちょうどよい（推奨） |
| 5 | 1.9 m | 1.1 m | 大きめ |

Position は (0, 0, 0)、Rotation は (0, 0, 0) のまま。画面は +Z を向いていて、
VRChat がアバターの正面として要求する向きと一致している。

**A-2. テスト用コンポーネントを外す**

`crt_tv` の `MorseCharTester` を Remove Component。VRChat 非対応なのでビルドで弾かれる。
**`Animator` は残す**（アバターに必須。Avatar 欄は None のままでよい）。

**A-2b. Generic Avatar アセットを作って Animator に割り当てる（必須）**

Animator の Avatar 欄が `None` のままだと、**VRChat は AV3（Playable Layers と
Expression Parameters）を初期化しない**。Unity の Play では動くし、VRChat 内でも
Animator 自身の Controller は動くので気づきにくいが、OSC も Expression Parameters も
一切効かない。OBJ 由来のモデルは Rig を Generic にしても Avatar アセットが作られない
ことがあるので、スクリプトで作る。

1. `unity_assets/Editor/GenericAvatarBuilder.cs` を `Assets/Editor/` に置く
2. Hierarchy で `crt_tv` を選ぶ
3. **Tools → Morse → Generic Avatar を作って Animator に割り当て**
4. Animator の Avatar 欄に `crt_tvAvatar` が入ったことを確認し、Ctrl+S

**A-3. VRC Avatar Descriptor を付ける**

1. `crt_tv` を選び、Add Component → `avatar` と検索 → **VRC Avatar Descriptor**
   （`Pipeline Manager` も自動で付く。触らない）
2. **View Position**: 視点の位置。`Edit` ボタンを押すと Scene ビューに球が出るので、
   **画面の中央、画面より少し手前（+Z 側）**へドラッグする。数値で入れるなら、
   Scale をかける前の座標で (−0.05, 0.22, 0.25) あたり。球が画面の**表側**に出て
   いることを Scene ビューで確認する。画面の裏側だと一人称でテレビの内側が見える
3. **Lip Sync**: `Default` のまま（口が無いので何も起きない）
4. **Eye Look**: 触らない（Disabled のまま）

**A-4. Playable Layers に FX を設定**

1. Descriptor の **Playable Layers** → `Customize`
2. **FX** の欄に `MorseFX`（今 Animator に入っている Controller）をドラッグ
3. Base / Additive / Gesture / Action は Default のまま。人型でないので歩行アニメは
   効かず、テレビが滑って移動する。それでよい

**A-5. Expression Parameters**

10-4 と同じ。Project で右クリック → Create → VRChat → Avatars → Expression Parameters
を作り、`MorseChar` / Float / Default 0 / **Saved OFF** / **Synced ON** の 1 行を足して、
Descriptor の **Expressions** → `Customize` → **Parameters** の欄に入れる。

**Menu も必須。** Expressions を Customize すると SDK は Parameters と Menu の両方を
要求する（無いと Builder に `VRCExpressionsMenu object reference is missing` が出る）。
Project で右クリック → Create → VRChat → Avatars → **Expressions Menu** を作り、
**中身は空のまま** Descriptor の Expressions → **Menu** の欄に入れる。
OSC が外から書くので、メニューに項目を足す必要はない。

**A-6. そのまま Play で最終確認**

Hierarchy で `crt_tv` を選んで ▶。Animator ウィンドウの `MorseChar` を動かして文字が
出ればアバター側は完成。あとは **10-6** へ。

> **一人称の見え方**: Generic アバターは人型と違って「頭を隠す」処理が無い。
> View Position を画面の手前に置いてあるので、正面を見ている限りテレビは
> 全部カメラの後ろにあり、視界に入らない。下や後ろを向くと自分の筐体が見える。
>
> **クリップの作り直しは不要**: Animator が `crt_tv` に付いたままなので、パスは
> `TV_Screen` のまま。Scale を変えてもパスは変わらない。

---

### 10-B. 既存の人型アバターに持たせる

BOOTH 等で入手した `.unitypackage` を `Assets` → `Import Package` → `Custom Package` で
取り込み、付属の Prefab を Hierarchy に置いた状態を前提にする。

### 10-1. TV をアバターに持たせる

1. Hierarchy で `crt_tv` を、アバターの**持たせたい骨の下**にドラッグする。
   手に持たせるなら `Armature` → `Hips` → `Spine` → `Chest` → … → `Right hand`
   （骨の名前はアバターにより多少違う）。胸の前に浮かせるなら `Chest` の下
2. `crt_tv` の Transform で位置・回転・**スケール**を調整する。実寸 44cm 幅なので
   手持ちなら Scale 0.3〜0.5 程度に縮める
3. **`crt_tv` に付けた `Animator` と `MorseCharTester` を Remove Component で外す。**
   テスト用に付けたもの。アバター本体の Animator（FX レイヤー）が代わりに動かす。
   残しておくと、二重に Animator が走って挙動が変になるか、SDK に弾かれる

---

### 10-2. クリップを作り直す

階層が変わったのでパスが変わる。**必ずやり直す。**

1. Hierarchy で `TV_Screen` を選ぶ
2. Tools → Morse → MorseChar クリップを生成
3. Console の `パス:` が `Armature/Hips/.../crt_tv/TV_Screen` のようにアバタールートからの
   フルパスになっていることを確認する。`"TV_Screen"` だけなら 10-1-3 で Animator を
   外し忘れている

生成スクリプトは「一番上の Animator を持つ親」をルートにするので、アバター本体の
Animator が唯一の Animator になっていればアバタールートからのパスになる。

---

### 10-3. FX Controller にレイヤーを足す

1. アバターのルートを選び、Inspector の **VRC Avatar Descriptor** を開く
2. **Playable Layers** の `Customize` を押し、**FX** の欄を見る
   - 既に Controller が入っている → それを使う（Project でダブルクリックして開く）
   - `Default Non-Transform` や空 → Project で Create → Animator Controller を作り
     `FX` の欄に入れる。**Base や Gesture ではなく FX**。マテリアルを動かすレイヤーは FX
3. Animator ウィンドウで、その Controller の **Parameters** タブ → `+` → Float →
   `MorseChar`
4. **Layers** タブ → `+` で新しいレイヤーを作り、名前を `MorseTV` にする
5. **レイヤー名の右の歯車を押し、Weight を 1 にする。**
   新規レイヤーの Weight は 0 で始まる。0 のままだと何も起きない。ここは全員が一度は踏む
6. そのレイヤーのグリッドで右クリック → Create State → Empty
7. ステートを選び、Motion に 10-2 のクリップ、**Motion Time にチェック → `MorseChar`**
8. **Write Defaults** は、そのアバターの他のレイヤーに合わせる
   （他のレイヤーのステートを1つ選んで見る。混在させると別の表情や衣装切替が壊れる）

---

### 10-4. Expression Parameters に登録する

1. Avatar Descriptor の **Expressions** → `Customize` → **Parameters** の欄を見る
   - 既にアセットが入っている → それを Project で選ぶ
   - 空 → Project で右クリック → Create → VRChat → Avatars → Expression Parameters を作り、
     欄に入れる
2. アセットの Inspector で `Add` を押し、1 行足す:

| 欄 | 値 |
|---|---|
| Name | `MorseChar`（大文字小文字まで一致させる。Python 側の `PARAM_NAME` と同じ） |
| Type | Float |
| Default | 0 |
| Saved | **OFF** |
| Synced | **ON** |

3. 上部に残りビット数が出る。Float は 8 bit。256 bit の予算を超えていたら他を削る

**Menu も必須。** Expressions を Customize すると SDK は Parameters と Menu の両方を
要求する（無いと Builder に `VRCExpressionsMenu object reference is missing` が出る）。
Project で右クリック → Create → VRChat → Avatars → **Expressions Menu** を作り、
**中身は空のまま** Descriptor の Expressions → **Menu** の欄に入れる。
OSC が外から書くので、メニューに項目を足す必要はない。

---

### 10-5. 手元で通し確認

アップロード前に、Unity の Play モードでもう一度動かす。

1. アバターのルートを Hierarchy で選ぶ
2. ▶ で Play
3. Animator ウィンドウで FX Controller の `MorseTV` レイヤーを表示し、Parameters の
   `MorseChar` を動かす → TV に文字が出る

出ない場合は 10-3-5 の Weight が 0 のまま、または 10-2 のパスが古い。

---

### 10-6. Build & Test → Build & Publish

1. メニュー **VRChat SDK → Show Control Panel**
2. **Authentication** タブでログイン
3. **Builder** タブでアバターを選ぶ。**Review Any Alerts** に出るものの対処:

| アラート | 対処 |
|---|---|
| meshes imported with Read/Write disabled | **Auto Fix** を押す |
| Blendshape Normals set to 'Calculate' … | **Auto Fix** を押す（このモデルには実害なし） |
| VRCExpressionsMenu object reference is missing | 空の Expressions Menu を作って Descriptor の Menu 欄に入れる（10-4 / A-5） |
| not imported as a humanoid rig（黄色） | 無視してよい。Generic アバターなので想定どおり |
| 非対応コンポーネント | `MorseCharTester` の外し忘れ。Remove Component |
4. まず **Build & Test**。アップロードせずに VRChat クライアント内で自分だけ試せる。
   VRChat を起動し、Avatars メニューの **Other** タブに出る。
   **ただし Build & Test のローカルアバター（ID `local:sdk_…`）では、VRChat が
   Expression Parameters を OSC に公開しない。** 見た目・アニメーションの確認には
   使えるが、**OSC で文字を出す確認は Build & Publish 後にしかできない**。
   （バンドルを展開して MorseChar が入っていることまで確認したうえで、OSCQuery に
   現れなかった。2026-09-16 に特定。手で設定ファイルを置いても読まれない）
5. 問題なければ **Build & Publish**。名前・サムネイル・Content Warnings を入れて Upload

**OSC が効いているかは OSCQuery で直接確認できる。** VRChat のログ
（`%USERPROFILE%\AppData\LocalLow\VRChat\VRChat\output_log_*.txt`）の
`Advertising Service ... of type OSCQuery on <port>` のポート番号を使い、ブラウザで
`http://127.0.0.1:<port>/avatar/parameters` を開く。`MorseChar` が並んでいれば
VRChat はこのアバターのパラメータを受け付けている。無ければ A-2b か Publish 漏れ。

---

### 10-7. VRChat 側で OSC を有効にする

1. VRChat でそのアバターに着替える
2. **Action Menu**（デスクトップは `R` キー長押し）→ **Options** → **OSC** → **Enabled**
3. 同じ場所の **OSC → Debug** を開くと、受信中のパラメータと値がリアルタイムで見える。
   `MorseChar` が並んでいればアバター側の準備は完了

**初めてテレビを着たら、必ず `Options → OSC → Reset Config` を1回押す。**
VRChat はアバター ID ごとの OSC 設定ファイルを**最初に着たときに1回だけ**生成して
使い回す。Build & Test のローカルアバターは ID が `local:sdk_crt_tv` で固定なので、
初回ビルド時点の Expression Parameters がそのまま残り、後から足した `MorseChar` が
受け付けられない。**実際にこれで数日詰まった。** OSC Debug のタイルは届いたアドレスを
何でも表示するので、あれが光っていても受け付けている証拠にはならない。
受け付けているかは `vrc_osc_listen.py` に返ってくるかで判断する。

Reset Config で直らなければファイルを直接消す:
`%USERPROFILE%\AppData\LocalLow\VRChat\VRChat\OSC\<ユーザーID>\Avatars\local_sdk_crt_tv.json`
を削除して着替え直すと再生成される。

---

### 10-8. 送信テスト

VRChat を起動したまま、PowerShell で:

```powershell
.\.venv\Scripts\python.exe vrc_morse_osc.py --demo HELLO WORLD
```

OSC Debug の `MorseChar` が動き、TV に H, E, L, L, O … と出れば通っている。
そのあと `.\.venv\Scripts\python.exe app.py` でサウンドボードを起動し、実際に送信する。

> `verify_setup.py` は VRChat 起動中だと 9000 番が塞がっていて OSC の項目だけ FAIL する。
> これは正常。

**届いているのに画面が変わらないとき**は、VRChat が送り返す OSC を見る:

```powershell
.\.venv\Scripts\python.exe vrc_osc_listen.py
```

を別の PowerShell で走らせたまま、テレビに着替える → `/avatar/change` が出る。
続けて `--demo` を流す → `/avatar/parameters/MorseChar 0.1481 …` と返ってくれば、
VRChat は**そのアバターの** `MorseChar` を実際に書き換えている（問題は FX 側）。
返ってこなければ、着ているアバターにそのパラメータが無いか、OSC 設定が古い
（Options → OSC → Reset Config）。OSC Debug のタイルは着ていないアバター宛でも
表示されるので、あれだけでは判断できない。

---

### 10-8b. 切り分けテストの戻し忘れチェック

診断のために一時的に変えたものは、本番ビルドの前に全部戻す:

| 変えたもの | 戻す先 |
|---|---|
| `MorseChar` クリップの Loop Time | OFF |
| `New State` の Motion Time | ON、パラメータ `MorseChar` |
| `New State` の Speed | 1 |
| Expression Parameters の `MorseChar` Default | 0 |
| `TV_Screen` の Albedo | 暗色（赤にしたなら戻す） |
| `TV_Screen` の Emission テクスチャ | `morse_glyph_atlas` |
| `TV_Screen` の Tiling / Offset | 0.125 / 0.125、0 / 0 |
| `crt_tv` の `MorseCharTester` | Remove Component |

---

### 10-9. 他人から見えているか確認する（最後に必ず）

自分の画面では 8bit 量子化が効かないので、`CLAUDE.md` 4-2 のずれは自分には見えない。
クリップは対策済みだが、**フレンドに見てもらって全文字が正しく出ることを確認する**まで
完成ではない。`--demo` で `ABCDEFGHIJKLMNOPQRSTUVWXYZ` を送ると確認しやすい。

`MIN_HOLD_SEC = 0.40` は人が多いインスタンスだと足りないことがある。文字が飛ぶと
言われたら `vrc_morse_osc.py` の値を 0.5〜0.6 に上げる。
