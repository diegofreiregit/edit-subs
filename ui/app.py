import threading
import os

import customtkinter as ctk
from tkinter import filedialog

from core.audio import extract_audio_segment, get_video_duration, cleanup
from core.speech import find_first_speech
from core.srt import get_first_subtitle_info, shift_srt


def _seconds_to_hms(s: float) -> str:
    s = int(s)
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"


def _hms_to_seconds(hms: str) -> float:
    parts = hms.strip().split(":")
    if len(parts) != 3:
        raise ValueError
    h, m, s = parts
    return int(h) * 3600 + int(m) * 60 + float(s)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SRT Auto Sync")
        self.geometry("520x680")
        self.resizable(False, False)

        # Shared
        self._srt_path = ctk.StringVar()
        self._output_folder = ctk.StringVar()

        # Auto
        self._video_path = ctk.StringVar()
        self._video_duration = 0.0
        self._range_start = ctk.StringVar(value="00:00:00")
        self._range_end = ctk.StringVar(value="00:10:00")
        self._model_size = ctk.StringVar(value="tiny")
        self._min_silence = ctk.StringVar(value="500")
        self._speech_pad = ctk.StringVar(value="400")
        self._min_confidence = ctk.StringVar(value="0.7")

        # Manual
        self._manual_offset = ctk.StringVar(value="0.0")

        self.r_progress = 99  # Will be updated dynamically in _build

        self._build()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 18))
        header.grid_columnconfigure(1, weight=1)
        icon = ctk.CTkFrame(header, width=32, height=32, corner_radius=8, fg_color="#3d8ef0")
        icon.grid(row=0, column=0, padx=(0, 10))
        icon.grid_propagate(False)
        ctk.CTkLabel(icon, text="⟳", font=ctk.CTkFont(size=16, weight="bold"), text_color="white").place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(header, text="SRT Auto Sync", font=ctk.CTkFont(size=15, weight="bold"), anchor="w").grid(row=0, column=1, sticky="w")

        r = 1

        self._section_label("Select video file (for Auto Detect)", row=r); r+=1
        r1 = self._row(row=r); r+=1
        ctk.CTkEntry(r1, textvariable=self._video_path, placeholder_text="No file selected…", height=36).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(r1, text="Browse", width=80, height=36, command=self._browse_video).grid(row=0, column=1)

        self._section_label("Analysis range  (max 10 min)", row=r); r+=1
        r2 = self._row(row=r); r+=1
        ctk.CTkLabel(r2, text="From", font=ctk.CTkFont(size=12), text_color="gray").grid(row=0, column=0, padx=(0, 6))
        ctk.CTkEntry(r2, textvariable=self._range_start, width=90, height=36, justify="center").grid(row=0, column=1, padx=(0, 12))
        ctk.CTkLabel(r2, text="To", font=ctk.CTkFont(size=12), text_color="gray").grid(row=0, column=2, padx=(0, 6))
        ctk.CTkEntry(r2, textvariable=self._range_end, width=90, height=36, justify="center").grid(row=0, column=3, padx=(0, 12))
        ctk.CTkLabel(r2, text="hh:mm:ss", font=ctk.CTkFont(size=10), text_color="gray").grid(row=0, column=4, padx=(12, 0))

        self._section_label("Whisper model", row=r); r+=1
        model_row = self._row(row=r); r+=1
        for size in ("tiny", "base", "small"):
            ctk.CTkRadioButton(model_row, text=size, variable=self._model_size, value=size,
                               font=ctk.CTkFont(size=11)).pack(side="left", padx=(0, 14))

        self._section_label("VAD tuning", row=r); r+=1
        vad_row = self._row(row=r); r+=1
        ctk.CTkLabel(vad_row, text="Min silence (ms)", font=ctk.CTkFont(size=11), text_color="gray").grid(row=0, column=0, padx=(0, 6))
        ctk.CTkEntry(vad_row, textvariable=self._min_silence, width=50, height=32, justify="center").grid(row=0, column=1, padx=(0, 16))
        ctk.CTkLabel(vad_row, text="Speech pad (ms)", font=ctk.CTkFont(size=11), text_color="gray").grid(row=0, column=2, padx=(0, 6))
        ctk.CTkEntry(vad_row, textvariable=self._speech_pad, width=50, height=32, justify="center").grid(row=0, column=3, padx=(0, 16))
        ctk.CTkLabel(vad_row, text="Min confidence", font=ctk.CTkFont(size=11), text_color="gray").grid(row=0, column=4, padx=(0, 6))
        ctk.CTkEntry(vad_row, textvariable=self._min_confidence, width=50, height=32, justify="center").grid(row=0, column=5)

        # SRT + Output
        self._section_label("SRT file", row=r); r+=1
        r_srt = self._row(row=r); r+=1
        ctk.CTkEntry(r_srt, textvariable=self._srt_path, placeholder_text="No file selected…", height=36).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(r_srt, text="Browse", width=80, height=36, command=self._browse_srt).grid(row=0, column=1)

        self._section_label("Output folder", row=r); r+=1
        r_out = self._row(row=r); r+=1
        ctk.CTkEntry(r_out, textvariable=self._output_folder, placeholder_text="No folder selected…", height=36).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(r_out, text="Browse", width=80, height=36, command=self._browse_folder).grid(row=0, column=1)

        self._section_label("Time offset (seconds)", row=r); r+=1
        r_off = self._row(row=r); r+=1
        ctk.CTkEntry(r_off, textvariable=self._manual_offset, width=120, height=36, justify="center").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(r_off, text="Use negative values to shift back", font=ctk.CTkFont(size=11), text_color="gray").grid(row=0, column=1, padx=(12, 0), sticky="w")

        # Divider
        ctk.CTkFrame(self, height=1, fg_color=("gray80", "gray25")).grid(row=r, column=0, sticky="ew", padx=24, pady=16); r+=1

        # Bottom bar
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=r, column=0, sticky="ew", padx=24, pady=(0, 20))
        bottom.grid_columnconfigure(0, weight=1)
        r+=1

        self._status_label = ctk.CTkLabel(bottom, text="", font=ctk.CTkFont(size=11), anchor="w", wraplength=200)
        self._status_label.grid(row=0, column=0, sticky="w")

        self.r_progress = r
        self._progress = ctk.CTkProgressBar(self, mode="indeterminate", height=4)

        btn_frame = ctk.CTkFrame(bottom, fg_color="transparent")
        btn_frame.grid(row=0, column=1, sticky="e")

        self._detect_btn = ctk.CTkButton(btn_frame, text="Detect Offset", width=110, height=36, command=self._start_detect)
        self._detect_btn.pack(side="left", padx=(0, 8))

        self._generate_btn = ctk.CTkButton(btn_frame, text="Generate SRT", width=110, height=36, command=self._start_generate)
        self._generate_btn.pack(side="left")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _section_label(self, text, row):
        ctk.CTkLabel(self, text=text, font=ctk.CTkFont(size=10), text_color="gray", anchor="w").grid(
            row=row, column=0, sticky="w", padx=24, pady=(10, 2))

    def _row(self, row):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=row, column=0, sticky="ew", padx=24)
        frame.grid_columnconfigure(0, weight=1)
        return frame

    # ── Browsing ───────────────────────────────────────────────────────────────

    def _browse_video(self):
        path = filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4 *.mkv *.avi *.mov *.m4v *.ts *.wmv"), ("All files", "*.*")]
        )
        if not path:
            return
        self._video_path.set(path)
        self._set_status("Reading video duration…", info=True)
        threading.Thread(target=self._load_duration, args=(path,), daemon=True).start()

    def _load_duration(self, path):
        try:
            dur = get_video_duration(path)
            self._video_duration = dur
            cap = min(dur, 600.0)
            self.after(0, lambda: self._range_end.set(_seconds_to_hms(cap)))
            self.after(0, lambda: self._set_status(f"Duration: {_seconds_to_hms(dur)}", info=True))
        except Exception as e:
            msg = str(e)
            self.after(0, lambda: self._set_status(msg, error=True))

    def _browse_srt(self):
        path = filedialog.askopenfilename(filetypes=[("SRT files", "*.srt"), ("All files", "*.*")])
        if path:
            self._srt_path.set(path)

    def _browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self._output_folder.set(folder)

    # ── Validation ─────────────────────────────────────────────────────────────

    def _validate_shared(self):
        if not self._srt_path.get().strip():
            raise ValueError("Please select an SRT file.")
        if not self._output_folder.get().strip():
            raise ValueError("Please select an output folder.")

    def _validate_auto(self):
        if not self._video_path.get().strip():
            raise ValueError("Please select a video file.")

        try:
            start = _hms_to_seconds(self._range_start.get())
            end = _hms_to_seconds(self._range_end.get())
        except ValueError:
            raise ValueError("Invalid time format. Use hh:mm:ss.")

        if end <= start:
            raise ValueError("End time must be greater than start time.")
        if (end - start) > 600:
            raise ValueError("Analysis range cannot exceed 10 minutes.")
        if self._video_duration and end > self._video_duration:
            raise ValueError(f"End time exceeds video duration ({_seconds_to_hms(self._video_duration)}).")

        try:
            int(self._min_silence.get())
            int(self._speech_pad.get())
            float(self._min_confidence.get())
        except ValueError:
            raise ValueError("Invalid VAD tuning values.")

        return start, end

    def _validate_manual(self):
        try:
            return float(self._manual_offset.get().strip())
        except ValueError:
            raise ValueError("Offset must be a number (e.g. 31.2 or -5).")

    # ── Generation ─────────────────────────────────────────────────────────────

    def _start_detect(self):
        try:
            start, end = self._validate_auto()
            if not self._srt_path.get().strip():
                raise ValueError("Please select an SRT file to calculate offset.")
        except ValueError as e:
            self._set_status(str(e), error=True)
            return

        self._detect_btn.configure(state="disabled")
        self._generate_btn.configure(state="disabled")
        self._progress.grid(row=self.r_progress, column=0, sticky="ew", padx=24, pady=(0, 8))
        self._progress.start()

        threading.Thread(target=self._run_detect, args=(start, end), daemon=True).start()

    def _start_generate(self):
        try:
            self._validate_shared()
            offset = self._validate_manual()
        except ValueError as e:
            self._set_status(str(e), error=True)
            return

        self._detect_btn.configure(state="disabled")
        self._generate_btn.configure(state="disabled")
        self._progress.grid(row=self.r_progress, column=0, sticky="ew", padx=24, pady=(0, 8))
        self._progress.start()

        threading.Thread(target=self._run_generate, args=(offset,), daemon=True).start()

    def _run_detect(self, start, end):
        wav_path = None
        try:
            self._update_status("Extracting audio segment…")
            wav_path = extract_audio_segment(
                self._video_path.get().strip(), start, end
            )

            self._update_status("Detecting first speech (this may take a moment)…")
            speech_ts, speech_word = find_first_speech(
                wav_path,
                segment_start_sec=start,
                model_size=self._model_size.get(),
                min_silence_duration_ms=int(self._min_silence.get()),
                speech_pad_ms=int(self._speech_pad.get()),
                min_word_confidence=float(self._min_confidence.get()),
            )

            self._update_status("Reading SRT first timestamp…")
            srt_ts, srt_text = get_first_subtitle_info(self._srt_path.get().strip())
            
            offset = speech_ts - srt_ts
            sign = "+" if offset >= 0 else ""

            self.after(0, lambda: self._manual_offset.set(f"{offset:.3f}"))
            
            msg = (f"Detected word '{speech_word}' at {_seconds_to_hms(speech_ts)}.\n"
                   f"Suggested shift {sign}{offset:.3f}s applied to Time offset.")
            self.after(0, lambda: self._set_status(msg))

        except Exception as e:
            msg = str(e)
            self.after(0, lambda: self._set_status(msg, error=True))
        finally:
            if wav_path:
                cleanup(wav_path)
            self.after(0, self._stop_progress)

    def _run_generate(self, offset):
        try:
            out_path = shift_srt(
                self._srt_path.get().strip(),
                self._output_folder.get().strip(),
                offset,
            )

            msg = f"Done — saved {os.path.basename(out_path)}"
            self.after(0, lambda: self._set_status(msg))

        except Exception as e:
            msg = str(e)
            self.after(0, lambda: self._set_status(msg, error=True))
        finally:
            self.after(0, self._stop_progress)


    def _stop_progress(self):
        self._progress.stop()
        self._progress.grid_forget()
        self._detect_btn.configure(state="normal")
        self._generate_btn.configure(state="normal")

    # ── Status helpers ─────────────────────────────────────────────────────────

    def _update_status(self, msg: str):
        self.after(0, lambda: self._set_status(msg, info=True))

    def _set_status(self, msg: str, error=False, info=False):
        if error:
            color = ("#c62828", "#ef5350")
        elif info:
            color = ("gray40", "gray60")
        else:
            color = ("#2e7d32", "#4caf7d")
        self._status_label.configure(text=msg, text_color=color)
