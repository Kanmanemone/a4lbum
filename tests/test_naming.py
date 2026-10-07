import pytest

from make_album import extract_caption, natural_key


@pytest.mark.parametrize(
    "file_name, caption",
    [
        ("283_벚꽃 축제 모습.jpg", "벚꽃 축제 모습"),
        ("3_엄마_아빠.jpg", "엄마_아빠"),
        ("벚꽃.jpg", "벚꽃"),
        ("7_.jpg", ""),
        ("12_  바다 앞에서  .JPEG", "바다 앞에서"),
        ("2026_여행.png", "여행"),
        # Digits without the "_" separator are part of the caption.
        ("2026여행.jpg", "2026여행"),
        ("5월 소풍.jpg", "5월 소풍"),
        ("2026 가을.jpg", "2026 가을"),
        ("123.jpg", "123"),
    ],
)
def test_extract_caption(file_name, caption):
    assert extract_caption(file_name) == caption


def test_numbers_compare_by_value():
    names = ["10_산.jpg", "2_바다.jpg", "1_집.jpg"]
    assert sorted(names, key=natural_key) == ["1_집.jpg", "2_바다.jpg", "10_산.jpg"]


def test_same_number_sorts_by_text():
    names = ["5_하늘.jpg", "5_가을.jpg"]
    assert sorted(names, key=natural_key) == ["5_가을.jpg", "5_하늘.jpg"]


def test_unnumbered_names_come_after_numbered():
    names = ["벚꽃.jpg", "100_끝.jpg", "1_처음.jpg"]
    assert sorted(names, key=natural_key) == ["1_처음.jpg", "100_끝.jpg", "벚꽃.jpg"]


def test_sort_is_case_insensitive_and_deterministic():
    names = ["b.jpg", "A.jpg", "a.jpg"]
    assert sorted(names, key=natural_key) == ["A.jpg", "a.jpg", "b.jpg"]
