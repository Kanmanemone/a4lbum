# Contract: 대화창 (005에서 바뀐 부분)

나머지는 [003 gui.md](../../003-photo-order-list/contracts/gui.md)와 같다.

## 안내 문구

"사진 순서" 목록 맨 위, 정렬 줄 아래에 회색 글자로:

- `파일 이름을 두 번 클릭하면 이름을 바꿀 수 있습니다.`
- `Double-click a file name to rename the file.`

## 이름 바꾸기

| 조작 | 결과 |
|------|------|
| 이름 라벨 두 번 클릭 | 순번 뒤 이름 자리에 입력 칸(순번은 보임), 확장자 뺀 이름이 전부 선택되고 포커스 |
| Enter / 포커스가 빠짐 / 다른 이름 두 번 클릭 / 앨범 만들기 | 확정: `rename_photo` → 목록 갱신 |
| Esc | 취소 |
| 만드는 중 두 번 클릭 | 아무 일 없음 |

결과 칸 문구(실패만):

| 경우 | 한국어 | English |
|------|--------|---------|
| 쓸 수 없는 글자 | `오류: 파일 이름에 \ / : * ? " < > | 는 쓸 수 없습니다.` | `Error: a file name cannot contain \ / : * ? " < > |` |
| 이미 있는 이름 | `오류: 같은 이름의 파일이 이미 있습니다: <새 이름>` | `Error: a file with that name already exists: <new name>` |
| 그 밖의 OS 오류 | `오류: <원래 이름>의 이름을 바꾸지 못했습니다: <오류>` | `Error: could not rename <old name>: <error>` |
