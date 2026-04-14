import re
import os
from datetime import datetime, timedelta


_PATTERN = re.compile(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})")


def _ts_to_seconds(ts: str) -> float:
    t = datetime.strptime(ts, "%H:%M:%S,%f")
    return t.hour * 3600 + t.minute * 60 + t.second + t.microsecond / 1_000_000


def _shift_ts(ts: str, offset: timedelta) -> str:
    t = datetime.strptime(ts, "%H:%M:%S,%f")
    base = datetime(2000, 1, 1, t.hour, t.minute, t.second, t.microsecond)
    shifted = base + offset
    # clamp to zero if offset is negative and result would be negative
    if shifted < datetime(2000, 1, 1):
        shifted = datetime(2000, 1, 1)
    return shifted.strftime("%H:%M:%S,%f")[:-3]


def get_first_subtitle_info(srt_path: str) -> tuple[float, str]:
    """Return the start time (seconds) and the text of the first subtitle entry."""
    with open(srt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        m = _PATTERN.search(line)
        if m:
            ts = _ts_to_seconds(m.group(1))
            # Extract text
            text_lines = []
            for j in range(i + 1, len(lines)):
                if not lines[j].strip():
                    break
                text_lines.append(lines[j].strip())
            return ts, " ".join(text_lines)
            
    raise ValueError("No valid timestamp found in the SRT file.")


def shift_srt(srt_path: str, output_folder: str, offset_seconds: float) -> str:
    """
    Shift all timestamps in srt_path by offset_seconds (can be negative).
    Writes to output_folder/<original>_shifted.srt and returns the output path.
    """
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()

    offset = timedelta(seconds=offset_seconds)

    def repl(match):
        return f"{_shift_ts(match.group(1), offset)} --> {_shift_ts(match.group(2), offset)}"

    new_content = _PATTERN.sub(repl, content)

    base_name = os.path.splitext(os.path.basename(srt_path))[0]
    output_path = os.path.join(output_folder, f"{base_name}_shifted.srt")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    return output_path
