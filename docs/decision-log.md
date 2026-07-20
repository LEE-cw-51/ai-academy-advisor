# 의사결정 로그

주요 기술적/제품적 의사결정과 그 이유를 기록한다.

## 2026-07-14 — AI 추천 엔드포인트 스켈레톤 + engagement API (Phase 4b-skeleton / 4c)

- **자연어 추천(`POST /recommendations/ai`)을 provider 포트 경유 파이프라인으로 구현**
  (`ai_recommendation_service.recommend`): 질문 기록 → 의도 분석 → 필터 → 벡터 근거 검색
  → 추천 이유 생성. 기본 provider가 전부 stub이라 키·비용 없이 end-to-end 동작하고,
  실제 임베딩/LLM/pgvector·LlamaIndex는 config만 바꿔 교체된다.
- **의도 분석은 규칙 기반이 현재 기본 구현** (`app/services/intent.py`의 `parse_intent`):
  stub LLM은 구조화 출력을 못 하므로, 학년/커리큘럼/수업형태/지역/예산을 키워드로 뽑아
  기존 `RecommendationRequest`로 변환한다. 순수 함수라 LLM 기반 파서로 저비용 교체 가능.
- **필터링은 기존 `academy_repository.list_recommendations`를 그대로 재사용** — 규칙 기반
  추천 로직을 중복 구현하지 않고 AI 파이프라인의 후보 선별 단계로 흡수.
- **RAG 근거 검색은 `vector_store.search()` 포트로만 호출**: 리뷰 ingest 파이프라인과 실제
  pgvector 스토어는 4b로 이연했으므로, 지금은 stub in-memory 스토어가 비어 있어 근거가
  빈 배열일 수 있다. 포트 호출 경로는 완성돼 실제 스토어로 갈아끼우면 그대로 동작.
- **engagement 쓰기 API(`/events`,`/feedback`,`/waitlist`)는 승인된 DB 직접 쓰기 예외**:
  `data-strategy.md`가 사용자 행동/리뷰 데이터를 git 정본이 아닌 DB 직접 쓰기로 규정한 것과
  일관. KPI(외부 행동률·대기자 등록률) 측정이 MVP 검증 목표(§5)의 핵심이라 우선 구현.
- **`/events`는 없는 `academy_id`에 404, 잘못된 `event` enum에 422**: 기존 `academies.py`의
  404 관례(존재 검증 후 HTTPException)와 Pydantic enum 검증을 각각 재사용. `academy_id`는
  nullable이라 학원 무관 이벤트도 허용.
- **`/waitlist`는 email/kakao 중 최소 하나 필수** (`model_validator`): 연락 수단 없는 등록을
  막아 대기자 데이터의 유효성을 보장.

## 2026-07-14 — AI 기반 골격: provider 추상화 + 리뷰·engagement 스키마 (Phase 4a)

- **얇은 Protocol 포트 채택** (`app/providers/base.py`): `EmbeddingProvider`/`LLMProvider`/
  `VectorStore`를 `typing.Protocol`로 정의하고 서비스 계층은 이 포트에만 의존한다.
  - 이유: 사용자 요구("기술스택·API를 상황에 따라 교체 가능하게")의 실체는 모델
    provider·벡터 스토어의 교체다. 얇은 포트 + config 선택(`factory.py`) 방식이 기존
    계층형(api/service/repository) 구조와 정합하고 의존성을 최소화한다.
- **기본 provider는 전부 stub** (`stub.py`): 실제 LLM/임베딩 호출 없이 결정적 구현으로
  파이프라인 골격만 검증. API 키·비용 0, 무설정 기동. 테스트 안정성 확보(결정적).
- **LlamaIndex는 다음 단계(4b)에서 `RagEngine` 포트 뒤에 채택**: LlamaIndex 자체가
  llm/embed_model/vector_store를 플러그블하게 다루므로 "핵심 엔진 채택"과 "교체 가능"이
  충돌하지 않는다. 엔진조차 단일 포트 뒤에 두어 교체 비용을 낮게 유지한다. 이번 단계에는
  llama-index/openai/sentence-transformers 의존성을 **추가하지 않음**.
- **리뷰·engagement 테이블 신설 + pgvector 도입** (마이그레이션 `0003`):
  `reviews`(임베딩 포함) / `search_history` / `click_logs` / `feedback` / `waitlist`.
  이 테이블들은 학원 사실(Fact) 테이블과 달리 **git 정본이 아닌 DB 직접 쓰기**다
  (`data-strategy.md` Phase 2 AI 요약 / Phase 3 사용자 데이터, engagement=런타임 로그).
- **`embedding` 컬럼은 이중화**: `JSON().with_variant(Vector(dim), "postgresql")` — 기존
  `academy.SubjectsJSON` 관례 재사용. SQLite 테스트는 JSON, 운영 postgres는 pgvector.
  마이그레이션은 dialect 가드(`op.get_bind().dialect.name`)로 postgres에서만 확장/Vector 생성.
- **`embedding_dim` 고정(기본 1024) = 마이그레이션 결합**: pgvector 컬럼 차원은 DDL 시점에
  고정되므로 임베딩 모델을 차원이 다른 것으로 바꾸면(예: bge-m3 1024 → OpenAI 1536)
  마이그레이션이 필요하다. 이 트레이드오프를 인지하고 기본값을 config로 노출.
- **ANN 인덱스(ivfflat/hnsw)는 이번에 만들지 않음**: 인덱스는 데이터가 쌓인 뒤 파라미터
  튜닝이 필요하므로 실제 RAG 단계(4b)로 이연. 지금은 컬럼만 준비.

## 2026-07-10 — 하남 미사 실데이터 전량 재수집 (CSV 업로드, 411건)
- **1차 수집(82건, 대화창 수기 입력)의 한계 해소**: 746건 전체를 채팅으로 옮겨
  적는 방식은 비현실적이라 일부(미사 주소 위주 선별)만 반영됐었다. 사용자가
  경기데이터드림 포털에서 하남시 조회 결과를 **CSV로 다운로드해 첨부**하면서
  746건 전체를 정확히 확보할 수 있었다.
- **CSV는 CP949(EUC-KR 계열) 인코딩** — `file` 명령이 이를 ISO-8859로 오탐지할
  정도로 흔한 함정. `encoding="cp949"`로 읽어야 한글이 깨지지 않는다.
- **CSV 헤더(한글)는 기존에 확정한 실제 API 필드명(영문)과 1:1 대응**:
  `시군명`→`SIGUN_NM`, `업종구분명`→`INDUTYPE_DIV_NM`, `시설명`→`FACLT_NM`,
  `교습과정명`→`CRSE_CLASS_NM`, `전화번호`→`TELNO`, `소재지우편번호`→`REFINE_ZIP_CD`,
  `소재지지번주소`→`REFINE_LOTNO_ADDR`, `소재지도로명주소`→`REFINE_ROADNM_ADDR`,
  `WGS84위도`→`REFINE_WGS84_LAT`, `WGS84경도`→`REFINE_WGS84_LOGT`. 등록번호 필드는
  CSV에도 없음 — 이 데이터셋엔 등록번호가 없다는 기존 추정이 다시 확인됨.
- **CSV → data.go.kr 표준 JSON 봉투로 1회성 변환** (스크래치패드 스크립트, 저장소에
  커밋하지 않음) 후 `data/registry/hanam-gg.json`으로 저장 — 기존 `extract_rows()`/
  `gg_row_to_record()`를 코드 변경 없이 그대로 재사용. 파싱된 746건은 API의
  `list_total_count`와 정확히 일치.
- **`convert_registry.py --source gg --filter 미사` 재실행**: 기존 82건은 자연키
  (이름+주소) 매치로 `load_existing_keys()`가 인식해 덮어쓰지 않고 스킵, 신규
  329건만 추가 생성 → 총 411건. 오류 0건.
- 업로드된 CSV 원본 파일은 세션 임시 업로드 경로에만 존재하며 저장소에는 포함하지
  않는다 (원본은 `data/registry/hanam-gg.json`으로 이미 변환·보관됨).

## 2026-07-10 — 하남 미사 실데이터 1차 수집 (gg 단일 소스)
- **경기데이터드림(gg) `SIGUN_NM=하남시` 서버측 필터로 하남시 전체 746건 확보**
  (사용자가 직접 API 호출; 승인 전 키는 파라미터를 무시하는 샘플 키 고정 응답이었고,
  포털에서 정식 승인 후 재호출하여 정상 필터링 확인). `SIGUN_CD`는 실제 데이터에
  값이 비어 있어 필터로 쓸 수 없었다 (`SIGUN_NM`만 사용).
- **NEIS 골격 없이 gg 단일 소스로 진행**: 사용자가 NEIS API 키를 보유하지 않아
  2-소스 순차 워크플로(나이스 골격 → gg enrich) 대신 gg만으로 신규 파일을 생성.
  자연키는 등록번호 없이 이름+주소만 사용 (gg 데이터셋에 등록번호 필드가 없다는
  기존 문서의 추정과 일치).
- **과목(수학) 필터링을 이번 수집에서 강제하지 않음**: `CRSE_CLASS_NM`(교습과정명)이
  "종합(대)"·"입시.검정 및 보습" 같은 넓은 카테고리라 "수학" 키워드로 정확히
  걸러내기 어려움을 확인. 대신 지역(`--filter 미사`, 주소 부분 일치)만 적용해
  미사 지역 학원을 과목 무관하게 전부 수집하고, 수학 학원 여부는 이후 별도 단계
  (LLM/RAG 기반 후처리)에서 가려내기로 함. `subjects`는 원래도 자동 채움 대상이
  아니라 수동 큐레이션 영역이라 이 결정이 3상태 원칙과 충돌하지 않는다.
- **원본 API 응답은 이 세션의 대화 relay를 통해 전달받아, 전량(746건) 대신 주소에
  "미사"가 포함된 학원 위주로 선별해 `data/registry/hanam-gg.xml`에 저장** —
  세션이 `*.go.kr`에 직접 접근할 수 없어 사용자가 대화창에 응답을 붙여넣는 방식
  으로 전달했고, 746건 전체를 한 글자씩 옮기는 대신 실질적으로 `--filter 미사`를
  통과할 주소만 우선 선별해 입력량을 줄였다 (변환 결과 82건 생성, 43건 필터 제외 —
  일부는 의도적으로 선별 단계에서 이미 걸러졌고 일부는 CLI의 이름+주소 필터를
  통과하지 못함).
- **기존 "(예시)" 개발용 픽스처 4개를 삭제**하고 위 82건으로 교체 (`data/README.md`
  에 이미 명시된 트리거 조건 충족).
- **`tests/test_importer.py`의 하드코딩된 `4`를 파일 개수 기반 동적 계산으로 변경**:
  정본 픽스처 개수가 예시 4건에서 실데이터 82건으로 바뀌며 기존 테스트가 깨짐 —
  향후 데이터가 늘어나도 테스트가 픽스처 개수와 독립적으로 유지되도록 수정.

## 2026-07-08 — gg(경기데이터드림) API 실제 응답 확인 및 필드명 확정
- **실제 서비스키로 `https://openapi.gg.go.kr/TninsttInstutM` 호출해 응답 확보**
  (사용자가 직접 브라우저로 호출; 이 Claude Code 세션은 조직 네트워크 정책상
  `*.go.kr` 아웃바운드가 차단되어 있어 세션 내에서는 호출 불가했음).
  응답은 `INFO-000`(정상 처리) XML, `list_total_count=34012`.
  서비스키는 코드/git 어디에도 포함하지 않았다 (수동 다운로드 워크플로 유지).
- **`gg_row_to_record()`의 best-effort 후보 키를 실제 필드명으로 확정**:
  `FACLT_NM`(시설명) / `REFINE_ROADNM_ADDR`·`REFINE_LOTNO_ADDR`(주소) /
  `TELNO`(전화번호, 기존 추측이 우연히 맞았음) / `REFINE_WGS84_LAT`·
  `REFINE_WGS84_LOGT`(좌표, 기존 추측이 맞았음) / `CRSE_CLASS_NM`(교습과정명).
  등록번호·등록상태 필드는 응답에 없음을 확인 — 기존 문서의 추정이 맞았음
  (자연키는 이름+주소만 사용, 상태 기준 필터링은 적용 안 됨)
- **XML 입력 파싱 지원 추가** (`convert_registry.py`의 `parse_xml_payload()`):
  이 API는 `Type=json` 파라미터를 줘도 XML로 응답함이 확인됨. 새 XML을
  기존 "나이스류" JSON 봉투 구조로 변환해 `extract_rows()`를 그대로
  재사용하도록 구현 — 별도 파싱 경로를 늘리지 않고 기존 로직 재사용
- **범위를 필드명 수정 + XML 파싱까지로 한정**: 앱이 이 API를 자동으로 호출하는
  기능(서비스키 설정, 라이브 HTTP fetch)은 이번에 추가하지 않음 — 기존과 동일하게
  "사람이 포털에서 수동 다운로드 → CLI로 변환" 워크플로 유지 (data-as-git 원칙과
  일관, 자동 호출은 필요해지면 별도로 검토)

## 2026-07-08 — Phase 3 추천 API: 예산·지역 필드 처리
- **`tuition_monthly_fee`(월 수강료, nullable Integer) 컬럼 신규 추가**
  - 이유: Phase 3 추천 조건 중 "예산"을 지원하려 했으나 기존 스키마/정본 데이터
    어디에도 수강료 필드가 없었음. 3상태 Boolean과 달리 수치형이라 "확인됨-없음"
    상태는 없고 `NULL`=미확인만 존재
  - 예산 필터(`budget_max`)는 `tuition_monthly_fee IS NOT NULL AND <= budget_max`로
    구현 — 기존 tri-state Boolean 필터가 `IS TRUE`/`IS FALSE`로 미확인(`NULL`)을
    제외하는 것과 동일한 관례를 수치 필드에도 적용
- **지역(region) 필터는 구조화된 컬럼을 만들지 않고 `address` 부분 문자열
  매칭으로 처리**
  - 이유: 현재 전 데이터가 미사동 단일 지역 예시라 구조화 이득이 적음.
    `data-strategy.md`의 "비파괴적 확장" 원칙에 따라 다지역 확장이 실제로
    필요해질 때 nullable `region`/`dong` 컬럼을 추가하면 되므로 지금 선반영하지 않음
- **`RecommendationRequest`는 `AcademyListParams`를 상속**하여 기존
  `GET /academies` 필터(level/class_type/curriculum/shuttle/q)를 그대로 재사용하고
  `region`/`budget_max` 2개만 추가 — 필터 빌더(`academy_repository._apply_filters`)
  중복 없이 `_apply_recommendation_filters`에서 감싸는 방식으로 확장

## 2026-07-07 — 공공데이터 2-소스 확장 (나이스 + 경기데이터드림)
- **경기데이터드림 "경기도_학원 및 교습소 현황" API를 나이스와 함께 지원**
  (`convert_registry.py --source {neis,gg}`)
  - 이유: 나이스(acaInsTiInfo)에 없는 전화번호·좌표(위경도)·교습과정명을 제공,
    두 소스가 상호보완적 (나이스는 등록번호·개원년도·폐원상태가 강점)
- **`--enrich` 모드 도입**: 자연키가 매치되면 null 필드만 채우고 이미 채워진
  값은 절대 덮어쓰지 않음 — 두 소스를 순차 실행(나이스 골격 생성 → gg로 보강)
  하는 워크플로를 지원
- **상태 필터를 "개원과 일치" → "폐원류 키워드 미포함"으로 변경**
  - 이유: 구현 중 실제로 발견한 버그 — gg 소스의 상태 값 어휘를 정확히 알 수
    없는데 나이스 전용 값("개원")과의 동등 비교를 그대로 쓰면 gg 데이터가
    전부 걸러질 뻔했음. 폐원/폐업/휴원 키워드 포함 여부로 판단해 미확인
    어휘에도 안전하게 기본 포함되도록 수정
- **gg 소스 필드명은 미확정 상태로 문서화 후 진행**: 포털 봇 차단으로 실제
  응답 확인 불가 → 후보 키를 여러 개 시도하는 방식으로 구현하고 실 응답
  확보 시 한 곳(`gg_row_to_record`)만 고치면 되도록 격리

## 2026-07-06 — Fact DB 전략 및 스키마 결정
- **제품 전략**: 평가/리뷰 대신 객관적 사실(Fact)만 모으는 DB 우선
  (Phase 1 사실 → Phase 2 AI 요약 → Phase 3 사용자 리뷰, `docs/data-strategy.md`)
  - 이유: 객관성 유지, 학원 항의 리스크 회피, 수집·업데이트 용이. 정확한 DB 자체가 자산
- **3상태 nullable Boolean** (초/중/고, 수업형태, 커리큘럼, 차량): `NULL`=미확인 / `FALSE`=확인됨-없음 / `TRUE`=확인됨-있음
  - 이유: ARRAY 컬럼은 "없음"과 "미확인"을 구분하지 못함 — 이 구분이 "가장 정확한 DB"의 본질.
    부수 효과로 SQLite 테스트 호환 확보. 어휘가 작고 안정적이라 컬럼-값 방식이 저렴
- **data-as-git**: 정본은 `data/academies/*.json`, DB는 멱등 임포터로 재구성되는 파생 저장소. 쓰기 API 없음
  - 이유: PR 리뷰·이력·출처 추적을 git이 제공. 소규모 단일 큐레이터 데이터셋에 적합.
    Phase 3 사용자 리뷰는 예외(DB 직접 쓰기)
- **int autoincrement PK** (UUID 대신): 공개 데이터라 열거 우려 없음, 환경 간 식별은 자연키
  (registration_number, name+address)가 담당
- **수작성 초기 마이그레이션** + `Base.metadata` 네이밍 컨벤션 도입 (테이블 0개인 지금이 무통증 시점)
- **드라이버 스킴 수정**: `postgresql://` → `postgresql+psycopg://`
  - 이유: psycopg v3만 설치되어 있는데 기본 스킴은 psycopg2 dialect로 해석되어 DB 사용 시점에 크래시
- **공공데이터 부트스트랩**: 나이스 학원민원서비스 변환기는 신규 파일 생성 전용
  (기존 파일은 절대 덮어쓰지 않음 — 수동 큐레이션 보호)

## 2026-07-03 — 초기 기술 스택 결정
- **Backend**: FastAPI + SQLAlchemy + Alembic + PostgreSQL + uv + Pydantic Settings
  - 이유: 빠른 개발 속도, 타입 안정성, 향후 AI(OpenAI API) 연동 용이성
- **패키지 관리**: uv 채택
  - 이유: 빠른 의존성 해석/설치, 최신 Python 프로젝트 표준(pyproject.toml) 지원
- **아키텍처**: 계층형(Layered) 구조 (api/service/repository 분리)
  - 이유: MVP 단계에서도 유지보수성과 테스트 용이성 확보, 향후 AI 서비스 계층 추가가 쉬움
- **Frontend/AI**: MVP 단계에서는 구조만 고려하고 실제 구현은 보류
  - 이유: 백엔드 도메인/API 안정화가 우선
