# Implementation Plan: A4 사진 앨범 페이지 만들기

**Branch**: `001-a4-photo-album` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-a4-photo-album/spec.md`

## Summary

사진 폴더 하나를 받아 A4 세로 PDF를 만든다. 사진은 파일 이름순(앞 숫자는 숫자 크기순)으로 페이지마다 위·아래 한 장씩 넣는다. 각 사진의 오른쪽 위 모서리에는 흰색 메모 라벨을 걸치고, 라벨에는 파일 이름에서 "숫자_"를 뗀 설명을 적는다.

기술적으로는 Python 스크립트 1개가 본체다. reportlab으로 PDF를 그리고, JPEG는 원본 바이트를 그대로 넣는다(스파이크로 확인). EXIF 회전은 픽셀을 건드리지 않고 PDF 좌표 변환으로 맞춘다. Claude Code `/album` 스킬은 이 스크립트를 실행해 주는 바로가기일 뿐이다.

## Technical Context

**Language/Version**: Python 3.10+ (개발 PC: 3.14.6)

**Primary Dependencies**: reportlab (PDF 생성), Pillow (이미지 검사·EXIF), pillow-heif (HEIC 읽기). 개발용: pytest, PyMuPDF (PDF 검사)

**Storage**: 없음. 입력은 사진 폴더(읽기 전용), 출력은 PDF 파일 1개다.

**Testing**: pytest. 테스트 사진은 Pillow로 만들고, 결과 PDF는 PyMuPDF로 검사한다([research.md R10](research.md#r10-테스트-방식)).

**Target Platform**: Windows 10/11 (기본 글꼴 맑은 고딕). 글꼴 경로만 `--font`로 바꾸면 다른 OS에서도 동작한다.

**Project Type**: CLI 스크립트 + Claude Code 스킬

**Performance Goals**: 사진 20장 기준 PDF 생성 60초 미만(SC-003). 재압축이 없으므로 실제로는 몇 초 수준으로 예상한다.

**Constraints**: JPEG 원본 바이트 보존(FR-002a/SC-007). 원본 폴더는 읽기만 한다. A4 100% 인쇄에서 여백 10mm 안에 모든 내용이 들어가야 한다. exe나 설치형 앱은 쓰지 않는다.

**Scale/Scope**: 한 번에 사진 수백 장 이하, 사용자 1명. PDF 용량은 원본 합계와 비슷하다.

미정(NEEDS CLARIFICATION) 항목은 없다. 모두 [research.md](research.md)에서 결정했다.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

`.specify/memory/constitution.md`가 아직 채워지지 않은 템플릿 상태라 적용할 원칙이 없다. 그래서 **게이트 통과(위반 없음)**로 본다. 대신 spec에서 나온 다음 제약을 자체 게이트로 확인했다.

| 게이트 | Phase 0 전 | Phase 1 후 |
|--------|-----------|-----------|
| exe/설치형 앱 없이 스크립트로 해결 | ✅ | ✅ Python 스크립트 1개 + 스킬 1개 |
| 원본 사진 무손실·무수정 | ⚠️ 라이브러리 미검증 | ✅ 스파이크로 JPEG 바이트 동일 확인, 출력은 폴더 밖 |
| 두 실행 방법의 결과 동일 | ✅ | ✅ 스킬은 CLI만 호출([album-command.md](contracts/album-command.md)) |
| 단순성(불필요한 구조 없음) | ✅ | ✅ 패키지·클래스 계층 없이 단일 모듈 |

## Project Structure

### Documentation (this feature)

```text
specs/001-a4-photo-album/
├── spec.md
├── plan.md              # 이 파일
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   ├── cli.md           # make_album.py 인터페이스
│   └── album-command.md # /album 스킬 인터페이스
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
scripts/
└── make_album.py          # 본체: 스캔 → 정렬·설명 추출 → 배치 계산 → PDF 쓰기 → 결과 보고

.claude/skills/album/
└── SKILL.md               # /album 바로가기 (contracts/album-command.md)

tests/
├── conftest.py            # 테스트 사진 생성 fixture (EXIF 포함 JPEG, PNG, 깨진 파일)
├── test_naming.py         # 설명 추출·자연 정렬 (FR-001a, FR-004)
├── test_layout.py         # 칸·사진·라벨 기하, 여백·겹침 불변식 (FR-005~008)
└── test_cli.py            # 종단 실행: 페이지 수, JPEG 바이트 보존, 경고, 종료 코드

requirements.txt           # reportlab, Pillow
requirements-dev.txt       # -r requirements.txt, pytest, PyMuPDF
README.md                  # 사용법 (사진 이름 규칙, 실행, 인쇄 설정)
```

**Structure Decision**: 단일 프로젝트로 하고 스크립트는 `scripts/make_album.py` 한 파일로 둔다. 구성은 순수 함수 층과 I/O 층 두 부분이다.

- **순수 함수**: `extract_caption`, `natural_key`, `layout_page`, `fit_label`. 테스트에서 바로 import해 검증한다.
- **I/O**: 폴더 스캔, PDF 쓰기, 결과 출력.

사용자가 원한 "스크립트 몇 개" 규모를 지키고 직접 읽고 고칠 수 있게 하려는 것이다.

## Phase 0 결과

[research.md](research.md)에 R1–R10을 정리했다. 핵심 결정은 다음과 같다.

- Python + reportlab(`useA85=0`)를 쓴다. JPEG 원본 바이트를 그대로 넣는 것을 검증했다.
- EXIF 회전은 PDF 좌표 변환으로 처리하고 재압축하지 않는다.
- 글꼴은 맑은 고딕이고, 이모지·기호는 Segoe UI Emoji/Symbol로 대체한다.
- 라벨은 사진 바깥으로 오른쪽 10mm, 위로 5mm 튀어나온다. 이 돌출분을 칸 안에 미리 비워 두어 잘리지 않게 한다.
- 출력 PDF는 사진 폴더의 부모 폴더에 `<폴더이름>_album.pdf`로 만든다.

## Phase 1 결과

- [data-model.md](data-model.md): PhotoItem, Slot, Label, AlbumPage, AlbumPdf, Warning과 기하 불변식
- [contracts/cli.md](contracts/cli.md): 인자, 출력 형식, 종료 코드
- [contracts/album-command.md](contracts/album-command.md): `/album` 스킬 동작과 금지 사항
- [quickstart.md](quickstart.md): 자동 테스트, 수동 실행, Claude 실행, 인쇄 확인 절차

## Risks

| 위험 | 대응 |
|------|------|
| reportlab 버전이 바뀌어 JPEG 원본 삽입 동작이 달라짐 | `test_cli.py`에서 바이트 동일성을 항상 검사한다. |
| JPEG·PNG 외 형식(HEIC, WEBP, GIF, BMP, TIFF, AVIF) | 임시 폴더에서 사진은 품질 95 JPEG, 그래픽·투명 이미지는 PNG로 변환해 넣는다(FR-014, research R7). HEIC는 pillow-heif가 없으면 설치 안내와 함께 경고 후 건너뛴다. |
| MPO(여러 장이 든 JPEG) | JPEG로 보고 그대로 넣는다. PDF 뷰어는 첫 장만 그린다(PyMuPDF로 확인). |
| 출력 PDF가 뷰어에서 열려 있어 덮어쓰기 실패 | exit 1과 "PDF 뷰어를 닫고 다시 실행" 메시지를 낸다. |
| 이모지 PDF 텍스트 추출 깨짐 | 인쇄에는 영향이 없다. 컬러 이모지는 범위 밖이다. |

## Complexity Tracking

위반 사항이 없어 해당 없음.
