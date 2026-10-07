"""Small window for building an A4 photo album without a terminal.

Pick a photo folder, press "앨범 만들기", and the same PDF as
`make_album.py` is produced. This is the entry point of the portable
앨범만들기.exe (see build_portable.ps1).

Usage:
    python scripts/album_app.py [PHOTO_DIR]
    python scripts/album_app.py --smoke-test PHOTO_DIR OUTPUT_PDF LOG_FILE   (build check)
"""

from __future__ import annotations

import os
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import make_album

TITLE = "A4 사진 앨범 만들기"


def _run(photo_dir, output):
    """Build the album; return the lines to show and the PDF path (None on failure)."""
    try:
        out, photos, pages, warnings = make_album.build_album(photo_dir, output or None)
    except make_album.AlbumError as exc:
        return [*map(str, exc.warnings), f"오류: {exc}"], None
    except Exception as exc:  # keep the window alive whatever happens
        return [f"오류: 예상하지 못한 문제가 생겼습니다: {exc}"], None
    return make_album.report_lines(out, photos, pages, warnings), out


class AlbumApp:
    def __init__(self, root, initial_folder=None):
        self.root = root
        self.busy = False
        self.last_pdf = None
        self.output_custom = False
        self._results = queue.Queue()

        root.title(TITLE)
        # Sizes are in screen pixels, so scale them with the display (tk scaling is 1.33 at 100%).
        zoom = float(root.tk.call("tk", "scaling")) / (96 / 72)
        root.minsize(int(520 * zoom), int(320 * zoom))
        root.geometry(f"{int(720 * zoom)}x{int(420 * zoom)}")
        root.protocol("WM_DELETE_WINDOW", self.on_close)

        frame = ttk.Frame(root, padding=12)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(3, weight=1)

        self.photo_dir = tk.StringVar()
        self.output = tk.StringVar()
        ttk.Label(frame, text="사진 폴더").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.photo_dir).grid(row=0, column=1, sticky="ew", padx=6)
        self.folder_button = ttk.Button(frame, text="찾아보기…", command=self.choose_folder)
        self.folder_button.grid(row=0, column=2)
        ttk.Label(frame, text="저장할 PDF").grid(row=1, column=0, sticky="w", pady=4)
        output_entry = ttk.Entry(frame, textvariable=self.output)
        output_entry.grid(row=1, column=1, sticky="ew", padx=6)
        output_entry.bind("<Key>", lambda _event: setattr(self, "output_custom", True))
        self.output_button = ttk.Button(frame, text="찾아보기…", command=self.choose_output)
        self.output_button.grid(row=1, column=2)

        buttons = ttk.Frame(frame)
        buttons.grid(row=2, column=0, columnspan=3, pady=10)
        self.build_button = ttk.Button(buttons, text="앨범 만들기", command=self.start)
        self.build_button.pack(side="left", padx=4)
        self.open_button = ttk.Button(buttons, text="PDF 열기", command=self.open_pdf, state="disabled")
        self.open_button.pack(side="left", padx=4)

        log_frame = ttk.LabelFrame(frame, text="결과", padding=4)
        log_frame.grid(row=3, column=0, columnspan=3, sticky="nsew")
        self.log = tk.Text(log_frame, height=10, wrap="word", state="disabled", font="TkDefaultFont")
        scroll = ttk.Scrollbar(log_frame, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.photo_dir.trace_add("write", self._refresh_default_output)
        if initial_folder and Path(initial_folder).is_dir():
            self.photo_dir.set(str(initial_folder))

    # --- fields ---------------------------------------------------------------

    def _refresh_default_output(self, *_):
        if self.output_custom:
            return
        folder = self.photo_dir.get().strip()
        self.output.set(str(make_album.default_output_path(folder)) if folder else "")

    def set_custom_output(self, path):
        self.output_custom = True
        self.output.set(path)

    def choose_folder(self):
        folder = filedialog.askdirectory(parent=self.root, title="사진 폴더 고르기",
                                         initialdir=self.photo_dir.get() or None)
        if folder:
            self.photo_dir.set(os.path.normpath(folder))

    def choose_output(self):
        current = Path(self.output.get()) if self.output.get() else None
        path = filedialog.asksaveasfilename(
            parent=self.root, title="저장할 PDF", defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialdir=current.parent if current else None,
            initialfile=current.name if current else "album.pdf")
        if path:
            self.set_custom_output(os.path.normpath(path))

    # --- building -------------------------------------------------------------

    def _show(self, lines):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.insert("end", "\n".join(lines))
        self.log.configure(state="disabled")

    def _set_busy(self, busy):
        self.busy = busy
        state = "disabled" if busy else "normal"
        for button in (self.build_button, self.folder_button, self.output_button):
            button.configure(state=state)
        self.build_button.configure(text="만드는 중…" if busy else "앨범 만들기")
        self.open_button.configure(state="normal" if self.last_pdf and not busy else "disabled")

    def start(self):
        folder = self.photo_dir.get().strip()
        if not folder:
            self._show(["사진 폴더를 먼저 골라 주세요."])
            return
        self.last_pdf = None
        self._set_busy(True)
        self._show(["만드는 중…"])
        output = self.output.get().strip()
        threading.Thread(target=lambda: self._results.put(_run(folder, output)), daemon=True).start()
        self.root.after(100, self._poll)

    def _poll(self):
        try:
            lines, pdf = self._results.get_nowait()
        except queue.Empty:
            self.root.after(100, self._poll)
            return
        self.last_pdf = pdf
        self._show(lines)
        self._set_busy(False)

    def open_pdf(self):
        if self.last_pdf:
            os.startfile(str(self.last_pdf))

    def on_close(self):
        if self.busy:
            messagebox.showinfo(TITLE, "앨범을 만드는 중입니다. 끝난 뒤 닫아 주세요.", parent=self.root)
            return
        self.root.destroy()


def _smoke_test(photo_dir, output, log_file):
    lines, pdf = _run(photo_dir, output)
    Path(log_file).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0 if pdf else 1


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["--smoke-test"]:
        return _smoke_test(*argv[1:4])
    if sys.platform == "win32":
        # Without this, Windows stretches the window as a bitmap on scaled
        # (125%, 150%…) displays and the Korean text looks blurry.
        try:
            import ctypes

            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass
    root = tk.Tk()
    AlbumApp(root, argv[0] if argv else None)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
