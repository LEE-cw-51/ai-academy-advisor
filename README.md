# AI Academy Advisor

하남 미사 지역의 수학학원을 AI가 추천해주는 도메인 특화 AI 서비스입니다. 현재는 MVP 단계로,
확장성보다 명확한 구조와 유지보수성을 우선하여 개발합니다.

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
├── data/                   # 학원 데이터
├── tests/                  # 테스트
├── docker-compose.yml
└── .env.example
```

더 자세한 내용은 [docs/](docs) 디렉터리를 참고하세요.
