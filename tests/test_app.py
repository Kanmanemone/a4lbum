"""State logic of the album window, driven through a hidden Tk root."""

import time
import tkinter as tk

import pytest

import album_app
import make_album


@pytest.fixture(scope="session")
def tk_root():
    # One Tk interpreter per session: creating many in a row is flaky on Windows.
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"no display for Tk: {exc}")
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def root(tk_root):
    window = tk.Toplevel(tk_root)
    window.withdraw()
    yield window
    if window.winfo_exists():
        window.destroy()


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
    _, photos, pages, warnings = make_album.build_album(photo_dir)
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
