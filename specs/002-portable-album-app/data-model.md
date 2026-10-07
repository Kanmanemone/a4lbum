# Data Model: 대화창 상태

**Feature**: [spec.md](spec.md)

저장소는 없다. 창이 열려 있는 동안만 다음 상태를 가진다. 앨범 자체의 데이터 모델은 [001 data-model](../001-a4-photo-album/data-model.md)을 그대로 쓴다.

## AppState

| Field | Type | 설명 / 규칙 |
|-------|------|-------------|
| `photo_dir` | str | 사진 폴더 경로 칸. 시작할 때 exe 인자로 받은 폴더가 있으면 그 값이다(FR-008). |
| `output` | str | 저장 PDF 경로 칸. |
| `output_custom` | bool | 사용자가 저장 경로를 직접 바꿨는지 여부. False면 `photo_dir`가 바뀔 때마다 `default_output_path(photo_dir)`로 다시 채운다(Edge Case). |
| `busy` | bool | 만드는 중이면 True. 이 동안 "앨범 만들기"와 두 "찾아보기" 버튼은 비활성이고, 창 닫기는 막는다(FR-006, research R6). |
| `last_pdf` | str \| None | 마지막으로 성공한 PDF 경로. 있을 때만 "PDF 열기"가 활성이다(FR-007). |
| `log` | 텍스트 | 결과 표시 영역. 실행할 때마다 지우고 새로 쓴다. |

## 상태 전이

```text
[준비] --앨범 만들기(폴더 비었음)--> [준비] + "사진 폴더를 먼저 골라 주세요."
[준비] --앨범 만들기--> [만드는 중] (busy=True, last_pdf=None, log="만드는 중…")
[만드는 중] --성공--> [준비] (log = report_lines, last_pdf=출력 경로)
[만드는 중] --AlbumError--> [준비] (log = 경고 줄 + "오류: …")
[만드는 중] --예상 못한 예외--> [준비] (log = "오류: 예상하지 못한 문제가 생겼습니다: <내용>")
```
