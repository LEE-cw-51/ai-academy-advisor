# 로드맵

## Phase 0 — 프로젝트 스캐폴딩 (완료)
- FastAPI 프로젝트 기본 구조 생성
- Docker / Docker Compose 구성 (PostgreSQL 포함)
- Health check API (`/`, `/health`, `/version`)
- 문서 구조 생성

## Phase 1 — 데이터 모델링
- 학원(Academy) 도메인 모델 설계 (SQLAlchemy models)
- Alembic 초기 마이그레이션 작성
- 학원 데이터 수집/정제 (data/)

## Phase 2 — 기본 CRUD API
- 학원 목록/상세 조회 API
- Repository / Service 계층 구현
- Pydantic Schema 정의

## Phase 3 — 추천 로직 (Rule 기반)
- 학년/지역/예산 등 조건 기반 필터링 추천
- 추천 결과 API

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
