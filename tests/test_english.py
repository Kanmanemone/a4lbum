"""The English app: "Photo Album Maker (English).exe" is the same program in English."""

from pathlib import Path

import pytest

import album_app
import make_album
from test_app import order


@pytest.fixture
def english(monkeypatch):
    monkeypatch.setattr(make_album, "LANG", "en")


@pytest.mark.parametrize(
    "exe, expected",
    [
        (r"C:\앨범\Photo Album Maker (English).exe", True),
        (r"C:\앨범\photo album maker (ENGLISH).EXE", True),
        (r"C:\앨범\앨범 만들기 (한국어).exe", False),
        (r"C:\English\앨범 만들기 (한국어).exe", False),
    ],
)
def test_language_follows_the_exe_name(exe, expected):
    assert album_app.is_english_exe(exe) is expected


def test_report_lines_in_english(english, tmp_path):
    warning = make_album.AlbumWarning("EMPTY_CAPTION", "7_.jpg", "x")
    notice = make_album.AlbumWarning("CONVERTED", "a.heic", "y")
    assert make_album.report_lines(tmp_path / "a.pdf", 1, 1, [notice, warning]) == [
        "Note: a.heic — y", "Warning: 7_.jpg — x",
        "Done: 1 photo → 1 page, 1 warning", f"PDF: {tmp_path / 'a.pdf'}"]
    assert make_album.report_lines(tmp_path / "a.pdf", 3, 2, [])[0] == "Done: 3 photos → 2 pages, 0 warnings"


def test_album_errors_in_english(english, tmp_path):
    with pytest.raises(make_album.AlbumError, match="^Photo folder not found: "):
        make_album.build_album(tmp_path / "없음")
    with pytest.raises(make_album.AlbumError, match="^No photos to add: "):
        make_album.build_album(tmp_path)


def test_window_in_english(english, root, photo_dir, four_photos):
    app = album_app.AlbumApp(root, str(photo_dir))
    assert root.title() == "Photo Album Maker (English)"
    assert app.sort_mode.get() == "By name"
    assert list(app.sort_box.cget("values")) == ["By name", "By date created", "By date modified", "By date taken"]
    assert [b.cget("text") for b in app.photo_list.rows[0][2]] == ["▲", "▼", "To top", "To bottom"]
    assert app.build_button.cget("text") == "Make album"

    app.move(3, "top")
    assert app.sort_mode.get() == "Custom" and order(app) == ["D.jpg", "A.jpg", "B.jpg", "C.jpg"]
    app.sort_mode.set("By date modified")
    app.on_sort_selected()
    assert app.photo_list.dates()[0]  # dates are shown for a date sort

    app.photo_dir.set("")
    app.start()
    assert app.log.get("1.0", "end").strip() == "Please choose a photo folder first."


def test_english_smoke_test(monkeypatch, photo_dir, make_jpeg, tmp_path):
    monkeypatch.setattr(make_album, "LANG", "ko")  # restored after main() switches it
    make_jpeg("1_집.jpg")
    out, log = tmp_path / "result.pdf", tmp_path / "log.txt"
    assert album_app.main(["--english", "--smoke-test", str(photo_dir), str(out), str(log)]) == 0
    assert "Done: 1 photo → 1 page, 0 warnings" in log.read_text(encoding="utf-8")
    assert album_app.main(["--smoke-test", str(photo_dir), str(out), str(log)]) == 0
    assert "완료: 사진 1장 → 1페이지, 경고 0건" in log.read_text(encoding="utf-8")


def test_window_titles_match_the_exe_names(monkeypatch):
    script = (Path(__file__).parent.parent / "build_portable.ps1").read_text(encoding="utf-8-sig")
    for lang in ("ko", "en"):
        monkeypatch.setattr(make_album, "LANG", lang)
        assert f"'{album_app.title()}'" in script
