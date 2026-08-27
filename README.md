# AI Academy Advisor (학원콕)

학원콕은 하남 미사 학부모가 학원과 아이의 학습 상태를 둘러싼 **블랙박스를 줄이고, 더 나은 질문과 판단을 하도록 돕는 무료 AI 보조 학원 탐색·추천 서비스**입니다. 출처와 확인일이 있는 객관적 학원 정보를 기반으로 사용자의 조건에 맞는 후보를 탐색하고, 상황과 고민을 상담 질문·추가 확인 항목으로 정리합니다.

당근 광고 반응에서 ‘지불한 비용에 비해 상담과 학습 관리가 충분한가’라는 문제의식이 나타난 것을 **후속 제품 가설**로 삼아, 현재는 상담 보조 AI를 핵심 사용 경험으로 구체화합니다. 반의 실제 인원, 질문 대응 인력, 오답 관리, 클리닉·보강처럼 아이가 실제로 받는 관리 구조를 상담에서 확인하도록 돕습니다. 이후에는 공개 리뷰를 탐색해, 출처와 확인일이 있는 객관적 사실과 출처·시점·한계가 표시된 주관적 경험을 구분하여 함께 제공하는 방향을 검증합니다.

학원콕은 학원 품질·교육비 대비 가성비를 단일 점수나 등급으로 판정하지 않습니다. 운영 정보가 확인되지 않으면 추정 대신 `상담에서 확인할 점`으로 표시하며, 대기행렬 관점의 `질문 대응 여유`는 향후 충분한 반 단위 관측값과 출처가 확보될 때에만 상담 보조를 위한 설명형 신호로 검토합니다. 제품 경계와 검증 순서는 [프로젝트 개요](docs/project.md), [데이터 전략](docs/data-strategy.md), [대기행렬 기반 질문 대응 여유 신호 제안](docs/queueing-management-signal-proposal.md)을 참고하세요. 수강 신청·예약·결제·상담 대행·리드 전달은 첫 MVP 범위에 포함하지 않습니다.

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

학원 데이터의 정본은 `data/academies/*.json`입니다. 파일 포맷과 수집 규칙은
[data/README.md](data/README.md), 데이터 전략은
[docs/data-strategy.md](docs/data-strategy.md)를 참고하세요.

## Railway 배포

백엔드는 `railway.json`(`backend/Dockerfile` 기반 빌드) 설정으로 Railway에 배포할 수 있습니다.

1. Railway에서 새 프로젝트를 만들고 이 GitHub 리포를 연동합니다.
2. 프로젝트에 **Postgres 플러그인**을 추가합니다. `DATABASE_URL`은 자동으로 서비스에 주입됩니다.
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
├── data/                   # 학원 데이터 (정본)
├── tests/                  # 테스트
├── .github/                # PR/Issue 템플릿 (AI 인계 형식)
├── AGENTS.md               # 에이전트 공통 계약 (모든 AI가 먼저 읽는 파일)
├── CLAUDE.md               # Claude 진입점 (AGENTS.md를 가리킴)
├── docker-compose.yml
└── .env.example
```

더 자세한 내용은 [docs/](docs) 디렉터리를 참고하세요.
