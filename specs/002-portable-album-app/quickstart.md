# Quickstart: 휴대용 앨범 프로그램 검증

창의 동작은 [contracts/gui.md](contracts/gui.md), 빌드 과정은 [contracts/build.md](contracts/build.md)를 참고한다.

## 1. 자동 테스트

```powershell
.\.venv\Scripts\python -m pytest -q
```

**기대**: 001 테스트와 `tests/test_app.py`가 모두 통과한다. `test_app.py`는 다음을 확인한다.
- 기본 출력 경로가 따라 바뀌는지, 직접 고른 경로는 유지되는지
- 폴더가 빈 채로 실행했을 때의 안내
- 성공했을 때 결과 문구가 CLI와 같고 "PDF 열기"가 활성이 되는지
- 실패했을 때 경고와 오류 문구가 보이는지
- exe 인자로 받은 폴더가 미리 채워지는지

## 2. 빌드 (smoke test 포함)

```powershell
powershell -ExecutionPolicy Bypass -File build_portable.ps1
```

**기대**: smoke test가 통과하고 `완료: 앨범 만들기.exe + app\ (… MB)`가 출력된다. smoke test가 실패하면 저장소의 exe와 `app\`은 그대로다.

## 3. 받는 사람 입장에서 확인 (수동)

1. 저장소를 GitHub에서 Download ZIP으로 받아(또는 `git archive --format=zip`) `바탕 화면\앨범 프로그램 시험\`처럼 한글·공백이 든 폴더에 푼다(SC-005).
2. `앨범 만들기.exe`를 더블클릭하면 검은 명령창 없이 대화창이 뜬다(FR-002, SC-002).
3. 사진 폴더 "찾아보기…"로 폴더를 고르면 저장 경로가 자동으로 채워진다.
4. "앨범 만들기"를 누르면 결과 영역에 `완료: …`와 `PDF: …`가 나오고, "PDF 열기"가 PDF를 연다.
5. 같은 폴더로 `python scripts/make_album.py <폴더> -o 비교.pdf`를 실행하면 결과 줄과 PDF 내용이 같다(SC-003).
6. 빈 폴더, 폴더 미선택, PDF를 연 채로 다시 만들기를 해 보고, 창에 안내가 나오며 꺼지지 않는지 확인한다(SC-004).
7. 사진 폴더를 exe 아이콘 위로 끌어다 놓으면 폴더가 채워진 창이 뜬다(FR-008).
