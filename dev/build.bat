pip install customtkinter pyinstaller
pyinstaller --onefile --windowed --name "SRT Timestamp Shifter" --collect-all customtkinter edit-subs.py
move dist\edit-subs.exe "SRT Timestamp Shifter.exe"