---

description: "Task list for 앨범 창에서 사진 파일 이름 바꾸기"
---

# Tasks: 앨범 창에서 사진 파일 이름 바꾸기

**Input**: Design documents from `specs/005-rename-photo-files/`

**Tests**: 포함. 기존 테스트는 모두 계속 통과해야 한다(FR-007).

## Phase 1: Setup / Phase 2: Foundational

새 의존성·새 파일 구조가 없어 작업이 없다.

## Phase 3: User Story 1 - 목록에서 파일 이름 바로 바꾸기 (P1) 🎯 MVP

### Tests

- [X] T001 [P] [US1] In `tests/test_app.py` test `album_app.rename_photo`: keeps the extension, strips spaces, `None` for empty/same name, `ValueError` for `/` and other forbidden characters, `FileExistsError` without overwriting, case-only change works
- [X] T002 [P] [US1] In `tests/test_app.py` test the window: double-click opens an entry with the stem selected; Return renames the file and the list; Escape cancels; name sort re-sorts; custom keeps the position; an existing name shows the error in the result log; nothing opens while busy

### Implementation

- [X] T003 [US1] In `scripts/album_app.py` add `rename_photo(folder, name, new_stem)` (research R2, R3)
- [X] T004 [US1] In `scripts/album_app.py` give `PhotoList` an `on_rename` callback, `<Double-Button-1>` on name labels, and `edit(index)` that grids a `ttk.Entry` over the label (Return/FocusOut commit once, Escape cancels)
- [X] T005 [US1] In `scripts/album_app.py` add `AlbumApp.rename(index, text)` (ignored while busy; `PhotoList.locked` blocks opening, `start()` commits an open edit first) plus the hint label under the sort bar (contracts/gui.md)

### Change request: 순번을 가리지 않는 입력 칸

- [X] T008 [US1] In `tests/test_app.py` check that the entry's left `padx` equals the label font's width of the row number part, so the number stays visible
- [X] T009 [US1] In `scripts/album_app.py` `PhotoList.edit` grid the entry with `padx=(width of the number part, 0)` (research R1a)

## Phase 4: Polish

- [X] T006 [P] Add one line about renaming to step 3 of `README.md` and `README.ko.md`
- [X] T007 Run `python -m pytest`
