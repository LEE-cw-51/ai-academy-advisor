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
   복사해 `DATABASE_URL`로 설정합니다. Transaction pooler(6543)는 Alembic에 맞지
   않을 수 있습니다.
4. 마이그레이션과 1회 시드 임포트:

```bash
cd backend
uv run alembic upgrade head
uv run python -m app.cli.import_academies ../data/academies --force
```

5. Railway(또는 로컬 `.env`)의 `DATABASE_URL`을 Supabase URL로 바꾸고 `/health`,
   `GET /academies`로 확인합니다. **기존 Railway Postgres는 안정될 때까지 플러그인을
   끄지 말고 읽기 전용 백업으로 남겨 둡니다.**
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

## Railway 배포

백엔드는 `railway.json`(`backend/Dockerfile` 기반 빌드) 설정으로 Railway에 배포할 수 있습니다.

1. Railway에서 새 프로젝트를 만들고 이 GitHub 리포를 연동합니다.
2. 프로젝트에 **Postgres 플러그인**을 추가하거나, Supabase `DATABASE_URL`(Session 5432)을
   Variables에 설정합니다.
3. 서비스의 Variables에 `OPENAI_API_KEY`를 직접 설정합니다. 브라우저
   프론트엔드(Vercel 등)에서 API를 호출하려면 `CORS_ORIGINS`도 함께 설정해야 합니다 —
   반드시 JSON 배열 형식이어야 하며(예: `["https://your-app.vercel.app"]`), 설정하지
   않으면 `http://localhost:3000` 기본값만 허용되어 배포된 프론트엔드의 요청이 CORS
   오류로 막힙니다.
4. `main` 브랜치에 push하면 `backend/Dockerfile`로 자동 빌드/배포되고, `/health`로 헬스체크됩니다.
5. DB 마이그레이션은 배포 후 Railway CLI로 1회 실행합니다.

```bash
railway run --service backend uv run alembic upgrade head
```

로컬 개발 흐름(`docker compose up --build`)은 이 설정과 무관하게 그대로 사용할 수 있습니다.

백엔드 재배포 시 저장소 루트가 아니라 **`backend`만** 올립니다 (루트 `railway up`은
Railpack이 모노레포 전체를 빌드하려다 실패할 수 있음):

```bash
railway up backend --path-as-root -y --detach
```

## Vercel 배포 (프론트엔드)

프론트는 [Vercel](https://vercel.com)에 배포합니다. 백엔드(Railway)·DB(Supabase)와 분리됩니다.

1. GitHub 리포 Import → **Root Directory**는 비워 둡니다(루트 `vercel.json`이
   `frontend`를 빌드). 폴더 선택에서 `frontend`가 보이면 그걸 골라도 됩니다.
2. Environment Variables (Production):
   - `NEXT_PUBLIC_API_URL` = Railway API URL (예: `https://ai-academy-advisor-production.up.railway.app`)
   - `NEXT_PUBLIC_NAVER_MAP_CLIENT_ID` = (선택) 네이버 지도 키
3. Railway `CORS_ORIGINS`에 Vercel Production URL + `http://localhost:3000`을 JSON 배열로 설정:

```bash
echo '["https://your-project.vercel.app","http://localhost:3000"]' | railway variable set CORS_ORIGINS --stdin
```

4. `main` push 시 Vercel이 자동 빌드·배포합니다. 자세한 안내는 [frontend/README.md](frontend/README.md).

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
