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

## Phase 4 — AI 연동 (RAG)

### 4a — 기반 골격 (완료)
- provider 추상화 계층(`app/providers/`): `EmbeddingProvider`/`LLMProvider`/`VectorStore`
  Protocol 포트 + 기본 stub 구현 + config 선택 팩토리 ✅
- 리뷰·engagement 스키마: `reviews`(pgvector 임베딩) / `search_history` / `click_logs` /
  `feedback` / `waitlist` 테이블 + 마이그레이션 `0003` ✅
- 실제 provider 호출/키 없이 동작 (기본 전부 stub, 비용 0)

### 4b — 실제 RAG (진행 중)
- **자연어 추천 엔드포인트 스켈레톤 완료** (`POST /recommendations/ai`) ✅
  - 파이프라인: 질문 기록 → 의도 분석 → 필터 → 벡터 근거 검색 → 추천 이유 생성
  - provider 포트 경유(기본 stub), 의도 분석은 규칙 기반 (`app/services/intent.py`)
  - 기존 `academy_repository.list_recommendations` 필터 재사용
- **LLM provider 실연동 완료**: Groq(Llama, 무료 티어) `GroqLLMProvider` 추가,
  `LLM_PROVIDER=groq`로 전환 가능 (`docs/decision-log.md`)
- **임베딩/VectorStore 실연동 완료**: `OpenAIEmbeddingProvider`(`text-embedding-3-small`,
  `dimensions=1024` truncation으로 스키마 변경 없이 사용) + `PgVectorStore`
  (`Review.embedding` 컬럼에 `cosine_distance()` 직접 검색) 추가.
  `EMBEDDING_PROVIDER=openai` + `VECTOR_STORE=pgvector`로 전환 가능 (`docs/decision-log.md`).
  리뷰 임베딩 백필 CLI(`app/cli/ingest_review_embeddings.py`)로 기존 리뷰 행을 채운다.
- LlamaIndex 기반 RAG 엔진을 단일 `RagEngine` 포트 뒤에 채택하는 것(교체 가능성 유지),
  프롬프트 설계(prompts/), 리뷰 원본 수집 파이프라인, ANN 인덱스(ivfflat/hnsw) 튜닝은
  다음 단계
- LLM 기반 의도 분석으로 `intent.parse_intent` 교체도 다음 단계

### 4c — engagement API (완료)
- 클릭 추적(`POST /events`), 피드백(`POST /feedback`), 대기자(`POST /waitlist`) ✅
- 자연어 추천 시 `SearchHistory` 기록 ✅
- KPI(외부 행동률·대기자 등록률 등) 측정용 DB 직접 쓰기 (`docs/data-strategy.md`)

## Phase 5 — 프론트엔드 클라이언트 (진행 중)
- **프론트 스택: Next.js(App Router) + TypeScript로 확정** (`docs/decision-log.md` 2026-07-31)
- 좌: SSE 스트리밍 채팅(`POST /chat`, 신규) / 우: 네이버 지도로 검색 결과 마커 표시
- engagement API(`/events`,`/feedback`,`/waitlist`) 연동이 KPI 계측의 실제 배선
- **P0** 좌표 노출 + CORS/railway 위생 ✅
- **P1** AI 소프트 필터 + 진짜 적합도 점수 (`scoring.py` / `recommendation_pipeline.py`) ✅
  — P2(`POST /chat` SSE)·P3(프론트)의 기반
- **P3** 안내형 추천 화면(학년·학교·과목·학습 스타일 입력 폼) + 지도 마커 + 랜딩/대기자 ✅
- **P2** `POST /chat` SSE 스트리밍 채팅 — **미착수**. 라우터 자체가 없으며(`backend/app/api/`),
  배포된 UI는 자유 대화형 채팅이 아니라 안내형 추천 폼이다. 완료된 것처럼 전제하지 않는다.

## Phase 4b (계속) — 리뷰 실데이터 수집 (진행 중)
- 리뷰 소스: **네이버 검색 오픈 API** `cafearticle`(지역 카페 공개글) + `blog` (`docs/decision-log.md` 2026-07-31)
- `local`(지역검색)로 학원 매칭 + `subjects`/`phone` 등 정본 파일 보강 (git 정본 원칙 유지)
- AI 요약만 화면에 노출, 원문 스니펫은 DB 보관 + RAG 근거 전용, git 커밋 금지

## Phase 6 — 배포 및 운영
- 운영 환경 Docker Compose / 인프라 구성 (infra/)
- 모니터링 및 로깅 고도화
