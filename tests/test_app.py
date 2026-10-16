"""State logic of the album window, driven through a hidden Tk root."""

import os
import time
import tkinter as tk
from datetime import datetime

import pytest

import album_app
import make_album


def wait_until_idle(app, timeout=30):
    deadline = time.monotonic() + timeout
    while app.busy:
        assert time.monotonic() < deadline, "album build did not finish"
        app.root.update()
        time.sleep(0.02)
    app.root.update()


def log_lines(app):
    return app.log.get("1.0", "end").strip().splitlines()


def enabled(button):
    return "disabled" not in button.state()


# --- US1 -------------------------------------------------------------------


def test_initial_folder_prefills_only_directories(root, photo_dir, tmp_path):
    app = album_app.AlbumApp(root, str(photo_dir))
    assert app.photo_dir.get() == str(photo_dir)
    assert app.output.get() == str(make_album.default_output_path(photo_dir))

    other = tk.Toplevel(root)
    app2 = album_app.AlbumApp(other, str(tmp_path / "file.txt"))
    assert app2.photo_dir.get() == ""
    assert app2.output.get() == ""


def test_output_follows_folder_until_customised(root, photo_dir, tmp_path):
    app = album_app.AlbumApp(root)
    app.photo_dir.set(str(photo_dir))
    assert app.output.get() == str(make_album.default_output_path(photo_dir))

    app.set_custom_output(str(tmp_path / "내 앨범.pdf"))
    app.photo_dir.set(str(tmp_path))
    assert app.output.get() == str(tmp_path / "내 앨범.pdf")


def test_build_shows_cli_lines_and_enables_open(root, photo_dir, make_jpeg):
    make_jpeg("1_집.jpg")
    make_jpeg("2_바다.jpg")
    make_jpeg("7_.jpg")
    app = album_app.AlbumApp(root, str(photo_dir))
    assert not enabled(app.open_button)

    app.start()
    assert app.busy
    assert not enabled(app.build_button) and not enabled(app.open_button)
    wait_until_idle(app)

    out = make_album.default_output_path(photo_dir)
    # The window leaves "숫자_" in captions unless its checkbox is ticked.
    _, photos, pages, warnings = make_album.build_album(photo_dir, strip_number=False)
    assert log_lines(app) == make_album.report_lines(out, photos, pages, warnings)
    assert app.last_pdf == out and out.exists()
    assert enabled(app.build_button) and enabled(app.open_button)


def test_open_pdf_uses_default_viewer(root, photo_dir, make_jpeg, monkeypatch):
    make_jpeg("1_집.jpg")
    opened = []
    monkeypatch.setattr(album_app.os, "startfile", opened.append, raising=False)
    app = album_app.AlbumApp(root, str(photo_dir))
    app.start()
    wait_until_idle(app)
    app.open_pdf()
    assert opened == [str(app.last_pdf)]


# --- US2 -------------------------------------------------------------------


def test_empty_folder_field_asks_for_folder(root):
    app = album_app.AlbumApp(root)
    app.start()
    assert not app.busy
    assert log_lines(app) == ["사진 폴더를 먼저 골라 주세요."]


def test_album_error_shows_warnings_then_error(root, photo_dir, make_broken):
    make_broken("broken.jpg")
    app = album_app.AlbumApp(root, str(photo_dir))
    app.start()
    wait_until_idle(app)
    lines = log_lines(app)
    assert lines[0].startswith("경고: broken.jpg — ")
    assert lines[-1].startswith("오류: 넣을 사진이 없습니다")
    assert enabled(app.build_button) and not enabled(app.open_button)
    assert not make_album.default_output_path(photo_dir).exists()


def test_unexpected_error_is_reported(root, photo_dir, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("뭔가 잘못됨")

    monkeypatch.setattr(album_app.make_album, "build_album", boom)
    app = album_app.AlbumApp(root, str(photo_dir))
    app.start()
    wait_until_idle(app)
    assert log_lines(app) == ["오류: 예상하지 못한 문제가 생겼습니다: 뭔가 잘못됨"]
    assert enabled(app.build_button)


def test_close_is_blocked_while_busy(root, monkeypatch):
    shown = []
    monkeypatch.setattr(album_app.messagebox, "showinfo", lambda *a, **k: shown.append(a))
    app = album_app.AlbumApp(root)
    app.busy = True
    app.on_close()
    assert shown and root.winfo_exists()
    app.busy = False


# --- Smoke-test entry point -----------------------------------------------


def test_smoke_test_mode_writes_log(photo_dir, make_jpeg, tmp_path):
    make_jpeg("1_집.jpg")
    out, log = tmp_path / "결과.pdf", tmp_path / "log.txt"
    assert album_app.main(["--smoke-test", str(photo_dir), str(out), str(log)]) == 0
    assert out.exists()
    assert "완료: 사진 1장 → 1페이지, 경고 0건" in log.read_text(encoding="utf-8")


def test_smoke_test_mode_reports_failure(tmp_path):
    log = tmp_path / "log.txt"
    assert album_app.main(["--smoke-test", str(tmp_path / "없음"), str(tmp_path / "x.pdf"), str(log)]) == 1
    assert log.read_text(encoding="utf-8").startswith("오류: ")


# --- 003: photo order list -------------------------------------------------


def order(app):
    return [p.name for p in app.photos]


def reverse_enabled(app):
    return "disabled" not in app.reverse_check.state()


def test_folder_shows_photos_in_name_order(root, photo_dir, make_jpeg, tmp_path):
    for name in ["10_산.jpg", "2_바다.jpg", "메모.txt"]:
        make_jpeg(name) if name.endswith(".jpg") else (photo_dir / name).write_text("x")
    app = album_app.AlbumApp(root, str(photo_dir))
    assert order(app) == ["2_바다.jpg", "10_산.jpg"]
    assert app.photo_list.labels() == ["  1   2_바다.jpg", "  2   10_산.jpg"]
    assert app.sort_mode.get() == "이름 순 정렬" and app.reverse.get() is False

    app.photo_dir.set(str(tmp_path / "없음"))
    assert order(app) == [] and app.photo_list.labels() == []


def test_empty_folder_says_no_photos(root, photo_dir):
    app = album_app.AlbumApp(root, str(photo_dir))
    assert app.photo_list.empty.winfo_manager() == "grid"
    app.photo_dir.set("")
    assert app.photo_list.empty.winfo_manager() == ""


def test_sort_mode_and_reverse(root, photo_dir, make_jpeg):
    for i, name in enumerate(["a.jpg", "b.jpg", "c.jpg"]):
        os.utime(make_jpeg(name), (0, 1_000_000 - i * 1000))
    app = album_app.AlbumApp(root, str(photo_dir))
    app.sort_mode.set("수정한 날짜 순 정렬")
    app.on_sort_selected()
    assert order(app) == ["c.jpg", "b.jpg", "a.jpg"]
    app.reverse.set(True)
    app.resort()
    assert order(app) == ["a.jpg", "b.jpg", "c.jpg"]


@pytest.mark.parametrize(
    "index, where, expected",
    [
        (2, "up", "ACBD"),
        (1, "down", "ACBD"),
        (2, "top", "CABD"),
        (1, "bottom", "ACDB"),
        (0, "up", "ABCD"),
        (0, "top", "ABCD"),
        (3, "down", "ABCD"),
        (3, "bottom", "ABCD"),
    ],
)
def test_move_buttons_switch_to_custom(root, photo_dir, four_photos, index, where, expected):
    app = album_app.AlbumApp(root, str(photo_dir))
    assert reverse_enabled(app)
    app.move(index, where)
    assert "".join(name[0] for name in order(app)) == expected
    assert app.sort_mode.get() == "커스텀" and not reverse_enabled(app)
    assert app.photo_list.labels()[0].endswith(f"{expected[0]}.jpg")


def test_row_buttons_call_move(root, photo_dir, four_photos):
    app = album_app.AlbumApp(root, str(photo_dir))
    buttons = app.photo_list.rows[2][2]
    assert [b.cget("text") for b in buttons] == ["▲", "▼", "맨 위로", "맨 아래로"]
    # A gap on the left of 맨 위로 separates it from ▲ ▼.
    assert [b.grid_info()["padx"] for b in buttons] == [0, 0, (8, 0), 0]
    buttons[2].invoke()
    assert "".join(name[0] for name in order(app)) == "CABD"


def test_choosing_a_sort_mode_leaves_custom(root, photo_dir, four_photos):
    app = album_app.AlbumApp(root, str(photo_dir))
    app.move(3, "top")
    app.sort_mode.set("이름 순 정렬")
    app.on_sort_selected()
    assert "".join(name[0] for name in order(app)) == "ABCD" and reverse_enabled(app)


def test_new_folder_resets_custom_to_name_order(root, photo_dir, four_photos, make_jpeg, tmp_path):
    app = album_app.AlbumApp(root, str(photo_dir))
    app.move(3, "top")
    other = tmp_path / "다른 폴더"
    other.mkdir()
    for name in ["2.jpg", "1.jpg"]:
        make_jpeg(name, folder=other)
    app.photo_dir.set(str(other))
    assert order(app) == ["1.jpg", "2.jpg"]
    assert app.sort_mode.get() == "이름 순 정렬" and reverse_enabled(app)


def test_new_folder_keeps_a_sort_mode_and_reverse(root, photo_dir, four_photos, make_jpeg, tmp_path):
    app = album_app.AlbumApp(root, str(photo_dir))
    app.reverse.set(True)
    app.resort()
    other = tmp_path / "다른 폴더"
    other.mkdir()
    for name in ["1.jpg", "2.jpg"]:
        make_jpeg(name, folder=other)
    app.photo_dir.set(str(other))
    assert order(app) == ["2.jpg", "1.jpg"] and app.reverse.get() is True


def test_start_passes_order_and_strip_number(root, photo_dir, four_photos, monkeypatch):
    calls = []

    def fake_build(photo_dir, output=None, font=None, order=None, strip_number=True):
        calls.append((order, strip_number))
        raise make_album.AlbumError("멈춤")

    monkeypatch.setattr(album_app.make_album, "build_album", fake_build)
    app = album_app.AlbumApp(root, str(photo_dir))
    assert app.strip_number.get() is False
    app.move(3, "top")
    app.start()
    wait_until_idle(app)
    app.strip_number.set(True)
    app.start()
    wait_until_idle(app)
    assert calls == [(["D.jpg", "A.jpg", "B.jpg", "C.jpg"], False),
                     (["D.jpg", "A.jpg", "B.jpg", "C.jpg"], True)]


def test_new_folder_list_starts_at_the_top(root, photo_dir, make_jpeg, tmp_path):
    for i in range(40):
        make_jpeg(f"{i}.jpg", size=(8, 8))
    app = album_app.AlbumApp(root, str(photo_dir))
    root.deiconify()
    root.update()
    canvas = app.photo_list.canvas
    canvas.yview_moveto(1.0)
    root.update()
    assert canvas.canvasy(0) > 0

    other = tmp_path / "다른 폴더"
    other.mkdir()
    make_jpeg("1.jpg", folder=other)
    app.photo_dir.set(str(other))
    root.update()
    assert canvas.canvasy(0) == 0


def test_date_sorts_show_their_dates(root, photo_dir, make_jpeg):
    os.utime(make_jpeg("b.jpg"), (0, datetime(2024, 5, 2, 8, 0, 0).timestamp()))
    os.utime(make_jpeg("a.jpg"), (0, datetime(2024, 5, 1, 9, 30, 15).timestamp()))
    app = album_app.AlbumApp(root, str(photo_dir))
    assert app.photo_list.dates() == ["", ""]

    app.sort_mode.set("수정한 날짜 순 정렬")
    app.on_sort_selected()
    assert app.photo_list.dates() == ["2024-05-01 09:30:15", "2024-05-02 08:00:00"]
    app.move(1, "top")  # 커스텀 keeps showing the dates it was sorted by
    assert app.photo_list.dates() == ["2024-05-02 08:00:00", "2024-05-01 09:30:15"]


def test_date_taken_is_read_only_for_its_sort(root, photo_dir, make_jpeg, monkeypatch):
    os.utime(make_jpeg("plain.jpg"), (0, datetime(2024, 5, 1, 9, 0, 0).timestamp()))
    calls = []
    monkeypatch.setattr(album_app.make_album, "date_taken", lambda path: calls.append(path))
    app = album_app.AlbumApp(root, str(photo_dir))
    assert calls == []

    app.sort_mode.set("촬영한 날짜 순 정렬")
    app.on_sort_selected()
    app.reverse.set(True)
    app.resort()
    assert len(calls) == 1  # once per folder
    assert app.photo_list.dates() == ["⚠ 2024-05-01 09:00:00"]


def test_no_taken_note_shows_only_with_the_mark(root, photo_dir, make_jpeg, monkeypatch):
    make_jpeg("plain.jpg")
    taken = {"plain.jpg": None}
    monkeypatch.setattr(album_app.make_album, "date_taken", lambda path: taken[path.name])
    app = album_app.AlbumApp(root, str(photo_dir))
    shown = lambda: app.no_taken_note.winfo_manager() == "pack"
    assert not shown()

    app.sort_mode.set("촬영한 날짜 순 정렬")
    app.on_sort_selected()
    assert shown()
    app.move(0, "top")  # 커스텀 keeps the taken dates and the note
    assert shown()
    app.sort_mode.set("수정한 날짜 순 정렬")
    app.on_sort_selected()
    assert not shown()

    taken["plain.jpg"] = datetime(2024, 5, 1).timestamp()
    app.load_photos()  # the same folder read again: now every photo has EXIF
    app.sort_mode.set("촬영한 날짜 순 정렬")
    app.on_sort_selected()
    assert not shown()


def test_strip_number_checkbox_explains_itself_on_hover(root):
    app = album_app.AlbumApp(root)
    tip = app.strip_tip
    assert tip.window is None
    tip.show()
    label = tip.window.winfo_children()[0]
    assert "283_벚꽃 축제 모습.jpg  →  벚꽃 축제 모습" in label.cget("text")
    tip.hide()
    assert tip.window is None

