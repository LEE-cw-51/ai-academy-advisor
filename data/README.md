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

## 공공데이터 변환 (나이스 + 경기데이터드림, 2-소스)

공식 등록 명단으로 뼈대 파일을 만들 수 있다. 두 소스는 상호보완적이다.

| 소스 | 제공 정보 | 명령 |
|---|---|---|
| `neis` (나이스 학원민원서비스, `acaInsTiInfo`) | 등록번호·개원년도·폐원상태 | `--source neis` (기본값) |
| `gg` (경기데이터드림/공공데이터포털 "경기도_학원 및 교습소 현황") | 전화번호·좌표(위경도)·교습과정명 | `--source gg` |

**gg 소스의 응답 필드명은 2026-07-08 실제 API 호출로 확정됐다** (`FACLT_NM`,
`REFINE_ROADNM_ADDR` 등 — 상세 매핑은 `docs/data-strategy.md` 참고). 이 API는
`Type=json`을 줘도 **XML로 응답**하며, `convert_registry.py`가 `.xml` 입력을
자동 인식해 처리한다.

### 1. 나이스로 먼저 골격 생성

1. https://open.neis.go.kr 에서 API 키 발급 후 `acaInsTiInfo` 조회
   (경기도교육청 `ATPT_OFCDC_SC_CODE=J10`, `ADMST_ZONE_NM=하남시`, `Type=json`)
2. 응답 JSON을 파일로 저장 (예: `data/registry/hanam-neis.json`)
3. 변환:

```bash
cd backend
uv run python -m app.cli.convert_registry ../data/registry/hanam-neis.json ../data/academies \
    --source neis --filter 미사
```

등록번호·학원명·주소·개원년도만 채워지고 나머지는 `null`(미확인)로 생성된다.
폐원/휴원 등 종료 상태의 학원은 기본 제외 (`--include-all`로 포함 가능).

### 2. 경기데이터드림으로 전화번호·좌표 보강

1. https://data.gg.go.kr (또는 https://data.go.kr) 가입 → "경기도_학원 및
   교습소 현황" 활용신청 → 인증키 발급 (국가 공공데이터 OpenAPI는 보통 즉시
   자동승인)
2. `https://openapi.gg.go.kr/TninsttInstutM?KEY=<발급키>&pIndex=1&pSize=<건수>`
   호출 (이 API는 `Type=json`을 줘도 XML로 응답한다). 응답을 파일로 저장
   (예: `data/registry/hanam-gg.xml`)
3. `--enrich`로 실행하면 1단계에서 만든 파일과 매치되는 학원의 **null 필드만**
   채운다 (전화번호·좌표 등). 이미 채워진 값은 절대 덮어쓰지 않는다:

```bash
cd backend
uv run python -m app.cli.convert_registry ../data/registry/hanam-gg.xml ../data/academies \
    --source gg --filter 미사 --course-keyword 수학 --enrich
```

- `--course-keyword 수학`: 교습과정명에 해당 키워드가 포함된 행만 변환 —
  이 프로젝트가 수학 학원에 집중하므로 원천에서 좁혀둔다. `--filter`(지역
  키워드)와 AND로 결합된다.
- `--enrich` 없이 실행하면 기존과 동일하게 diff만 리포트하고 파일은 건드리지 않는다.
- 두 소스 모두 **이미 존재하는 학원 파일을 절대 덮어쓰지 않는다** — 자연키
  (등록번호, 없으면 이름+주소)로 매치하며, `--enrich` 모드에서도 null이 아닌
  값은 그대로 보존된다.

## 현재 들어있는 데이터

2026-07-10 기준 `academies/`에는 경기데이터드림(gg) 소스로 수집한 하남 미사 지역
학원/교습소 실데이터 411건이 들어있다 (`--source gg --filter 미사`로 변환,
`docs/decision-log.md` 참고). 하남시 전체 746건 원본(포털에서 다운로드한 CSV,
`data/registry/hanam-gg.json`으로 변환해 보관)을 지역 필터에 통과시킨 결과다.
개발용 "(예시)" 가상 픽스처 4개는 실데이터 수집이 시작되어 모두 삭제했다.

과목(수학) 여부는 이번 수집에서 필터링하지 않았다 — 공공데이터의 `교습과정명`이
"종합(대)"처럼 넓은 카테고리라 정확한 과목 판별이 어려워, 미사 지역 학원을
과목 무관하게 우선 전부 수집하고 수학 학원 여부는 이후 별도 단계(LLM/RAG 등)에서
가려낼 방침이다. `subjects` 등 과목 관련 필드는 원래도 수동 큐레이션 대상이라
이번 레코드에서는 모두 `null`(미확인)이다.
