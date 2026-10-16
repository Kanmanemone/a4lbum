"""Small window for building an A4 photo album without a terminal.

Pick a photo folder, arrange the photo order in the list (sort by name,
created or modified date, or move photos one by one), and press "앨범 만들기"
to get the same kind of PDF as `make_album.py`, in the listed order. A
checkbox decides whether a leading "숫자_" is dropped from the captions. This
is the entry point of the portable "앨범 만들기 (한국어).exe" and
"Photo Album Maker (English).exe" (see build_portable.ps1): the two are the
same program, and an exe name containing "(English)" switches it to English.

Usage:
    python scripts/album_app.py [--english] [PHOTO_DIR]
    python scripts/album_app.py [--english] --smoke-test PHOTO_DIR OUTPUT_PDF LOG_FILE   (build check)
"""

from __future__ import annotations

import os
import queue
import sys
import threading
import tkinter as tk
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import make_album
from make_album import tr

SORT_KEYS = ("name", "created", "modified", "taken")
CUSTOM = "custom"  # after the user moves a photo by hand; not selectable
# Marks a 촬영한 날짜 that is really the modified date (no EXIF). Plain U+26A0:
# Tk draws no color emoji, and the U+FE0F variant may show as a box.
NO_TAKEN_MARK = "⚠"
MOVES = ("up", "down", "top", "bottom")


def is_english_exe(executable):
    """True for the English copy of the exe, e.g. "Photo Album Maker (English).exe"."""
    return "(english)" in Path(executable).stem.casefold()


def title():
    """Window title: the exe name without ".exe" (build_portable.ps1 uses the same names)."""
    return tr("앨범 만들기 (한국어)", "Photo Album Maker (English)")


def sort_label(key):
    """Text shown in the sort box for a sort key (or CUSTOM)."""
    return {"name": tr("이름 순 정렬", "By name"),
            "created": tr("만든 날짜 순 정렬", "By date created"),
            "modified": tr("수정한 날짜 순 정렬", "By date modified"),
            "taken": tr("촬영한 날짜 순 정렬", "By date taken"),
            CUSTOM: tr("커스텀", "Custom")}[key]


def move_label(where):
    return {"up": "▲", "down": "▼", "top": tr("맨 위로", "To top"),
            "bottom": tr("맨 아래로", "To bottom")}[where]


def strip_number_help():
    """Hover text of the "숫자_" checkbox (the README leaves this to the window)."""
    return tr("체크하면 파일 이름 맨 앞의 \"숫자_\"를 빼고 메모 라벨에 넣습니다.\n"
              "\n"
              "  283_벚꽃 축제 모습.jpg  →  벚꽃 축제 모습\n"
              "  3_엄마_아빠.jpg  →  엄마_아빠  (맨 앞 \"숫자_\"만 뺌)\n"
              "  2026여행.jpg  →  2026여행  (숫자 뒤에 \"_\"가 없으면 그대로)\n"
              "\n"
              "체크하지 않으면 확장자만 뺀 파일 이름이 그대로 들어갑니다.",
              "When ticked, a leading \"number_\" is removed from the file name in the note label.\n"
              "\n"
              "  283_Cherry blossoms.jpg  →  Cherry blossoms\n"
              "  3_Mom_and_Dad.jpg  →  Mom_and_Dad  (only the leading \"number_\")\n"
              "  2026trip.jpg  →  2026trip  (unchanged without \"_\" after the number)\n"
              "\n"
              "When not ticked, the label is the file name without its extension.")


class Tooltip:
    """A small window with help text, shown at once while the pointer is on a widget."""

    def __init__(self, widget, text):
        self.widget, self.text = widget, text
        self.window = None
        widget.bind("<Enter>", self.show, add="+")
        widget.bind("<Leave>", self.hide, add="+")
        widget.bind("<ButtonPress>", self.hide, add="+")

    def show(self, _event=None):
        if self.window is not None:
            return
        self.window = tk.Toplevel(self.widget)
        self.window.wm_overrideredirect(True)
        x = self.widget.winfo_rootx() + 16
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.window.wm_geometry(f"+{x}+{y}")
        tk.Label(self.window, text=self.text, justify="left", background="#FFFFE1", relief="solid",
                 borderwidth=1, padx=8, pady=6).pack()

    def hide(self, _event=None):
        if self.window is not None:
            self.window.destroy()
            self.window = None


def sort_photos(photos, mode, reverse):
    """Photos (make_album.PhotoFile) in the order of a sort key; date ties go by name.

    Photos without an EXIF shooting time use their modified date for "taken".
    """
    if mode == "created":
        key = lambda p: (p.created, make_album.natural_key(p.name))
    elif mode == "modified":
        key = lambda p: (p.modified, make_album.natural_key(p.name))
    elif mode == "taken":
        key = lambda p: (p.modified if p.taken is None else p.taken, make_album.natural_key(p.name))
    else:
        key = lambda p: make_album.natural_key(p.name)
    result = sorted(photos, key=key)
    if reverse:
        result.reverse()
    return result


def _format_date(timestamp):
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def _run(photo_dir, output, order=None, strip_number=True):
    """Build the album; return the lines to show and the PDF path (None on failure)."""
    try:
        out, photos, pages, warnings = make_album.build_album(
            photo_dir, output or None, order=order, strip_number=strip_number)
    except make_album.AlbumError as exc:
        return [*map(str, exc.warnings), tr(f"오류: {exc}", f"Error: {exc}")], None
    except Exception as exc:  # keep the window alive whatever happens
        return [tr(f"오류: 예상하지 못한 문제가 생겼습니다: {exc}",
                   f"Error: something unexpected went wrong: {exc}")], None
    return make_album.report_lines(out, photos, pages, warnings), out


class PhotoList(ttk.Frame):
    """Scrollable list of file names; every row has ▲ ▼ 맨 위로 맨 아래로 buttons.

    Rows are positional: row i always shows the i-th photo, so reordering only
    rewrites label texts and rows are created or destroyed only when the count changes.
    """

    def __init__(self, parent, on_move):
        super().__init__(parent)
        self.on_move = on_move
        self.rows = []
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0, height=1)
        scroll = ttk.Scrollbar(self, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner = ttk.Frame(self.canvas)
        self.inner.columnconfigure(0, weight=1)
        window = self.canvas.create_window(0, 0, window=self.inner, anchor="nw")
        self.inner.bind("<Configure>",
                        lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(window, width=e.width))
        self.empty = ttk.Label(self.inner, text=tr("사진이 없습니다.", "No photos."))
        # The wheel scrolls the list only while the pointer is over it.
        self.bind("<Enter>", lambda _e: self.bind_all("<MouseWheel>", self._on_wheel))
        self.bind("<Leave>", lambda _e: self.unbind_all("<MouseWheel>"))

    def _on_wheel(self, event):
        if self.canvas.yview() != (0.0, 1.0):
            self.canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")

    def _add_row(self):
        index = len(self.rows)
        label = ttk.Label(self.inner, anchor="w")
        label.grid(row=index, column=0, sticky="ew")
        date = ttk.Label(self.inner, anchor="e")
        date.grid(row=index, column=1, sticky="e", padx=(0, 12))
        # Width only for the one-symbol buttons; Korean words size themselves.
        buttons = [ttk.Button(self.inner, text=move_label(where), width=3 if where in ("up", "down") else None,
                              command=lambda w=where: self.on_move(index, w)) for where in MOVES]
        for column, button in enumerate(buttons, 2):
            # A small gap separates the one-step ▲ ▼ from 맨 위로/맨 아래로.
            button.grid(row=index, column=column, padx=(8, 0) if column == 4 else 0)
        self.rows.append((label, date, buttons))

    def show(self, names, dates, folder_chosen):
        """names and dates (text shown after the name, may be "") in list order."""
        while len(self.rows) < len(names):
            self._add_row()
        while len(self.rows) > len(names):
            label, date, buttons = self.rows.pop()
            for widget in (label, date, *buttons):
                widget.destroy()
        for i, ((label, date, _), name, text) in enumerate(zip(self.rows, names, dates), 1):
            label.configure(text=f"{i:>3}   {name}")
            date.configure(text=text)
        if names or not folder_chosen:
            self.empty.grid_forget()
        else:
            self.empty.grid(row=0, column=0, sticky="w")

    def labels(self):
        return [label.cget("text") for label, _, _ in self.rows]

    def dates(self):
        return [date.cget("text") for _, date, _ in self.rows]


class AlbumApp:
    def __init__(self, root, initial_folder=None):
        self.root = root
        self.busy = False
        self.last_pdf = None
        self.output_custom = False
        self.photos = []  # make_album.PhotoFile, in album order
        self.taken_read = False  # EXIF shooting times read for this folder (see _read_taken)
        self.dated_by = "name"  # sort key whose date the list shows
        self._results = queue.Queue()

        root.title(title())
        # Sizes are in screen pixels, so scale them with the display (tk scaling is 1.33 at 100%).
        zoom = float(root.tk.call("tk", "scaling")) / (96 / 72)
        # Keep the window on screen at 150%+ display scaling.
        fit = int(root.winfo_screenheight() * 0.75)
        root.minsize(int(560 * zoom), min(int(520 * zoom), fit))
        root.geometry(f"{int(760 * zoom)}x{min(int(680 * zoom), fit)}")
        root.protocol("WM_DELETE_WINDOW", self.on_close)

        frame = ttk.Frame(root, padding=12)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(2, weight=3)
        frame.rowconfigure(5, weight=1)

        self.photo_dir = tk.StringVar()
        self.output = tk.StringVar()
        ttk.Label(frame, text=tr("사진 폴더", "Photo folder")).grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.photo_dir).grid(row=0, column=1, sticky="ew", padx=6)
        self.folder_button = ttk.Button(frame, text=tr("찾아보기…", "Browse…"), command=self.choose_folder)
        self.folder_button.grid(row=0, column=2)
        ttk.Label(frame, text=tr("저장할 PDF", "Save PDF as")).grid(row=1, column=0, sticky="w", pady=4)
        output_entry = ttk.Entry(frame, textvariable=self.output)
        output_entry.grid(row=1, column=1, sticky="ew", padx=6)
        output_entry.bind("<Key>", lambda _event: setattr(self, "output_custom", True))
        self.output_button = ttk.Button(frame, text=tr("찾아보기…", "Browse…"), command=self.choose_output)
        self.output_button.grid(row=1, column=2)

        order_frame = ttk.LabelFrame(frame, text=tr("사진 순서", "Photo order"), padding=4)
        order_frame.grid(row=2, column=0, columnspan=3, sticky="nsew", pady=(6, 0))
        bar = ttk.Frame(order_frame)
        bar.pack(fill="x", pady=(0, 4))
        self.sort_mode = tk.StringVar(value=sort_label("name"))  # the shown text
        self.reverse = tk.BooleanVar(value=False)
        ttk.Label(bar, text=tr("정렬", "Sort")).pack(side="left")
        self.sort_box = ttk.Combobox(bar, textvariable=self.sort_mode, values=[sort_label(k) for k in SORT_KEYS],
                                     state="readonly", width=18)
        self.sort_box.pack(side="left", padx=6)
        self.sort_box.bind("<<ComboboxSelected>>", self.on_sort_selected)
        self.reverse_check = ttk.Checkbutton(bar, text=tr("역순(내림차순)으로 정렬", "Reverse (descending)"),
                                             variable=self.reverse,
                                             command=self.resort)
        self.reverse_check.pack(side="left", padx=6)
        self.no_taken_note = ttk.Label(bar, text=f"{NO_TAKEN_MARK} " + tr(
            "촬영 정보가 없어 수정한 날짜로 대신함", "No date taken; date modified used instead"))
        self.photo_list = PhotoList(order_frame, self.move)
        self.photo_list.pack(fill="both", expand=True)

        self.strip_number = tk.BooleanVar(value=False)
        strip_check = ttk.Checkbutton(frame, text=tr('파일 이름 앞 "숫자_" 빼고 메모 라벨 넣기',
                                                     'Drop a leading "number_" from file names in note labels'),
                                      variable=self.strip_number)
        strip_check.grid(row=3, column=0, columnspan=3, sticky="w", pady=(8, 0))
        self.strip_tip = Tooltip(strip_check, strip_number_help())

        buttons = ttk.Frame(frame)
        buttons.grid(row=4, column=0, columnspan=3, pady=10)
        self.build_button = ttk.Button(buttons, text=tr("앨범 만들기", "Make album"), command=self.start)
        self.build_button.pack(side="left", padx=4)
        self.open_button = ttk.Button(buttons, text=tr("PDF 열기", "Open PDF"), command=self.open_pdf,
                                      state="disabled")
        self.open_button.pack(side="left", padx=4)

        log_frame = ttk.LabelFrame(frame, text=tr("결과", "Result"), padding=4)
        log_frame.grid(row=5, column=0, columnspan=3, sticky="nsew")
        self.log = tk.Text(log_frame, height=6, wrap="word", state="disabled", font="TkDefaultFont")
        scroll = ttk.Scrollbar(log_frame, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.photo_dir.trace_add("write", self._refresh_default_output)
        self.photo_dir.trace_add("write", self.load_photos)
        if initial_folder and Path(initial_folder).is_dir():
            self.photo_dir.set(str(initial_folder))

    # --- photo order ----------------------------------------------------------

    def _folder(self):
        folder = self.photo_dir.get().strip()
        return folder if folder and Path(folder).is_dir() else None

    def load_photos(self, *_):
        folder = self._folder()
        self.photos = make_album.list_photo_files(folder) if folder else []
        self.taken_read = False
        if self.mode() == CUSTOM:
            self.sort_mode.set(sort_label("name"))
            self.reverse_check.state(["!disabled"])
        self.resort()
        self.photo_list.canvas.yview_moveto(0)  # a new folder starts at its first photo

    def _read_taken(self):
        """Read EXIF shooting times once per folder, only when 촬영한 날짜 순 needs them.

        Opening every photo (large HEIC files included) can take seconds, so a
        plain folder listing does not do it.
        """
        folder = self._folder()
        if folder and not self.taken_read:
            self.root.configure(cursor="watch")
            self.root.update_idletasks()
            try:
                self.photos = [replace(p, taken=make_album.date_taken(Path(folder, p.name)))
                               for p in self.photos]
            finally:
                self.root.configure(cursor="")
            self.taken_read = True

    def mode(self):
        """The sort key of the text in the sort box (CUSTOM after hand moves)."""
        return next(k for k in (*SORT_KEYS, CUSTOM) if sort_label(k) == self.sort_mode.get())

    def resort(self):
        mode = self.mode()
        if mode == "taken":
            self._read_taken()
        self.photos = sort_photos(self.photos, mode, self.reverse.get())
        # The list keeps showing these dates after hand moves (커스텀).
        self.dated_by = mode
        self._show_photos()

    def on_sort_selected(self, _event=None):
        self.reverse_check.state(["!disabled"])
        self.resort()

    def move(self, index, where):
        """Move a photo (top/up/down/bottom); any press switches the mode to 커스텀."""
        photo = self.photos.pop(index)
        target = {"top": 0, "up": max(index - 1, 0),
                  "down": min(index + 1, len(self.photos)), "bottom": len(self.photos)}[where]
        self.photos.insert(target, photo)
        self.sort_mode.set(sort_label(CUSTOM))
        self.reverse_check.state(["disabled"])
        self._show_photos()

    def _date_text(self, photo):
        if self.dated_by == "created":
            return _format_date(photo.created)
        if self.dated_by == "modified":
            return _format_date(photo.modified)
        if self.dated_by == "taken":
            if photo.taken is None:
                return f"{NO_TAKEN_MARK} {_format_date(photo.modified)}"
            return _format_date(photo.taken)
        return ""

    def _show_photos(self):
        dates = [self._date_text(p) for p in self.photos]
        self.photo_list.show([p.name for p in self.photos], dates, self._folder() is not None)
        # Explain the mark only while at least one row shows it.
        if any(d.startswith(NO_TAKEN_MARK) for d in dates):
            self.no_taken_note.pack(side="left", padx=6)
        else:
            self.no_taken_note.pack_forget()

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
        folder = filedialog.askdirectory(parent=self.root, title=tr("사진 폴더 고르기", "Choose a photo folder"),
                                         initialdir=self.photo_dir.get() or None)
        if folder:
            self.photo_dir.set(os.path.normpath(folder))

    def choose_output(self):
        current = Path(self.output.get()) if self.output.get() else None
        path = filedialog.asksaveasfilename(
            parent=self.root, title=tr("저장할 PDF", "Save PDF as"), defaultextension=".pdf",
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
        self.build_button.configure(text=tr("만드는 중…", "Making…") if busy else tr("앨범 만들기", "Make album"))
        self.open_button.configure(state="normal" if self.last_pdf and not busy else "disabled")

    def start(self):
        folder = self.photo_dir.get().strip()
        if not folder:
            self._show([tr("사진 폴더를 먼저 골라 주세요.", "Please choose a photo folder first.")])
            return
        self.last_pdf = None
        self._set_busy(True)
        self._show([tr("만드는 중…", "Making…")])
        output = self.output.get().strip()
        # Snapshot the list and checkbox now; changes made while building wait for the next run.
        order = [p.name for p in self.photos]
        strip_number = self.strip_number.get()
        threading.Thread(target=lambda: self._results.put(_run(folder, output, order, strip_number)),
                         daemon=True).start()
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
            messagebox.showinfo(title(), tr("앨범을 만드는 중입니다. 끝난 뒤 닫아 주세요.",
                                            "The album is still being made. Please close the window "
                                            "after it is done."), parent=self.root)
            return
        self.root.destroy()


def _smoke_test(photo_dir, output, log_file):
    lines, pdf = _run(photo_dir, output)
    Path(log_file).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0 if pdf else 1


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    english = "--english" in argv or (getattr(sys, "frozen", False) and is_english_exe(sys.executable))
    make_album.LANG = "en" if english else "ko"
    argv = [a for a in argv if a != "--english"]
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
