# AGENTS.md — 에이전트 공통 계약

이 저장소는 여러 AI(ChatGPT · Claude · Cursor · Manus)와 Founder가 함께 일하는 프로젝트다.
**이 파일이 모든 에이전트의 공통 계약이며, GitHub 저장소가 단일 정본(Single Source of Truth)이다.**

도구별 진입점(`CLAUDE.md`, `.cursor/rules/`)은 모두 이 파일을 가리킨다. 규칙이 바뀌면
각 도구 설정이 아니라 **이 파일을 고쳐 PR로 반영**한다. 도구 설정에만 있는 규칙은 다른
에이전트가 볼 수 없으므로 존재하지 않는 것으로 취급한다.

---

## 1. 작업을 시작하기 전에 읽는 것

순서대로 확인한다. 이 단계를 건너뛴 제안·구현은 기존 결정과 충돌할 가능성이 높다.

1. `README.md` — 실행·배포 방법
2. `AGENTS.md` (이 파일) — 공통 계약
3. `docs/project.md` — 제품 정의와 현재 단계
4. `docs/roadmap.md` — 지금 어느 Phase에 있는가
5. `docs/decision-log.md` — **이미 내려진 결정과 그 이유** (최신순, 되돌리려면 근거 필요)
6. `docs/architecture.md` · `docs/api.md` · `docs/database.md` · `docs/data-strategy.md` — 변경 범위에 해당하는 것
7. 관련 Issue / PR / 테스트

## 2. AI 조직과 역할

| 담당 | 역할 | 주 산출물 |
|---|---|---|
| **Founder** | 최종 의사결정자 | 승인, 우선순위, 사업 판단 |
| **ChatGPT** | CEO / PM / 전략 | 방향성, MVP 범위, 사업 우선순위, 요구사항 |
| **Claude** | CTO / Senior Engineer | 아키텍처·보안·확장성 검토, 코드 리뷰, 기술 결정 |
| **Cursor** | Developer / IDE | 코드 구현, 리팩터링, 테스트 |
| **Manus** | Research & Execution | 웹 조사, 복수 출처 검증, 데이터 수집·정리, 외부 실행 |

역할은 소유권이지 담장이 아니다. 다른 역할의 영역을 침범해야 한다면 **먼저 그 사실을 밝히고**
근거를 제시한다. 중요한 사업 판단의 최종 결정권은 항상 Founder에게 있다.
상세 권한·금지 사항은 [docs/ai-team.md](docs/ai-team.md) 참고.

## 3. 결과를 남기는 곳

| 성격 | 남기는 곳 |
|---|---|
| 지속적으로 유효한 제품 정의·전략·요구사항 | `docs/project.md`, `docs/roadmap.md` |
| 기술·데이터·제품 **결정과 그 이유** | `docs/decision-log.md` (최신을 맨 위에, `## YYYY-MM-DD — 제목`) |
| 외부 동작 변경 (엔드포인트·응답 계약) | `docs/api.md` |
| 조사 결과·시장/경쟁사 분석 | Issue 또는 `docs/` 신규 문서 + decision-log 링크 |
| 삽질·참고 자료 | `docs/learning-log.md` |
| 작업 인계 | PR 본문 (템플릿 사용) |

세션 안에서만 유효한 내용은 문서로 만들지 않는다. **문서 증식보다 기존 문서 갱신을 우선**한다.

## 4. 작업 원칙

- **Build Less, Learn Faster** — 불필요한 완벽주의·과도한 엔지니어링·근거 없는 기능 추가를 피한다.
- **Evidence Before Assumption** — 중요한 결론을 단일 출처에만 의존하지 않는다. 확인되지 않은 값은 추측하지 않는다.
- **Ship Early** — 고객 검증 > 매출 가능성 > 핵심 제품 개발 > 자동화 > 운영 효율 순으로 우선순위를 판단한다.
- **Keep Context** — 다음 담당자가 맥락을 재구성하지 않아도 되게 남긴다.

요청이 충분히 명확하면 바로 실행한다. 합리적 가정으로 진행 가능하면 **가정을 밝힌 뒤** 실행한다.
큰 방향 오류나 되돌리기 어려운 위험이 있을 때만 핵심 질문을 최소화해 확인한다.

중요한 기술적 선택은 **문제 → 현재 구조 → 대안 → 트레이드오프 → 추천안 → 구현** 순으로 제시한다.

## 5. 제품과 현재 범위

하남 미사 지역 학원의 구조화된 정보를 바탕으로 맞춤 추천을 제공하는 서비스(‘학원콕’)다.
핵심 자산은 UI가 아니라 **출처와 확인일을 갖춘 정확한 지역 학원 사실 데이터베이스**이며,
현재는 유지보수 가능한 MVP를 우선한다.

배포된 웹 UI는 ‘하남 미사’를 고정한 **안내형 추천 화면**이다. 학년·학교·과목·학습 스타일·추가
요구를 입력하면 추천 결과와 지도 마커를 함께 보여준다.
**자유 대화형 채팅과 SSE 스트리밍(`POST /chat`)은 아직 구현 완료 범위가 아니다** — 완료된 것처럼
문서화하거나 전제하지 않는다.

## 6. 기술·구조 기준

**스택**: 백엔드 Python 3.11+ / FastAPI / SQLAlchemy 2 / Alembic / PostgreSQL+pgvector /
Pydantic Settings / uv. 프론트 Next.js 15 App Router / TypeScript / Tailwind.
기본 실행은 Docker Compose(backend + pgvector Postgres), Railway 배포는 `backend/Dockerfile` + `railway.json`.

**계층**: `api → services → repositories → models/DB`

- 라우터는 HTTP·스키마 검증·서비스 호출만 담당한다.
- 서비스는 비즈니스 규칙을 담당하며 **ORM을 직접 조회하지 않는다**. 데이터 접근은 Repository가 캡슐화한다.
- `services/scoring.py`는 모델/ORM에 의존하지 않는 **순수 랭킹 모듈**로 유지한다 (테스트로 강제됨).
- `services/recommendation_pipeline.py`는 추천·향후 채팅의 공용 DB→Pydantic 경계다.
  **ORM 객체나 열린 세션을 응답/스트리밍 계층으로 넘기지 않는다.** 모든 DB 작업은 이 경계 안에서 끝낸다.

**AI 구성요소**는 `app/providers/`의 얇은 Protocol과 factory를 통해서만 연결한다.
기본값은 결정적인 stub이고, 실제 LLM·임베딩·벡터 저장소는 설정으로 opt-in한다.
새 공급자를 도입할 때는 기존 포트를 우선 확장하고 **호출부를 특정 벤더 SDK에 결합하지 않는다.**
OpenAI 임베딩 + pgvector 사용 시 `embedding_dim`은 DB `Vector(dim)` 스키마와 결합되어 있으므로
차원 변경은 마이그레이션과 함께 계획한다.

**비밀 값**은 `.env` / 플랫폼 환경변수로만 관리한다. 코드·데이터 정본·문서·PR 본문에 기록하지 않는다.

## 7. 데이터 정본 규칙

`data/academies/*.json`이 학원 사실 데이터의 **유일한 git 정본**이고, DB는 `import_academies`로
재구성되는 파생 저장소다.

- 학원 사실 수정 순서: **JSON 수정 → 검증(`--dry-run`)/PR 리뷰 → 머지 → DB 임포트**
- **학원 사실용 쓰기 API를 추가하지 않는다.**
- `reviews`, `search_history`, `click_logs`, `feedback`, `waitlist`는 사용자 행동·AI 근거
  데이터이므로 **승인된 DB 직접 쓰기 예외**다.
- 리뷰 원문 스니펫과 원시 수집 데이터는 정본 JSON·git에 커밋하지 않는다(`data/raw/`는 gitignore).
  화면에는 AI 요약·근거만 노출한다.
- 공개된 검증 가능 정보만 입력한다. 확인되지 않으면 `null`로 남긴다.
- 3상태 Boolean: `true`=확인됨/있음, `false`=확인됨/없음, `null`=미확인. 엄격히 구분한다.
- **휴리스틱으로 사실 필드를 채우지 않는다** — 이름에 “수학”이 있다고 `subjects`를 추측해 쓰지 않는다.
- 가능한 한 `source_note`와 `last_verified_at`을 남긴다.
- 자연키(`registration_number`, 없으면 `name`+`address`) 중복을 만들지 않는다.
- 공공데이터 변환·보강은 기존 CLI와 `--enrich`의 **null-보강 원칙**을 따르며 기존 수동 큐레이션을 덮어쓰지 않는다.

자세한 내용: [docs/data-strategy.md](docs/data-strategy.md)

## 8. 추천 · API 계약

**`GET /academies` · `POST /recommendations` — 하드 필터 계약**
모든 조건은 AND이며, Boolean/수강료가 `null`인 항목은 결과에 포함하지 않는다.
명시적 필터 UI와 디버그 용도로 유지하므로 **소프트 랭킹으로 바꾸거나 AI 경로와 성급히 통합하지 않는다.**

**`POST /recommendations/ai` — 넓은 후보 풀 + 소프트 적합도 랭킹**

- NULL이 많은 실제 데이터에서 결과가 비지 않도록 3상태 사실·예산·과목 신호를 SQL 배제가 아니라
  **랭킹으로** 반영한다.
- 후보가 없을 때만 `q → region` 순으로 완화하고, 완화 사실은 `relaxed`에 노출한다.
- `score`는 **동일 응답 내 순위 비교용 상대값**이다. 별점·퍼센트·신뢰도처럼 표시하거나 저장하지 않는다.
- `matched_conditions` / `unknown_conditions` / `conflicts` / `parsed_intent` / `evidence_reviews`의
  투명성 계약을 유지한다.
- 과목 추출은 검증된 사실이 아니라 **런타임 랭킹 신호**로만 취급한다.

목록·추천 응답의 **좌표는 지도 표시에 필요하므로 보존**한다.
전체 계약: [docs/api.md](docs/api.md)

## 9. 프론트엔드와 운영 연동

- API 접근은 `frontend/src/lib/api.ts`에 집중하고, 백엔드 주소는 `NEXT_PUBLIC_API_URL`로 설정한다.
- 지도는 네이버 지도 JavaScript API 키가 있을 때만 활성화되는 **선택 기능**이다.
- 클릭 추적은 UX를 막지 않되, 추천 카드의 전화·웹사이트·길찾기·상세보기 행동은 `/events` 계약을
  따라 KPI 측정에 연결한다.
- 배포 프론트엔드가 백엔드를 호출하면 `CORS_ORIGINS`는 **반드시 JSON 배열**로 설정한다.

## 10. 검증

**머지 완료를 검증 완료로 간주하지 않는다.** 항상 기준선 검증을 다시 수행한다.

| 범위 | 명령 |
|---|---|
| 백엔드 | `cd backend && uv sync && uv run pytest ../tests` |
| 프론트엔드 | `cd frontend && npm ci && npm run build` |
| 데이터 반영 전 | `cd backend && uv run python -m app.cli.import_academies ../data/academies --dry-run` |
| DB 반영 | `cd backend && uv run alembic upgrade head && uv run python -m app.cli.import_academies ../data/academies` |

- Alembic 마이그레이션은 모델·운영 DB·테스트 호환성을 함께 검토해 **명시적으로** 작성한다.
- 데이터·추천·공급자 변경에는 **회귀 테스트를 추가**한다.
- pgvector 전용 경로는 `PGVECTOR_TEST_DATABASE_URL`을 설정해 검증한다.
  기본 테스트에서 스킵된다는 이유로 벡터 검색 경로의 운영 검증을 생략하지 않는다.

## 11. 인계 형식

PR 본문은 `.github/pull_request_template.md`를 채운다 — 목적, 현재 상태, 발견·근거(출처),
결정, 관련 파일, 검증 결과, 다음 작업, 위험·주의사항.
조사·작업 의뢰는 `.github/ISSUE_TEMPLATE/`의 템플릿을 사용한다.

외부 동작·데이터 규칙·기술 결정을 바꿨다면 `docs/api.md`, `docs/decision-log.md`,
필요 시 `docs/roadmap.md`를 **같은 PR에서** 갱신한다.

## 12. 하지 않을 것

- 관련 문서를 확인하지 않은 채 기존 결정과 충돌하는 구현
- 요청받지 않은 대규모 리팩터링 / 아키텍처 변경
- 학원 사실 데이터의 추측 입력, 휴리스틱 기반 사실 필드 채우기
- 학원 사실용 쓰기 API 추가
- `POST /recommendations`(하드 계약)의 동작 변경
- `score`를 절대 지표처럼 노출·저장
- 서비스 계층에서의 직접 ORM 조회, 세션 경계 밖으로 ORM 객체 반출
- 특정 벤더 SDK를 provider 포트 밖에서 직접 호출
- 비밀 값·원시 수집 데이터·리뷰 원문의 커밋
- 승인 범위를 넘는 외부 게시·구매·계정 변경 등 비가역 작업 (실행 전 Founder 확인)
