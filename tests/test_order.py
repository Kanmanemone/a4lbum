"""Photo list for the app window, its sort modes, and build_album(order, strip_number)."""

import os

import pytest

import album_app
import make_album
from make_album import PhotoFile


@pytest.fixture
def captured(monkeypatch):
    """Record the photo order and captions build_album lays out."""
    seen = []
    real = make_album.layout_pages

    def spy(items, measure):
        seen[:] = [(item.file_name, item.caption) for item in items]
        return real(items, measure)

    monkeypatch.setattr(make_album, "layout_pages", spy)
    return seen


# --- list_photo_files --------------------------------------------------------


def test_lists_only_album_candidates(photo_dir, make_jpeg, make_broken):
    make_jpeg("1_집.jpg")
    make_jpeg(".숨김.jpg")
    make_broken("broken.jpg")
    (photo_dir / "Thumbs.db").write_bytes(b"x")
    (photo_dir / "메모.txt").write_text("x", encoding="utf-8")
    (photo_dir / "raw.cr2").write_bytes(b"x")
    (photo_dir / "하위폴더.jpg").mkdir()

    photos = make_album.list_photo_files(photo_dir)
    assert sorted(p.name for p in photos) == ["1_집.jpg", "broken.jpg"]
    jpeg = next(p for p in photos if p.name == "1_집.jpg")
    st = (photo_dir / "1_집.jpg").stat()
    assert jpeg.modified == st.st_mtime
    assert jpeg.created == getattr(st, "st_birthtime", st.st_ctime)


def test_missing_folder_lists_nothing(tmp_path):
    assert make_album.list_photo_files(tmp_path / "없음") == []


# --- sort_photos -------------------------------------------------------------

PHOTOS = [
    PhotoFile("10_산.jpg", created=100, modified=300),
    PhotoFile("2_바다.jpg", created=300, modified=100),
    PhotoFile("1_집.jpg", created=200, modified=100),
]


def names(photos):
    return [p.name for p in photos]


@pytest.mark.parametrize(
    "mode, expected",
    [
        ("name", ["1_집.jpg", "2_바다.jpg", "10_산.jpg"]),
        ("created", ["10_산.jpg", "1_집.jpg", "2_바다.jpg"]),
        # Same modified date for 1_ and 2_: name order breaks the tie.
        ("modified", ["1_집.jpg", "2_바다.jpg", "10_산.jpg"]),
    ],
)
def test_sort_modes_and_reverse(mode, expected):
    assert names(album_app.sort_photos(PHOTOS, mode, False)) == expected
    assert names(album_app.sort_photos(PHOTOS, mode, True)) == expected[::-1]


def test_modified_date_sort_on_real_files(photo_dir, make_jpeg):
    for i, name in enumerate(["a.jpg", "b.jpg", "c.jpg"]):
        os.utime(make_jpeg(name), (0, 1_000_000 - i * 1000))
    photos = make_album.list_photo_files(photo_dir)
    assert names(album_app.sort_photos(photos, "modified", False)) == ["c.jpg", "b.jpg", "a.jpg"]


# --- build_album(order, strip_number) ------------------------------------------


def test_order_none_keeps_name_order(photo_dir, make_jpeg, captured):
    for name in ["10_산.jpg", "2_바다.jpg", "1_집.jpg"]:
        make_jpeg(name)
    make_album.build_album(photo_dir)
    assert [n for n, _ in captured] == ["1_집.jpg", "2_바다.jpg", "10_산.jpg"]


def test_order_is_followed_with_new_files_last(photo_dir, make_jpeg, captured):
    for name in ["1_집.jpg", "2_바다.jpg", "3_숲.jpg", "5_새.jpg", "4_새.jpg"]:
        make_jpeg(name)
    order = ["3_숲.jpg", "지워짐.jpg", "1_집.jpg", "2_바다.jpg"]
    _, photos, pages, _ = make_album.build_album(photo_dir, order=order)
    assert [n for n, _ in captured] == ["3_숲.jpg", "1_집.jpg", "2_바다.jpg", "4_새.jpg", "5_새.jpg"]
    assert (photos, pages) == (5, 3)


def test_strip_number_choice(photo_dir, make_jpeg, captured):
    make_jpeg("1_집.jpg")
    make_album.build_album(photo_dir, strip_number=False)
    assert captured == [("1_집.jpg", "1_집")]
    make_album.build_album(photo_dir)
    assert captured == [("1_집.jpg", "집")]
