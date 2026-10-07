# Implementation Plan: 압축만 풀면 쓰는 앨범 프로그램(exe + 대화창)

**Branch**: `002-portable-album-app` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-portable-album-app/spec.md`

## Summary

001의 `make_album.py`를 그대로 쓰는 작은 tkinter 대화창(`scripts/album_app.py`)을 만든다. 이것을 PyInstaller onedir로 `앨범만들기.exe`로 묶는다. 빌드 스크립트 하나가 다음을 순서대로 한다.

1. 깨끗한 빌드 환경을 만든다.
2. exe를 빌드한다.
3. Python 없는 한글 경로에서 실제로 앨범을 만들어 보는 자동 검증을 한다.
4. 저장소 최상위의 `앨범 만들기.exe`와 `app\`을 교체한다(커밋 대상, 2026-10-07 변경 요청).

## Technical Context

**Language/Version**: Python 3.10+ (빌드 PC: 3.14.6). 받는 사람 PC에는 Python이 필요 없다.

**Primary Dependencies**: 001과 같다(reportlab, Pillow, pillow-heif). GUI는 표준 라이브러리 tkinter다. 빌드에만 PyInstaller ≥ 6.10을 쓴다.

**Storage**: 없음

**Testing**: pytest. GUI 상태 로직은 숨긴 Tk 창으로 테스트한다. 배포물은 빌드 스크립트의 smoke test로 검증한다(research R4).

**Target Platform**: Windows 10/11 64비트

**Project Type**: 데스크톱 GUI(단일 창) + 빌드 스크립트

**Performance Goals**: 창이 10초 안에 뜬다(SC-002, onedir은 1~2초 예상). 앨범 생성 속도는 001과 같다.

**Constraints**:
- 받는 사람 PC에 설치·인터넷이 필요 없다.
- 콘솔 창이 뜨지 않는다.
- 한글·공백 경로에서 동작한다.
- 001의 앨범 규칙을 다시 구현하지 않는다.

**Scale/Scope**: 창 1개, 버튼 4개, 빌드 스크립트 1개

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

`.specify/memory/constitution.md`가 아직 채워지지 않은 템플릿이라 **적용할 원칙이 없다(통과)**. spec에서 나온 자체 게이트로 확인했다.

| 게이트 | Phase 0 전 | Phase 1 후 |
|--------|-----------|-----------|
| 압축 해제만으로 실행(설치·Python 불필요) | ⚠️ 미검증 | ✅ 스파이크: PATH에서 Python을 뺀 한글 경로에서 실행 성공 |
| 001 앨범 규칙 재구현 금지 | ✅ | ✅ GUI는 `make_album.build_album`과 `report_lines`만 호출 |
| 오버엔지니어링 금지 | ✅ | ✅ 새 파일 3개(앱, 빌드 스크립트, 사용법), 설정 UI 없음 |

## Project Structure

### Documentation (this feature)

```text
specs/002-portable-album-app/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── gui.md           # 대화창 동작
│   └── build.md         # 빌드 명령·결과물 구성·smoke test
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
scripts/
├── make_album.py          # 001 본체. default_output_path(), report_lines()만 떼어 냄
└── album_app.py           # 새로 추가: tkinter 대화창 + --smoke-test 진입점

build_portable.ps1         # 새로 추가: .build-venv → PyInstaller → smoke test → 최상위 exe·app\ 교체
앨범 만들기.exe            # 빌드 결과(커밋됨): 사용자가 더블클릭하는 프로그램
app/                      # 빌드 결과(커밋됨): Python 런타임과 라이브러리
packaging/
└── build_helpers.py       # 새로 추가: 검사용 샘플 사진 생성 (PowerShell 5.1의 따옴표·한글 문제 회피)

requirements-build.txt     # 새로 추가: -r requirements.txt, pyinstaller>=6.10

tests/
└── test_app.py            # 새로 추가: 대화창 상태 로직 테스트

.gitignore                 # .build-venv/, build/, dist/ 추가
```

**Structure Decision**:
- 앱 로직은 `album_app.py` 한 파일로 하고, `make_album`을 import해서 쓴다.
- 빌드는 PowerShell 스크립트 하나로 한다. Windows 전용 배포물이고 사용자 셸이 PowerShell이다.
- PyInstaller `.spec` 파일은 따로 두지 않고 명령줄 옵션으로 지정해서 관리할 파일을 줄인다.

## Phase 0 결과

[research.md](research.md) R1–R8. 핵심 결정은 다음과 같다.
- PyInstaller onedir + `--windowed`
- tkinter
- 매번 새로 만드는 `.build-venv`
- 숨은 인자 `--smoke-test`로 배포물을 자동 검증
- 결과물을 저장소 최상위에 커밋(R5)
- 만드는 중에는 창 닫기를 막음

## Phase 1 결과

- [data-model.md](data-model.md): 대화창 상태
- [contracts/gui.md](contracts/gui.md): 창 구성, 버튼 상태, 문구
- [contracts/build.md](contracts/build.md): `build_portable.ps1` 동작, 결과물 구성, 검증
- [quickstart.md](quickstart.md): 빌드 → 다른 경로에 풀기 → 실행 확인

## Risks

| 위험 | 대응 |
|------|------|
| 백신·SmartScreen 경고 | onedir로 오탐을 줄이고, README 사용법에 "추가 정보 → 실행"을 안내한다. |
| PyInstaller가 Python 새 버전을 늦게 지원 | requirements-build에 최소 버전을 적고, 빌드 실패 시 메시지를 그대로 보여 준다. |
| 묶음에서 DLL·데이터 누락 | smoke test가 HEIC가 포함된 실제 PDF 생성을 확인한 뒤에만 저장소의 exe를 바꾼다. |
| 받는 사람이 zip 안에서 바로 실행 | README 사용법에 "압축 풀기"를 단계로 적는다. |
| 빌드할 때마다 저장소가 커짐(약 66MB, zip 약 28MB) | 코드를 바꿨을 때만 다시 빌드해 커밋한다. 파일당 최대 약 22MB로 GitHub 제한 안이다. |

## Complexity Tracking

위반 사항이 없어 해당 없음.
