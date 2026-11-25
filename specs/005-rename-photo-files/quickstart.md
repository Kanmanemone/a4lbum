# Quickstart: 앨범 창에서 사진 파일 이름 바꾸기

## 자동 확인

```powershell
python -m pytest
```

`tests/test_app.py`의 005 테스트(`rename_photo`, 두 번 클릭 편집, Enter/Esc, 커스텀 유지, 만드는 중 막기, 오류 표시)와 기존 테스트가 모두 통과해야 한다.

## 손으로 확인

1. `python scripts/album_app.py examples\photos`의 복사본 폴더로 창을 연다.
2. `1_Beach.jpg`를 두 번 클릭 → `1_Beach`가 선택된 입력 칸이 뜬다.
3. `1_Sea`로 고치고 Enter → 폴더에 `1_Sea.jpg`, 목록도 `1_Sea.jpg`.
4. 다시 두 번 클릭해 `2_Sunset`(이미 있음) 입력 → 결과 칸에 이미 있다는 오류, 파일은 그대로.
5. `a/b` 입력 → 쓸 수 없는 글자 오류.
6. Esc → 아무것도 바뀌지 않는다.
