# 🎲 Subtitle Sync Editor for Windows - CustomTkinter App
A simple `.srt` editor for subtitle-audio synchronization.

<img src="images/app_image.png" alt="Sales Per Country" width="760">

## 🪪 Project Overview
This project implements a simple tool used to import `.srt` files and adjust every subtitle timestamp inside the file to a specified amount of seconds. Using `ffmpeg` and `faster-whisper`, we are able to detect the first word inside the video file and adjust the timestamps accordingly.

## 📄 How to use
If you want, there is a portable version of this app ready to download in this repository at `portable/`. Just download it and place it in whanever directory you prefer to start using it. This building process was made using the `pyinstaller` package.
- SRT No Auto Sync - Simpler version just for `.srt` edition (Code can be found on latest commit).

If you want the SRT Auto Sync version, you can execute it by running `python main.py`. To build your own portable, run `build.bat`.

### 💻 Workflow

**Optional - SRT Auto Sync version:** Select the video and detect the first word that it was said.
1. Select the video file
2. Adjust the analysis window (only 10 minutes allowed)
3. Select the whisper model
4. Adjust the VAD parameters
    Min silence (ms): This controls how long of a pause (in milliseconds) the system needs to hear before it splits the audio into separate sections.
    Speech pad (ms): This controls how much extra audio (in milliseconds) should be included after a detected speech segment ends.
    Min confidence: This sets the minimum confidence score (from 0 to 1) required for a transcribed segment to be considered valid.
5. Click on "Detect Offset"

**Main Workflow:**
1. Import the `.srt` file
2. Specify the output folder location
3. Click on  SRT for the new file
After the new file was generated, import it using your favorite video player.

You can make your own build by running the bat located at `build.bat` after you done changing your preferences. Once the building process is done, you can safely delete `build/`, `dist/` (after you take the `.exe` file generated inside it) and the `.spec` file. These all are temporary files used in the build process.

## 📁 Project Structure
```text
edit-subs/
├── core/
│   ├── __init__.py
│   ├── audio.py  <-- Logic for audio extraction
│   ├── speech.py <-- Whisper speech detection
│   └── srt.py    <-- SRT manipulation
├── images/
│   └── app_image.png
├── portable/
│   └── SRT No Auto Sync.exe
├── tools/
│   └── upx/      <-- Binary compression tool for the build process
├── ui/
│   ├── __init__.py
│   └── app.py    <-- CustomTkinter interface
├── build.bat
├── main.py
├── README.md
└── requirements.txt
```
## 🛠️ Tools Used
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- [faster-whisper](https://github.com/guillaumekln/faster-whisper)
- [ctranslate2](https://github.com/guillaumekln/ctranslate2)
- [ffmpeg](https://ffmpeg.org/)
- [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg)
- [UPX](https://upx.github.io/)
---
*Developed by [Diego Freire](https://github.com/diegofreiregit)*