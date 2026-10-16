# Data Model: 사진 순서 목록

## PhotoFile (목록 한 줄)

`make_album.list_photo_files(folder)`가 돌려준다. 사진을 열지 않는다.

| 필드 | 뜻 |
|------|----|
| `name` | 파일 이름(확장자 포함). 폴더 안에서 고유하며 목록·`order`의 키다. |
| `created` | 만든 날짜(epoch 초). `st_birthtime`, 없으면 `st_ctime` |
| `modified` | 수정한 날짜(epoch 초). `st_mtime` |
| `taken` | 촬영한 날짜(epoch 초) 또는 None. 창이 "촬영한 날짜 순 정렬"을 처음 고를 때 `date_taken`으로 채운다 |

반환 순서는 정해져 있지 않다. 정렬은 `sort_photos`가 한다.

## 정렬 상태 (창)

| 필드 | 값 | 기본 |
|------|----|------|
| `sort_mode` | `"이름 순 정렬"` / `"만든 날짜 순 정렬"` / `"수정한 날짜 순 정렬"` / `"촬영한 날짜 순 정렬"` / `"커스텀"` | `"이름 순 정렬"` |
| `dated_by` | 목록에 보일 날짜의 정렬 방식(마지막으로 정렬한 방식, 커스텀이어도 유지) | `"이름 순 정렬"`(날짜 없음) |
| `reverse` | bool. `sort_mode == "커스텀"`이면 비활성(값은 유지) | False |
| `photos` | 현재 목록 순서의 `PhotoFile` 리스트 | `[]` |

### 상태 전이

```text
폴더 바뀜 ──▶ photos = list_photo_files(폴더)
              sort_mode가 "커스텀"이면 "이름 순 정렬"로 되돌림
              sort_photos(photos, sort_mode, reverse)

방식 고름(3개 중) ──▶ sort_mode = 그 방식, 역순 활성, sort_photos(...)
역순 토글 ─────────▶ sort_photos(...)          (커스텀이 아닐 때만 가능)
버튼 4개 누름 ────▶ photos에서 해당 항목 이동, sort_mode = "커스텀", 역순 비활성
                     (이동이 없는 경우—맨 위에서 ▲ 등—에도 "커스텀"이 된다: "버튼을 건드는 순간")
```

## sort_photos(photos, mode, reverse) → list

- 이름: `natural_key(name)`
- 만든 날짜: `(created, natural_key(name))`
- 수정한 날짜: `(modified, natural_key(name))`
- 촬영한 날짜: `(taken, natural_key(name))`, `taken`이 None이면 `modified`로 대신
- `reverse`이면 결과를 뒤집는다.

## 앨범 옵션 (`build_album`에 전달)

| 인자 | 창에서 | CLI·`/album` |
|------|--------|--------------|
| `order` | "앨범 만들기"를 누른 순간 `[p.name for p in photos]` | `None`(이름 순) |
| `strip_number` | "숫자_" 체크박스(기본 False) | `True`(기존 동작) |
