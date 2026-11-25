# Quickstart: 사진 목록에 마우스를 올리면 썸네일 보이기

## 자동 확인

```powershell
.venv\Scripts\python -m pytest
```

`tests/test_app.py`의 006 테스트(`make_thumbnail` 크기·방향·실패, 머물면 뜸, 나가면 닫힘, 일찍 나가면 안 뜸, 깨진 파일 문구, 캐시 재사용)와 기존 테스트가 모두 통과해야 한다.

## 손으로 확인

1. `examples\photos`의 복사본으로 `python scripts/album_app.py <폴더>`를 연다.
2. `1_Beach.jpg` 이름 위에 마우스를 두면 0.4초쯤 뒤 해변 사진이 뜬다. 마우스를 치우면 사라진다.
3. 이름들 위로 마우스를 빠르게 훑으면 멈춘 곳의 사진만 뜬다.
4. HEIC 사진이 있는 폴더에서도 창이 멈추지 않고 잠시 뒤 뜬다.
5. 창 오른쪽 아래 끝 이름에서도 미리보기가 화면 안에 있다.
