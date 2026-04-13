from datetime import datetime, timedelta
import os
import re

# Load full file
with open('paste.txt', 'r', encoding='utf-8') as f:
    content = f.read()

offset = timedelta(seconds=31.2)

def shift_timestamp(ts):
    # ts format: HH:MM:SS,mmm
    t = datetime.strptime(ts, '%H:%M:%S,%f')
    base = datetime(2000,1,1, t.hour, t.minute, t.second, t.microsecond)
    shifted = base + offset
    return shifted.strftime('%H:%M:%S,%f')[:-3]

# Replace all timestamps
pattern = re.compile(r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})')

def repl(match):
    start = match.group(1)
    end = match.group(2)
    return f"{shift_timestamp(start)} --> {shift_timestamp(end)}"

new_content = pattern.sub(repl, content)

# Create output folder if it doesn't exist
os.makedirs('output', exist_ok=True)

# Save adjusted file
with open('output/paste_shifted.srt', 'w', encoding='utf-8') as f:
    f.write(new_content)

new_content[:4000]