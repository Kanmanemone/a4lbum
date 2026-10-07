"""Helpers for build_portable.ps1 (kept in Python to avoid PowerShell quoting issues).

    python packaging/build_helpers.py samples <PHOTO_DIR>
"""

import sys
from pathlib import Path

from PIL import Image


def make_samples(folder):
    """One JPEG, one HEIC and one GIF with Korean names: 3 photos -> 2 pages."""
    import pillow_heif

    pillow_heif.register_heif_opener()
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    photo = Image.merge("RGB", [Image.effect_noise((1600, 1200), 60),
                                Image.linear_gradient("L").resize((1600, 1200)),
                                Image.effect_noise((1600, 1200), 30)])
    photo.save(folder / "1_첫 사진.jpg", quality=90)
    photo.save(folder / "2_아이폰 사진.heic", "HEIF")
    graphic = Image.new("RGB", (1600, 1200), "white")
    graphic.paste((230, 60, 60), (200, 200, 800, 800))
    graphic.save(folder / "3_그림.gif")


if __name__ == "__main__":
    command, *args = sys.argv[1:]
    {"samples": make_samples}[command](*args)
