---

description: "Task list for 사진 목록에 마우스를 올리면 썸네일 보이기"
---

# Tasks: 사진 목록에 마우스를 올리면 썸네일 보이기

**Input**: Design documents from `specs/006-photo-hover-thumbnail/`

**Prerequisites**: plan.md, spec.md, research.md, contracts/gui.md, quickstart.md

**Tests**: 포함. quickstart.md가 `tests/test_app.py`의 006 테스트를 검증 수단으로 정한다. 기존 테스트는 모두 계속 통과해야 한다(FR-007).

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup / Phase 2: Foundational

새 의존성·새 파일이 없어 작업이 없다.

## Phase 3: User Story 1 - 파일 이름 위에서 사진 미리 보기 (P1) 🎯 MVP

**Goal**: 이름 위에 0.4초 머물면 바른 방향의 미리보기가 뜨고, 나가면 닫힌다.

**Independent Test**: quickstart "손으로 확인" 2~5단계, `pytest tests/test_app.py`

### Tests

- [X] T001 [P] [US1] In `tests/test_app.py` test `album_app.make_thumbnail(path, size)`: long side ≤ size with the ratio kept; EXIF orientation 6 on a landscape JPEG gives a portrait thumbnail; a broken file raises; the photo file bytes are unchanged (FR-006)
- [X] T002 [P] [US1] In `tests/test_app.py` test the window: entering a name label then waiting shows one preview with an image; leaving closes it; leaving before the delay opens nothing and starts no decoding; a broken file shows `미리보기를 볼 수 없습니다`; a second hover uses the cache (no second `make_thumbnail` call); `load_photos` empties the cache; starting a rename closes the preview

### Implementation

- [X] T003 [US1] In `scripts/album_app.py` add `make_thumbnail(path, size)` (`Image.open`, `draft("RGB", (size, size))`, `ImageOps.exif_transpose`, `thumbnail((size, size))`, return a loaded copy) per research R3
- [X] T004 [US1] In `scripts/album_app.py` give `PhotoList` a `photo_path(index)` callback, a thumbnail cache, `<Enter>`/`<Leave>`/`<ButtonPress>` on name labels, a 0.4 s `after` that calls `_request(index)`, a daemon-thread decode with results through a `queue.Queue` polled by `after` (research R1), and a borderless `Toplevel` preview placed at the pointer +20 and kept on screen (research R2, contracts/gui.md)
- [X] T005 [US1] In `scripts/album_app.py` close the preview on wheel scroll, on `edit()`, and in `show()`; in `AlbumApp` pass `photo_path` and clear the cache in `load_photos` (research R4)

**Checkpoint**: US1 tests pass; all earlier tests pass

## Phase 4: Polish

- [X] T006 [P] Add one line about the hover preview to step 3 of `README.md` and `README.ko.md`
- [X] T007 Run `.venv\Scripts\python -m pytest` and the manual checks in `quickstart.md` (screenshot of a preview)

## Dependencies & Execution Order

- T001, T002 (tests) → T003 → T004 → T005 → T006, T007
- T001 and T002 touch only `tests/test_app.py`; T006 only the READMEs.

## Parallel Example: User Story 1

```text
T001 and T002 can be written together (same test file, independent tests).
T006 can be done any time after T005.
```

## Implementation Strategy

US1 is the whole feature and the MVP: implement T003–T005, verify with the tests and one screenshot, then T006.
