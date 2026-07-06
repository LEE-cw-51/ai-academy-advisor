# 데이터 디렉터리

이 저장소의 **정본(source of truth)은 `data/academies/`의 JSON 파일**이다.
DB는 임포터가 재구성하는 파생 저장소이며, 학원 데이터의 추가·수정은 항상
파일 수정 → PR 리뷰 → 임포트 순서로 진행한다. (쓰기 API는 의도적으로 없음)

## 파일 구조

- `academies/<ascii-slug>.json` — 학원당 1파일. 파일명은 ASCII 소문자와 하이픈만 사용.
- JSON 키는 DB 컬럼과 1:1로 대응한다 (필드 사전: `docs/data-strategy.md`).

## 값 규칙 (3상태 원칙)

| 값 | 의미 |
|---|---|
| `true` | 확인됨 — 있음 |
| `false` | 확인됨 — 없음 |
| `null` | **미확인** (추측 금지) |

- 모든 키를 항상 쓰고, 미확인 값은 `null`로 남긴다. 수집 공백이 한눈에 보이게 하기 위함이다.
- 확인하지 않은 사실을 `true`/`false`로 적지 않는다. 이 구분이 "정확한 DB"의 핵심이다.
- `source_note`에 출처(홈페이지, 전화 확인, 공공데이터 등)를, `last_verified_at`에 확인일을 기록한다.

## 자연키 (중복 방지)

1. `registration_number` — 공식 학원 등록번호 (가능하면 반드시 채울 것)
2. `(name, address)` — 등록번호가 없을 때의 대체 키

같은 등록번호나 같은 (학원명, 주소)를 가진 파일이 2개 있으면 임포트가 거부된다.

## 임포트

```bash
cd backend
uv run python -m app.cli.import_academies ../data/academies --dry-run   # 검증만 (DB 불필요)
uv run python -m app.cli.import_academies ../data/academies             # DB 업서트
```

- 임포트는 **sync 의미론**: 파일 내용으로 전 필드를 덮어쓴다 (`null` 포함).
- 파일에 없는 DB 행은 삭제하지 않고 리포트만 한다. 폐원 등으로 행을 지울 때는
  파일 삭제 후 DB에서 수동으로 삭제한다.

## 공공데이터 변환 (나이스 학원민원서비스)

공식 등록 명단으로 뼈대 파일을 만들 수 있다.

1. https://open.neis.go.kr 에서 API 키 발급 후 `acaInsTiInfo` 조회
   (경기도교육청 `ATPT_OFCDC_SC_CODE=J10`, `ADMST_ZONE_NM=하남시`, `Type=json`)
2. 응답 JSON을 파일로 저장 (예: `data/registry/hanam.json`)
3. 변환:

```bash
cd backend
uv run python -m app.cli.convert_registry ../data/registry/hanam.json ../data/academies --filter 미사
```

- 등록번호·학원명·주소·개원년도만 채워지고 나머지는 `null`(미확인)로 생성된다.
- **이미 존재하는 학원 파일은 절대 덮어쓰지 않고** 공공데이터와의 차이만 리포트한다.
- 폐원/휴원 학원은 기본 제외 (`--include-all`로 포함 가능).

## 현재 들어있는 데이터

`academies/`의 `*(예시)` 파일 4개는 **개발용 가상 픽스처**다 (실존 학원 아님,
전화번호는 `031-000-xxxx` 가짜 패턴). 실제 수집 데이터가 쌓이기 시작하면
예시 파일은 삭제한다.
