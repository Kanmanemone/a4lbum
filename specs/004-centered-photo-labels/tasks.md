# Tasks: 글자에 꼭 맞는 메모 라벨과 페이지 정중앙에 놓이는 사진

**Input**: Design documents from `specs/004-centered-photo-labels/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/layout.md, quickstart.md

**Tests**: 포함한다. plan.md의 Testing과 quickstart.md 1단계가 `tests/test_layout.py`의 새 불변식을 요구한다.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

없음(기존 프로젝트·의존성 그대로).

## Phase 2: Foundational

없음. 두 이야기는 같은 파일(`scripts/make_album.py`)의 서로 다른 함수를 고친다.

---

## Phase 3: User Story 1 - 사진이 종이 좌우 정중앙에 놓인다 (Priority: P1) 🎯 MVP

**Goal**: 사진 자리를 좌우 같은 폭으로 줄이고 위아래는 페이지 가운데 선 대칭으로 해, 라벨이 사진 위치를 밀지 않게 한다.

**Independent Test**: 가로·세로·파노라마 사진으로 `fit_photo(slot_geometry(...))` 결과의 좌우 여백이 같고, 위·아래 칸이 y = 148.5mm 대칭인지 확인한다.

### Tests for User Story 1

- [X] T001 [US1] `tests/test_layout.py`의 `test_photo_fits_box_keeping_aspect_and_centered`를 새 규칙으로 고친다: `box.w == cell.w - 2 * LABEL_OUT_X`, `box.h == cell.h - LABEL_OUT_Y`, 위 칸은 `box.top == cell.top - LABEL_OUT_Y`·`box.y == cell.y`, 아래 칸은 `box.y == cell.y + LABEL_OUT_Y`·`box.top == cell.top`. 사진 좌우 여백(`rect.x` 와 `PAGE_W - rect.right`)이 0.1mm 이하로 같은지 확인을 더한다.
- [X] T002 [US1] `tests/test_layout.py`에 같은 모양 사진의 위·아래 `photo_rect`가 `PAGE_H / 2` 선에 대해 대칭(`top.y - PAGE_H/2 == PAGE_H/2 - bottom.top`)인지 확인하는 테스트를 SHAPES 전체로 더한다.

### Implementation for User Story 1

- [X] T003 [US1] `scripts/make_album.py`의 `slot_geometry(position)`을 고친다: `box = Rect(cell.x + LABEL_OUT_X, cell.y + (0 if top else LABEL_OUT_Y), cell.w - 2 * LABEL_OUT_X, cell.h - LABEL_OUT_Y)` (contracts/layout.md 표: top → 20, 153.5, 170, 128.5 / bottom → 20, 15, 170, 128.5). 모듈 맨 위 독스트링·주석에 "사진은 종이 가운데, 라벨은 그 사진에 붙인다"는 규칙이 드러나게 한 줄 남긴다.

**Checkpoint**: `pytest tests/test_layout.py`의 US1 테스트와 기존 라벨 불변식(인쇄 영역, 15%)이 통과한다.

---

## Phase 4: User Story 2 - 메모 라벨이 글자 길이에 꼭 맞고 글자는 가운데에 (Priority: P2)

**Goal**: 라벨 최소 너비를 10mm로 낮추고, 사진 밖으로 나오는 폭을 `min(LABEL_OUT_X, w / 2)`로, 글자를 줄마다 가운데 정렬한다.

**Independent Test**: "집", "Beach", 여러 줄 설명으로 라벨 너비 = clamp(가장 긴 줄 + 5, 10, 64), 내미는 폭, 줄별 가운데 x를 확인한다.

### Tests for User Story 2

- [X] T004 [US2] `tests/test_layout.py`의 `test_label_invariants`를 고친다: `label.rect.right == photo.right + min(LABEL_OUT_X, label.rect.w / 2)`, 너비 = `min(max(가장 긴 줄 폭 + 2 * LABEL_PAD_X, LABEL_MIN_W), LABEL_MAX_W)`, 라벨과 사진이 가로로 겹치는 폭이 `label.rect.w / 2` 이상. 기존 인쇄 영역·15%·일부만 겹침 확인은 그대로 둔다.
- [X] T005 [US2] `tests/test_layout.py`에 짧은 설명 테스트를 더한다: "Beach"(측정 함수 기준) 라벨 너비가 `글자 폭 + 2 * LABEL_PAD_X`이고 30mm보다 좁다, "집" 라벨 너비는 `LABEL_MIN_W`(10mm)다.
- [X] T006 [US2] `tests/test_layout.py`에 줄 가로 위치 테스트를 더한다: 새 헬퍼 `line_x(label, line, measure)`가 `label.rect.x + (label.rect.w - measure(line, size)) / 2`이고, 여러 줄 라벨에서 줄마다 왼쪽·오른쪽 빈칸이 같다.

### Implementation for User Story 2

- [X] T007 [US2] `scripts/make_album.py`: `LABEL_MIN_W`를 `10.0`으로(주석: 한 줄 라벨 높이 정도), `_build_label`에서 내미는 폭을 `min(LABEL_OUT_X, w / 2)`로 계산해 `Rect(photo.right + out - w, top - h, w, h)`를 만든다. `LABEL_OUT_X` 주석을 "최대"로 고친다.
- [X] T008 [US2] `scripts/make_album.py`: `line_x(label, line, measure)` 헬퍼를 더하고 `_draw_label`에서 줄 시작 x를 `line_x(label, line, fonts.measure) * MM`으로 바꾼다(이모지 대체 글꼴 포함 폭).

**Checkpoint**: `pytest`가 모두 통과한다.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [X] T009 `tests/test_cli.py`·`tests/test_app.py` 등 전체 `pytest`를 돌려 다른 테스트가 배치 변경으로 깨지지 않는지 확인하고, 깨지면 새 규칙에 맞게 고친다.
- [X] T010 quickstart.md 2단계대로 `examples/photos`로 PDF를 만들어 사진 좌우 여백과 라벨 모양을 PDF 좌표(또는 렌더 이미지)로 확인한다.
- [X] T011 README.md·README.ko.md·`.claude/skills/album/SKILL.md`에 라벨 크기·사진 위치를 수치로 적은 곳이 있으면 새 규칙으로 고친다(없으면 그대로).
- [X] T012 `powershell -ExecutionPolicy Bypass -File build_portable.ps1`로 두 exe, `app\`, `examples\photos_album.pdf`를 다시 만든다(실행 중인 exe가 없어야 함).

---

## Dependencies & Execution Order

- US1(T001–T003)과 US2(T004–T008)는 서로 독립이지만 같은 파일을 고치므로 순서대로 한다: T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008.
- Polish(T009–T012)는 두 이야기가 끝난 뒤. T012는 T009 통과 후.

## Parallel Opportunities

- 같은 두 파일만 고치므로 병렬 작업 이점이 없다. T011(문서)만 T009/T010과 병렬 가능.

## Implementation Strategy

1. MVP: US1만으로도 인쇄물의 좌우 쏠림이 사라진다.
2. US2로 라벨 모양을 다듬는다.
3. 테스트·예시 PDF 확인 후 exe를 다시 빌드한다.
