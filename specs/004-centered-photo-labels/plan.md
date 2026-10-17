# Implementation Plan: 글자에 꼭 맞는 메모 라벨과 페이지 정중앙에 놓이는 사진

**Branch**: `004-centered-photo-labels` | **Date**: 2026-10-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/004-centered-photo-labels/spec.md`

## Summary

배치 규칙은 모두 `scripts/make_album.py`의 Layout·Rendering 부분에 있다. 세 곳만 고친다.

1. `slot_geometry`: 사진 자리(box)를 칸 왼쪽에 붙여 오른쪽만 줄이던 것을, 좌우를 `LABEL_OUT_X`씩 같은 폭으로 줄인다. 위아래는 페이지 바깥쪽(위 칸은 위, 아래 칸은 아래)만 `LABEL_OUT_Y` 줄여, 두 사진 자리가 페이지 위아래 가운데 선을 기준으로 대칭이 되게 한다. 사진은 `fit_photo`가 지금처럼 box 가운데에 둔다.
2. `_build_label`: 최소 너비 `LABEL_MIN_W`를 30mm에서 10mm(한 줄 라벨 높이 정도)로 낮추고, 사진 밖으로 나오는 폭을 `min(LABEL_OUT_X, w / 2)`로 한다.
3. `_draw_label`: 줄마다 `(라벨 너비 - 줄 폭) / 2`만큼 띄워 가운데 정렬한다.

CLI·`/album`·창 모두 같은 함수를 쓰므로 한 번에 바뀐다(FR-008). 끝으로 `build_portable.ps1`로 exe와 예시 PDF를 다시 만든다.

## Technical Context

**Language/Version**: Python 3.10+ (개발·빌드 PC: 3.14)

**Primary Dependencies**: 기존과 같다(reportlab, Pillow, pillow-heif, tkinter). 새 의존성 없음.

**Storage**: 없음

**Testing**: pytest. `tests/test_layout.py`의 배치 불변식을 새 규칙으로 고치고, 좌우 가운데·위아래 대칭·라벨 너비·글자 가운데 정렬 테스트를 더한다.

**Target Platform**: Windows 10/11 64비트

**Project Type**: CLI 라이브러리 + 데스크톱 GUI(배치 규칙은 라이브러리에만 있음)

**Performance Goals**: 변화 없음(계산 몇 줄)

**Constraints**:
- 기존 FR(비율 유지, 잘라내지 않음, 인쇄 가능 영역, 15% 가림 상한) 유지
- 오버엔지니어링 금지: 새 파일·새 설정·새 옵션 없음, 상수와 세 함수만 고침

**Scale/Scope**: `make_album.py` 10~20줄, 테스트 수십 줄

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

`.specify/memory/constitution.md`는 채워지지 않은 템플릿이라 적용할 원칙이 없다(통과). 자체 게이트로 확인했다.

| 게이트 | Phase 0 전 | Phase 1 후 |
|--------|-----------|-----------|
| 배치 규칙은 `make_album.py` 한 곳에서만 | ✅ | ✅ `slot_geometry`, `_build_label`, `_draw_label`만 고침 |
| 기존 001 FR-005~007 유지 | ✅ | ✅ 테스트의 불변식(인쇄 영역, 15%, 일부만 겹침) 그대로 둠 |
| 오버엔지니어링 금지 | ✅ | ✅ 새 모듈·옵션 없음 |

## Project Structure

### Documentation (this feature)

```text
specs/004-centered-photo-labels/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── layout.md        # 바뀐 배치 규칙(수치)
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
scripts/
└── make_album.py      # LABEL_MIN_W, slot_geometry(), _build_label(), _draw_label()

tests/
└── test_layout.py     # 새 배치 불변식

앨범 만들기 (한국어).exe, Photo Album Maker (English).exe, app/, examples/photos_album.pdf
                       # build_portable.ps1로 다시 빌드
```

**Structure Decision**: 기존 구조 그대로. 앨범 창(`album_app.py`)과 `/album` 스킬은 배치를 직접 다루지 않아 고치지 않는다.

## Complexity Tracking

위반 없음.
