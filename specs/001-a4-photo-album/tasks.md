---

description: "Task list for A4 사진 앨범 페이지 만들기"
---

# Tasks: A4 사진 앨범 페이지 만들기

**Input**: Design documents from `specs/001-a4-photo-album/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: 포함. plan.md의 Project Structure와 quickstart.md §1이 pytest 테스트(`tests/`)를 산출물로 정의했다.

**Organization**: 사용자 스토리별로 묶었다. 본체가 `scripts/make_album.py` 한 파일이라, 같은 파일을 고치는 작업은 [P]를 붙이지 않았다.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 병렬 가능(다른 파일, 미완료 작업 의존 없음)
- **[Story]**: US1 / US2 / US3

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 의존성 선언과 폴더 구조

- [X] T001 Create `requirements.txt` at repo root with `reportlab>=4.0` and `Pillow>=10.0`, and `requirements-dev.txt` with `-r requirements.txt`, `pytest>=8`, `PyMuPDF>=1.24` (research.md 의존성 요약)
- [X] T002 [P] Create empty dirs/files `scripts/make_album.py` (module docstring only) and `tests/__init__.py`-free layout: `tests/conftest.py` placeholder; add `pytest.ini` (or `[tool.pytest.ini_options]` in `pyproject.toml`) setting `testpaths = tests` and `pythonpath = scripts` so tests can `import make_album`
- [X] T003 [P] Add Python artifacts (`__pycache__/`, `.pytest_cache/`, `*_album.pdf`) to `.gitignore`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 모든 스토리가 쓰는 상수·데이터 구조·테스트 fixture

- [X] T004 In `scripts/make_album.py` define layout constants in mm (data-model.md / research.md R5): `PAGE_W=210`, `PAGE_H=297`, `MARGIN=10`, `GAP=10`, `CELL_H=133.5`, `LABEL_OUT_X=10`, `LABEL_OUT_Y=5`, `LABEL_MIN_W=30`, `LABEL_MAX_W=64`, `FONT_START_PT=11`, `FONT_MIN_PT=8`, `MAX_LINES=3`, `MAX_CAPTION_CHARS=60`, `MAX_OVERLAP_RATIO=0.15`, `LOW_DPI=150`, label colors `#FFF4A8` fill / gray border / 1mm shadow; and set `reportlab.rl_config.useA85 = 0` before canvas creation (research.md R2)
- [X] T005 In `scripts/make_album.py` define dataclasses `Rect(x, y, w, h)` with `right`, `top`, `area`, `intersection_area(other)`, `contains(other)`; `PhotoItem(path, file_name, caption, sort_key, kind, pixel_size, orientation, display_size)`; `Label(lines, font_size_pt, rect, truncated)`; `Slot(position, cell, photo_box, photo_rect, label)`; `AlbumPage(number, top, bottom)`; `AlbumWarning(code, file_name, message)` with codes `UNREADABLE, UNSUPPORTED_FORMAT, EMPTY_CAPTION, LONG_CAPTION, CAPTION_TRUNCATED, LOW_RESOLUTION, MISSING_GLYPH` (data-model.md)
- [X] T006 [P] In `tests/conftest.py` add fixtures that build test photos with Pillow into `tmp_path`: `make_jpeg(name, size=(1200, 900), orientation=None)` writing EXIF Orientation tag 0x0112 when given; `make_png(name, size, alpha=True)`; `make_broken(name)` writing non-image bytes with `.jpg` extension; and `sha256(path)` helper

**Checkpoint**: 상수·모델·fixture 준비 완료

---

## Phase 3: User Story 1 - 사진과 설명으로 인쇄용 앨범 페이지 만들기 (Priority: P1) 🎯 MVP

**Goal**: 사진 폴더 → 파일 이름순, 페이지당 위·아래 2장, 오른쪽 위 메모 라벨, 원본 화질 그대로인 A4 PDF

**Independent Test**: "숫자_설명" 이름 사진 4장 폴더로 실행 → A4 2페이지, 각 사진에 설명 라벨, JPEG 바이트 보존

### Tests for User Story 1 ⚠️

> 먼저 작성하고 실패를 확인한 뒤 구현한다.

- [X] T007 [P] [US1] In `tests/test_naming.py` test `extract_caption`: `"283_벚꽃 축제 모습.jpg"→"벚꽃 축제 모습"`, `"3_엄마_아빠.jpg"→"엄마_아빠"` (only leading `^\d+_` removed once), `"벚꽃.jpg"→"벚꽃"`, `"7_.jpg"→""`, surrounding spaces trimmed; test `natural_key` ordering `["10_산.jpg","2_바다.jpg","1_집.jpg"]` → `1_집, 2_바다, 10_산`, same number sorts by following text, non-numbered names sort after numbered ones (FR-001a, FR-004, research.md R6)
- [X] T008 [P] [US1] In `tests/test_layout.py` test `layout_page` / `fit_label` invariants for landscape 4:3, portrait 3:4, extreme panorama 4:1 and tall 1:4 photos, in both top and bottom slots, with 1-, 2- and 3-line captions: photo aspect preserved and centered in `photo_box` = cell minus right 10mm / top 5mm (FR-006); label top-right = photo top-right + (10, 5); label width within 30–64mm; label and photo inside printable area 10–200 × 10–287 (FR-007); `0 < overlap ≤ 0.15 × photo area` and label not fully inside photo (FR-005); long caption shrinks font to ≥8pt then truncates with "…" and sets `truncated`
- [X] T009 [P] [US1] In `tests/test_cli.py` end-to-end test calling `make_album.main([folder, "-o", out])`: 4 JPEGs → 2 pages each 210×297mm (±0.5mm) via PyMuPDF; 3 photos → 2 pages with page 2 holding one image (FR-008, SC-001); order of images follows natural sort; label texts extracted from page match captions (`"벚꽃 축제 모습"` without `283_`/`.jpg`); every embedded JPEG stream (`doc.xref_stream_raw`) equals the original file bytes and original files' sha256 unchanged and no new files appear in the photo folder (SC-007, FR-002a); default output path is `<parent>/<folder>_album.pdf`; EXIF orientation 6 photo of pixel size 1200×900 is placed with a portrait-shaped image rect (FR-013); PNG with alpha is embedded

### Implementation for User Story 1

- [X] T010 [US1] In `scripts/make_album.py` implement `extract_caption(file_name) -> str` (strip extension, remove leading `^\d+_` once, trim) and `natural_key(file_name) -> tuple` (split stem by `(\d+)`, ints for digit runs, `casefold()` text, tie-break by original name) (research.md R6)
- [X] T011 [US1] In `scripts/make_album.py` implement `scan_folder(folder) -> (list[PhotoItem], list[Warning])`: only direct children; accept `.jpg/.jpeg/.png` case-insensitive; silently ignore other files, names starting with `.`, `Thumbs.db`, `desktop.ini`; open with Pillow and `verify()`, then reopen to read `pixel_size`, real format (`kind` follows actual format, not extension), and EXIF Orientation 0x0112 (default 1; values 5–8 swap `display_size`); sort by `natural_key` (research.md R7, data-model.md PhotoItem)
- [X] T012 [US1] In `scripts/make_album.py` implement `slot_geometry(position) -> (cell, photo_box)` (top cell `(10, 153.5, 190, 133.5)`, bottom cell `(10, 10, 190, 133.5)`, photo_box = cell minus right 10 / top 5 → 180×128.5) and `fit_photo(display_size, photo_box) -> Rect` (max size keeping aspect, centered)
- [X] T013 [US1] In `scripts/make_album.py` implement `fit_label(caption, photo_rect, measure) -> Label | None` where `measure(text, size_pt)` returns width in mm: return None for empty caption; start at 11pt, wrap by character into ≤3 lines within `LABEL_MAX_W` minus padding; if it does not fit reduce 1pt down to 8pt; then truncate last line with "…" (`truncated=True`); width = clamp(text width + padding, 30, 64); place top-right corner at photo top-right + (10, 5); while overlap > 15% of photo area reduce font, then lines (FR-005, research.md R5)
- [X] T014 [US1] In `scripts/make_album.py` implement `layout_pages(items, measure) -> list[AlbumPage]`: pair items in order into pages (top, bottom), bottom None for odd last item (FR-003, FR-008)
- [X] T015 [US1] In `scripts/make_album.py` implement fonts: register `C:\Windows\Fonts\malgun.ttf` (or `--font` path) as primary, `seguiemj.ttf` and `seguisym.ttf` as fallbacks when present; provide `measure()` and a `draw_text_runs()` that splits text into runs by first font containing each glyph (check via the TTF cmap); collect `MISSING_GLYPH` warning when no font has a glyph (research.md R3, FR-012)
- [X] T016 [US1] In `scripts/make_album.py` implement `render_pdf(pages, out_path, fonts)` with reportlab canvas (A4, mm→pt): draw each photo by **file path** with `drawImage` (PNG with `mask="auto"`) applying EXIF orientation 2–8 via `translate/rotate/scale` transforms only (no pixel re-encoding, research.md R4); draw label shadow, `#FFF4A8` fill, gray border, then text lines; write to `out_path`
- [X] T017 [US1] In `scripts/make_album.py` implement `main(argv=None) -> int` with argparse per contracts/cli.md (`PHOTO_DIR`, `-o/--output`, `--font`); default output `<PHOTO_DIR parent>/<PHOTO_DIR name>_album.pdf`; run scan → layout → render; print to stdout `완료: 사진 N장 → P페이지, 경고 W건` and `PDF: <absolute path>`; force UTF-8 stdout (`sys.stdout.reconfigure(encoding="utf-8")`); `if __name__ == "__main__": sys.exit(main())`

**Checkpoint**: T007–T009 통과. US1만으로 앨범 PDF를 만들 수 있다.

---

## Phase 4: User Story 2 - 복잡한 설치 없이 간단히 실행하기 (Priority: P2)

**Goal**: 스크립트 명령 1개 또는 Claude `/album` 지시 1개로 같은 PDF 생성

**Independent Test**: 터미널에서 `python scripts/make_album.py <폴더>` 실행, Claude에서 `/album <폴더>` 실행 → 같은 결과

### Tests for User Story 2 ⚠️

- [X] T018 [P] [US2] In `tests/test_cli.py` add test running the script as a subprocess (`[sys.executable, "scripts/make_album.py", folder]`) asserting exit code 0, last stdout lines match `^완료: 사진 \d+장 → \d+페이지, 경고 \d+건$` and `^PDF: ` + existing absolute path; and test that re-running after renaming one photo overwrites the PDF and the new caption appears (US2 scenario 2)

### Implementation for User Story 2

- [X] T019 [P] [US2] Create `.claude/skills/album/SKILL.md` per contracts/album-command.md: frontmatter `name: album`, description (Korean+English), `argument-hint: <사진 폴더>`; steps: ask for folder if missing, check `python -c "import reportlab, PIL"` and offer `pip install -r requirements.txt`, run `python scripts/make_album.py "<PHOTO_DIR>" [-o ...]`, relay PDF path, page count, warnings verbatim, remind "실제 크기(100%)" printing; prohibitions: never alter layout/captions outside the script, never rename/move photos unless explicitly asked
- [X] T020 [P] [US2] Create `README.md` (Korean) at repo root: 사진 이름 규칙(`숫자_설명.jpg`, 정렬·설명 추출 예시), 준비(`pip install -r requirements.txt`), 실행 두 가지(스크립트 / `/album`), 출력 위치, 인쇄 설정(A4, 실제 크기 100%), HEIC는 JPEG로 내보내기, 경고 목록 의미

**Checkpoint**: US1 + US2 동작

---

## Phase 5: User Story 3 - 입력 문제를 알아차리기 (Priority: P3)

**Goal**: 문제 사진을 파일 이름과 함께 알리고 나머지로 PDF 완성

**Independent Test**: 깨진 파일 + "7_.jpg" 섞어 실행 → 두 경고 모두 파일 이름 포함, PDF 생성

### Tests for User Story 3 ⚠️

- [X] T021 [P] [US3] In `tests/test_cli.py` add tests: broken `.jpg` → stdout line `경고: broken.jpg — ...` and PDF built from remaining photos (FR-009, FR-010); `7_.jpg` → `EMPTY_CAPTION` warning and image placed without label; `.heic` file → `UNSUPPORTED_FORMAT` warning; caption > 60 chars → `LONG_CAPTION` warning; 100×75 px JPEG → `LOW_RESOLUTION` warning; folder with zero valid photos → exit 1, stderr `오류: ...`, no PDF; nonexistent folder → exit 1; `notes.txt`/`desktop.ini` produce no warning (SC-006)

### Implementation for User Story 3

- [X] T022 [US3] In `scripts/make_album.py` emit warnings in `scan_folder`/layout: `UNREADABLE` (open/verify failure, skip), `UNSUPPORTED_FORMAT` for `.heic/.heif/.webp/.gif/.bmp/.tif/.tiff` (skip), `EMPTY_CAPTION` (keep, no label), `LONG_CAPTION` when `len(caption) > 60`, `CAPTION_TRUNCATED` from `fit_label`, `LOW_RESOLUTION` when effective dpi = pixels / (placed mm / 25.4) < 150 on either axis; print each as `경고: <file_name> — <message>` before the summary (contracts/cli.md)
- [X] T023 [US3] In `scripts/make_album.py` `main()` handle fatal errors per contracts/cli.md: missing/not-a-directory folder, zero valid photos ("넣을 사진이 없습니다"), font file missing, output write failure (`PermissionError` → "PDF 뷰어를 닫고 다시 실행해 주세요") → stderr `오류: <내용>`, return 1; argparse errors → 2; never create the PDF when returning 1

**Checkpoint**: 모든 스토리 동작

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T024 [P] In `tests/test_cli.py` add performance test: 20 JPEGs (3000×2000) → PDF in < 60 s (SC-003)
- [X] T025 Run `python -m pytest tests -q` and fix failures; then execute quickstart.md §2 with generated sample photos and visually check the rendered first page (render page to PNG via PyMuPDF and inspect)
- [X] T026 Review `scripts/make_album.py` for dead code and keep it a single readable module (plan.md 단순성 게이트)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** → **Foundational (Phase 2)** → **US1 (Phase 3)** → US2 / US3 → **Polish**
- US2와 US3는 US1의 `main()`을 사용하므로 US1 이후. 서로는 독립(US2는 SKILL.md/README, US3는 경고·오류 처리).

### Within Each User Story

- 테스트(T007–T009, T018, T021) 먼저 작성 → 실패 확인 → 구현
- US1 구현 순서: T010 → T011 → T012 → T013 → T014 → T015 → T016 → T017 (같은 파일, 순차)

### Parallel Opportunities

- T002, T003 (Setup)
- T006 (fixture)와 T004–T005는 다른 파일
- T007, T008, T009 (서로 다른 테스트 파일)
- T019, T020 (SKILL.md, README.md)
- T018, T021, T024는 같은 `tests/test_cli.py`라 순차 권장

---

## Parallel Example: User Story 1

```text
Task: "tests/test_naming.py — extract_caption / natural_key 테스트" (T007)
Task: "tests/test_layout.py — layout/label 기하 불변식 테스트" (T008)
Task: "tests/test_cli.py — 종단 PDF 검사" (T009)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1–2 완료
2. Phase 3 (US1) 완료 → `python scripts/make_album.py <폴더>`로 앨범 PDF 생성 가능
3. **STOP and VALIDATE**: T007–T009 통과, PDF 육안 확인

### Incremental Delivery

1. US1 → MVP
2. US2 → `/album` 바로가기 + README
3. US3 → 경고·오류 처리
4. Polish → 성능 테스트, quickstart 검증

---

## Phase 7: Convergence

- [X] T027 In `scripts/make_album.py` `Fonts.__init__` look up fallback fonts `seguiemj.ttf` / `seguisym.ttf` in the Windows fonts folder (`default_font_path().parent`) instead of the `--font` file's folder, so emoji/symbol fallback survives a custom `--font` per plan: research R3 (partial)
- [X] T028 Update `specs/001-a4-photo-album/contracts/album-command.md` 동작 1 to state the Python selection rule already used by `.claude/skills/album/SKILL.md` (repo `.venv\Scripts\python.exe` if present, else `python`) per contracts/album-command.md (unrequested)
---

## Phase 8: Change Request (2026-10-06)

- [X] T029 In `scripts/make_album.py` change label colors to white fill `#FFFFFF` with neutral gray border `#B4B4B4` (shadow unchanged) per spec Clarifications (변경 요청: 라벨 흰색), FR-005
- [X] T030 [P] In `tests/test_naming.py` add cases proving digits without `_` are kept: `2026여행.jpg→2026여행`, `5월 소풍.jpg→5월 소풍`, `2026 가을.jpg→2026 가을`, `123.jpg→123` per FR-001a (behavior already correct)
- [X] T031 Add `pillow-heif>=0.18` to `requirements.txt`; in `scripts/make_album.py` register the HEIF opener when available, convert `.heic/.heif` with `ImageOps.exif_transpose` to quality-95 4:4:4 JPEG inside a `TemporaryDirectory` owned by `build_album`, keep the original file name for captions/warnings, emit `알림: <name> — HEIC를 JPEG(품질 95)로 변환해 넣었습니다. 원본 파일은 그대로입니다.` (code `HEIC_CONVERTED`, not counted in `경고 W건`); without pillow-heif keep the `UNSUPPORTED_FORMAT` warning with an install hint per FR-014
- [X] T032 In `tests/test_cli.py` add HEIC end-to-end test (notice line, summary count, original hash and folder listing unchanged, embedded JPEG 1200×900, caption shown) and switch the unsupported-format case to `.webp` plus an invalid `.heic` → `UNREADABLE` per FR-014, SC-006
- [X] T033 [P] Update README.md, `.claude/skills/album/SKILL.md` (dependency check includes `pillow_heif`), contracts/cli.md (알림 line), contracts/album-command.md, research.md R5/R7, data-model.md, quickstart.md, plan.md for the change request
---

## Phase 9: Change Request 2 (2026-10-06)

- [X] T034 In `scripts/make_album.py` decide by actual image format instead of extension: embed `JPEG`/`MPO`/`PNG` as-is (MPO treated as `jpeg`, fixing phone MPO `.jpg` files being reported unreadable); convert every other readable format among `.heic/.heif/.avif/.webp/.gif/.bmp/.tif/.tiff` (and misnamed files) in the temp folder — first frame, upright via `exif_transpose`, PNG when ≤256 colors or transparent, else JPEG quality 95 4:4:4 — reporting `알림: <name> — <FMT>를 <target>로 변환해 넣었습니다.` (code `CONVERTED`, plus a first-frame note for multi-frame files); warn `UNSUPPORTED_FORMAT` only for camera RAW (`.cr2/.cr3/.nef/.arw/.dng/.orf/.rw2/.raf`) or HEIC without pillow-heif per FR-014, research R7
- [X] T035 In `scripts/make_album.py` print collected warnings before `오류:` when the album cannot be built (e.g. every file unreadable) so the user sees why per SC-006
- [X] T036 In `tests/test_cli.py` add parametrized conversion tests (WEBP/BMP/TIFF/AVIF photo → JPEG, GIF/BMP graphic and transparent WEBP → PNG, animated GIF first-frame note, WEBP misnamed `.jpg`), MPO embedded without conversion, warnings printed on fatal error; switch the unsupported case to RAW `.CR2` per FR-014, SC-006
- [X] T037 [P] Record the JPEG-vs-PNG benchmark in research.md R7 and update spec, plan, data-model, contracts/cli.md, quickstart.md, README.md, SKILL.md
