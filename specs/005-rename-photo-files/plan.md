# Implementation Plan: 앨범 창에서 사진 파일 이름 바꾸기

**Branch**: `005-rename-photo-files` | **Date**: 2026-11-25 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/005-rename-photo-files/spec.md`

## Summary

`scripts/album_app.py`만 고친다.

- 순수 함수 `rename_photo(folder, name, new_stem) -> str | None`: 검사하고 `os.rename`한 뒤 새 파일 이름을 돌려준다(바꿀 것이 없으면 `None`). 쓸 수 없는 글자는 `ValueError`, OS 오류는 `OSError`.
- `PhotoList`: 이름 라벨에 `<Double-Button-1>`을 걸어 같은 칸에 `ttk.Entry`를 띄운다. Enter·FocusOut은 확정, Esc는 취소. 확정하면 `on_rename(index, text)`.
- `AlbumApp.rename(index, text)`: 만드는 중이면 무시, `rename_photo` 호출, `self.photos[index]`를 `replace(p, name=new)`로 바꾸고 커스텀이 아니면 `resort()`. 실패는 결과 칸에 보이고 목록을 다시 읽는다.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: 기존과 같다. 새 의존성 없음.

**Storage**: 폴더의 파일 이름 자체.

**Testing**: pytest. `rename_photo`는 임시 폴더로, 창 동작은 기존처럼 숨긴 Tk 창으로.

**Constraints**: 덮어쓰기·다른 폴더로 이동 금지(SC-002). `make_album.py`는 건드리지 않는다.

## Constitution Check

`.specify/memory/constitution.md`는 아직 채워지지 않은 템플릿이라 적용할 원칙이 없다(통과). 자체 게이트:

| 게이트 | 결과 |
|--------|------|
| 앨범 규칙은 `make_album.py` 한 곳에서만 | ✅ 이름 바꾸기는 창 기능이라 `album_app.py`에 둔다 |
| CLI·`/album` 불변 | ✅ `make_album.py` 변경 없음 |
| 오버엔지니어링 금지 | ✅ 새 파일·새 의존성·Undo·일괄 변경 없음 |

## Project Structure

```text
specs/005-rename-photo-files/
├── spec.md, plan.md, research.md, quickstart.md, tasks.md
├── contracts/gui.md
└── checklists/requirements.md

scripts/album_app.py     # rename_photo(), PhotoList 편집 칸, AlbumApp.rename(), 안내 문구
tests/test_app.py        # rename_photo와 창 동작 테스트
README.md, README.ko.md  # 사용법에 한 줄
```

데이터 모델 변화가 없어 data-model.md는 두지 않는다(`PhotoFile.name`만 바뀐다).

## Complexity Tracking

위반 없음.
