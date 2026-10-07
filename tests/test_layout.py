import pytest

from make_album import (
    LABEL_MAX_W,
    LABEL_MIN_W,
    LABEL_OUT_X,
    LABEL_OUT_Y,
    MAX_OVERLAP_RATIO,
    PRINTABLE,
    fit_label,
    fit_photo,
    slot_geometry,
)

EPS = 1e-6


def measure(text, size_pt):
    """Deterministic stand-in for font metrics: every glyph is 0.6em wide."""
    return len(text) * size_pt * 0.6 * 25.4 / 72


SHAPES = {
    "landscape": (4000, 3000),
    "portrait": (3000, 4000),
    "panorama": (4000, 1000),
    "tall": (1000, 4000),
}
CAPTIONS = {
    "short": "집",
    "medium": "벚꽃 축제 모습",
    "long": "가족 모두 함께 바닷가에서 해 질 무렵 찍은 사진, 강아지도 같이 뛰어놀았다",
    "very_long": "아주 " * 60,
}


@pytest.mark.parametrize("position", ["top", "bottom"])
@pytest.mark.parametrize("shape", SHAPES)
def test_photo_fits_box_keeping_aspect_and_centered(position, shape):
    cell, box = slot_geometry(position)
    assert box.w == pytest.approx(cell.w - LABEL_OUT_X)
    assert box.h == pytest.approx(cell.h - LABEL_OUT_Y)
    w, h = SHAPES[shape]
    rect = fit_photo((w, h), box)
    assert rect.w / rect.h == pytest.approx(w / h)
    assert rect.w == pytest.approx(box.w) or rect.h == pytest.approx(box.h)
    assert box.contains(rect)
    assert rect.x - box.x == pytest.approx(box.right - rect.right)
    assert rect.y - box.y == pytest.approx(box.top - rect.top)


@pytest.mark.parametrize("position", ["top", "bottom"])
@pytest.mark.parametrize("shape", SHAPES)
@pytest.mark.parametrize("caption", CAPTIONS)
def test_label_invariants(position, shape, caption):
    _, box = slot_geometry(position)
    photo = fit_photo(SHAPES[shape], box)
    label = fit_label(CAPTIONS[caption], photo, measure)

    assert label is not None
    assert label.rect.right == pytest.approx(photo.right + LABEL_OUT_X)
    assert label.rect.top == pytest.approx(photo.top + LABEL_OUT_Y)
    assert LABEL_MIN_W - EPS <= label.rect.w <= LABEL_MAX_W + EPS
    assert 1 <= len(label.lines) <= 3
    assert PRINTABLE.contains(label.rect)
    assert PRINTABLE.contains(photo)

    overlap = label.rect.intersection_area(photo)
    assert 0 < overlap <= MAX_OVERLAP_RATIO * photo.area + EPS
    assert not photo.contains(label.rect)


def test_long_caption_shrinks_then_truncates():
    _, box = slot_geometry("top")
    photo = fit_photo(SHAPES["landscape"], box)

    medium = fit_label(CAPTIONS["long"], photo, measure)
    assert 8 <= medium.font_size_pt <= 11

    huge = fit_label(CAPTIONS["very_long"], photo, measure)
    assert huge.truncated
    assert huge.font_size_pt == 8
    assert huge.lines[-1].endswith("…")


def test_short_caption_keeps_start_font():
    _, box = slot_geometry("top")
    photo = fit_photo(SHAPES["landscape"], box)
    label = fit_label("집", photo, measure)
    assert label.font_size_pt == 11
    assert label.lines == ["집"]
    assert not label.truncated


def test_empty_caption_has_no_label():
    _, box = slot_geometry("top")
    photo = fit_photo(SHAPES["landscape"], box)
    assert fit_label("", photo, measure) is None


def test_label_wraps_within_max_width():
    _, box = slot_geometry("top")
    photo = fit_photo(SHAPES["landscape"], box)
    label = fit_label(CAPTIONS["long"], photo, measure)
    assert len(label.lines) > 1
    for line in label.lines:
        assert measure(line, label.font_size_pt) <= LABEL_MAX_W
