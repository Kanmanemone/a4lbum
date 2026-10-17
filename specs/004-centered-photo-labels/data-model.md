# Data Model: 글자에 꼭 맞는 메모 라벨과 페이지 정중앙에 놓이는 사진

새 엔티티는 없다. 기존 `Slot`·`Label`의 값을 정하는 규칙만 바뀐다(수치는 [contracts/layout.md](contracts/layout.md)).

## Slot (변경 없음: 필드)

| 필드 | 바뀐 규칙 |
|------|-----------|
| `cell` | 그대로(인쇄 가능 영역의 위/아래 절반) |
| `photo_box` | 좌우 `LABEL_OUT_X`씩 줄임. 위 칸은 위쪽, 아래 칸은 아래쪽만 `LABEL_OUT_Y` 줄임 |
| `photo_rect` | 그대로 `photo_box` 안 가운데(→ 좌우 중심이 종이 가운데) |

## Label (변경 없음: 필드)

| 필드 | 바뀐 규칙 |
|------|-----------|
| `rect.w` | `clamp(가장 긴 줄 폭 + 2 × LABEL_PAD_X, LABEL_MIN_W = 10, LABEL_MAX_W = 64)` |
| `rect.right` | `photo.right + min(LABEL_OUT_X, rect.w / 2)` |
| `rect.top` | 그대로 `photo.top + LABEL_OUT_Y` |
| `lines` 그리는 위치 | 줄마다 라벨 가로 가운데 |

## 불변식(테스트로 확인)

- `photo_rect` 좌우 여백이 같다(종이 기준, 0.1mm 이하 차이).
- 같은 사진의 위·아래 `photo_rect`는 y = 148.5mm 선에 대해 대칭이다.
- 라벨은 인쇄 가능 영역 안, 사진에 일부만 겹치고 가리는 면적 ≤ 15%, 라벨 너비의 절반 이상이 사진 위.
