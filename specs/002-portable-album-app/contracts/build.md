# Contract: `build_portable.ps1`

코드를 바꾼 뒤 저장소 최상위의 `앨범 만들기 (한국어).exe`, `Photo Album Maker (English).exe`, `app\`을 다시 만드는 명령이다. 빌드 PC에는 Python 3.10+이 필요하고, 저장소를 받아 쓰는 사용자 PC에는 아무것도 필요 없다.

두 exe는 한 번 빌드한 exe의 같은 복사본이고 `app\`을 함께 쓴다. 프로그램은 자기 exe 이름에 `(English)`가 있으면 영어로 동작하고, exe 이름에서 `.exe`를 뺀 것을 창 제목으로 쓴다(2026-10-16 변경 요청).

## 사용법

```powershell
powershell -ExecutionPolicy Bypass -File build_portable.ps1 [-Python <python.exe 경로>]
```

- `-Python`의 기본값은 `py -3`(있으면) 또는 `python`이다.

## 단계

0. 저장소 안의 exe가 실행 중이면 바로 멈춘다(`실행 중인 앨범 프로그램을 먼저 닫아 주세요: …`). 실행 중인 exe가 `app\`을 잡고 있으면 4단계가 중간에 실패해 `app\`이 반쯤 지워지기 때문이다.
1. `.build-venv\`를 지우고 새로 만든 뒤 `pip install -r requirements-build.txt`를 실행한다(research R3).
2. PyInstaller를 실행한다: `--noconfirm --clean --windowed --onedir --name a4lbum --contents-directory app --icon packaging\app.ico --distpath build\dist --workpath build\work --specpath build --paths scripts scripts\album_app.py`. 결과 `build\dist\a4lbum\a4lbum.exe`를 두 이름으로 복사하고 원래 이름은 지운다.
3. **Smoke test** (FR-010, research R4):
   1. 결과를 `%TEMP%\a4lbum 검사 <난수>\앨범 프로그램\`에 복사한다.
   2. 같은 위치의 `사진 모음\`에 샘플 사진을 만든다: JPEG, HEIC, GIF 각 1장, 한글 이름(`packaging\build_helpers.py samples`).
   3. PATH에서 Python 경로를 뺀 채 두 exe를 각각 `--smoke-test …`로 실행한다.
   4. 둘 다 exit 0이고 PDF가 있어야 한다. 로그에는 한국어 exe면 `완료: 사진 3장 → 2페이지`, 영어 exe면 `Done: 3 photos → 2 pages`가 있어야 통과다.
   5. 실패하면 로그를 보여 주고 exit 1로 끝나며 저장소의 exe와 `app\`은 바꾸지 않는다.
4. 저장소 최상위의 `app\`을 지우고 새 결과로 바꾼다. 예전 이름 `앨범 만들기.exe`가 있으면 지우고, 두 exe를 덮어쓴다.
5. `완료: 앨범 만들기 (한국어).exe + Photo Album Maker (English).exe + app\ (<크기> MB). 함께 커밋하세요.`를 출력한다.

exe 이름은 스크립트의 `$KoName`·`$EnName`과 `album_app.title()`이 같아야 한다(`tests/test_english.py`가 확인).

## 저장소 최상위 구성 (커밋됨)

```text
앨범 만들기 (한국어).exe          # 한국어 사용자가 더블클릭
Photo Album Maker (English).exe   # 영어 사용자가 더블클릭
app/                              # Python 런타임·라이브러리 (/app/** -text, !/app/** 로 바이트 그대로 전부 커밋)
```

## 종료 코드

- 0: 교체 완료
- 1: 어느 단계든 실패(메시지 출력, 저장소의 exe는 그대로)
