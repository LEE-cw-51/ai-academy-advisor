# 로드맵

## Phase 0 — 프로젝트 스캐폴딩 (완료)
- FastAPI 프로젝트 기본 구조 생성
- Docker / Docker Compose 구성 (PostgreSQL 포함)
- Health check API (`/`, `/health`, `/version`)
- 문서 구조 생성

## Phase 1 — 데이터 모델링 (완료)
- 학원(Academy) 도메인 모델 설계 (SQLAlchemy models) ✅
- Alembic 초기 마이그레이션 작성 (`0001`) ✅
- 정본 데이터 파이프라인: `data/academies/*.json` → 임포터 ✅
- 공공데이터(나이스 학원민원서비스) 변환 스크립트 ✅
- 실제 학원 데이터 수집은 지속 작업 (전략: `docs/data-strategy.md`)

## Phase 2 — 기본 CRUD API (조회 완료)
- 학원 목록/상세 조회 API ✅ (`GET /academies` 필터 검색, `GET /academies/{id}`)
- Repository / Service 계층 구현 ✅
- Pydantic Schema 정의 ✅
- 쓰기 API는 의도적으로 없음 — 정본이 git JSON이므로 (`docs/data-strategy.md`)

## Phase 3 — 추천 로직 (Rule 기반, 완료)
- 학년/지역/예산 등 조건 기반 필터링 추천 ✅
- 추천 결과 API (`POST /recommendations`) ✅ (`docs/api.md`)
- 예산 필터를 위해 `tuition_monthly_fee` 컬럼 신규 추가 (`docs/decision-log.md`)
- 지역 필터는 구조화된 컬럼 없이 `address` 부분 일치로 처리 (여러 지역 확장 시 재검토)

## Phase 4 — AI 연동
- OpenAI API 연동
- 프롬프트 설계 (prompts/)
- 자연어 질의 기반 추천

## Phase 5 — Flutter 클라이언트
- 학원 검색/추천 화면
- 백엔드 API 연동

## Phase 6 — 배포 및 운영
- 운영 환경 Docker Compose / 인프라 구성 (infra/)
- 모니터링 및 로깅 고도화
