# Data Model: A4 사진 앨범 페이지 만들기

**Feature**: [spec.md](spec.md) | **Research**: [research.md](research.md)

저장소(DB)는 없다. 모든 데이터는 한 번 실행하는 동안 메모리에만 있고, 입력은 사진 폴더, 출력은 PDF 1개다. 길이 단위는 mm이고 원점은 페이지 왼쪽 아래(PDF 좌표계)다.

## PhotoItem (사진 항목)

폴더 안의 사진 파일 1개에 해당한다.

| Field | Type | 설명 / 규칙 |
|-------|------|-------------|
| `path` | Path | PDF에 넣을 파일 경로. 원본은 읽기 전용이다(FR-002a). JPEG·MPO·PNG가 아니면 임시 폴더의 변환본(JPEG 또는 PNG)이다(FR-014). |
| `file_name` | str | 확장자를 포함한 파일 이름. 경고 메시지에 쓴다. |
| `caption` | str | 설명. stem에서 `^\d+_`를 한 번 떼고 앞뒤 공백을 지운 값이다(FR-001a, R6). 빈 문자열일 수 있다. |
| `sort_key` | tuple | stem의 자연 정렬 키(R6). |
| `kind` | `"jpeg"` \| `"png"` | 넣는 파일의 실제 형식. MPO는 `jpeg`로 본다. |
| `pixel_size` | (int, int) | 원본 픽셀 가로·세로. |
| `orientation` | int 1–8 | EXIF Orientation. 없으면 1이다. |
| `display_size` | (int, int) | 회전 후 표시 기준 가로·세로. orientation이 5–8이면 `pixel_size`의 가로·세로를 바꾼다. |

**검증 규칙**

- 열기·검사에 실패하면 PhotoItem을 만들지 않고 `AlbumWarning(UNREADABLE)`을 낸다.
- `caption == ""`이면 PhotoItem은 유지하고 라벨 없이 배치하며 `AlbumWarning(EMPTY_CAPTION)`을 낸다.
- `len(caption) > 60`이면 `AlbumWarning(LONG_CAPTION)`을 낸다. 라벨에 다 안 들어가 잘렸으면 `AlbumWarning(CAPTION_TRUNCATED)`도 낸다.

## Slot (사진 칸)

| Field | Type | 설명 |
|-------|------|------|
| `position` | `"top"` \| `"bottom"` | 페이지 안의 위치. |
| `cell` | Rect | 칸 전체. top은 (10, 153.5, 190, 133.5), bottom은 (10, 10, 190, 133.5)이다. |
| `photo_box` | Rect | 사진이 들어갈 수 있는 상자. `cell`에서 오른쪽 10mm, 위쪽 5mm를 뺀 180×128.5다(R5). |
| `photo_rect` | Rect | 실제 사진 위치. `display_size` 비율을 유지해 `photo_box` 안에 최대로 맞추고 가운데 정렬한다(FR-006). |
| `label` | Label \| None | caption이 비었으면 None. |

## Label (메모 라벨)

| Field | Type | 설명 |
|-------|------|------|
| `lines` | list[str] | 줄바꿈된 텍스트. 1–3줄이다. |
| `font_size_pt` | float | 11에서 시작해 최소 8까지 줄인다. |
| `rect` | Rect | 오른쪽 위 꼭짓점 = `photo_rect` 오른쪽 위 + (10, 5). 너비는 30–64mm다. |
| `truncated` | bool | "…"로 잘렸는지 여부. |

**불변식**

- `rect`는 페이지 인쇄 가능 영역(10–200 × 10–287) 안에 있다(FR-007, SC-004).
- `area(rect ∩ photo_rect) ≤ 0.15 × area(photo_rect)`다(FR-005).
- `rect`는 `photo_rect`와 겹치되 완전히 포함되지는 않는다. 즉 "일부만 겹침"이다.

## AlbumPage (앨범 페이지)

| Field | Type | 설명 |
|-------|------|------|
| `number` | int | 1부터 시작한다. |
| `top` | Slot | 항상 있다. |
| `bottom` | Slot \| None | 사진 수가 홀수인 마지막 페이지에서는 None이다(FR-008). |

## AlbumPdf (앨범 PDF)

| Field | Type | 설명 |
|-------|------|------|
| `output_path` | Path | 기본값은 `<폴더 부모>/<폴더이름>_album.pdf`다(R8). |
| `pages` | list[AlbumPage] | 길이는 ⌈N/2⌉이다(SC-001). N은 유효한 PhotoItem 수다. |
| `warnings` | list[AlbumWarning] | |

## AlbumWarning (경고)

| Field | Type | 설명 |
|-------|------|------|
| `code` | enum | `UNREADABLE`, `UNSUPPORTED_FORMAT`, `CONVERTED`(알림, 경고 건수 제외), `EMPTY_CAPTION`, `LONG_CAPTION`, `CAPTION_TRUNCATED`, `LOW_RESOLUTION`, `MISSING_GLYPH` |
| `file_name` | str | 문제가 된 파일 이름(SC-006). |
| `message` | str | 한국어 설명. |

## 처리 흐름 (상태 전이)

```text
폴더 스캔 → 후보 파일 → [형식/열기 검사] → PhotoItem (실패 시 Warning, 제외)
→ 자연 정렬 → 2개씩 묶어 AlbumPage → Slot·Label 배치 계산 → PDF 쓰기 → 결과 보고
```

유효한 PhotoItem이 0개면 PDF를 만들지 않고 종료한다(Edge Case, exit 1).
