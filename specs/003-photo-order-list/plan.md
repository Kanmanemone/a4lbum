# Implementation Plan: 앨범 창에서 사진 순서 정하기와 "숫자_" 빼기 선택

**Branch**: `003-photo-order-list` | **Date**: 2026-10-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-photo-order-list/spec.md`

## Summary

002의 tkinter 창(`scripts/album_app.py`)에 사진 순서 목록을 넣는다. 목록 위에는 정렬 방식 콤보박스("이름 순 정렬" / "만든 날짜 순 정렬" / "수정한 날짜 순 정렬", 직접 옮기면 "커스텀")와 "역순으로 정렬" 체크박스가 있다. 각 줄에는 [맨 위로] [▲] [▼] [맨 아래로] 버튼이 있다. 창 아래에는 "숫자_" 빼기 체크박스를 둔다.

앨범 규칙은 계속 `make_album.py`가 정한다. 여기에는 두 선택 인자만 더한다.

- `build_album(..., order=None, strip_number=True)`
- `list_photo_files(folder)`: 목록에 보일 파일. `scan_folder`와 같은 거르기 규칙을 쓴다.

인자 기본값이 기존 동작이라, CLI와 `/album`은 바뀌지 않는다(FR-011). 끝으로 `build_portable.ps1`로 exe와 `app\`을 다시 만든다.

## Technical Context

**Language/Version**: Python 3.10+ (개발·빌드 PC: 3.14.6)

**Primary Dependencies**: 기존과 같다(reportlab, Pillow, pillow-heif, 표준 tkinter). 새 의존성은 없다.

**Storage**: 없음. 순서와 체크 상태는 창을 닫으면 사라진다.

**Testing**: pytest. 정렬·목록·`build_album(order, strip_number)`는 순수 함수 테스트, 창 상태는 기존처럼 숨긴 Tk 창으로 테스트한다.

**Target Platform**: Windows 10/11 64비트

**Project Type**: 데스크톱 GUI(단일 창) + 기존 CLI 라이브러리

**Performance Goals**: 사진 300장 폴더를 고르고 목록이 보이기까지 2초 이내(SC-001). 목록을 만들 때 사진 파일을 열지 않고, 이름과 파일 시스템 날짜만 읽는다.

**Constraints**:
- CLI 결과 불변(FR-011)
- 002 창 동작 불변(FR-012)
- 오버엔지니어링 금지: 새 파일 없이 기존 두 모듈만 고친다.

**Scale/Scope**: 위젯 몇 개 추가, 함수 3~4개 추가

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

`.specify/memory/constitution.md`가 아직 채워지지 않은 템플릿이라 적용할 원칙이 없다(통과). spec에서 나온 자체 게이트로 확인했다.

| 게이트 | Phase 0 전 | Phase 1 후 |
|--------|-----------|-----------|
| 앨범 규칙은 `make_album.py` 한 곳에서만 | ✅ | ✅ 창은 `list_photo_files`, `natural_key`, `build_album`만 호출 |
| CLI·`/album` 결과 불변 | ✅ | ✅ 새 인자의 기본값이 기존 동작(`order=None`, `strip_number=True`) |
| 오버엔지니어링 금지 | ✅ | ✅ 새 모듈·설정 저장·드래그 없음. 버튼 4개와 체크박스 2개, 콤보박스 1개 |

## Project Structure

### Documentation (this feature)

```text
specs/003-photo-order-list/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── gui.md           # 바뀐 창 구성과 동작
│   └── album-api.md     # make_album에 더한 함수·인자
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
scripts/
├── make_album.py      # list_photo_files(), extract_caption(strip_number), build_album(order, strip_number)
└── album_app.py       # 정렬 함수 sort_photos(), 목록 UI(PhotoList), 체크박스 2개, start()에서 order·strip_number 전달

tests/
├── test_naming.py     # extract_caption(strip_number=False)
├── test_order.py      # 새로 추가: list_photo_files, sort_photos, build_album(order, strip_number)
└── test_app.py        # 목록·정렬·옮기기·커스텀·체크박스 창 동작

앨범 만들기.exe, app/  # build_portable.ps1로 다시 빌드해 커밋
README.md              # 창 사용법에 목록·체크박스 설명 추가
```

**Structure Decision**: 기존 단일 프로젝트 구조를 그대로 쓴다. 정렬 함수는 창에서만 쓰므로 `album_app.py`에 둔다. 파일 거르기 규칙은 앨범과 목록이 같아야 하므로 `make_album.py`에 둔다.

## Complexity Tracking

위반 없음.
