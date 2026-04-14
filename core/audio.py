import subprocess
import tempfile
import os
import re
import imageio_ffmpeg


def extract_audio_segment(video_path: str, start_sec: float, end_sec: float) -> str:
    """
    Extract a mono 16kHz WAV segment from a video file using ffmpeg.
    Returns the path to a temporary WAV file.
    Raises RuntimeError if ffmpeg is not found or extraction fails.
    """
    duration = end_sec - start_sec
    if duration <= 0:
        raise ValueError("End time must be greater than start time.")
    if duration > 600:
        raise ValueError("Segment duration cannot exceed 10 minutes (600 seconds).")

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.close()

    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
    
    cmd = [
        ffmpeg_path, "-y",
        "-ss", str(start_sec),
        "-i", video_path,
        "-t", str(duration),
        "-vn",                  # no video
        "-ac", "1",             # mono
        "-ar", "16000",         # 16kHz — optimal for Whisper
        "-f", "wav",
        tmp.name,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg error:\n{result.stderr.strip()}")

    return tmp.name


def get_video_duration(video_path: str) -> float:
    """
    Returns video duration in seconds using ffmpeg.
    """
    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
    
    cmd = [ffmpeg_path, "-i", video_path]
    # ffmpeg normally exits with code 1 when no output file is specified, so we don't check returncode.
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", result.stderr)
    if not match:
        if "No such file" in result.stderr:
            raise FileNotFoundError(f"Video file not found: {video_path}")
        raise RuntimeError(f"Could not parse video duration.\n{result.stderr[:200]}")
        
    h, m, s = match.groups()
    return int(h) * 3600 + int(m) * 60 + float(s)




def cleanup(path: str):
    try:
        os.unlink(path)
    except OSError:
        pass
