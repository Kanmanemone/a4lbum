# Implementation Plan: 사진 목록에 마우스를 올리면 썸네일 보이기

**Branch**: `006-photo-hover-thumbnail` | **Date**: 2026-11-25 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/006-photo-hover-thumbnail/spec.md`

## Summary

`scripts/album_app.py`만 고친다.

- 순수 함수 `make_thumbnail(path, size) -> PIL.Image`: 열고(`draft`로 JPEG를 작게 디코드), `ImageOps.exif_transpose`로 방향을 맞추고, `thumbnail`로 줄인다. 열 수 없으면 예외.
- `PhotoList`: 이름 라벨에 `<Enter>`/`<Leave>`/`<ButtonPress>`를 건다. 0.4초 머물면 썸네일을 요청한다. 캐시에 있으면 바로, 없으면 데몬 스레드에서 `make_thumbnail`을 돌려 큐로 받고 `after` 폴링으로 꺼내(앨범 만들기와 같은 패턴) 아직 그 줄 위에 있을 때만 띄운다. 미리보기는 테두리 없는 `Toplevel` 하나다.
- `AlbumApp`: `PhotoList`에 `index → 파일 경로` 함수를 넘기고, 폴더를 새로 읽을 때 캐시를 비운다.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: 기존 Pillow(+pillow-heif), tkinter의 `PIL.ImageTk`. 새 의존성 없음.

**Storage**: 메모리 캐시(경로 → 줄인 그림 또는 실패). 창을 닫으면 사라진다.

**Testing**: pytest. `make_thumbnail`은 임시 사진으로, 창 동작은 숨긴 Tk 창으로.

**Performance Goals**: 12MP JPEG 약 0.16초, 12MP HEIC 약 1.7초(측정). 그래서 디코딩은 UI 스레드 밖에서 한다(spec Edge Cases: 창이 멈추지 않음).

**Constraints**: 원본 파일 읽기만(FR-006). `make_album.py`는 건드리지 않는다.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

`.specify/memory/constitution.md`는 아직 채워지지 않은 템플릿이라 적용할 원칙이 없다(통과). 자체 게이트:

| 게이트 | Phase 0 전 | Phase 1 후 |
|--------|-----------|-----------|
| 앨범 규칙은 `make_album.py` 한 곳에서만 | ✅ | ✅ 미리보기는 창 기능이라 `album_app.py`에 둔다 |
| CLI·`/album` 불변 | ✅ | ✅ `make_album.py` 변경 없음 |
| 오버엔지니어링 금지 | ✅ | ✅ 새 파일·디스크 캐시·스레드 풀 없음. 스레드는 요청 하나에 하나, 같은 사진이 진행 중이면 다시 시작하지 않음 |

## Project Structure

### Documentation (this feature)

```text
specs/006-photo-hover-thumbnail/
├── spec.md, plan.md, research.md, quickstart.md, tasks.md
├── contracts/gui.md
└── checklists/requirements.md
```

데이터 모델은 캐시 딕셔너리 하나라 data-model.md는 두지 않는다(research R4).

### Source Code (repository root)

```text
scripts/album_app.py   # make_thumbnail(), PhotoList 미리보기, AlbumApp 연결
tests/test_app.py      # make_thumbnail, 머물기·나가기·실패·캐시 테스트
README.md, README.ko.md  # 사용법 한 줄
```

**Structure Decision**: 기존 단일 프로젝트 구조 그대로.

## Complexity Tracking

위반 없음.
