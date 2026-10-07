# Contract: Claude Code `/album` 스킬

위치: `.claude/skills/album/SKILL.md`

## 호출

```text
/album <PHOTO_DIR> [추가 지시]
```

- `PHOTO_DIR`가 없으면 사용자에게 사진 폴더 경로를 한 번 묻는다.
- 추가 지시(예: "바탕화면에 저장해 줘")는 [cli.md](cli.md)의 `-o` 같은 옵션으로 바꿔 전달한다. CLI에 없는 기능이면 할 수 없다고 말한다.

## 동작

1. Python을 고른다. 저장소 루트에 `.venv\Scripts\python.exe`가 있으면 그것을, 없으면 `python`을 쓴다(이하 `<PY>`). `<PY> -c "import reportlab, PIL, pillow_heif"`로 의존성을 확인하고, 없으면 `<PY> -m pip install -r requirements.txt`를 실행할지 사용자에게 묻는다.
2. `<PY> scripts/make_album.py "<PHOTO_DIR>" [옵션]`을 실행한다.
3. 종료 코드와 출력을 그대로 전달한다:
   - 0 → PDF 경로, 페이지 수, 경고 목록(파일 이름 포함)을 알리고, "실제 크기(100%)"로 인쇄하라고 안내한다.
   - 1/2 → 오류 내용과 해결 방법을 알린다.

## 금지 사항

- 앨범 레이아웃이나 설명 텍스트를 스크립트 밖에서 바꾸거나 따로 만들지 않는다(FR-011a). 두 실행 방법의 결과는 같아야 한다.
- 사진 파일의 이름을 바꾸거나 수정·이동하지 않는다. 사용자가 명시적으로 요청한 경우만 예외다.
