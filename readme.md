# Marker
## Desktop app

The HTML UI can be run as a Windows desktop application with pywebview.
VoiceMeeter must be installed separately because it provides the virtual audio
devices used as the microphone route.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

To create the executable:

```powershell
.\.venv\Scripts\python.exe -m PyInstaller `
    --noconfirm --clean --onefile --windowed `
    --name MorseCodeSoundboard `
    --add-data "morse_code_soundboard.html;." app.py
```

The executable is created at `dist\MorseCodeSoundboard\MorseCodeSoundboard.exe`.
In the app, select the VoiceMeeter virtual input under the output device list,
then select the corresponding VoiceMeeter output as the microphone in Discord,
OBS, or another communication app.
---

## VRChat 連携（モールス送信中の文字をアバターのTV画面に出す）

モールス音声だけでは相手が解読できないので、送信中の文字を1文字ずつ
VRChat のアバターパラメータへ送り、ブラウン管TVの画面に表示する。

```
HTML(送信中の文字) -> app.py / vrc_morse_osc.py -> OSC/UDP 127.0.0.1:9000 -> VRChat
```

- `vrc_morse_osc.py` … OSC送信ブリッジ。標準ライブラリのみで動く
- `unity_assets/` … Unity へ持っていくもの（TVモデル、グリフアトラス、UV表）
- `verify_setup.py` … 全体の整合性チェック。作業前に走らせる
- `CLAUDE.md` … 設計判断と残作業をまとめた引き継ぎ書
- `UNITY_GUIDE.md` … Unity 側の作業手順（初心者向け・画面操作レベル）

### 動作確認

```powershell
.\.venv\Scripts\python.exe verify_setup.py
.\.venv\Scripts\python.exe vrc_morse_osc.py --demo HELLO WORLD
```

- C:\Users\hehua\Documents\GitHub\PythonProject1\.venv\Scripts\python.exe C:\Users\hehua\Documents\GitHub\PythonProject1\vrc_morse_osc.py --demo HELLO WORLD

`verify_setup.py` は VRChat 起動中だと 9000 番が埋まるため OSC の項目だけ
FAIL する。これは想定内。

### VRChat 側の準備

1. アバターの Expression Parameters に float `MorseChar` を追加
2. ゲーム内で Action Menu → Options → OSC → Enabled
3. パラメータを後から足した場合は同じメニューで OSC 設定をリセット

~~Unity 側の組み立て手順は `CLAUDE.md` の 8-3 を参照。~~
全体の組み立て手順は `UNITY_GUIDE.md` にまとめたのでそちらを参照。