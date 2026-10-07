"""Fixtures that build throwaway test photos with Pillow."""

import hashlib

import pytest
from PIL import Image

ORIENTATION_TAG = 0x0112


@pytest.fixture
def photo_dir(tmp_path):
    folder = tmp_path / "2026_여행"
    folder.mkdir()
    return folder


@pytest.fixture
def make_jpeg(photo_dir):
    def _make(name, size=(1200, 900), orientation=None, color=(200, 120, 150), folder=None):
        path = (folder or photo_dir) / name
        img = Image.new("RGB", size, color)
        if orientation is not None:
            exif = Image.Exif()
            exif[ORIENTATION_TAG] = orientation
            img.save(path, "JPEG", quality=90, exif=exif)
        else:
            img.save(path, "JPEG", quality=90)
        return path

    return _make


@pytest.fixture
def make_png(photo_dir):
    def _make(name, size=(800, 1200), alpha=True):
        path = photo_dir / name
        mode, color = ("RGBA", (10, 200, 10, 180)) if alpha else ("RGB", (10, 200, 10))
        Image.new(mode, size, color).save(path, "PNG")
        return path

    return _make


@pytest.fixture
def make_broken(photo_dir):
    def _make(name):
        path = photo_dir / name
        path.write_bytes(b"this is not an image")
        return path

    return _make


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
