# Research: 압축만 풀면 쓰는 앨범 프로그램

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Date**: 2026-10-06

스파이크는 이 PC(Windows 11, Python 3.14.6, PyInstaller 6.22.3)의 scratchpad에서 실행했다.

## R1. exe를 만드는 방법

- **Decision**: PyInstaller **onedir** 모드와 `--windowed`를 쓴다. 결과는 `앨범만들기.exe`와 `_internal\` 폴더다.
- **Rationale**:
  - 001의 Python 코드를 그대로 쓰므로 앨범 규칙을 다시 구현할 필요가 없다(FR-004).
  - 스파이크 결과:
    - 한글 exe 이름으로 빌드됐다.
    - Python을 PATH에서 뺀 상태에서 한글·공백·이모지 경로(`받는 사람 PC …\앨범 프로그램`, `사진 모음 🌸`)에서 실행해 JPEG·HEIC·GIF가 든 폴더로 PDF를 만들었다(exit 0).
    - pillow-heif의 네이티브 라이브러리도 추가 설정 없이 함께 묶였다.
  - onedir은 실행할 때 압축을 풀지 않아 빨리 뜬다(SC-002). onefile보다 백신 오탐도 적다.
- **Alternatives considered**:
  - **onefile**: exe 하나로 깔끔하지만 실행할 때마다 임시 폴더에 수십 MB를 풀어 느리다. 백신 오탐도 잦다.
  - **휴대용 Python + .bat**: 사용자가 exe를 요구했다.
  - **C# WinForms 실행기 + 휴대용 Python**: 언어가 둘이 되어 관리 부담이 크다.

## R2. 대화창 GUI

- **Decision**: Python 표준 라이브러리 `tkinter`(+ `ttk`)를 쓴다. 모듈은 `scripts/album_app.py` 하나다.
- **Rationale**: 추가 의존성이 없고, PyInstaller가 Tcl/Tk를 자동으로 묶는다. 필요한 위젯(경로 칸, 폴더/파일 선택 대화상자, 버튼, 텍스트 영역)이 모두 있다.
- **Alternatives considered**: PySide/PyQt는 묶음이 100MB 이상으로 커진다. 웹 UI는 과하다.

## R3. 깨끗한 빌드 환경

- **Decision**: 빌드 스크립트가 저장소의 `.build-venv\`를 매번 새로 만든다. 그 안에 `requirements.txt`와 `pyinstaller`만 설치한다.
- **Rationale**: 스파이크에서 개발용 `.venv`에 실험용으로 깔아 둔 numpy(26MB)가 딸려 들어가 묶음이 91.8MB가 됐다. 빌드 환경을 깨끗이 하면 쓰지 않는 패키지가 들어가지 않고, 다른 PC에서 빌드해도 같은 결과가 나온다.

## R4. 빌드 검증 (FR-010)

- **Decision**: exe에 숨은 인자 `--smoke-test <사진폴더> <출력PDF> <로그파일>`을 둔다. 빌드 스크립트는 다음 순서로 확인한다.
  1. 결과물을 한글·공백이 든 임시 경로에 복사한다.
  2. Python을 PATH에서 뺀다.
  3. JPEG·HEIC·GIF 샘플로 이 인자를 실행해 exit 0과 PDF 생성을 확인한다.
  4. 실패하면 저장소의 exe를 바꾸지 않는다.
- **Rationale**: `--windowed` exe는 콘솔 출력이 없어서 종료 코드와 로그 파일로 확인한다. 실제 배포물과 같은 exe를 검사하므로, 묶음 누락(DLL, 데이터 파일)을 확실히 잡는다.

## R5. 배포 방법: 빌드 결과를 저장소에 커밋 (2026-10-07 변경)

- **Decision**:
  - PyInstaller `--contents-directory app`으로 빌드해 `앨범 만들기.exe`와 `app\`을 저장소 최상위에 두고 커밋한다.
  - `.gitattributes`의 `/app/** -text`로 바이트 그대로 저장한다.
  - `.gitignore`의 `!/app/**`로 `*.pyc` 같은 무시 규칙에서 빼서 1012개 파일이 모두 커밋되게 한다.
- **Rationale**: 사용자는 GitHub 저장소 zip 하나만 받아 압축을 풀고 바로 써야 한다. 인터넷이나 별도 배포 파일이 필요하면 안 된다(stand-alone).
  - 처음 시도한 "첫 실행 때 uv로 Python을 내려받기"는 인터넷이 필요해 버렸다.
  - "별도 배포 zip"은 사용자에게 받을 파일이 하나 더 생겨 버렸다.
  - 검증: 저장소 zip(27.9MB)을 한글·공백 경로에 풀고 Python을 PATH에서 숨긴 상태에서 exe 창이 0.3초 만에 떴고, HEIC가 포함된 앨범을 만들었다.
  - 비용: 빌드할 때마다 저장소가 약 66MB씩 커지므로 코드를 바꿨을 때만 다시 빌드한다.

## R6. 만드는 중 창 닫기 (Edge Case)

- **Decision**: 만드는 중에 창을 닫으려 하면 "앨범을 만드는 중입니다. 끝난 뒤 닫아 주세요." 안내만 띄우고 닫지 않는다.
- **Rationale**: 001의 `render_pdf`는 임시 PDF를 쓴 뒤 바꿔치기하는 방식이다. 작업 스레드를 강제로 끊으면 임시 파일이 남을 수 있다. 앨범 생성은 보통 몇 초라서 기다리게 하는 편이 가장 단순하고 안전하다.

## R7. 결과 문구를 CLI와 같게

- **Decision**: `make_album.py`에서 결과 줄을 만드는 부분을 `report_lines()`로, 기본 출력 경로 계산을 `default_output_path()`로 떼어 낸다. CLI와 GUI가 둘 다 이 함수를 쓴다.
- **Rationale**: SC-003과 FR-005(같은 문구)를 코드 수준에서 보장한다. 001의 동작은 바뀌지 않는다.

## R8. 서명과 SmartScreen

- **Decision**: 코드 서명을 하지 않고, 사용법 안내에 "Windows의 PC 보호 → 추가 정보 → 실행"을 적는다.
- **Rationale**: 인증서는 비용이 들어 개인 프로젝트로는 과하다.

## R9. 고해상도 화면에서 선명하게 (구현 중 추가)

- **Decision**: 창을 만들기 전에 `ctypes.windll.shcore.SetProcessDpiAwareness(1)`을 호출한다. 창의 처음 크기와 최소 크기는 `tk scaling / (96/72)` 배율을 곱해 정한다.
- **Rationale**: 이 호출이 없으면 Windows가 배율이 적용된 화면(이 PC는 200%)에서 창을 비트맵으로 늘려 한글이 흐릿하게 보였다(육안 확인으로 발견). 배율을 인식하면 Tk가 글꼴을 직접 크게 그린다. 대신 픽셀로 지정한 창 크기가 상대적으로 작아지므로 배율을 곱한다. 이 호출은 Windows 8.1 이상에만 있어서, 없으면 조용히 건너뛴다.