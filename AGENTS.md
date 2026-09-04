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

학원콕의 상위 목표는 **학부모가 학원과 아이의 학습 상태를 둘러싼 블랙박스를 줄이고, 더 나은 질문과 판단을 하도록 돕는 것**이다. 바쁜 학부모는 아이가 수업에서 실제로 무엇을 경험하는지, 진도·오답·보강·질문 대응·소통이 어떻게 이루어지는지 직접 확인하기 어렵고, 사춘기 학생과의 정보 비대칭 때문에 강사 상담에 과도하게 의존하기 쉽다. 학원콕은 이를 확인 가능한 질문·정보·다음 행동으로 바꾼다.

첫 공개 MVP는 하남 미사 고정의 **무료 AI 보조 학원 탐색 도구**다. 사용자가 현재 다니는 학원 또는 원하는 조건과 고민을 입력하면, AI는 탐색 조건·상담 질문·추가 확인 항목으로 구조화한다. 화면은 출처·확인일이 있는 학원 기본 정보·지도·공개 연락처와 후보 근거·미확인 항목을 보여 주고, 사용자가 직접 전화·웹사이트·길찾기를 하게 한다. 핵심 자산은 UI가 아니라 **출처와 확인일을 갖춘 정확한 학원 사실 데이터베이스**이고, 지금은 유지보수 가능한 MVP가 우선이다.

첫 MVP에서는 학원 품질이나 아이의 상태를 단정하지 않는다. 확인되지 않은 수업 방식·오답 관리·질문 대응·클리닉·고등 연계 정보는 사실처럼 채우지 말고 **상담에서 확인할 점**으로만 제시한다. 공개 리뷰는 출처·시점·한계를 밝힌 주관적 경험 근거이며 학원 사실 DB를 덮어쓰지 않는다. 학원 전체 `teacher_count`·`classroom_count`만으로 반별 질문 대응 인력이나 교육 품질을 추론하지 않는다. 결과는 ‘최고’·‘확정 추천’·‘교육비 대비 우수’가 아니라 **조건과 관련해 확인해 볼 후보 정보**로 표현한다.

수강 신청, 예약, 결제, 상담 접수 대행, 학부모 연락처의 학원 전달, 대가성 결과 순위, 유료 상단 노출, 필수 로그인, 자녀 실명·생년월일·성적표·상세 자유 서술의 기본 수집은 첫 MVP 범위에 넣지 않는다. 로그인은 관심 학원 저장 또는 결과 재방문 수요가 검증된 뒤에만 선택적으로 검토한다. 전화·웹사이트·길찾기 클릭은 비식별 이벤트로만 남긴다.

배포된 `/`·`/check`·`/checklists`는 현재 소개·점검·체크리스트 퍼널이며, `/app`은 하남 미사 고정의 안내형 추천 화면이다. 실제 공개 탐색 MVP는 `상황 입력 → AI 조건/질문 정리 → 후보 정보·지도·근거/미확인 항목 → 사용자 직접 행동` 흐름으로 구현한다. **자유 대화형 채팅과 SSE 스트리밍(`POST /chat`)은 아직 미구현이며 첫 MVP의 기본 범위도 아니다.**

수익화는 무료 탐색의 유용성과 데이터 신뢰가 검증된 뒤에만 `무료 질문/탐색 → 데이터 신뢰·반복 사용 → 강화 프로필 수요 → 선택형 상담 예약·리드 연결` 순으로 검토한다. 광고·강화 프로필은 명확히 표시하고, 지불 여부가 일반 후보의 순서·AI 근거·추천 논리에 영향을 주면 안 된다. 당근 유료 광고는 무료 제품 구조와 별개로 심사 요건을 서면 확인한 뒤에만 재개한다.

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

**데이터** — 운영 정본은 Supabase Postgres `academies` 테이블이고 Founder는 Studio Table
Editor로 일상 수정한다. `data/academies/*.json`은 시드·백업 덤프이며 git 이력은 참고용이다.
컷오버·재해복구만 `import_academies --force`(또는 `ALLOW_ACADEMY_IMPORT=1`)로 JSON→DB.
학원 사실용 **공개** 쓰기 API는 만들지 않는다. 스키마 변경은 Alembic만.
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
cd backend && uv run python -m app.cli.import_academies ../data/academies --dry-run   # JSON 시드 검증
cd backend && uv run python -m app.cli.export_academies ../data/backups/YYYY-MM-DD   # 운영 DB 백업 덤프
```

머지됐다는 사실을 검증 완료로 치지 않는다. 데이터·추천·provider를 건드렸으면 회귀 테스트를 하나 남긴다.
pgvector 전용 경로는 `PGVECTOR_TEST_DATABASE_URL`을 설정해야 실제로 돈다 (기본 테스트에선 스킵).

## 9. 인계

PR 본문에 **무엇을 왜 했고, 어디까지 됐고, 다음에 뭘 하면 되는지**를 남긴다.
템플릿(`.github/`)이 있지만 형식이 목적은 아니다 — 다음 사람이 맥락을 다시 파헤치지 않으면 성공이다.
