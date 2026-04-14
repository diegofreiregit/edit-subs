@echo off
pip install -r requirements.txt

pyinstaller ^
  --onefile ^
  --windowed ^
  --name "SRT Auto Sync" ^
  --collect-all customtkinter ^
  --collect-all faster_whisper ^
  --collect-all ctranslate2 ^
  --hidden-import=tiktoken_ext.openai_public ^
  --hidden-import=tiktoken_ext ^
  --exclude-module tkinter ^
  --exclude-module matplotlib ^
  --exclude-module scipy ^
  --upx-dir "tools\upx" ^
  main.py

echo.
echo Done. Executable is in dist\SRT Auto Sync.exe
pause
