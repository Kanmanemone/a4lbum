"""Build a printable A4 photo album PDF from a folder of photos.

Each A4 page holds two photos (top and bottom), centered on the page. A
sticky-note label hangs off the top-right corner of every photo; room for it is
kept on both sides so it never pushes the photo off center. The label shows the
photo's caption, taken from the file
name: "283_벚꽃 축제 모습.jpg" -> "벚꽃 축제 모습". Photos are ordered by file
name, comparing leading numbers by value. These are the CLI defaults; the app
window (album_app.py) passes its own photo order and may keep the "숫자_".

JPEG files are embedded byte-for-byte (no resizing or re-compression) and the
photo folder is only ever read. Other formats (HEIC, WEBP, GIF, BMP, TIFF, AVIF)
are converted in a temporary folder first: photos to JPEG quality 95, graphics
and transparent images to lossless PNG.

Usage: python scripts/make_album.py <PHOTO_DIR> [-o OUTPUT_PDF] [--font FONT_TTF]
"""

from __future__ import annotations

import argparse
import os
import re
import stat
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageOps
from reportlab import rl_config
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

try:
    import pillow_heif

    pillow_heif.register_heif_opener()
    HEIF_AVAILABLE = True
except ImportError:
    HEIF_AVAILABLE = False

# Keep JPEG streams identical to the source files instead of ASCII85-encoding them.
rl_config.useA85 = 0

# --- Layout constants (mm) ---------------------------------------------------

PAGE_W, PAGE_H = 210.0, 297.0
MARGIN = 10.0
GAP = 10.0
CELL_H = (PAGE_H - 2 * MARGIN - GAP) / 2  # 133.5

LABEL_OUT_X = 10.0  # how far the label sticks out past the photo's right edge
LABEL_OUT_Y = 5.0  # ... and above its top edge
LABEL_MIN_W, LABEL_MAX_W = 30.0, 64.0
LABEL_PAD_X, LABEL_PAD_Y = 2.5, 2.5
LINE_SPACING = 1.3
FONT_START_PT, FONT_MIN_PT = 11, 8
MAX_LINES = 3
MAX_CAPTION_CHARS = 60
MAX_OVERLAP_RATIO = 0.15
LOW_DPI = 150

LABEL_FILL = HexColor("#FFFFFF")
LABEL_BORDER = HexColor("#B4B4B4")
LABEL_SHADOW = HexColor("#000000")
LABEL_SHADOW_ALPHA = 0.12
LABEL_SHADOW_OFFSET = 1.0
LABEL_TEXT = HexColor("#333333")

MM = 72 / 25.4  # points per mm
PT = 25.4 / 72  # mm per point

PHOTO_EXTS = {".jpg", ".jpeg", ".jfif", ".png",
              ".heic", ".heif", ".avif", ".webp", ".gif", ".bmp", ".tif", ".tiff"}
HEIF_EXTS = {".heic", ".heif"}  # readable only with pillow-heif
RAW_EXTS = {".cr2", ".cr3", ".nef", ".arw", ".dng", ".orf", ".rw2", ".raf"}
# Formats PDF can hold as-is; everything else is converted first (see _convert).
EMBEDDABLE = {"JPEG": "jpeg", "MPO": "jpeg", "PNG": "png"}
CONVERT_JPEG_QUALITY = 95
IGNORED_NAMES = {"thumbs.db", "desktop.ini"}
ZERO_WIDTH = {"\u200d", "\ufe0e", "\ufe0f"}

ORIENTATION_TAG = 0x0112
EXIF_IFD = 0x8769
DATE_TAKEN_TAGS = (0x9003, 0x9004)  # DateTimeOriginal, DateTimeDigitized

# --- Language ------------------------------------------------------------------

# Messages are Korean; the English app (album_app.py run as "... (English).exe")
# sets this to "en" once at start-up. The CLI always stays Korean.
LANG = "ko"


def tr(ko, en):
    """The message for the current language."""
    return en if LANG == "en" else ko


def _count(n, word):
    return f"{n} {word}" + ("" if n == 1 else "s")


# --- Data model ----------------------------------------------------------------


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    w: float
    h: float

    @property
    def right(self):
        return self.x + self.w

    @property
    def top(self):
        return self.y + self.h

    @property
    def area(self):
        return self.w * self.h

    def intersection_area(self, other):
        w = min(self.right, other.right) - max(self.x, other.x)
        h = min(self.top, other.top) - max(self.y, other.y)
        return max(w, 0.0) * max(h, 0.0)

    def contains(self, other, eps=1e-6):
        return (
            other.x >= self.x - eps
            and other.y >= self.y - eps
            and other.right <= self.right + eps
            and other.top <= self.top + eps
        )


PRINTABLE = Rect(MARGIN, MARGIN, PAGE_W - 2 * MARGIN, PAGE_H - 2 * MARGIN)


@dataclass(frozen=True)
class PhotoFile:
    """A photo file as listed in the app window (dates are epoch seconds).

    taken is the camera's shooting time from EXIF, or None when the photo has none.
    """

    name: str
    created: float
    modified: float
    taken: float | None = None


@dataclass
class PhotoItem:
    path: Path
    file_name: str
    caption: str
    sort_key: tuple
    kind: str
    pixel_size: tuple[int, int]
    orientation: int
    display_size: tuple[int, int]


@dataclass
class Label:
    lines: list[str]
    font_size_pt: float
    rect: Rect
    truncated: bool


@dataclass
class Slot:
    position: str
    cell: Rect
    photo_box: Rect
    photo_rect: Rect
    item: PhotoItem
    label: Label | None


@dataclass
class AlbumPage:
    number: int
    top: Slot
    bottom: Slot | None


@dataclass
class AlbumWarning:
    code: str
    file_name: str
    message: str

    @property
    def is_notice(self):
        """Informational only: printed as "알림" and not counted as a warning."""
        return self.code == "CONVERTED"

    def __str__(self):
        kind = tr("알림", "Note") if self.is_notice else tr("경고", "Warning")
        return f"{kind}: {self.file_name} — {self.message}"


class AlbumError(Exception):
    """A problem that stops the album from being built."""

    def __init__(self, message, warnings=()):
        super().__init__(message)
        self.warnings = list(warnings)


# --- File names ----------------------------------------------------------------


def extract_caption(file_name, strip_number=True):
    stem = os.path.splitext(file_name)[0]
    if strip_number:
        stem = re.sub(r"^\d+_", "", stem, count=1)
    return stem.strip()


def natural_key(file_name):
    stem = os.path.splitext(file_name)[0]
    parts = re.split(r"(\d+)", stem)
    key = tuple((0, int(p)) if p.isdigit() else (1, p.casefold()) for p in parts if p)
    return key, file_name


# --- Scanning ------------------------------------------------------------------


def _is_hidden(entry):
    if entry.name.startswith(".") or entry.name.casefold() in IGNORED_NAMES:
        return True
    attrs = getattr(entry.stat(), "st_file_attributes", 0)
    return bool(attrs & getattr(stat, "FILE_ATTRIBUTE_HIDDEN", 0))


def _read_photo(path):
    with Image.open(path) as img:
        img.verify()
    with Image.open(path) as img:
        kind = EMBEDDABLE.get(img.format)
        orientation = img.getexif().get(ORIENTATION_TAG, 1)
        if orientation not in range(1, 9):
            orientation = 1
        return kind, img.size, orientation


def _has_alpha(img):
    if img.mode in ("RGBA", "LA", "PA") or "transparency" in img.info:
        return img.convert("RGBA").getchannel("A").getextrema()[0] < 255
    return False


def _convert(src, work_dir):
    """Save a photo PDF cannot hold as-is into work_dir; return (path, description).

    Photos become JPEG quality 95 (visually lossless, ~5x smaller than PNG).
    Graphics with at most 256 colors or with transparency become lossless PNG,
    which is both smaller and sharper for them.
    """
    with Image.open(src) as img:
        name = "HEIC" if img.format == "HEIF" and src.suffix.casefold() == ".heic" else img.format
        multi = getattr(img, "n_frames", 1) > 1
        img.seek(0)
        img = ImageOps.exif_transpose(img)
        stem = Path(work_dir) / str(len(os.listdir(work_dir)))
        if _has_alpha(img) or img.getcolors(256) is not None:
            dst, target = stem.with_suffix(".png"), tr("PNG(무손실)", "PNG (lossless)")
            img.convert("RGBA" if _has_alpha(img) else "RGB").save(dst, "PNG")
        else:
            dst, target = stem.with_suffix(".jpg"), tr(f"JPEG(품질 {CONVERT_JPEG_QUALITY})",
                                                       f"JPEG (quality {CONVERT_JPEG_QUALITY})")
            img.convert("RGB").save(dst, "JPEG", quality=CONVERT_JPEG_QUALITY, subsampling=0)
    note = tr(" 여러 장면이 든 파일이라 첫 장면만 넣었습니다.",
              " The file holds several frames; only the first was added.") if multi else ""
    return dst, tr(f"{name}를 {target}로 변환해 넣었습니다.{note} 원본 파일은 그대로입니다.",
                   f"Converted {name} to {target}.{note} The original file is unchanged.")


def _photo_entries(folder):
    """Yield (entry, None) for each photo to try, or (None, warning) for a skipped one."""
    for entry in os.scandir(folder):
        if not entry.is_file() or _is_hidden(entry):
            continue
        ext = os.path.splitext(entry.name)[1].casefold()
        if ext in RAW_EXTS or (ext in HEIF_EXTS and not HEIF_AVAILABLE):
            hint = (tr("카메라 RAW 파일은 JPEG로 내보낸 뒤 넣어 주세요.",
                       "Export camera RAW files to JPEG first.") if ext in RAW_EXTS
                    else tr("pillow-heif를 설치하면 넣을 수 있습니다(pip install -r requirements.txt).",
                            "Install pillow-heif to include it (pip install -r requirements.txt)."))
            yield None, AlbumWarning("UNSUPPORTED_FORMAT", entry.name,
                                     tr(f"지원하지 않는 사진 형식이라 건너뛰었습니다. {hint}",
                                        f"Skipped: unsupported photo format. {hint}"))
        elif ext in PHOTO_EXTS:
            yield entry, None


def date_taken(path):
    """EXIF shooting time as epoch seconds (local time), or None.

    Only the file header is read, not the pixels.
    """
    try:
        with Image.open(path) as img:
            exif = img.getexif().get_ifd(EXIF_IFD)
        for tag in DATE_TAKEN_TAGS:
            value = exif.get(tag)
            if isinstance(value, str) and value.strip():
                return datetime.strptime(value.strip()[:19], "%Y:%m:%d %H:%M:%S").timestamp()
    except Exception:  # unreadable file or malformed date such as "0000:00:00 00:00:00"
        pass
    return None


def list_photo_files(folder):
    """The files the album would try, with their file dates, without opening them.

    taken stays None here; reading EXIF is slow for large folders (see date_taken).
    """
    try:
        photos = []
        for entry, _ in _photo_entries(folder):
            if entry is not None:
                st = entry.stat()
                photos.append(PhotoFile(entry.name, getattr(st, "st_birthtime", st.st_ctime), st.st_mtime))
        return photos
    except OSError:
        return []


def scan_folder(folder, work_dir, strip_number=True):
    """Collect photos in folder; formats PDF cannot hold are converted into work_dir."""
    items, warnings = [], []
    for entry, warning in _photo_entries(folder):
        if warning:
            warnings.append(warning)
            continue
        path = Path(entry.path)
        try:
            kind, size, orientation = _read_photo(path)
            if kind is None:
                path, message = _convert(path, work_dir)
                warnings.append(AlbumWarning("CONVERTED", entry.name, message))
                kind, size, orientation = _read_photo(path)
        except Exception:
            warnings.append(AlbumWarning("UNREADABLE", entry.name,
                                         tr("사진 파일을 열 수 없어 건너뛰었습니다.",
                                            "Skipped: the photo file cannot be opened.")))
            continue
        display = (size[1], size[0]) if orientation >= 5 else size
        items.append(PhotoItem(path, entry.name, extract_caption(entry.name, strip_number), natural_key(entry.name),
                               kind, size, orientation, display))
    items.sort(key=lambda item: item.sort_key)
    return items, warnings


# --- Layout --------------------------------------------------------------------


def slot_geometry(position):
    """The half-page cell and the box the photo is centered in.

    The box leaves room for the label on both sides and on the page-edge side
    (above the top photo, below the bottom one), so photos sit on the page's
    center line and the two slots mirror each other about the page middle.
    """
    top = position == "top"
    cell = Rect(MARGIN, MARGIN + CELL_H + GAP if top else MARGIN, PAGE_W - 2 * MARGIN, CELL_H)
    box = Rect(cell.x + LABEL_OUT_X, cell.y if top else cell.y + LABEL_OUT_Y,
               cell.w - 2 * LABEL_OUT_X, cell.h - LABEL_OUT_Y)
    return cell, box


def fit_photo(display_size, box):
    w, h = display_size
    scale = min(box.w / w, box.h / h)
    pw, ph = w * scale, h * scale
    return Rect(box.x + (box.w - pw) / 2, box.y + (box.h - ph) / 2, pw, ph)


def _wrap(text, size, max_w, measure):
    """Greedy wrap by character, breaking at the last space when possible."""
    lines, line = [], ""
    for ch in text:
        if ch == "\n":
            ch = " "
        if measure(line + ch, size) <= max_w or not line:
            line += ch
            continue
        cut = line.rfind(" ")
        if cut > 0:
            lines.append(line[:cut].rstrip())
            line = line[cut + 1:] + ch
        else:
            lines.append(line)
            line = ch
        line = line.lstrip()
    if line.strip():
        lines.append(line.rstrip())
    return lines


def _ellipsize(line, size, max_w, measure):
    line = line.rstrip()
    while line and measure(line + "…", size) > max_w:
        line = line[:-1].rstrip()
    return line + "…"


def _build_label(caption, size, max_lines, photo, measure):
    inner = LABEL_MAX_W - 2 * LABEL_PAD_X
    lines = _wrap(caption, size, inner, measure)
    truncated = len(lines) > max_lines
    if truncated:
        lines = lines[:max_lines]
        lines[-1] = _ellipsize(lines[-1], size, inner, measure)
    text_w = max(measure(line, size) for line in lines)
    w = min(max(text_w + 2 * LABEL_PAD_X, LABEL_MIN_W), LABEL_MAX_W)
    h = len(lines) * size * LINE_SPACING * PT + 2 * LABEL_PAD_Y
    right, top = photo.right + LABEL_OUT_X, photo.top + LABEL_OUT_Y
    return Label(lines, size, Rect(right - w, top - h, w, h), truncated)



def _overlap_ok(label, photo):
    return label.rect.intersection_area(photo) <= MAX_OVERLAP_RATIO * photo.area


def fit_label(caption, photo, measure):
    if not caption:
        return None
    sizes = range(FONT_START_PT, FONT_MIN_PT - 1, -1)
    # Prefer the largest font that shows the whole caption.
    for size in sizes:
        label = _build_label(caption, size, MAX_LINES, photo, measure)
        if not label.truncated and _overlap_ok(label, photo):
            return label
    # Otherwise cut it short at the smallest font, dropping lines if the label
    # would cover too much of the photo.
    for max_lines in range(MAX_LINES, 0, -1):
        label = _build_label(caption, FONT_MIN_PT, max_lines, photo, measure)
        if _overlap_ok(label, photo):
            return label
    return label


def layout_pages(items, measure):
    pages = []
    for i in range(0, len(items), 2):
        slots = []
        for position, item in zip(("top", "bottom"), items[i:i + 2]):
            cell, box = slot_geometry(position)
            photo = fit_photo(item.display_size, box)
            slots.append(Slot(position, cell, box, photo, item, fit_label(item.caption, photo, measure)))
        pages.append(AlbumPage(len(pages) + 1, slots[0], slots[1] if len(slots) > 1 else None))
    return pages


def page_warnings(pages, fonts):
    warnings = []
    for page in pages:
        for slot in (page.top, page.bottom):
            if slot is None:
                continue
            item, name = slot.item, slot.item.file_name
            if not item.caption:
                warnings.append(AlbumWarning("EMPTY_CAPTION", name,
                                             tr("설명이 비어 있어 메모 라벨 없이 넣었습니다.",
                                                "The caption is empty, so the photo has no note label.")))
            elif len(item.caption) > MAX_CAPTION_CHARS:
                warnings.append(AlbumWarning("LONG_CAPTION", name,
                                        tr(f"설명이 {len(item.caption)}자로 권장 길이({MAX_CAPTION_CHARS}자)를 넘습니다.",
                                           f"The caption has {len(item.caption)} characters, more than the "
                                           f"recommended {MAX_CAPTION_CHARS}.")))
            if slot.label and slot.label.truncated:
                warnings.append(AlbumWarning("CAPTION_TRUNCATED", name,
                                        tr("설명이 메모 라벨에 다 들어가지 않아 뒷부분을 '…'로 줄였습니다.",
                                           "The caption did not fit in the note label, so its end became '…'.")))
            missing = fonts.missing(item.caption)
            if missing:
                warnings.append(AlbumWarning("MISSING_GLYPH", name,
                                        tr(f"글꼴에 없는 글자({''.join(missing)})는 빼고 표시했습니다.",
                                           f"Characters missing from the font ({''.join(missing)}) were left out.")))
            dpi = min(item.display_size[0] / (slot.photo_rect.w / 25.4),
                      item.display_size[1] / (slot.photo_rect.h / 25.4))
            if dpi < LOW_DPI:
                warnings.append(AlbumWarning("LOW_RESOLUTION", name,
                                        tr(f"해상도가 낮아(약 {dpi:.0f}dpi) 인쇄하면 흐릿할 수 있습니다.",
                                           f"Low resolution (about {dpi:.0f} dpi); it may look blurry in print.")))
    return warnings


# --- Fonts ---------------------------------------------------------------------


def default_font_path():
    return Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / "malgun.ttf"


class Fonts:
    """Primary label font plus emoji/symbol fallbacks, chosen per character."""

    def __init__(self, primary):
        primary = Path(primary)
        if not primary.is_file():
            raise AlbumError(tr(f"글꼴 파일을 찾을 수 없습니다: {primary} (--font로 지정할 수 있습니다)",
                                f"Font file not found: {primary} (choose one with --font)"))
        system_fonts = default_font_path().parent
        fallbacks = [system_fonts / "seguiemj.ttf", system_fonts / "seguisym.ttf"]
        self.faces = []
        for i, path in enumerate([primary, *fallbacks]):
            if i and not path.is_file():
                continue
            name = f"AlbumFont{i}"
            try:
                font = TTFont(name, str(path))
            except Exception as exc:
                if i == 0:
                    raise AlbumError(tr(f"글꼴 파일을 읽을 수 없습니다: {path} ({exc})",
                                        f"Cannot read the font file: {path} ({exc})")) from exc
                continue
            pdfmetrics.registerFont(font)
            self.faces.append((name, font.face.charToGlyph))

    def _font_for(self, ch):
        for name, cmap in self.faces:
            if ord(ch) in cmap:
                return name
        return None

    def runs(self, text):
        """Split text into (font_name, text) runs, dropping unsupported glyphs."""
        runs = []
        for ch in text:
            name = self._font_for(ch)
            if name is None:
                continue
            if runs and runs[-1][0] == name:
                runs[-1][1] += ch
            else:
                runs.append([name, ch])
        return runs

    def missing(self, text):
        return sorted({ch for ch in text if ch not in ZERO_WIDTH and self._font_for(ch) is None})

    def measure(self, text, size_pt):
        width = sum(pdfmetrics.stringWidth(run, name, size_pt) for name, run in self.runs(text))
        return width * PT


# --- Rendering -----------------------------------------------------------------


def _orientation_matrix(orientation, w, h):
    """Affine (a, b, c, d, e, f) mapping the raw image onto a w×h display box."""
    return {
        1: (1, 0, 0, 1, 0, 0),
        2: (-1, 0, 0, 1, w, 0),
        3: (-1, 0, 0, -1, w, h),
        4: (1, 0, 0, -1, 0, h),
        5: (0, -1, -1, 0, w, h),
        6: (0, -1, 1, 0, 0, h),
        7: (0, 1, 1, 0, 0, 0),
        8: (0, 1, -1, 0, w, 0),
    }[orientation]


def _draw_photo(c, slot):
    rect, item = slot.photo_rect, slot.item
    w, h = rect.w * MM, rect.h * MM
    raw_w, raw_h = (h, w) if item.orientation >= 5 else (w, h)
    c.saveState()
    c.translate(rect.x * MM, rect.y * MM)
    c.transform(*_orientation_matrix(item.orientation, w, h))
    # Passing the path (not decoded pixels) lets reportlab embed JPEG bytes as-is.
    c.drawImage(str(item.path), 0, 0, width=raw_w, height=raw_h,
                mask="auto" if item.kind == "png" else None)
    c.restoreState()


def _draw_label(c, label, fonts):
    r = label.rect
    c.saveState()
    c.setFillColor(LABEL_SHADOW)
    c.setFillAlpha(LABEL_SHADOW_ALPHA)
    c.rect((r.x + LABEL_SHADOW_OFFSET) * MM, (r.y - LABEL_SHADOW_OFFSET) * MM, r.w * MM, r.h * MM,
           stroke=0, fill=1)
    c.setFillAlpha(1)
    c.setFillColor(LABEL_FILL)
    c.setStrokeColor(LABEL_BORDER)
    c.setLineWidth(0.5)
    c.rect(r.x * MM, r.y * MM, r.w * MM, r.h * MM, stroke=1, fill=1)

    c.setFillColor(LABEL_TEXT)
    size = label.font_size_pt
    line_h = size * LINE_SPACING
    y = r.top * MM - LABEL_PAD_Y * MM - (line_h + size * 0.75) / 2
    for line in label.lines:
        x = (r.x + LABEL_PAD_X) * MM
        for name, run in fonts.runs(line):
            c.setFont(name, size)
            c.drawString(x, y, run)
            x += pdfmetrics.stringWidth(run, name, size)
        y -= line_h
    c.restoreState()


def render_pdf(pages, out_path, fonts):
    out_path = Path(out_path)
    fd, tmp = tempfile.mkstemp(suffix=".pdf", dir=out_path.parent)
    os.close(fd)
    try:
        c = canvas.Canvas(tmp, pagesize=(PAGE_W * MM, PAGE_H * MM))
        c.setTitle(out_path.stem)
        for page in pages:
            for slot in (page.top, page.bottom):
                if slot is not None:
                    _draw_photo(c, slot)
            for slot in (page.top, page.bottom):
                if slot is not None and slot.label is not None:
                    _draw_label(c, slot.label, fonts)
            c.showPage()
        c.save()
        os.replace(tmp, out_path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


# --- CLI -----------------------------------------------------------------------


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="make_album.py",
        description="사진 폴더로 A4 앨범 PDF를 만듭니다. 사진 이름 '숫자_설명.jpg'의 '설명'이 메모 라벨에 들어갑니다.",
    )
    parser.add_argument("photo_dir", metavar="PHOTO_DIR", help="사진이 들어 있는 폴더")
    parser.add_argument("-o", "--output", help="출력 PDF 경로 (기본: <폴더 부모>/<폴더이름>_album.pdf)")
    parser.add_argument("--font", help=f"메모 라벨 글꼴 TTF 경로 (기본: {default_font_path()})")
    return parser.parse_args(argv)


def _use_utf8_console():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass


def default_output_path(photo_dir):
    # abspath, not resolve(): keep mapped/subst drive letters as the user typed them.
    folder = Path(os.path.abspath(photo_dir))
    return folder.parent / f"{folder.name}_album.pdf"


def report_lines(out, photo_count, page_count, warnings):
    """The result lines shown to the user (CLI stdout and the app window)."""
    warning_count = sum(not w.is_notice for w in warnings)
    return [*map(str, warnings),
            tr(f"완료: 사진 {photo_count}장 → {page_count}페이지, 경고 {warning_count}건",
               f"Done: {_count(photo_count, 'photo')} → {_count(page_count, 'page')}, "
               f"{_count(warning_count, 'warning')}"),
            f"PDF: {out}"]


def build_album(photo_dir, output=None, font=None, order=None, strip_number=True):
    """Build the album PDF.

    order: file names in the wanted order (the app's list); photos not in it go
    last in name order. strip_number: drop a leading "숫자_" from captions.
    """
    folder = Path(photo_dir)
    if not folder.is_dir():
        raise AlbumError(tr(f"사진 폴더를 찾을 수 없습니다: {folder}", f"Photo folder not found: {folder}"))
    folder = Path(os.path.abspath(folder))
    out = Path(os.path.abspath(output)) if output else default_output_path(folder)

    # Converted photos live here until the PDF is written; the photo folder stays untouched.
    with tempfile.TemporaryDirectory(prefix="a4lbum_") as work_dir:
        items, warnings = scan_folder(folder, work_dir, strip_number)
        if order is not None:
            rank = {name: i for i, name in enumerate(order)}
            items.sort(key=lambda item: (0, rank[item.file_name]) if item.file_name in rank
                       else (1, item.sort_key))
        if not items:
            raise AlbumError(tr(f"넣을 사진이 없습니다: {folder}", f"No photos to add: {folder}"), warnings)
        fonts = Fonts(font or default_font_path())
        pages = layout_pages(items, fonts.measure)
        warnings += page_warnings(pages, fonts)

        try:
            render_pdf(pages, out, fonts)
        except PermissionError as exc:
            raise AlbumError(tr(f"PDF를 저장할 수 없습니다: {out} — PDF 뷰어에서 열려 있다면 닫고 다시 실행해 주세요.",
                                f"Cannot save the PDF: {out} — if it is open in a PDF viewer, close it "
                                f"and try again.")) from exc
        except OSError as exc:
            raise AlbumError(tr(f"PDF를 저장할 수 없습니다: {out} ({exc})",
                                f"Cannot save the PDF: {out} ({exc})")) from exc
    return out, len(items), len(pages), warnings


def main(argv=None):
    _use_utf8_console()
    args = _parse_args(argv)
    try:
        out, photo_count, page_count, warnings = build_album(args.photo_dir, args.output, args.font)
    except AlbumError as exc:
        for warning in exc.warnings:
            print(warning)
        print(f"오류: {exc}", file=sys.stderr)
        return 1
    for line in report_lines(out, photo_count, page_count, warnings):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
