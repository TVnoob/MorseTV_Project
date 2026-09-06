$ErrorActionPreference = "Stop"

python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name MorseCodeSoundboard `
    --add-data "morse_code_soundboard.html;." `
    app.py

Write-Host "Created dist\MorseCodeSoundboard\MorseCodeSoundboard.exe"
