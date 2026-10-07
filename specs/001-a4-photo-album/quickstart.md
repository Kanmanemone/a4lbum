# Quickstart: A4 사진 앨범 만들기 검증 가이드

기능이 처음부터 끝까지 동작하는지 확인하는 절차. 인터페이스 세부는 [contracts/cli.md](contracts/cli.md), 배치 규칙은 [data-model.md](data-model.md) 참고.

## 준비물

- Windows 10/11 (맑은 고딕 글꼴 기본 탑재)
- Python 3.10 이상
- 의존성 설치 (저장소 루트에서):

  ```powershell
  pip install -r requirements.txt          # 실행용: reportlab, Pillow
  pip install -r requirements-dev.txt      # 테스트용: pytest, PyMuPDF
  ```

## 1. 자동 테스트

```powershell
python -m pytest tests -q
```

**기대 결과**: 전부 통과. 다음을 확인한다.

| 검증 | 연결 |
|------|------|
| 사진 N장 → ⌈N/2⌉페이지, 홀수면 마지막 페이지 아래 칸 비움 | SC-001, FR-008 |
| 페이지 크기 210×297mm | FR-002 |
| JPEG 이미지 스트림이 원본 파일 바이트와 동일, 원본 파일 해시 불변 | SC-007, FR-002a |
| "2_바다", "10_산", "1_집" → 집·바다·산 순서 | FR-004 |
| "283_벚꽃 축제 모습.jpg" → 라벨 텍스트 "벚꽃 축제 모습" | FR-001a |
| 모든 사진·라벨 사각형이 10mm 여백 안, 라벨-사진 겹침 ≤15%이고 0보다 큼 | FR-005, FR-007, SC-004 |
| EXIF Orientation 6 사진이 세로로 배치됨 | FR-013 |
| 깨진 파일, "7_.jpg", RAW(CR2) → 파일 이름 포함 경고, 나머지로 PDF 생성 | FR-009, FR-010, SC-006 |
| HEIC·AVIF·WEBP·BMP·TIFF 사진 → JPEG, GIF·그래픽·투명 이미지 → PNG로 변환해 배치(알림), 원본·폴더 불변 | FR-014 |
| MPO(여러 장 JPEG) → 변환 없이 JPEG로 배치 | FR-014 |
| "2026여행.jpg" → 라벨 "2026여행" (밑줄 없는 숫자는 유지) | FR-001a |
| 사진 0장 폴더 → exit 1, PDF 없음 | Edge Case |
| 사진 20장 생성 시간 < 60초 | SC-003 |

## 2. 수동 실행 (Claude 없이)

```powershell
mkdir $env:TEMP\album_test
# 휴대폰 사진 3장을 복사해 이름을 바꾼다: 1_집.jpg, 2_바다.jpg, 283_벚꽃 축제 모습.jpg
python scripts/make_album.py $env:TEMP\album_test
```

**기대 결과**: `완료: 사진 3장 → 2페이지, 경고 0건`, `PDF: ...\album_test_album.pdf` 출력. PDF를 열어:

- 1페이지: 위 "집", 아래 "바다" / 2페이지: 위 "벚꽃 축제 모습", 아래 비어 있음
- 각 사진 오른쪽 위 모서리에 걸친 흰색 메모 라벨, 일부만 사진에 겹침
- 세로 사진이 눕지 않고 바르게 서 있음

## 3. Claude Code에서 실행

Claude Code에서 `/album %TEMP%\album_test` 입력.

**기대 결과**: 2번과 같은 PDF 경로·페이지 수가 보고되고, 생성된 PDF 내용이 2번과 같다(SC-002).

## 4. 인쇄 확인 (수동)

1. PDF 뷰어에서 인쇄 → 배율 **"실제 크기"(100%)**, 용지 A4.
2. 인쇄물 확인: 사진·라벨이 잘리지 않음 (SC-004).
3. A4 클리어 파일에 넣고 확인: 사진 2장과 라벨이 파일 테두리에 가려지지 않음 (SC-005).
