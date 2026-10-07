---
name: "album"
description: "사진 폴더로 A4 앨범 PDF를 만든다 (Build a printable A4 photo album PDF from a photo folder). 위·아래 한 장씩, 파일 이름의 설명을 사진 오른쪽 위 메모 라벨로 넣는다."
argument-hint: "<사진 폴더> [추가 지시, 예: 바탕화면에 저장]"
user-invocable: true
disable-model-invocation: false
---

# /album — A4 사진 앨범 PDF 만들기

이 스킬은 `scripts/make_album.py`를 대신 실행해 주는 **바로가기**다. 앨범 내용(순서, 배치, 라벨 문구)은 전부 스크립트가 정한다. 계약: `specs/001-a4-photo-album/contracts/album-command.md`.

## User Input

```text
$ARGUMENTS
```

## 절차

1. **사진 폴더 확인**: 입력에서 사진 폴더 경로를 찾는다. 없으면 사용자에게 한 번 묻는다.
2. **Python 고르기**: 저장소 루트에 `.venv\Scripts\python.exe`가 있으면 그것을, 없으면 `python`을 쓴다. 이하 `<PY>`.
3. **의존성 확인**: `<PY> -c "import reportlab, PIL, pillow_heif"`가 실패하면 `<PY> -m pip install -r requirements.txt`를 실행해도 될지 사용자에게 묻고, 동의하면 설치한다.
4. **추가 지시 변환**: 추가 지시는 CLI 옵션으로만 바꾼다.
   - 저장 위치/파일 이름 → `-o "<경로>.pdf"`
   - 라벨 글꼴 → `--font "<TTF 경로>"`
   - 그 밖의 요청(레이아웃 변경, 표지, 사진 편집 등)은 지원하지 않는다고 알리고 옵션 없이 진행할지 묻는다.
5. **실행** (저장소 루트에서): `<PY> scripts/make_album.py "<사진 폴더>" [옵션]`
6. **결과 전달**:
   - 종료 코드 0: `PDF:` 경로, 사진 수·페이지 수, `알림:`·`경고:` 줄을 **그대로** 보여 준다. 그리고 "PDF 뷰어에서 A4, **실제 크기(100%)**로 인쇄하세요"라고 안내한다.
   - 종료 코드 1/2: `오류:` 내용을 보여 주고 해결 방법을 한 줄로 제안한다(폴더 경로 확인, PDF 뷰어 닫기, RAW는 JPEG로 내보내기 등).

## 하지 말 것

- 스크립트 밖에서 앨범 레이아웃이나 라벨 문구를 바꾸거나 PDF를 따로 만들지 않는다. `/album`과 스크립트 직접 실행의 결과는 같아야 한다.
- 사용자가 명시적으로 요청하지 않는 한 사진 파일의 이름을 바꾸거나 수정·이동·삭제하지 않는다.

## 사진 이름 규칙 (사용자 안내용)

- `숫자_설명.jpg` → 라벨에 `설명`이 들어간다. 예: `283_벚꽃 축제 모습.jpg` → "벚꽃 축제 모습"
- 순서는 파일 이름순이고 앞 숫자는 숫자 크기순이다(`2_…`가 `10_…`보다 앞).
- JPEG/PNG는 그대로, HEIC·AVIF·WEBP·GIF·BMP·TIFF는 스크립트가 자동 변환해 넣는다(사진은 JPEG 95, 그래픽·투명 이미지는 PNG; 원본은 그대로). 카메라 RAW는 지원하지 않는다.
- 밑줄 없이 숫자로 시작하는 이름(`2026여행.jpg`)은 숫자를 떼지 않는다.
