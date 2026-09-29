# CLAUDE.md

**작업 전 [AGENTS.md](AGENTS.md)를 읽는다.** 에이전트 공통 메모 — 제품 범위, 계층 규칙,
데이터 정본 원칙, API 계약, 검증 명령이 거기 있다. 여기엔 Claude 역할의 특이사항만 둔다.
규칙이 바뀌면 이 파일이 아니라 `AGENTS.md`를 고친다.

## 이 프로젝트에서 Claude의 역할 — CTO / Senior Engineer

- 아키텍처 설계, 보안·확장성 검토, 코드 리뷰, 기술 결정의 트레이드오프 분석을 담당한다.
- 기술적 선택은 **문제 → 현재 구조 → 대안 → 트레이드오프 → 추천안 → 구현** 순으로 제시한다.
- MVP 범위와 사업 우선순위는 ChatGPT·Founder의 영역이다. 기술적으로 더 나은 설계라도
  범위를 넓히는 제안이면 근거와 비용을 함께 제시하고 결정을 위임한다.
- 실제 구현·리팩터링은 기본적으로 Cursor의 역할이다. 요청받은 범위에서 필요한 변경은 직접
  수행하되 최소·명확하게 한다.

역할 전체는 [docs/ai-team.md](docs/ai-team.md) 참고.

## 자주 틀리는 지점 (구현·리뷰 시 우선 확인)

- `services/scoring.py`는 ORM/모델 import 금지 — 순수 랭킹 모듈 (테스트로 강제됨)
- `recommendation_pipeline.py` 밖으로 ORM 객체·열린 세션을 넘기지 않는다
- `POST /recommendations`(하드 필터)와 `POST /recommendations/ai`(소프트 랭킹)는
  **의도적으로 분리된 두 계약**이다. DRY를 이유로 통합하지 않는다
- `score`는 응답 내 상대값 — 별점·퍼센트·신뢰도로 표시하거나 저장하지 않는다
- 학원 사실 운영 정본은 Supabase Postgres `academies`(Studio 수정). git JSON은 시드·백업. 공개 쓰기 API 없음
- 확인되지 않은 사실은 `null`. 휴리스틱으로 채우지 않는다
- 벤더 SDK는 `app/providers/` 포트 뒤에서만 호출한다

## 아키텍처·보안 리뷰

아키텍처·보안을 검토할 때, 그리고 PR이 배포·인증·DB·provider·공개 쓰기를 건드릴 때 아래를 본다. 계층·provider·배포 구조는 여기에 다시 적지 않는다. [docs/architecture.md](docs/architecture.md)를 읽는다. 제보·범위·CI 기준은 [SECURITY.md](SECURITY.md)다.

- **모듈 의존** — `api → services → repositories`. 벤더 SDK는 `app/providers/` 포트 밖에서 호출하지 않는다.
- **결합** — `services/scoring.py`는 ORM·모델을 import하지 않는다. `recommendation_pipeline.py` 밖으로 ORM 객체나 열린 세션을 넘기지 않는다.
- **인증·인가** — `public` 테이블은 Data API에 열지 않는다. migration `0007`/`0011`과 같이 정책 없는 RLS + `anon`·`authenticated` `REVOKE`. 학원 사실 공개 쓰기 API를 만들지 않는다. `NEXT_PUBLIC_`에는 브라우저에 나가도 되는 값만 둔다.
- **데이터 흐름** — 확인 안 된 사실은 `null`. 전화·웹사이트·길찾기 클릭은 비식별 이벤트만 남긴다. 자녀 실명·성적은 기본으로 수집하지 않는다.
- **장애** — 외부 LLM·임베딩 실패가 처리되지 않은 5xx로만 끝나지 않는지. 서버리스 DB는 `NullPool`과 transaction pooler 포트 6543을 유지하는지.
- **확장** — `POST /recommendations`와 `POST /recommendations/ai`는 분리된 두 계약으로 둔다. `score`는 저장하거나 별점·퍼센트로 보여주지 않는다.

## 검증

```bash
cd backend && uv sync && uv run pytest ../tests     # 백엔드
cd frontend && npm ci && npm run build              # 프론트엔드
```

머지되었다는 사실을 검증 완료로 간주하지 않는다. 항상 다시 실행한다.
