# AGENTS.md — 에이전트 공통 메모

이 저장소는 여러 AI(ChatGPT · Claude · Cursor · Manus)와 Founder가 함께 쓴다.
AI끼리는 서로의 대화를 볼 수 없으므로, **저장소에 남지 않은 규칙과 결정은 없는 것과 같다.**
그래서 공통으로 알아야 할 것을 여기에 모은다.

> 이건 초기 버전이고, 계속 고쳐 쓸 문서다. 현실과 다르거나 지키기 불편하면
> 몰래 어기지 말고 이 파일을 고쳐서 PR을 올린다. 도구별 설정(Cursor 규칙, 커스텀
> 인스트럭션)에만 규칙을 추가하면 다른 AI가 볼 수 없으니 여기로 가져온다.

---

## 1. 작업 전에 훑어볼 것

- `docs/roadmap.md` — 지금 어느 Phase인가
- `docs/decision-log.md` — **이미 내려진 결정과 이유** (최신순). 여기와 충돌하는 제안을
  하려면 무엇이 바뀌어서 재검토가 필요한지 먼저 말한다
- 손대는 범위의 문서: `docs/architecture.md` · `api.md` · `database.md` · `data-strategy.md`
- `README.md` — 실행·배포 방법

## 2. 역할

| 담당 | 역할 |
|---|---|
| **Founder** | 최종 의사결정자 — 사업 판단·우선순위·승인 |
| **ChatGPT** | CEO / PM / 전략 — 방향성, MVP 범위, 요구사항 |
| **Claude** | CTO / Senior Engineer — 아키텍처·보안·확장성 검토, 코드 리뷰 |
| **Cursor** | Developer — 코드 구현, 리팩터링, 테스트 |
| **Manus** | Research & Execution — 웹 조사, 출처 검증, 데이터 수집·정리, 외부 실행 |

역할은 담장이 아니라 기본값이다. 넘어가야 하면 그렇게 하되 **그 사실을 밝힌다.**
다만 중요한 사업 판단의 최종 결정권은 항상 Founder에게 있다. AI는 선택지와 근거를 만든다.

자세한 역할·인계 규약: [docs/ai-team.md](docs/ai-team.md)

## 3. 결과를 어디에 남기나

- **결정과 그 이유** → `docs/decision-log.md` 맨 위 (`## YYYY-MM-DD — 제목`).
  가장 중요한 한 가지다. 나중에 되돌리려는 사람이 이유를 알 수 있게 쓴다.
- **외부 동작(엔드포인트·응답) 변경** → `docs/api.md`
- **제품 정의·범위 / Phase 진행** → `docs/project.md` · `docs/roadmap.md`
- **작업 인계** → PR 본문
- **조사 결과** → Issue 또는 `docs/` 문서 + decision-log 링크

새 문서를 만들기 전에 기존 문서 갱신으로 되는지 먼저 본다. 세션 안에서만 유효한 내용은 남기지 않는다.

## 4. 일하는 방식

- **Build Less, Learn Faster** — 과도한 엔지니어링, 근거 없는 기능 추가를 피한다
- **Evidence Before Assumption** — 확인 안 된 값은 추측하지 않는다. 중요한 결론을 단일 출처에 의존하지 않는다
- **Ship Early** — 고객 검증 > 매출 가능성 > 핵심 제품 > 자동화 > 운영 효율
- **Keep Context** — 다음 담당자가 맥락을 재구성하지 않아도 되게 남긴다

명확하면 바로 실행한다. 가정이 필요하면 **가정을 밝히고** 실행한다.
되돌리기 어려운 위험이 있을 때만 멈추고 확인한다.
기술 선택은 **문제 → 현재 구조 → 대안 → 트레이드오프 → 추천안** 순으로 제시한다.

## 5. 제품과 현재 범위

하남 미사 지역 학원의 구조화된 정보로 맞춤 추천을 하는 서비스(‘학원콕’)다.
핵심 자산은 UI가 아니라 **출처와 확인일을 갖춘 정확한 학원 사실 데이터베이스**이고,
지금은 유지보수 가능한 MVP가 우선이다.

배포된 `/`는 출시 전 소개·대기자 페이지다. 주 CTA는 카카오톡 출시 알림이며,
점검·카카오 체크리스트 전환은 `/check`만 담당한다. `/check`는 로그인·저장 없는
3문항 정적 도구(인트로 → 문항 → 결과+카카오)다. `/checklists`는 채널 웰컴메시지용
웹 체크리스트 허브다(페이월 없음). ‘하남 미사’ 고정의 **안내형 추천 화면**(학년·학교·
과목·학습 스타일 입력)은 `/app`에만 있다.
**자유 대화형 채팅과 SSE 스트리밍(`POST /chat`)은 아직 미구현**이니 있는 것처럼 전제하지 않는다.

## 6. 코드 구조

스택: FastAPI · SQLAlchemy 2 · Alembic · PostgreSQL+pgvector · uv / Next.js 15 · TypeScript · Tailwind

계층은 `api → services → repositories → models/DB`. 라우터는 HTTP와 검증만,
비즈니스 규칙은 서비스, DB 접근은 Repository가 맡는다.
AI 구성요소(LLM·임베딩·벡터)는 `app/providers/`의 Protocol 뒤에서만 쓴다 — 기본값은 stub이고
실제 공급자는 설정으로 켠다. 벤더 SDK를 포트 밖에서 직접 호출하지 않는다.

비밀 값은 `.env` / 플랫폼 변수로만. 코드·문서·PR에 쓰지 않는다.

## 7. 이건 지키자 (뒤에 이유가 있는 것들)

대부분은 유연하게 가되, 아래는 **실제로 버그가 났거나 데이터 신뢰를 깨는 지점**이라
바꾸려면 decision-log를 먼저 읽고 근거를 대자.

**데이터** — `data/academies/*.json`이 학원 사실의 유일한 git 정본이고 DB는 파생물이다.
수정은 JSON → `--dry-run` → PR → 머지 → 임포트 순서. 학원 사실용 쓰기 API는 만들지 않는다.
확인 안 된 값은 `null` (3상태: `true`=있음 / `false`=없음 / `null`=미확인).
이름에 "수학"이 있다고 `subjects`를 추측해 채우지 않는다. 가능하면 `source_note`·`last_verified_at`을 남긴다.
리뷰 원문·원시 수집 데이터는 커밋하지 않는다. → [docs/data-strategy.md](docs/data-strategy.md)
(`reviews`/`search_history`/`click_logs`/`feedback`/`waitlist`는 DB 직접 쓰기가 허용된 예외다.)

**추천 경로 두 개는 일부러 분리돼 있다** — `POST /recommendations`는 하드 필터(AND, null 제외),
`POST /recommendations/ai`는 넓은 후보 + 소프트 랭킹이다. NULL이 많은 실데이터에서 결과가
비지 않게 하려고 나눈 것이니 DRY를 이유로 합치지 않는다. → [docs/api.md](docs/api.md)

**`score`는 응답 안에서의 상대 순위값**이다. 별점·퍼센트·신뢰도처럼 보여주거나 저장하지 않는다.

**`services/scoring.py`는 ORM/모델을 import하지 않는 순수 모듈**이고,
**`recommendation_pipeline.py` 밖으로 ORM 객체나 열린 세션을 내보내지 않는다** (테스트로 강제됨).

**목록·추천 응답의 좌표는 지도 표시에 필요하니 그대로 둔다.** 배포 프론트가 붙으면 `CORS_ORIGINS`는 JSON 배열로 설정한다.

## 8. 검증

```bash
cd backend && uv sync && uv run pytest ../tests     # 백엔드
cd frontend && npm ci && npm run build              # 프론트엔드
cd backend && uv run python -m app.cli.import_academies ../data/academies --dry-run   # 데이터 변경 시
```

머지됐다는 사실을 검증 완료로 치지 않는다. 데이터·추천·provider를 건드렸으면 회귀 테스트를 하나 남긴다.
pgvector 전용 경로는 `PGVECTOR_TEST_DATABASE_URL`을 설정해야 실제로 돈다 (기본 테스트에선 스킵).

## 9. 인계

PR 본문에 **무엇을 왜 했고, 어디까지 됐고, 다음에 뭘 하면 되는지**를 남긴다.
템플릿(`.github/`)이 있지만 형식이 목적은 아니다 — 다음 사람이 맥락을 다시 파헤치지 않으면 성공이다.
