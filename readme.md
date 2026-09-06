# Marker
#### Geminiに命令1回目でなんかできました
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