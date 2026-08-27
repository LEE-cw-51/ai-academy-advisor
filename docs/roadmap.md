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
  — 2026-08-15 이후 배포 랜딩은 `POST /waitlist`를 호출하지 않으며, 대기자 KPI는
  카카오 채널 클릭(`kakao_channel`) 수로 대체. API 계약·테스트는 유지.

## Phase 5 — 프론트엔드 클라이언트 (진행 중)
- **프론트 스택: Next.js(App Router) + TypeScript로 확정** (`docs/decision-log.md` 2026-07-31)
- engagement API(`/events`,`/feedback`,`/waitlist`) 연동이 KPI 계측의 실제 배선
- **P0** 좌표 노출 + CORS/railway 위생 ✅
- **P1** AI 소프트 필터 + 상대 적합도 점수 (`scoring.py` / `recommendation_pipeline.py`) ✅
  — 공개 UI에서는 별점·신뢰도·확정 추천으로 표현하지 않고 후보 근거·미확인 항목과 함께 쓴다.
- **P3 기반** 안내형 추천 화면(학년·학교·과목·학습 스타일 입력 폼) + 지도 마커 + 랜딩/대기자 ✅
  — 현재 `/`·`/check`·`/checklists`는 소개·점검·체크리스트 퍼널이며, `/app`은 하남 미사 고정의 안내형 추천 화면이다. 랜딩은 `POST /waitlist`를 호출하지 않는다.
- **`POST /chat` SSE 스트리밍 채팅** — **미착수**. 라우터 자체가 없으며(`backend/app/api/`), 첫 공개 MVP의 기본 범위도 아니다. 배포된 UI는 자유 대화형 채팅이 아니라 안내형 추천 폼이다.

## Phase 5b — 질문 우선 무료 탐색 MVP (다음 제품 검증 우선순위)

### Stage 0 — 서비스·광고 경계 확정
- 공개 제품을 `무료·무결제·무예약·무상담대행·무리드전달` 구조로 유지한다.
- 당근 유료 광고 재개 전 랜딩/서비스 URL과 구조를 제시해, 필요한 서류·푸터 표기·광고 계정 요건을 서면으로 확인한다.

### Stage 1 — 객관적 후보 탐색을 잇는 상담 보조 AI 유용성 검증
- 출처와 확인일이 있는 객관적 학원 정보 기반 후보 탐색·추천을 유지한다. 상담 보조 AI는 추천을 대체하는 기능이 아니라, 추천 결과를 상담과 비교 판단으로 연결하는 경험이다.
- 학부모의 현재 상황·학년군·과목·걱정을 입력받아, AI가 상담에서 물어볼 질문 3~5개를 구조화한다.
- 질문은 과목·학습 목표별 일반 상담 항목과 함께, 실제 반 인원, 동시 질문 대응 인력, 질문이 몰리는 시간의 운영, 오답 피드백, 클리닉·보강 조건 등 `질문 대응·오답 관리` 축을 포함한다.
- 5~10명의 실제 학부모에게 사용성을 확인한다. 측정은 질문을 실제로 쓰겠다는 반응, 빠진 질문, 다음 행동의 질적 확인을 우선한다. 수치·가동률 설명이 질문 자체보다 혼란을 키우면 계산 노출은 보류한다.
- 자녀 실명·성적표·상세 자유 서술을 기본 수집하지 않고, 원시 인터뷰·개인정보를 Git 정본에 남기지 않는다.

### Stage 2 — 조건 기반 후보 탐색·추천
- 핵심 흐름: `상황 입력 → AI 조건/상담 질문 정리 → 객관적 후보 정보·지도·근거/미확인 항목 → 사용자 직접 행동`.
- 결과에는 출처·확인일이 있는 기본 정보, 후보로 보인 이유, 상담에서 확인할 점을 함께 표시한다. 반 인원·질문 대응 인력·오답 관리·클리닉처럼 데이터가 없는 운영 정보는 추정·점수화하지 않고 상담에서 확인할 점으로만 표시한다.
- 공개 리뷰 탐색이 준비되면 객관적 후보 정보에 리뷰 기반 경험 근거를 보완한다. 리뷰는 사실 데이터를 덮어쓰지 않으며, 출처·시점·한계가 드러나는 주관적 정보로 별도 표시한다.
- 전화·웹사이트·길찾기는 사용자가 직접 실행하고, `검색 시작 → 결과 조회 → 후보 상세 → 외부 행동`만 비식별 이벤트로 계측한다.

### Stage 3 — 데이터 신뢰와 반복 사용
- 실제 수요가 높은 세그먼트부터 공개 검증 가능한 과목·대상·운영 정보를 null-보강 원칙으로 늘린다.
- 반별 실제 인원, 수업 중 질문 가능 시간, 동시 질문 대응 인력 등은 학원 전체 사실이 아니라 반·과목·시간대·관측일에 종속된 운영 정보다. 확인 가능한 출처와 최신성을 확보할 수 있는지 소규모로 검증한다.
- 충분한 관측값이 있어도 `질문 대응 여유`는 학원 종합 평점·교육비 대비 점수·추천 랭킹 가중치로 쓰지 않는다. 입력값·관측 시점·미확인 항목을 함께 보여 주는 설명형 신호로만 후속 실험한다.
- 관심 학원 저장·결과 재방문 수요가 반복적으로 확인될 때에만 선택형 로그인과 저장 기능을 검토한다. 등록 후 관리 이행 점검의 개인 기록·저장도 같은 게이트 뒤에 검토한다.

상세 설계와 검증 순서는 [대기행렬 기반 질문 대응 여유 신호 제안](queueing-management-signal-proposal.md)을 참고한다.

### Stage 4 이후 — 수익화 게이트
- 무료 탐색의 유용성과 데이터 신뢰를 먼저 검증한 뒤, 학원 정보 최신화·강화 프로필 수요를 확인한다.
- 광고 또는 강화 프로필은 명확히 표시하고, 학원의 지불 여부가 일반 후보 순위·AI 근거·추천 논리에 영향을 주지 않게 한다.
- 상담 예약·리드 연결은 부모의 반복 수요, 명시적 제3자 제공 동의, 학원 응답 운영, 사업자·개인정보·광고 요건 검토가 모두 충족된 뒤 별도로 결정한다.

## Phase 4b (계속) — 리뷰 실데이터 탐색·근거화 (진행 중)
- **목적**: 객관적 학원 사실 데이터 기반 후보 탐색·추천을 유지하면서, 공개 웹의 주관적 학부모 경험을 상담 보조 AI와 후보 비교에 보완한다. 리뷰는 학원 사실이나 품질 판정으로 바꾸지 않는다.
- 리뷰 소스: **네이버 검색 오픈 API** `cafearticle`(지역 카페 공개글) + `blog` (`docs/decision-log.md` 2026-07-31)
- `local`(지역검색)로 학원 매칭 + `subjects`/`phone` 등 정본 파일 보강 (git 정본 원칙 유지)
- AI 요약만 화면에 노출하고, 경험 근거에는 출처·시점·한계를 함께 표시한다. 원문 스니펫은 DB 보관 + RAG 근거 전용이며 git에 커밋하지 않는다. 리뷰 요약은 객관적 사실·런타임 탐색 신호·상담에서 확인할 점과 구분해 표시한다.
- 공개 리뷰의 단일 별점, 감성 점수, 요약만으로 학원 품질 또는 교육비 대비 가치를 단정하지 않는다.

## Phase 6 — 배포 및 운영
- 운영 환경 Docker Compose / 인프라 구성 (infra/)
- 모니터링 및 로깅 고도화
