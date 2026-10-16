---

description: "Task list for 앨범 창에서 사진 순서 정하기와 '숫자_' 빼기 선택"
---

# Tasks: 앨범 창에서 사진 순서 정하기와 "숫자_" 빼기 선택

**Input**: Design documents from `specs/003-photo-order-list/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: 포함. quickstart.md가 `tests/test_order.py`와 `tests/test_app.py`의 003 테스트를 검증 수단으로 정의한다. 기존 001·002 테스트는 모두 계속 통과해야 한다(FR-011, FR-012).

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

새 의존성·새 파일 구조가 없어 Setup 작업은 없다.

---

## Phase 2: Foundational

- [X] T001 In `scripts/make_album.py` move the file filter of `scan_folder` (is file, not `_is_hidden`, RAW / HEIC-without-pillow-heif → `UNSUPPORTED_FORMAT` warning, ext in `PHOTO_EXTS`) into one helper `_photo_entries(folder)` yielding `(entry, warning_or_None)` so that `scan_folder` and the new `list_photo_files` share it; `scan_folder` output and warnings must stay identical (research R1)

**Checkpoint**: `pytest` passes unchanged

---

## Phase 3: User Story 1 - 사진 목록을 보고 정렬 방식 고르기 (P1) 🎯 MVP

**Goal**: 폴더를 고르면 사진 목록이 보이고, 이름/만든 날짜/수정한 날짜 정렬과 역순을 고를 수 있으며, PDF가 목록 순서대로 만들어진다

**Independent Test**: quickstart "손으로 확인" 1~2단계, `pytest tests/test_order.py tests/test_app.py`

### Tests for User Story 1

- [X] T002 [P] [US1] Create `tests/test_order.py`: `list_photo_files` returns only album candidates (skips hidden file, `Thumbs.db`, `.txt`, `.cr2`; includes a broken `.jpg`) as `PhotoFile(name, created, modified)`; returns `[]` for a missing folder
- [X] T003 [P] [US1] In `tests/test_order.py` test `album_app.sort_photos(photos, mode, reverse)` for the three modes using `os.utime` for modified dates and hand-made `PhotoFile` values for created dates: name mode equals `natural_key` order (`2_` before `10_`), date ties fall back to name order, `reverse=True` is the exact reversal
- [X] T004 [P] [US1] In `tests/test_order.py` test `build_album(order=[...])`: page order follows `order`; names missing from the folder are ignored; files not in `order` are appended in `natural_key` order; `order=None` keeps the old order (capture the ordered items by monkeypatching `make_album.layout_pages` with a wrapper that records `[i.file_name for i in items]`)
- [X] T005 [P] [US1] In `tests/test_app.py` add tests: choosing a folder fills `app.photos` in name order and `app.sort_mode.get() == "이름 순 정렬"`, `app.reverse.get() is False`; selecting `"수정한 날짜 순 정렬"` and toggling reverse reorders; a non-folder path empties the list; `start()` passes `order=[p.name for p in app.photos]` to `build_album` (monkeypatch)

### Implementation for User Story 1

- [X] T006 [US1] In `scripts/make_album.py` add `@dataclass(frozen=True) class PhotoFile(name: str, created: float, modified: float)` and `list_photo_files(folder) -> list[PhotoFile]` built on `_photo_entries` (no image opening; `created = st_birthtime` if present else `st_ctime`, `modified = st_mtime`; `[]` when the folder is missing or unreadable) per `contracts/album-api.md`
- [X] T007 [US1] In `scripts/make_album.py` add `order=None` to `build_album(photo_dir, output=None, font=None, order=None, strip_number=True)`: after `scan_folder`, if `order` is given sort items by `(0, index)` for names in `order` else `(1, item.sort_key)`; returns/warnings unchanged (research R5)
- [X] T008 [US1] In `scripts/album_app.py` add module constants `SORT_MODES = ("이름 순 정렬", "만든 날짜 순 정렬", "수정한 날짜 순 정렬")`, `CUSTOM = "커스텀"` and pure `sort_photos(photos, mode, reverse) -> list` (name: `natural_key(name)`; dates: `(date, natural_key(name))`; then reverse the list if `reverse`) (data-model.md)
- [X] T009 [US1] In `scripts/album_app.py` add the "사진 순서" `LabelFrame` between the output row and the build buttons: readonly `ttk.Combobox` (`self.sort_mode`, values `SORT_MODES`, default `"이름 순 정렬"`), `ttk.Checkbutton` "역순으로 정렬" (`self.reverse`, default False), and a scrollable list (Canvas + inner Frame + vertical Scrollbar, mouse-wheel scrolling while the pointer is over the list); each row = `"{n}  {name}"` label; rows are rebuilt only when the photo count changes, otherwise only label texts change; show `사진이 없습니다.` when a folder is set but has no photos (research R3, contracts/gui.md)
- [X] T010 [US1] In `scripts/album_app.py` reload `self.photos = list_photo_files(folder)` whenever `photo_dir` changes (existing trace), empty when not a directory; `<<ComboboxSelected>>` and reverse toggle re-sort via `sort_photos`; `start()` passes `order=[p.name for p in self.photos]` to `_run`/`build_album` (extend `_run(photo_dir, output, order=None, strip_number=True)`)
- [X] T011 [US1] In `scripts/album_app.py` enlarge the window (initial ≈760×680, min ≈560×520, scaled by zoom), give the list frame the growing row and shrink the result log to `height=6` (research R7)

**Checkpoint**: US1 tests pass; 001/002 tests pass

---

## Phase 4: User Story 2 - 사진 하나하나 순서 옮기기 (P2)

**Goal**: 줄마다 [맨 위로] [▲] [▼] [맨 아래로] 버튼으로 옮기고, 누르면 정렬 표시가 "커스텀"이 된다

**Independent Test**: quickstart "손으로 확인" 3단계, `pytest tests/test_app.py`

### Tests for User Story 2

- [X] T012 [P] [US2] In `tests/test_app.py` add tests with 4 photos [A,B,C,D]: `app.move(2, "up")` → [A,C,B,D]; `move(1,"down")` → [A,C,B,D]; `move(2,"top")` → [C,A,B,D]; `move(1,"bottom")` → [A,C,D,B]; no-op at the edges keeps order; after any move `sort_mode.get() == "커스텀"` and the reverse checkbox is disabled; selecting a sort mode afterwards re-sorts and re-enables reverse; changing folder while custom resets to `"이름 순 정렬"`; `start()` after moves passes the custom order

### Implementation for User Story 2

- [X] T013 [US2] In `scripts/album_app.py` add `move(index, where)` with `where in ("top", "up", "down", "bottom")`: move the item in `self.photos`, refresh labels, set `self.sort_mode` to `CUSTOM` and disable the reverse checkbox even when nothing moved (data-model.md state transitions); add the four `ttk.Button`s `맨 위로 ▲ ▼ 맨 아래로` to each row calling `move(row_index, …)`
- [X] T014 [US2] In `scripts/album_app.py` make `<<ComboboxSelected>>` re-enable the reverse checkbox, and make a folder change while `CUSTOM` reset `sort_mode` to `"이름 순 정렬"` before sorting (FR-008, spec Edge Cases)

**Checkpoint**: US1+US2 tests pass

---

## Phase 5: User Story 3 - "숫자_"를 뺄지 직접 고르기 (P3)

**Goal**: 체크했을 때만 라벨에서 맨 앞 "숫자_"를 뺀다(기본 해제). CLI는 그대로

**Independent Test**: quickstart "손으로 확인" 4~5단계, `pytest tests/test_naming.py tests/test_app.py`

### Tests for User Story 3

- [X] T015 [P] [US3] In `tests/test_naming.py` add `extract_caption("283_벚꽃 축제 모습.jpg", strip_number=False) == "283_벚꽃 축제 모습"` and that the default still strips
- [X] T016 [P] [US3] In `tests/test_app.py` add tests: `app.strip_number.get() is False` by default; `start()` passes `strip_number=False`/`True` to `build_album` following the checkbox (monkeypatch); in `tests/test_order.py` `build_album(strip_number=False)` keeps `1_집` as the caption (check via captured items)

### Implementation for User Story 3

- [X] T017 [US3] In `scripts/make_album.py` add `strip_number=True` to `extract_caption(file_name, strip_number=True)`, `scan_folder(folder, work_dir, strip_number=True)` and pass it from `build_album(..., strip_number=True)` (contracts/album-api.md)
- [X] T018 [US3] In `scripts/album_app.py` add `ttk.Checkbutton` "파일 이름 앞 '숫자_' 빼고 메모 라벨 넣기" (`self.strip_number = tk.BooleanVar(value=False)`) above the build buttons and pass its value from `start()` to `_run` → `build_album(strip_number=…)`

**Checkpoint**: all tests pass

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T019 [P] Update `README.md` window usage: the photo order list, sort modes, reverse, 맨 위로/▲/▼/맨 아래로 buttons, "커스텀", and the "숫자_" checkbox (default off)
- [X] T020 [P] Update module docstrings in `scripts/album_app.py` and `scripts/make_album.py` (`make_album` docstring: ordering/caption rules are the CLI defaults; the window can change them)
- [X] T021 Run `.venv\Scripts\python.exe -m pytest` (all green), time `list_photo_files` + `sort_photos` on a 300-file folder (must be < 2 s, SC-001), then launch `scripts/album_app.py` on a sample folder and check quickstart steps 1–5
- [X] T022 Rebuild with `powershell -ExecutionPolicy Bypass -File build_portable.ps1` so `앨범 만들기.exe` and `app\` include the change; smoke test must pass
- [X] T023 Refresh `docs/app-window.png` with a screenshot of the new window if possible

---

## Dependencies & Execution Order

- Phase 2 (T001) → US1 (T006 needs `_photo_entries`)
- US1 → US2 (move needs the list rows and `self.photos`)
- US3 is independent of US1/US2 for `make_album.py` (T017), but T018 edits the same `start()` as T010 → do after T010
- Polish after all stories; T022 after T021

## Parallel Example

```text
# US1 tests together (different test targets, same new file written in one pass):
T002, T003, T004 → tests/test_order.py ; T005 → tests/test_app.py
# US3 tests:
T015 (tests/test_naming.py) ∥ T016 (tests/test_app.py, tests/test_order.py)
```

## Implementation Strategy

1. MVP = Phase 2 + US1: 목록·정렬·역순·목록 순서대로 PDF
2. US2: 옮기기 버튼과 "커스텀"
3. US3: "숫자_" 체크박스
4. Polish: README, 테스트 전체, exe 재빌드

---

## Phase 7: Convergence

- [X] T024 Scroll the photo list back to the top whenever `AlbumApp.load_photos` reloads a folder (e.g. `PhotoList.canvas.yview_moveto(0)`), and add a `tests/test_app.py` test that scrolls a long list down, switches to a short folder and expects `canvas.canvasy(0) == 0`, per spec Edge Cases "다른 폴더를 고르면 목록은 새 폴더로 바뀌고" / FR-001 (partial)

## Phase 8: Convergence

- [X] T025 Rebuild `앨범 만들기.exe` and `app\` with `build_portable.ps1` from the final `scripts/album_app.py` (window height cap and T024 are newer than the bundled exe), per plan: "build_portable.ps1로 exe와 app\을 다시 만든다" / T022 (partial)
