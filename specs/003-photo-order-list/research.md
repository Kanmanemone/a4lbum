# Research: 사진 순서 목록과 "숫자_" 빼기 선택

## R1. 목록에 보일 파일을 정하는 규칙

- **Decision**: `make_album.list_photo_files(folder)`가 `scan_folder`와 같은 거르기 조건을 쓴다. 대상은 파일이고 숨김·시스템 파일이 아니며 확장자가 `PHOTO_EXTS`인 것이다. HEIC/HEIF는 pillow-heif가 있을 때만 포함한다. 거르기 조건은 두 함수가 함께 쓰는 `_photo_entries()` 하나로 모은다. 사진 파일은 열지 않는다.
- **Rationale**: 목록과 앨범의 대상이 어긋나지 않는다. 파일을 열지 않으므로 300장도 즉시 나온다(SC-001). 열 수 없는 파일은 만들 때 기존처럼 경고를 내고 건너뛴다(spec Edge Cases).
- **Alternatives considered**: 목록을 만들 때 `_read_photo`로 검증하는 방법은 HEIC 디코딩 등으로 느려 탈락했다. `scan_folder`를 그대로 부르는 방법은 변환까지 해서 탈락했다.

## R2. "만든 날짜"·"수정한 날짜" 값

- **Decision**: 수정한 날짜는 `st_mtime`이다. 만든 날짜는 `st_birthtime`(Python 3.12+, Windows)이고, 없으면 `st_ctime`을 쓴다(Windows에서 3.12 미만의 `st_ctime`은 만든 날짜다). 날짜가 같으면 `natural_key`(이름 순)로 놓는다. 역순은 정렬 결과 리스트를 그대로 뒤집는다.
- **Rationale**: 탐색기의 "만든 날짜"/"수정한 날짜"와 같다. 동률을 이름으로 풀어 순서가 매번 같다. "역순 = 정확히 뒤집기"라서 체크를 켜고 끄면 원래 순서로 돌아온다(US1-4).
- **Alternatives considered**: EXIF 촬영 날짜는 사진을 열어야 해 느리고, 사용자가 말한 "만든 날짜"와도 다르다(spec Assumptions).

## R3. 목록 위젯 형태

- **Decision**: `Canvas` + 내부 `Frame`으로 스크롤 목록을 만든다. 줄마다 `순번  파일 이름` 라벨 하나와 `ttk.Button` 4개("맨 위로", "▲" 한 칸 위로, "▼" 한 칸 아래로, "맨 아래로")를 둔다. ⤒/⤓ 같은 기호는 글꼴에 따라 깨지거나 뜻이 불분명해 사용자가 말한 이름을 글자로 쓴다. 줄 위젯은 폴더를 바꿔 개수가 달라질 때만 다시 만든다. 순서를 바꾸면 라벨 글자만 고쳐 쓰므로 클릭 반응이 빠르다. 마우스 휠로 스크롤된다.
- **Rationale**: 사용자가 "리스트 항목 별로 버튼"을 원했다. `Treeview` 셀을 버튼처럼 쓰면 버튼으로 보이지 않는다. 줄 재사용으로 수백 장도 충분히 빠르다.
- **Alternatives considered**: `Treeview` + 선택 항목용 버튼 4개(목록 밖)는 위젯이 적지만 요청한 형태가 아니라 탈락했다. 드래그로 옮기기는 범위 밖이다.

## R4. 정렬 방식 표시와 "커스텀"

- **Decision**: 읽기 전용 `ttk.Combobox`이고, 값은 정렬 방식 3개다. 옮기기 버튼을 누르면 콤보박스 글자를 "커스텀"으로 바꾸고(값 목록에는 없음) "역순으로 정렬"을 비활성화한다. 콤보박스에서 방식을 고르면(`<<ComboboxSelected>>`) 다시 정렬하고 역순을 활성화한다.
- **Rationale**: "커스텀"은 결과 상태지 사용자가 고르는 방식이 아니다(FR-007). 커스텀일 때 역순의 의미가 모호하므로 막는다(FR-008).
- **Alternatives considered**: 커스텀에서 역순을 누르면 현재 목록을 뒤집는 방법은 체크 상태와 실제 순서가 따로 놀아 탈락했다.

## R5. 순서를 앨범에 전달하는 방법

- **Decision**: `build_album(..., order=[파일 이름…])`. `scan_folder` 결과를 `order`의 위치로 정렬한다. `order`에 없는 파일(목록 이후 생긴 파일)은 뒤에 `natural_key` 순으로 붙인다. `order`에만 있고 폴더에 없는 이름은 무시한다.
- **Rationale**: 목록을 띄운 뒤 폴더가 바뀌어도 앨범이 깨지지 않는다(spec Edge Cases). 폴더 읽기·변환·경고 흐름은 그대로 쓴다.
- **Alternatives considered**: 경로 목록만 받아 폴더를 다시 읽지 않는 방법은 숨김·RAW 경고 흐름을 따로 만들어야 해서 탈락했다.

## R6. "숫자_" 빼기

- **Decision**: `extract_caption(file_name, strip_number=True)`, `scan_folder(..., strip_number=True)`, `build_album(..., strip_number=True)`. 기본값이 기존 동작이라 CLI·`/album`은 그대로다. 창에서는 `tk.BooleanVar(value=False)`를 넘긴다(체크 해제가 기본, FR-010). 해제면 설명은 확장자를 뺀 이름을 `strip()`한 것이다.
- **Rationale**: 사용자는 "체크 시에만 제거"를 요청했다. CLI는 범위 밖이라 기존 동작을 유지한다.
- **Alternatives considered**: 기본값을 CLI까지 "빼지 않음"으로 바꾸는 방법은 FR-011 위반이라 탈락했다. CLI 옵션 추가는 요청 밖이라 하지 않는다.

## R7. 창 크기

- **Decision**: 처음 크기는 약 760×680, 최소 크기는 약 560×520으로 키운다(기존과 같이 화면 배율을 곱한다). 남는 높이는 목록이 가장 많이 차지하고, 결과 영역은 높이 6줄로 줄인다.
- **Rationale**: 목록이 주 작업 영역이 되었다.
