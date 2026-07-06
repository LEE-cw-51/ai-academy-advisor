# 의사결정 로그

주요 기술적/제품적 의사결정과 그 이유를 기록한다.

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
