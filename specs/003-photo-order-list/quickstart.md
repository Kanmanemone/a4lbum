# Quickstart: 사진 순서 목록 확인하기

## 준비

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

## 자동 테스트

```powershell
.venv\Scripts\python.exe -m pytest
```

기대 결과는 다음과 같다.

- 기존 테스트(001·002)가 모두 통과한다. CLI 결과가 그대로다(FR-011).
- `tests/test_order.py`와 `tests/test_app.py`의 003 테스트가 통과한다(정렬 3종·역순·옮기기 4종·커스텀 전이·`order`·`strip_number`).

## 손으로 확인 (창)

1. `.venv\Scripts\python.exe scripts\album_app.py`를 실행하고 사진 폴더를 고른다.
   - 기대: 목록에 사진 파일 이름이 이름 순(앞 숫자는 크기순)으로 뜨고, 정렬은 "이름 순 정렬"이다.
2. "수정한 날짜 순 정렬"을 고르고 "역순으로 정렬"을 체크한다.
   - 기대: 가장 최근에 수정한 사진이 맨 위에 온다.
3. 아무 줄의 [맨 아래로]를 누른다.
   - 기대: 그 사진이 맨 아래로 가고, 정렬 표시는 "커스텀", 역순 체크박스는 회색이다.
4. "숫자_" 체크박스를 해제한 채 "앨범 만들기"를 누르고 PDF를 연다.
   - 기대: 사진 순서가 목록과 같고, 라벨에 `283_` 같은 앞 번호가 그대로 있다.
5. 체크박스를 체크하고 다시 만든다.
   - 기대: 라벨에서 앞 번호가 빠진다.

## 배포물

```powershell
powershell -ExecutionPolicy Bypass -File build_portable.ps1
```

기대: smoke test가 통과하고 최상위 `앨범 만들기.exe`와 `app\`이 바뀐다. exe로 1~5단계를 반복해 같은 결과를 확인한다.
