import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pymupdf
import pytest
from PIL import Image

import make_album
from conftest import sha256

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "make_album.py"
PT_TO_MM = 25.4 / 72


def run(folder, *extra):
    return make_album.main([str(folder), *map(str, extra)])


def default_pdf(folder):
    return folder.parent / f"{folder.name}_album.pdf"


def page_images(page):
    """(xref, bbox) of every image on the page, top to bottom."""
    # One entry per placement; get_image_rects() would merge identical images.
    found = [(info["xref"], pymupdf.Rect(info["bbox"])) for info in page.get_image_info(xrefs=True)]
    return sorted(found, key=lambda item: item[1].y0)


def lines_of(capsys):
    return capsys.readouterr().out.strip().splitlines()


# --- US1 -------------------------------------------------------------------


def test_four_photos_make_two_a4_pages(photo_dir, make_jpeg):
    for name in ["1_집.jpg", "2_바다.jpg", "3_산.jpg", "4_강.jpg"]:
        make_jpeg(name)
    assert run(photo_dir) == 0

    doc = pymupdf.open(default_pdf(photo_dir))
    assert doc.page_count == 2
    for page in doc:
        assert page.rect.width * PT_TO_MM == pytest.approx(210, abs=0.5)
        assert page.rect.height * PT_TO_MM == pytest.approx(297, abs=0.5)
        assert len(page_images(page)) == 2


def test_odd_count_leaves_last_bottom_empty(photo_dir, make_jpeg):
    for name in ["1_a.jpg", "2_b.jpg", "3_c.jpg"]:
        make_jpeg(name)
    assert run(photo_dir) == 0

    doc = pymupdf.open(default_pdf(photo_dir))
    assert doc.page_count == 2
    [(_, rect)] = page_images(doc[1])
    assert rect.y1 < doc[1].rect.height / 2  # sits in the top half


def test_order_and_captions_follow_file_names(photo_dir, make_jpeg):
    colors = {"2_바다.jpg": (0, 0, 255), "10_산.jpg": (0, 255, 0), "1_집.jpg": (255, 0, 0)}
    for name, color in colors.items():
        make_jpeg(name, color=color)
    make_jpeg("283_벚꽃 축제 모습.jpg")
    assert run(photo_dir) == 0

    doc = pymupdf.open(default_pdf(photo_dir))
    raw = {name: (photo_dir / name).read_bytes() for name in colors}
    placed = [doc.xref_stream_raw(xref) for page in doc for xref, _ in page_images(page)]
    assert placed[:3] == [raw["1_집.jpg"], raw["2_바다.jpg"], raw["10_산.jpg"]]

    text = "".join(page.get_text() for page in doc)
    for caption in ["집", "바다", "산", "벚꽃 축제 모습"]:
        assert caption in text
    assert "283_" not in text and ".jpg" not in text


def test_jpeg_bytes_and_originals_are_preserved(photo_dir, make_jpeg, make_png):
    paths = [make_jpeg("1_a.jpg", size=(4000, 3000)), make_jpeg("2_b.jpg"), make_png("3_c.png")]
    before = {p: sha256(p) for p in paths}
    listing = sorted(os.listdir(photo_dir))
    assert run(photo_dir) == 0

    assert {p: sha256(p) for p in paths} == before
    assert sorted(os.listdir(photo_dir)) == listing

    doc = pymupdf.open(default_pdf(photo_dir))
    streams = [doc.xref_stream_raw(xref) for page in doc for xref, _ in page_images(page)]
    assert paths[0].read_bytes() in streams
    assert paths[1].read_bytes() in streams
    assert len(streams) == 3  # the PNG is embedded too


def test_exif_rotation_places_portrait(photo_dir, make_jpeg):
    path = make_jpeg("1_세로.jpg", size=(1200, 900), orientation=6)
    original = path.read_bytes()
    assert run(photo_dir) == 0

    doc = pymupdf.open(default_pdf(photo_dir))
    [(xref, rect)] = page_images(doc[0])
    assert rect.height > rect.width
    assert doc.xref_stream_raw(xref) == original


def test_custom_output_path(photo_dir, make_jpeg, tmp_path):
    make_jpeg("1_a.jpg")
    out = tmp_path / "out" / "앨범.pdf"
    out.parent.mkdir()
    assert run(photo_dir, "-o", out) == 0
    assert out.exists()
    assert not default_pdf(photo_dir).exists()


# --- US2 -------------------------------------------------------------------


def test_script_runs_standalone_and_reports(photo_dir, make_jpeg):
    make_jpeg("1_집.jpg")
    make_jpeg("2_바다.jpg")
    make_jpeg("3_산.jpg")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(photo_dir)],
        capture_output=True,
        encoding="utf-8",
        cwd=REPO,
    )
    assert result.returncode == 0, result.stderr
    out = result.stdout.strip().splitlines()
    assert re.fullmatch(r"완료: 사진 3장 → 2페이지, 경고 0건", out[-2])
    assert out[-1].startswith("PDF: ")
    pdf = Path(out[-1][len("PDF: "):])
    assert pdf.is_absolute() and pdf.exists()


def test_rerun_after_rename_updates_caption(photo_dir, make_jpeg):
    path = make_jpeg("1_옛 설명.jpg")
    assert run(photo_dir) == 0
    path.rename(photo_dir / "1_새 설명.jpg")
    assert run(photo_dir) == 0

    text = pymupdf.open(default_pdf(photo_dir))[0].get_text()
    assert "새 설명" in text
    assert "옛 설명" not in text


# --- US3 -------------------------------------------------------------------


def test_problem_files_are_reported_and_skipped(photo_dir, make_jpeg, make_broken, capsys):
    make_jpeg("1_좋은 사진.jpg")
    make_broken("broken.jpg")
    make_jpeg("7_.jpg")
    (photo_dir / "IMG_0001.CR2").write_bytes(b"raw")
    (photo_dir / "IMG_0002.heic").write_bytes(b"not really heic")
    make_jpeg("8_" + "가" * 61 + ".jpg")
    make_jpeg("9_작은 사진.jpg", size=(100, 75))
    (photo_dir / "notes.txt").write_text("memo", encoding="utf-8")
    (photo_dir / "desktop.ini").write_text("", encoding="utf-8")
    (photo_dir / "sub").mkdir()
    make_jpeg("1_하위.jpg", folder=photo_dir / "sub")

    assert run(photo_dir) == 0
    out = lines_of(capsys)
    warnings = [line for line in out if line.startswith("경고: ")]

    def warned(name, keyword):
        return any(line.startswith(f"경고: {name} — ") and keyword in line for line in warnings)

    assert warned("broken.jpg", "열 수 없")
    assert warned("7_.jpg", "설명이 비어")
    assert warned("IMG_0001.CR2", "지원하지 않")
    assert warned("IMG_0002.heic", "열 수 없")
    assert warned("8_" + "가" * 61 + ".jpg", "60자")
    assert warned("9_작은 사진.jpg", "해상도")
    assert not any("notes.txt" in w or "desktop.ini" in w or "하위" in w for w in warnings)
    assert out[-2] == f"완료: 사진 4장 → 2페이지, 경고 {len(warnings)}건"

    doc = pymupdf.open(default_pdf(photo_dir))
    assert sum(len(page_images(page)) for page in doc) == 4


def test_heic_is_converted_and_placed(photo_dir, make_jpeg, capsys):
    pytest.importorskip("pillow_heif")
    make_jpeg("1_집.jpg")
    heic = photo_dir / "2_아이폰 사진.HEIC"
    photo_like((1200, 900)).save(heic, "HEIF")
    before = sha256(heic)
    listing = sorted(os.listdir(photo_dir))

    assert run(photo_dir) == 0
    out = lines_of(capsys)
    assert "알림: 2_아이폰 사진.HEIC — HEIC를 JPEG(품질 95)로 변환해 넣었습니다. 원본 파일은 그대로입니다." in out
    assert out[-2] == "완료: 사진 2장 → 1페이지, 경고 0건"

    assert sha256(heic) == before
    assert sorted(os.listdir(photo_dir)) == listing
    page = pymupdf.open(default_pdf(photo_dir))[0]
    images = page_images(page)
    assert len(images) == 2
    bottom = page.parent.extract_image(images[1][0])
    assert bottom["ext"] == "jpeg"
    assert (bottom["width"], bottom["height"]) == (1200, 900)
    assert "아이폰 사진" in page.get_text()


def photo_like(size=(900, 600)):
    """An image with far more than 256 colors, like a real photo."""
    noise = Image.effect_noise(size, 60)
    gradient = Image.linear_gradient("L").resize(size)
    return Image.merge("RGB", [noise, gradient, noise.transpose(Image.Transpose.FLIP_LEFT_RIGHT)])


def graphic_like(size=(900, 600)):
    img = Image.new("RGB", size, "white")
    img.paste((230, 60, 60), (100, 100, 400, 400))
    return img


def save_animated_gif(path):
    frames = [graphic_like(), Image.new("RGB", (900, 600), (60, 60, 230))]
    frames[0].save(path, "GIF", save_all=True, append_images=frames[1:])


@pytest.mark.parametrize(
    "name, write, expect_ext, message",
    [
        ("1_웹사진.webp", lambda p: photo_like().save(p, "WEBP", quality=90), "jpeg", "WEBP를 JPEG(품질 95)로"),
        ("1_비트맵.bmp", lambda p: photo_like().save(p, "BMP"), "jpeg", "BMP를 JPEG(품질 95)로"),
        ("1_스캔.tiff", lambda p: photo_like().save(p, "TIFF"), "jpeg", "TIFF를 JPEG(품질 95)로"),
        ("1_새 형식.avif", lambda p: photo_like().save(p, "AVIF"), "jpeg", "AVIF를 JPEG(품질 95)로"),
        ("1_그림.gif", lambda p: graphic_like().save(p, "GIF"), "png", "GIF를 PNG(무손실)로"),
        ("1_도표.bmp", lambda p: graphic_like().save(p, "BMP"), "png", "BMP를 PNG(무손실)로"),
        ("1_투명.webp", lambda p: _transparent(photo_like()).save(p, "WEBP"), "png", "WEBP를 PNG(무손실)로"),
        ("1_움짤.gif", save_animated_gif, "png", "첫 장면만"),
        ("1_이름만 jpg.jpg", lambda p: photo_like().save(p, "WEBP"), "jpeg", "WEBP를 JPEG(품질 95)로"),
    ],
)
def test_other_formats_are_converted(photo_dir, capsys, name, write, expect_ext, message):
    path = photo_dir / name
    write(path)
    before = sha256(path)
    listing = sorted(os.listdir(photo_dir))

    assert run(photo_dir) == 0
    notices = [line for line in lines_of(capsys) if line.startswith(f"알림: {name} — ")]
    assert len(notices) == 1 and message in notices[0]

    assert sha256(path) == before
    assert sorted(os.listdir(photo_dir)) == listing
    doc = pymupdf.open(default_pdf(photo_dir))
    [(xref, _)] = page_images(doc[0])
    assert doc.extract_image(xref)["ext"] == expect_ext


def _transparent(img):
    img = img.convert("RGBA")
    img.putalpha(Image.linear_gradient("L").resize(img.size))
    return img


def test_mpo_jpeg_is_embedded_as_is(photo_dir, capsys):
    path = photo_dir / "1_멀티픽처.jpg"
    photo_like().save(path, "MPO", save_all=True, append_images=[graphic_like()])
    assert Image.open(path).format == "MPO"

    assert run(photo_dir) == 0
    assert not any(line.startswith("알림:") for line in lines_of(capsys))
    doc = pymupdf.open(default_pdf(photo_dir))
    [(xref, _)] = page_images(doc[0])
    assert doc.extract_image(xref)["ext"] == "jpeg"
    pix = doc[0].get_pixmap(dpi=20)
    assert pix.width > 0


def test_no_usable_photos_still_lists_problems(photo_dir, make_broken, capsys):
    make_broken("broken.jpg")
    assert run(photo_dir) == 1
    captured = capsys.readouterr()
    assert "경고: broken.jpg — " in captured.out
    assert captured.err.startswith("오류: 넣을 사진이 없습니다")


def test_report_lines_match_cli_output(photo_dir, make_jpeg, capsys):
    make_jpeg("1_집.jpg")
    make_jpeg("7_.jpg")
    graphic_like().save(photo_dir / "2_그림.gif")
    assert run(photo_dir) == 0
    printed = lines_of(capsys)

    out, photos, pages, warnings = make_album.build_album(photo_dir)
    assert make_album.report_lines(out, photos, pages, warnings) == printed
    assert out == make_album.default_output_path(photo_dir)


def test_paths_keep_the_drive_letter_the_user_chose(tmp_path, monkeypatch):
    # resolve() would turn a mapped or subst drive (Z:\사진) into its real or UNC path.
    monkeypatch.setattr(make_album.Path, "resolve", lambda self, *a, **k: Path(r"\\nas\share") / self.name)
    folder = tmp_path / "2026 제주 여행"
    assert make_album.default_output_path(folder) == tmp_path / "2026 제주 여행_album.pdf"


def test_empty_caption_photo_has_no_label(photo_dir, make_jpeg):
    make_jpeg("7_.jpg")
    assert run(photo_dir) == 0
    page = pymupdf.open(default_pdf(photo_dir))[0]
    assert page.get_text().strip() == ""
    assert len(page_images(page)) == 1


def test_no_photos_fails_without_pdf(photo_dir, capsys):
    (photo_dir / "notes.txt").write_text("memo", encoding="utf-8")
    assert run(photo_dir) == 1
    assert capsys.readouterr().err.startswith("오류: ")
    assert not default_pdf(photo_dir).exists()


def test_missing_folder_fails(tmp_path, capsys):
    assert run(tmp_path / "없는 폴더") == 1
    assert capsys.readouterr().err.startswith("오류: ")


def test_missing_font_fails(photo_dir, make_jpeg, capsys):
    make_jpeg("1_a.jpg")
    assert run(photo_dir, "--font", photo_dir / "nope.ttf") == 1
    assert capsys.readouterr().err.startswith("오류: ")
    assert not default_pdf(photo_dir).exists()


def test_custom_font_keeps_emoji_fallback(tmp_path):
    primary = tmp_path / "fonts" / "label.ttf"
    primary.parent.mkdir()
    primary.write_bytes(make_album.default_font_path().read_bytes())
    fonts = make_album.Fonts(primary)
    if not (make_album.default_font_path().parent / "seguiemj.ttf").is_file():
        pytest.skip("Segoe UI Emoji is not installed")
    assert fonts.missing("벚꽃 🌸") == []


def test_bad_arguments_exit_2():
    with pytest.raises(SystemExit) as exc:
        make_album.main([])
    assert exc.value.code == 2


# --- Polish ----------------------------------------------------------------


def test_twenty_photos_under_a_minute(photo_dir, make_jpeg):
    for i in range(1, 21):
        make_jpeg(f"{i}_사진 {i}.jpg", size=(3000, 2000))
    start = time.perf_counter()
    assert run(photo_dir) == 0
    assert time.perf_counter() - start < 60
    assert pymupdf.open(default_pdf(photo_dir)).page_count == 10
