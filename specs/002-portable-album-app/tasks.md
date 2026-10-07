---

description: "Task list for 압축만 풀면 쓰는 앨범 프로그램(exe + 대화창)"
---

# Tasks: 압축만 풀면 쓰는 앨범 프로그램(exe + 대화창)

**Input**: Design documents from `specs/002-portable-album-app/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: 포함. quickstart.md §1이 `tests/test_app.py`를 정의하고, 배포물은 빌드 스크립트의 smoke test로 검증한다(FR-010).

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

- [X] T001 [P] Create `requirements-build.txt` with `-r requirements.txt` and `pyinstaller>=6.10`
- [X] T002 [P] Add `.build-venv/`, `build/`, `dist/` to `.gitignore`

---

## Phase 2: Foundational

- [X] T003 In `scripts/make_album.py` extract `default_output_path(folder) -> Path` (`<folder parent>/<folder name>_album.pdf`, folder resolved) and `report_lines(out, photo_count, page_count, warnings) -> list[str]` (notice/warning lines, `완료: 사진 N장 → P페이지, 경고 W건` counting non-notice warnings, `PDF: <out>`); make `build_album` and `main` use them without changing CLI output (research R7)
- [X] T004 [P] In `tests/test_naming.py` or `tests/test_cli.py` add a test that `report_lines` reproduces the CLI stdout lines exactly for a run with a notice and a warning

**Checkpoint**: 001 tests still pass

---

## Phase 3: User Story 1 - 압축 풀고 exe로 앨범 만들기 (P1) 🎯 MVP

**Goal**: 대화창에서 폴더를 골라 001과 같은 PDF를 만들고 PDF를 연다

**Independent Test**: `python scripts/album_app.py`로 창을 띄워 폴더 선택 → 앨범 만들기 → PDF 열기

### Tests for User Story 1 ⚠️

- [X] T005 [P] [US1] In `tests/test_app.py` (skip module if `tkinter.Tk()` raises `TclError`) using a withdrawn Tk root: `AlbumApp(root, initial_folder)` pre-fills `photo_dir` only when it is a directory (FR-008); setting `photo_dir` updates `output` to `default_output_path` while `output_custom` is False and leaves it alone once True; `start()` with photos runs to completion (pump `root.update()` until `busy` is False, timeout 30 s), log text equals `"\n".join(report_lines(...))`, `last_pdf` set, "PDF 열기" enabled, PDF exists (contracts/gui.md)

### Implementation for User Story 1

- [X] T006 [US1] Create `scripts/album_app.py`: `AlbumApp` class per contracts/gui.md — window title "A4 사진 앨범 만들기", rows for 사진 폴더 / 저장할 PDF with `ttk.Entry` + "찾아보기…" (`filedialog.askdirectory` / `asksaveasfilename(defaultextension=".pdf")` setting `output_custom=True`), buttons "앨범 만들기" / "PDF 열기", read-only scrolled `Text` result area, resizable; state fields `photo_dir`, `output`, `output_custom`, `busy`, `last_pdf` (data-model.md); trace on `photo_dir` refreshes default output when not custom
- [X] T007 [US1] In `scripts/album_app.py` implement `start()`: run `make_album.build_album(photo_dir, output)` on a daemon `threading.Thread`, deliver result through `queue.Queue` polled with `root.after(100, ...)`; while busy disable 만들기 (text "만드는 중…") and both 찾아보기 and PDF 열기, log `만드는 중…`; on success write `report_lines` and enable PDF 열기; `open_pdf()` uses `os.startfile(last_pdf)`
- [X] T008 [US1] In `scripts/album_app.py` add `main(argv)`: `--smoke-test <photo_dir> <output_pdf> <log_file>` runs `build_album` without a window, writes `report_lines` (or warnings + `오류: …`) to the log file in UTF-8, returns 0/1 (research R4); otherwise create Tk root, `AlbumApp(root, argv[0] if given)`, `mainloop()`; guard `if __name__ == "__main__": sys.exit(main(sys.argv[1:]))`

**Checkpoint**: 창에서 앨범 생성 가능 (US1 MVP)

---

## Phase 4: User Story 2 - 문제 상황을 창에서 바로 이해하기 (P2)

### Tests for User Story 2 ⚠️

- [X] T009 [P] [US2] In `tests/test_app.py` add: `start()` with empty `photo_dir` logs `사진 폴더를 먼저 골라 주세요.` and creates nothing; folder with only a broken photo logs `경고: broken.jpg — …` then `오류: 넣을 사진이 없습니다…` and keeps 만들기 enabled / PDF 열기 disabled; unexpected exception (monkeypatch `build_album` to raise `RuntimeError`) logs `오류: 예상하지 못한 문제가 생겼습니다:`; `on_close()` while `busy` does not destroy the window (monkeypatch `messagebox.showinfo`)

### Implementation for User Story 2

- [X] T010 [US2] In `scripts/album_app.py` handle errors per contracts/gui.md 문구: empty folder message, `AlbumError` → its `warnings` lines + `오류: <message>`, other exceptions → `오류: 예상하지 못한 문제가 생겼습니다: <exc>`; always return to ready state (FR-005, SC-004)
- [X] T011 [US2] In `scripts/album_app.py` set `root.protocol("WM_DELETE_WINDOW", on_close)`; when busy show `messagebox.showinfo` with `앨범을 만드는 중입니다. 끝난 뒤 닫아 주세요.` and keep the window (research R6)

---

## Phase 5: User Story 3 - 배포용 zip 만들기 (P3)

- [X] T012 [P] [US3] Create `packaging/사용법.txt` (Korean, CRLF, UTF-8 with BOM for Notepad): 먼저 압축을 풀 것, `앨범만들기.exe` 실행, SmartScreen "추가 정보 → 실행", 사진 이름 규칙(`숫자_설명.jpg`), 지원 형식·자동 변환, 인쇄 설정(A4, 실제 크기 100%), `_internal` 폴더를 지우거나 옮기지 말 것
- [X] T013 [US3] Create `build_portable.ps1` per contracts/build.md: `param([string]$Python)`, `$ErrorActionPreference='Stop'`; recreate `.build-venv` and install `requirements-build.txt`; run PyInstaller (`--noconfirm --clean --windowed --onedir --name 앨범만들기 --paths scripts scripts\album_app.py`); copy `packaging\사용법.txt`; smoke test in `%TEMP%\a4lbum 검사 <random>\` with JPEG+HEIC+GIF Korean-named samples generated by the build venv Python, Python removed from PATH, `Start-Process -Wait -PassThru` exit code + PDF exists + log contains `완료: 사진 3장 → 2페이지`; on failure print log and `exit 1`; create `dist\앨범만들기-windows.zip` with Python `zipfile` (top folder `앨범만들기/`); print `완료: dist\앨범만들기-windows.zip (<MB> MB)`
- [X] T014 [US3] Run `build_portable.ps1` and fix issues until it prints 완료; extract the zip into a Korean+space path and run the smoke test against the extracted exe (SC-005)

---

## Phase 6: Polish

- [X] T015 [P] Update `README.md` with a "받는 사람에게 전달하기" section (build command, zip 위치, 받는 사람은 압축 풀고 exe 실행) and the 창 실행 방법 for developers (`python scripts/album_app.py`)
- [X] T016 Launch the built exe, capture a screenshot of the window, and visually verify layout and Korean text rendering; verify the window appears within 10 s (SC-002)
- [X] T017 Run `python -m pytest -q` and confirm all pass

---

## Dependencies & Execution Order

- Setup → Foundational(T003) → US1 → US2 → US3 → Polish
- `album_app.py`(T006–T008, T010–T011)는 같은 파일이라 순차
- US3의 빌드(T013–T014)는 US1·US2 완료 후 (exe가 최종 코드여야 함)

### Parallel Opportunities

- T001, T002 / T004, T005 / T009, T012

## Implementation Strategy

1. T003으로 001과 문구 공유 → US1 창 MVP → US2 오류 처리 → US3 빌드·zip → 문서·육안 확인

---

## Phase 7: Convergence

- [X] T018 Document `packaging/build_helpers.py` (sample photos + UTF-8 zip, kept in Python to avoid PowerShell 5.1 quoting/encoding issues) in `specs/002-portable-album-app/plan.md` Project Structure and `contracts/build.md` steps 4·5 per plan: Project Structure (unrequested)
- [X] T019 Document the DPI-awareness call and display-scaled window size of `scripts/album_app.py` in `specs/002-portable-album-app/research.md` (new R9) and `contracts/gui.md` 창 구성 per plan: research (unrequested)
---

## Phase 8: Change Request (2026-10-07) — the repository zip is the stand-alone download

- [X] T020 In `build_portable.ps1` build with `--name "앨범 만들기" --contents-directory app` into `build\dist`, keep the Python-less smoke test, then replace `앨범 만들기.exe` and `app\` at the repo root instead of writing a zip; remove `packaging/사용법.txt` and the zip helper from `packaging/build_helpers.py` per FR-009, FR-010
- [X] T021 Add `.gitattributes` (`/app/** -text`, `*.exe binary`, CRLF for `*.bat`/`*.ps1`) and `!/app/**` in `.gitignore`; verify all 1012 runtime files are committed byte for byte per research R5
- [X] T022 Build and commit `앨범 만들기.exe` + `app\`; verify with a `git archive` zip of the tree extracted to a Korean+space path with Python hidden from PATH: smoke test passes (HEIC included) and the window opens in 0.3 s per SC-001, SC-005
- [X] T023 Rewrite README 사용법 as Download ZIP → 압축 풀기 → 사진 준비 → `앨범 만들기.exe` → 인쇄, with no separate distribution section and no internet or built-zip mention; mention format conversion only in passing in the intro
