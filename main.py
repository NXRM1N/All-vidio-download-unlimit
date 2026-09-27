"""UNI DOWNLOAD - simple GUI video downloader built on yt-dlp."""
import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from yt_dlp import YoutubeDL

QUALITY_PRESETS = {
    "Лучшее качество": "bestvideo+bestaudio/best",
    "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
    "Только звук (MP3)": "bestaudio/best",
}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("UNI DOWNLOAD 1.0")
        self.geometry("640x480")
        self.minsize(560, 420)

        self.out_dir = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads"))
        self.quality = tk.StringVar(value="Лучшее качество")
        self.log_queue: "queue.Queue[str]" = queue.Queue()
        self.cancel_flag = threading.Event()
        self.worker: threading.Thread | None = None

        self._build_ui()
        self.after(150, self._drain_log_queue)

    def _build_ui(self):
        pad = {"padx": 8, "pady": 6}

        tk.Label(self, text="Ссылки на видео (по одной в строке):").pack(anchor="w", **pad)
        self.urls_box = tk.Text(self, height=8)
        self.urls_box.pack(fill="both", expand=False, padx=8)

        row = tk.Frame(self)
        row.pack(fill="x", **pad)

        tk.Label(row, text="Качество:").pack(side="left")
        quality_menu = ttk.Combobox(
            row, textvariable=self.quality, values=list(QUALITY_PRESETS.keys()), state="readonly"
        )
        quality_menu.pack(side="left", padx=8)

        tk.Label(row, text="Папка:").pack(side="left", padx=(16, 0))
        tk.Entry(row, textvariable=self.out_dir, width=28).pack(side="left", padx=8)
        tk.Button(row, text="Обзор...", command=self._pick_dir).pack(side="left")

        btn_row = tk.Frame(self)
        btn_row.pack(fill="x", **pad)
        self.start_btn = tk.Button(btn_row, text="Скачать", command=self._start_download, bg="#2e7d32", fg="white")
        self.start_btn.pack(side="left")
        self.cancel_btn = tk.Button(btn_row, text="Отмена", command=self._cancel, state="disabled")
        self.cancel_btn.pack(side="left", padx=8)

        self.progress = ttk.Progressbar(self, mode="determinate", maximum=100)
        self.progress.pack(fill="x", padx=8, pady=(0, 6))

        tk.Label(self, text="Лог:").pack(anchor="w", padx=8)
        self.log_box = tk.Text(self, height=10, state="disabled", bg="#111", fg="#0f0")
        self.log_box.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def _pick_dir(self):
        chosen = filedialog.askdirectory(initialdir=self.out_dir.get())
        if chosen:
            self.out_dir.set(chosen)

    def _log(self, message: str):
        self.log_queue.put(message)

    def _drain_log_queue(self):
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_box.configure(state="normal")
                self.log_box.insert("end", message + "\n")
                self.log_box.see("end")
                self.log_box.configure(state="disabled")
        except queue.Empty:
            pass
        self.after(150, self._drain_log_queue)

    def _start_download(self):
        urls = [line.strip() for line in self.urls_box.get("1.0", "end").splitlines() if line.strip()]
        if not urls:
            messagebox.showwarning("UNI DOWNLOAD", "Вставьте хотя бы одну ссылку.")
            return
        os.makedirs(self.out_dir.get(), exist_ok=True)

        self.cancel_flag.clear()
        self.start_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.progress["value"] = 0

        self.worker = threading.Thread(target=self._download_all, args=(urls,), daemon=True)
        self.worker.start()

    def _cancel(self):
        self.cancel_flag.set()
        self._log("Отмена запрошена, завершаю текущую загрузку...")

    def _progress_hook(self, d):
        if self.cancel_flag.is_set():
            raise KeyboardInterrupt("cancelled by user")
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            if total:
                percent = d.get("downloaded_bytes", 0) / total * 100
                self.progress["value"] = percent
        elif d["status"] == "finished":
            self.progress["value"] = 100
            self._log(f"Готово: {d.get('filename', '')}")

    def _download_all(self, urls: list[str]):
        want_audio_only = self.quality.get() == "Только звук (MP3)"
        format_spec = QUALITY_PRESETS[self.quality.get()]

        ydl_opts = {
            "format": format_spec,
            "outtmpl": os.path.join(self.out_dir.get(), "%(title)s.%(ext)s"),
            "progress_hooks": [self._progress_hook],
            "noplaylist": False,
            "quiet": True,
            "no_warnings": True,
        }
        if want_audio_only:
            ydl_opts["postprocessors"] = [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
            ]

        for url in urls:
            if self.cancel_flag.is_set():
                break
            self._log(f"Скачивание: {url}")
            try:
                with YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            except KeyboardInterrupt:
                self._log("Загрузка отменена.")
                break
            except Exception as exc:
                self._log(f"Ошибка при скачивании {url}: {exc}")

        self._log("Все задачи завершены.")
        self.start_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")


if __name__ == "__main__":
    App().mainloop()
