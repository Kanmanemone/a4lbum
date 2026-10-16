# Contract: `make_album` 모듈에 더하는 것

기존 함수의 인자는 모두 뒤에 기본값과 함께 더한다. 기본값으로 부르면 결과가 이 기능 전과 같다(FR-011, SC-005).

## `extract_caption(file_name, strip_number=True) -> str`

- `strip_number=True`: 기존과 같다. 맨 앞 `숫자_`를 한 번 빼고 `strip()`한다. 예: `283_벚꽃 축제 모습.jpg` → `벚꽃 축제 모습`
- `strip_number=False`: 확장자를 뺀 이름을 `strip()`한다. 예: `283_벚꽃 축제 모습.jpg` → `283_벚꽃 축제 모습`

## `list_photo_files(folder) -> list[PhotoFile]`

- `scan_folder`가 앨범에 넣으려고 시도할 파일과 같은 집합이다. 숨김·시스템 파일, 사진 확장자가 아닌 파일, RAW, pillow-heif가 없을 때의 HEIC/HEIF는 뺀다.
- 사진을 열거나 변환하지 않는다. 폴더가 없거나 읽을 수 없으면 `[]`이다.
- `PhotoFile(name, created, modified, taken=None)`: [data-model.md](../data-model.md). 이 함수는 `taken`을 채우지 않는다.

## `date_taken(path) -> float | None`

- 사진의 EXIF 촬영 시각(DateTimeOriginal, 없으면 DateTimeDigitized)을 로컬 시각 epoch 초로 돌려준다. 헤더만 읽고 픽셀은 풀지 않는다.
- 촬영 정보가 없거나, 날짜가 잘못됐거나(`0000:00:00 …`), 파일을 열 수 없으면 `None`이다.

## `scan_folder(folder, work_dir, strip_number=True)`

라벨 설명을 `extract_caption(name, strip_number)`로 만든다. 그 밖은 기존과 같다.

## `build_album(photo_dir, output=None, font=None, order=None, strip_number=True)`

- `order=None`: 기존처럼 `natural_key` 순서다.
- `order=[이름…]`: `order`에 있는 사진은 그 순서대로 놓는다. 없는 사진은 그 뒤에 `natural_key` 순으로 붙인다. 폴더에 없는 이름은 무시한다.
- `strip_number`는 `scan_folder`로 넘긴다.
- 반환값·예외·경고는 기존과 같다.
