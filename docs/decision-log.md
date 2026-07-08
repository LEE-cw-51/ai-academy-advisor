# 의사결정 로그

주요 기술적/제품적 의사결정과 그 이유를 기록한다.

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
