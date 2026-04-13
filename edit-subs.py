import customtkinter as ctk
from tkinter import filedialog
import re
import os
from datetime import datetime, timedelta


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def shift_timestamp(ts, offset):
    t = datetime.strptime(ts, "%H:%M:%S,%f")
    base = datetime(2000, 1, 1, t.hour, t.minute, t.second, t.microsecond)
    shifted = base + offset
    return shifted.strftime("%H:%M:%S,%f")[:-3]


def process_file(input_path, output_folder, seconds):
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    offset = timedelta(seconds=seconds)
    pattern = re.compile(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})")

    def repl(match):
        return f"{shift_timestamp(match.group(1), offset)} --> {shift_timestamp(match.group(2), offset)}"

    new_content = pattern.sub(repl, content)

    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(output_folder, f"{base_name}_shifted.srt")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    return output_path


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SRT Timestamp Shifter")
        self.geometry("480x380")
        self.resizable(False, False)

        self._input_path = ctk.StringVar()
        self._output_folder = ctk.StringVar()
        self._offset = ctk.StringVar(value="0.0")

        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 16))
        header.grid_columnconfigure(1, weight=1)

        icon_frame = ctk.CTkFrame(header, width=32, height=32, corner_radius=8, fg_color="#3d8ef0")
        icon_frame.grid(row=0, column=0, padx=(0, 10))
        icon_frame.grid_propagate(False)
        ctk.CTkLabel(icon_frame, text="≡", font=ctk.CTkFont(size=16, weight="bold"), text_color="white").place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(header, text="SRT Timestamp Shifter", font=ctk.CTkFont(size=15, weight="bold"), anchor="w").grid(row=0, column=1, sticky="w")

        # Input file
        ctk.CTkLabel(self, text="INPUT FILE", font=ctk.CTkFont(size=10), text_color="gray", anchor="w").grid(row=1, column=0, sticky="w", padx=24)
        row1 = ctk.CTkFrame(self, fg_color="transparent")
        row1.grid(row=2, column=0, sticky="ew", padx=24, pady=(4, 12))
        row1.grid_columnconfigure(0, weight=1)
        ctk.CTkEntry(row1, textvariable=self._input_path, placeholder_text="No file selected…", height=36).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(row1, text="Browse", width=80, height=36, command=self._browse_file).grid(row=0, column=1)

        # Output folder
        ctk.CTkLabel(self, text="OUTPUT FOLDER", font=ctk.CTkFont(size=10), text_color="gray", anchor="w").grid(row=3, column=0, sticky="w", padx=24)
        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.grid(row=4, column=0, sticky="ew", padx=24, pady=(4, 12))
        row2.grid_columnconfigure(0, weight=1)
        ctk.CTkEntry(row2, textvariable=self._output_folder, placeholder_text="No folder selected…", height=36).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(row2, text="Browse", width=80, height=36, command=self._browse_folder).grid(row=0, column=1)

        # Offset
        ctk.CTkLabel(self, text="TIME OFFSET (seconds — negative to shift back)", font=ctk.CTkFont(size=10), text_color="gray", anchor="w").grid(row=5, column=0, sticky="w", padx=24)
        ctk.CTkEntry(self, textvariable=self._offset, width=110, height=36).grid(row=6, column=0, sticky="w", padx=24, pady=(4, 0))

        # Divider
        ctk.CTkFrame(self, height=1, fg_color=("gray80", "gray25")).grid(row=7, column=0, sticky="ew", padx=24, pady=16)

        # Bottom bar
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=8, column=0, sticky="ew", padx=24, pady=(0, 20))
        bottom.grid_columnconfigure(0, weight=1)

        self._status_label = ctk.CTkLabel(bottom, text="", font=ctk.CTkFont(size=12), text_color=("#2e7d32", "#4caf7d"), anchor="w")
        self._status_label.grid(row=0, column=0, sticky="w")

        ctk.CTkButton(bottom, text="Generate", width=110, height=36, command=self._generate).grid(row=0, column=1)

    def _browse_file(self):
        path = filedialog.askopenfilename(filetypes=[("SRT files", "*.srt")])
        if path:
            self._input_path.set(path)
            if not self._output_folder.get():
                self._output_folder.set(os.path.dirname(path))

    def _browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self._output_folder.set(folder)

    def _generate(self):
        self._status_label.configure(text="", text_color=("#2e7d32", "#4caf7d"))

        input_path = self._input_path.get().strip()
        output_folder = self._output_folder.get().strip()
        offset_str = self._offset.get().strip()

        if not input_path:
            self._set_error("Please select an .srt file.")
            return
        if not output_folder:
            self._set_error("Please select an output folder.")
            return
        try:
            seconds = float(offset_str)
        except ValueError:
            self._set_error("Offset must be a number (e.g. 31.2 or -5).")
            return

        try:
            out = process_file(input_path, output_folder, seconds)
            self._status_label.configure(text=f"Saved: {os.path.basename(out)}", text_color=("#2e7d32", "#4caf7d"))
        except Exception as e:
            self._set_error(str(e))

    def _set_error(self, msg):
        self._status_label.configure(text=msg, text_color=("#c62828", "#ef5350"))


if __name__ == "__main__":
    App().mainloop()