# Quickstart: 글자에 꼭 맞는 메모 라벨과 페이지 정중앙에 놓이는 사진

## 준비

```powershell
.venv\Scripts\python -m pip install -r requirements-dev.txt   # 처음 한 번
```

## 1. 자동 테스트

```powershell
.venv\Scripts\python -m pytest
```

기대: 모두 통과. `tests/test_layout.py`가 좌우 가운데, 위아래 대칭, 라벨 너비·내미는 폭, 글자 가운데 정렬, 기존 불변식(인쇄 영역, 15% 가림)을 확인한다.

## 2. 예시 앨범으로 눈으로 확인

```powershell
.venv\Scripts\python scripts\make_album.py examples\photos -o $env:TEMP\check_album.pdf
```

PDF를 열어 확인한다([contracts/layout.md](contracts/layout.md) 수치 참고).

- 가로로 긴 사진의 왼쪽·오른쪽 여백이 같다.
- "Beach" 같은 짧은 설명의 라벨이 글자에 꼭 맞고, 글자가 라벨 가운데에 있다.
- 라벨은 여전히 사진 오른쪽 위 모서리에 걸쳐 있고 종이 가장자리 10mm 안쪽이다.

## 3. exe와 예시 PDF 다시 만들기

```powershell
powershell -ExecutionPolicy Bypass -File build_portable.ps1
```

기대: 두 exe 검사 통과, `examples\photos_album.pdf`가 새 배치로 다시 만들어진다.
