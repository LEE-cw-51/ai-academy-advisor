# AI Academy Advisor (학원콕)

학원콕은 하남 미사 학부모가 학원과 아이의 학습 상태를 둘러싼 **블랙박스를 줄이고, 더 나은 질문과 판단을 하도록 돕는 무료 AI 보조 학원 탐색 서비스**입니다. 사용자의 상황과 고민을 탐색 조건·상담 질문·추가 확인 항목으로 정리하고, 출처와 확인일이 있는 학원 기본 정보를 보여줍니다.

상담 질문은 `POST /consultation/questions`로 구조화할 수 있습니다. 반 인원·질문 대응·오답 관리처럼 확인되지 않은 운영 정보는 점수로 만들지 않고 `상담에서 확인할 점`으로 둡니다. 공개 리뷰는 사실 DB와 분리한 주관적 근거입니다. 후속 신호 설계는 [대기행렬 기반 질문 대응 여유 신호 제안](docs/queueing-management-signal-proposal.md), 당근·카카오 카피 초안은 [마케팅 초안](docs/marketing-daangn-kakao.md)을 참고하세요. 당근 유료 광고는 심사 요건을 서면 확인하기 전에 재개하지 않습니다. 수강 신청·예약·결제·상담 대행·리드 전달은 첫 MVP 범위에 포함하지 않습니다.

현재는 MVP 단계로, 확장성보다 명확한 구조와 유지보수성을 우선하여 개발합니다.

> **AI와 함께 작업한다면 먼저 [AGENTS.md](AGENTS.md)를 읽으세요.**
> 이 저장소는 여러 AI(ChatGPT·Claude·Cursor·Manus)가 공유하는 단일 정본이며,
> 공통 계약과 역할 규약은 [AGENTS.md](AGENTS.md)와 [docs/ai-team.md](docs/ai-team.md)에 있습니다.

## 기술 스택

**Backend**
- Python
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- uv
- Pydantic Settings

**Frontend**
- Next.js 15 (App Router, TypeScript, Tailwind)
- 네이버 지도 JavaScript API (선택)

**AI**
- provider 추상화 계층(`app/providers/`) — LLM/임베딩/벡터 스토어를 config로 교체
- 기본값은 전부 stub (실제 호출·키 없이 동작). 실제 어댑터(OpenAI/bge-m3/pgvector)·
  LlamaIndex RAG 엔진은 다음 단계에서 같은 포트 뒤에 추가
- 벡터 검색용 pgvector (PostgreSQL 확장)

**Deployment**
- Docker
- Docker Compose

## 실행 방법

### 1. 환경변수 설정

```bash
cp .env.example .env
```

### 2. Docker Compose로 실행 (권장)

```bash
docker compose up --build
```

- API: http://localhost:8000
- Health check: http://localhost:8000/health

### 3. 로컬에서 직접 실행 (uv 사용)

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

### 4. 프론트엔드 실행 (Next.js)

백엔드가 `http://localhost:8000`에서 떠 있는 상태에서:

```bash
cd frontend
cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL, (선택) 네이버 지도 키
npm install
npm run dev
```

- 앱: http://localhost:3000
- 자세한 안내는 [frontend/README.md](frontend/README.md)를 참고하세요.

### 5. 테스트 실행

```bash
cd backend
uv sync
uv run pytest ../tests
```

### 6. DB 마이그레이션 및 학원 데이터 적재

```bash
cd backend
uv run alembic upgrade head
uv run python -m app.cli.import_academies ../data/academies --dry-run   # 검증만
uv run python -m app.cli.import_academies ../data/academies             # DB 반영
```

학원 데이터의 **운영 정본**은 Supabase Postgres `academies` 테이블입니다.
`data/academies/*.json`은 시드·백업용이며, 파일 포맷과 수집 규칙은
[data/README.md](data/README.md), 데이터 전략은
[docs/data-strategy.md](docs/data-strategy.md)를 참고하세요.

## Supabase 운영 DB (학원 사실 정본)

1. [Supabase](https://supabase.com)에서 프로젝트를 만듭니다.
2. **Database → Extensions**에서 `vector`를 활성화합니다 (리뷰 임베딩용).
3. **Project Settings → Database → Connection string**에서 **Session mode (5432)** URL을
   복사해 `DATABASE_URL`로 설정합니다. **Transaction pooler(6543)는 Alembic·이 CLI들처럼
   오래 사는 프로세스에는 맞지 않습니다** — 6543은 Vercel 백엔드 함수(서버리스, `NullPool`)
   전용이며 `.env.example`에 두 포트 용도가 각각 설명돼 있습니다.
4. 마이그레이션과 1회 시드 임포트:

```bash
cd backend
uv run alembic upgrade head
uv run python -m app.cli.import_academies ../data/academies --force
```

5. 로컬 `.env`의 `DATABASE_URL`을 Supabase URL(5432)로 바꾸고 `/health`,
   `GET /academies`로 확인합니다. 백엔드 Vercel 프로젝트의 Production+Preview
   Variables에는 6543(transaction pooler) URL을 설정합니다 — 아래 배포 절차 참고.
6. 일상 수정은 **Supabase Table Editor → academies**에서 합니다. 공개 API 쓰기는
   없습니다. 컬럼/테이블 추가는 Studio가 아니라 Alembic입니다.
7. 백업 덤프: `uv run python -m app.cli.export_academies ../data/backups/YYYY-MM-DD`

운영 DB에는 `import_academies`가 기본 거부됩니다(Studio 수정 보호). 재해복구만
`--force` 또는 `ALLOW_ACADEMY_IMPORT=1`을 사용하세요.

### Cursor Supabase MCP (read_only)

에이전트가 DB 스키마·행 수·extension 상태를 **조회·검증**할 때 씁니다. 스키마 변경은
Alembic이 정본이며 MCP `apply_migration`은 쓰지 않습니다.

1. Supabase Dashboard → **Project Settings → General** → **Reference ID**를 복사합니다.
2. [`.cursor/mcp.json`](.cursor/mcp.json) URL의 `YOUR_PROJECT_REF`를 위 ID로 바꿉니다
   (템플릿: [`.cursor/mcp.json.example`](.cursor/mcp.json.example)). 비밀번호·service_role·
   PAT는 파일에 넣지 않습니다 — [호스팅 MCP](https://supabase.com/docs/guides/getting-started/mcp)는 OAuth로 인증합니다.
3. Cursor **Settings → Tools & MCP**에서 MCP를 켜고 `supabase` 서버를 ON 합니다.
4. 브라우저에서 Supabase OAuth 로그인 후 해당 프로젝트 권한을 허용합니다. 연결이 안 되면
   Cursor를 완전히 종료한 뒤 다시 시작합니다.
5. **도구 호출 전 수동 승인**을 유지합니다. `execute_sql` 제안 시 SQL 내용을 확인한 뒤 승인하세요.

연결 확인 예시 (채팅):

> Supabase MCP로 `academies` 테이블이 있는지, `vector` extension이 켜져 있는지 확인해 줘.

컷오버 후 추가 확인:

> `academies` 행 수와 `last_verified_at`이 null인 비율을 조회해 줘.

에이전트가 사용할 MCP 도구: `list_tables`, `list_extensions`, `execute_sql`(read_only SELECT).
`apply_migration`은 쓰지 않습니다.

## 배포 (Vercel, 백엔드+프론트 분리 프로젝트)

백엔드(FastAPI)와 프론트(Next.js)는 **각각 별도의 Vercel 프로젝트**로 배포한다
(2026-09-04, Railway 고정비를 피하기 위한 이전 — `docs/decision-log.md`).
공개 프론트 정본·Preview·배포 체크 기준은 **Vercel만**이다. Netlify
(`academykok.netlify.app`)는 쓰지 않으며, Founder가 Netlify 사이트 `academykok`의
Git 연동을 해제해야 PR에 `netlify/.../deploy-preview` 체크가 남지 않는다
(2026-09-07, 저장소만으로는 불가). 프로덕션 프론트
`https://ai-academy-advisor-ten.vercel.app`, 백엔드
`https://ai-academy-advisor-backend.vercel.app`.
백엔드는 `backend/pyproject.toml`의 `[tool.vercel] entrypoint = "app.main:app"`로
`app/main.py`의 FastAPI 인스턴스 전체가 서버리스 함수 하나로 서빙된다.

1. **백엔드 프로젝트**: 이 GitHub 리포를 연동하고 Root Directory를 `backend`로 지정한다.
   Variables에 `DATABASE_URL`(Supabase, 위 절 참고)·`OPENAI_API_KEY`·`GROQ_API_KEY` 등을 설정한다.
2. **DB 커넥션**: Vercel Functions는 서버리스라 `DATABASE_URL`은 Supabase Supavisor
   **transaction pooler(포트 6543)** 를 쓴다. `backend/app/db/session.py`가 이 모드에 맞춰
   `NullPool` + `psycopg` `prepare_threshold=None`으로 이미 구성돼 있다 — 세션 풀러(5432)로
   바꾸면 동시 요청이 늘 때 커넥션이 금방 바닥난다.
3. **프론트 프로젝트**: Root Directory `frontend`. `next.config.ts`의 `rewrites()`가
   `/api/backend/*`를 서버 전용 env `BACKEND_ORIGIN`(백엔드 프로젝트의 프로덕션 URL)으로
   프록시한다 — 브라우저는 항상 같은 오리진만 호출하므로 **CORS 설정이 아예 필요 없다**.
   `NEXT_PUBLIC_API_URL`은 프록시를 우회해 백엔드를 직접 호출하고 싶을 때만 설정한다.
4. `main` 브랜치에 push하면 두 프로젝트 모두 자동 배포된다. CLI로 재배포할 때는
   **저장소 루트**에서 실행한다 — `frontend/`만 올리면 Root Directory=`frontend` 설정과
   어긋나 실패한다.
5. DB 마이그레이션은 로컬에서 Supabase 세션 풀러(5432)로 1회 실행한다.

```bash
cd backend && uv run alembic upgrade head
```

로컬 개발 흐름(`docker compose up --build`, 또는 `uv run uvicorn app.main:app`)은 이
설정과 무관하게 그대로 사용할 수 있다. `backend/Dockerfile`·`docker-compose.yml`은
로컬 전용으로 유지한다.

프론트 Environment Variables (Production)의 `NEXT_PUBLIC_NAVER_MAP_CLIENT_ID`(선택,
네이버 지도 키)는 위 배포 절차의 `BACKEND_ORIGIN`과 함께 백엔드 프로젝트가 아니라
**프론트 프로젝트**에 설정한다. 자세한 안내는 [frontend/README.md](frontend/README.md).

## 프로젝트 구조

```
ai-academy-advisor/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/            # 라우터
│   │   ├── core/           # 설정, 로깅
│   │   ├── db/             # DB 세션/엔진
│   │   ├── models/         # SQLAlchemy 모델
│   │   ├── schemas/        # Pydantic 스키마
│   │   ├── services/       # 비즈니스 로직
│   │   ├── repositories/   # 데이터 접근 계층
│   │   ├── providers/      # AI provider 포트+어댑터 (LLM/임베딩/벡터, 교체 가능)
│   │   ├── dependencies/   # 공용 의존성
│   │   └── utils/          # 유틸리티
│   ├── alembic/            # DB 마이그레이션
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/               # Next.js 앱 (학원콕 UI)
├── docs/                   # 프로젝트 문서
├── data/                   # 학원 JSON 시드·백업 덤프
├── tests/                  # 테스트
├── .github/                # PR/Issue 템플릿 (AI 인계 형식)
├── AGENTS.md               # 에이전트 공통 계약 (모든 AI가 먼저 읽는 파일)
├── CLAUDE.md               # Claude 진입점 (AGENTS.md를 가리킴)
├── docker-compose.yml
└── .env.example
```

더 자세한 내용은 [docs/](docs) 디렉터리를 참고하세요.
