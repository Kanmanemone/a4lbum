# Research: 사진 목록에 마우스를 올리면 썸네일 보이기

## R1. 디코딩 시간과 스레드

- **측정** (4032×3024, 이 PC): JPEG 163ms, PNG 407ms, HEIC 1720ms (`draft` + `exif_transpose` + `thumbnail(320)`).
- **Decision**: 디코딩은 데몬 스레드에서 하고 결과는 `queue.Queue`로 받아 Tk `after` 폴링으로 꺼낸다(앨범 만들기 `_run`/`_poll`과 같은 패턴). `ImageTk.PhotoImage`는 UI 스레드에서 만든다.
- **Rationale**: HEIC 1.7초를 UI 스레드에서 하면 창이 멈춘다. Tk는 다른 스레드에서 부르면 안 된다.
- **Alternatives considered**: 동기 디코딩은 HEIC에서 탈락했다. 스레드 풀·취소 가능한 작업은 요청이 0.4초 머무를 때만 생겨 필요 없다.

## R2. 뜨는 시점과 위치

- **Decision**: 이름 라벨 `<Enter>`에서 0.4초 `after`를 걸고, `<Leave>`·`<ButtonPress>`·휠 스크롤·이름 편집·목록 갱신에서 취소하고 닫는다. 위치는 포인터 오른쪽 아래(+20, +20)이고, 화면 밖으로 나가면 왼쪽·위로 당긴다.
- **Rationale**: 빠르게 지나가는 줄은 디코딩조차 시작하지 않는다(US1-3). 기존 `Tooltip`은 즉시 뜨는 글자용이라, 같은 모양(테두리 없는 `Toplevel`)을 쓰되 지연·이미지는 `PhotoList`가 다룬다.

## R3. 크기와 방향

- **Decision**: 긴 변 `240 × zoom` 화면 픽셀(zoom은 창과 같은 tk scaling 기준). `ImageOps.exif_transpose`로 앨범과 같은 방향. JPEG는 `draft`로 디코딩을 줄인다.

## R4. 캐시

- **Decision**: `{경로 문자열: PIL.Image 또는 None(실패)}`. 폴더를 새로 읽을 때(`load_photos`) 비운다. 이름을 바꾸면 경로가 달라져 자연히 새로 만든다.
- **Rationale**: 같은 사진을 다시 볼 때 바로 뜬다(SC-001). 320px 이하 그림이라 수백 장도 메모리 부담이 작다.
