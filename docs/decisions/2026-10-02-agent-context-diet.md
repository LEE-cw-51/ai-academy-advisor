# 에이전트 컨텍스트 정리 — 중복 규칙·범용 스킬·대용량 파일을 줄인다

- 날짜: 2026-10-02
- 상태: 채택
- 대체: 없음

## 계기

매 턴 Cursor에 올라가는 규칙이 세 벌이었다. `AGENTS.md`, `CLAUDE.md`, `.cursor/rules/project-context.mdc`가 같은 함정 목록(scoring 순수 모듈, 추천 API 분리, `score` 비저장, `null` 원칙)과 검증 명령을 반복했다. `.agents/skills/design-taste-frontend`(약 86KB)와 `redesign-existing-projects`는 `.gitignore`가 범용 스킬을 무시하기 전에 커밋되어 추적 중이었고, 디스크에만 있던 `archify`는 약 8MB였다. 동결된 `docs/decision-log.md`(약 1,500줄)는 통째로 읽히기 쉬웠고, 맨 위 2026-09-13 항목은 이미 퇴역한 `/check`·`/checklists`를 유지한다고 적고 있었다. `.cursorignore`는 없었다.

같은 문제가 문서의 “지금”에도 있다. `docs/roadmap.md`는 위에서 Phase 4·5를 진행 중으로 적고, 아래 Phase 5e(2026-09-23)가 실제 검증 단계다. Phase 6은 Docker Compose 운영인데 배포 정본은 Vercel 한 프로젝트다. `AGENTS.md` §5, `docs/project.md`, 마케팅 문서의 “1분 점검” 블록이 그 이전 단계를 현재형으로 남겨 둔다. `.cursor/skills`와 `.claude/skills`의 범용 스킬 사본은 git에서 무시돼도 Cursor 인덱스에는 남는다.

## 결정

- 범용 스킬 `design-taste-frontend`·`redesign-existing-projects`는 추적을 끊고 삭제한다. `archify`도 삭제한다. `skills-lock.json`에는 `web-design-guidelines`만 남긴다. 프로젝트 시각 언어 정본은 [2026-09-25 결정](2026-09-25-visual-language.md), 다이어그램 정본은 `docs/diagrams/academy-advisor.architecture.json`이다.
- `.cursorignore`로 대용량·비정본 파일(`data/registry/`, `data/raw/`, `docs/design/academy-kok-landing.html`, `docs/diagrams/*.html`, archify 전달 스냅샷, `tmp_audit_out/`, `*.db`)을 에이전트 인덱스·검색에서 뺀다. `.cursor/skills/*`와 `.claude/skills/*`의 범용 사본도 빼고 `landing-funnel-change`만 남긴다. `web-design-guidelines`의 추적 정본은 `.agents/skills/`다.
- `CLAUDE.md`와 `.cursor/rules/project-context.mdc`는 역할과 "정본은 `AGENTS.md`" 포인터만 둔다. `CLAUDE.md`의 아키텍처·보안 리뷰 체크리스트는 [2026-09-28 보안 기준](2026-09-28-security-baseline.md)이 PR 리뷰 도구로 쓰므로 남기되, `AGENTS.md` §6·§7과 겹치는 항목은 뺀다.
- `AGENTS.md` 1절에 `docs/decision-log.md`는 날짜 제목으로 검색해 해당 항목만 읽는다는 한 줄을 둔다. 같은 절의 roadmap 지시는 파일 전체가 아니라 `## 현재`만 읽게 좁힌다.
- 지금 할 일의 정본은 `docs/roadmap.md`의 `## 현재` 하나다. 지금은 Phase 5e 학부모 학습 점검 반복 루프 검증이고, 배포 정본은 [2026-09-14 Vercel 한 프로젝트](2026-09-14-single-vercel-project-services.md)다. 그 아래 단계 본문은 기록으로 둔다.
- `AGENTS.md` §5의 제품 제약(미확인은 `null`, 확정 추천 금지, `/app`, 채팅은 MVP 밖, 리드 연결 금지)은 남긴다. “지금 검증하는 일”은 roadmap `## 현재`를 가리키게 한다.
- `docs/project.md`의 “현재 단계”와 “최신 사업화·검증 기준 (2026-09-18)” 앞에, 2026-09-22·09-23 결정이 검증 초점을 좁혔다는 배너를 둔다. 제품 원칙 본문은 유지한다.
- `docs/marketing-daangn-kakao.md`에서 공개 제품이 “1분 학원 점검·상담 전 질문”이라고 한 블록은 2026-09-14 이전 초안으로 표시한다. 광고 본문은 다시 쓰지 않는다.
- `docs/business-model-canvas.md`의 “현재 1순위는 모델 A” 반복 문장 중 앞 문장만 뺀다.
- `docs/learning-log.md`는 2026-07-03 한 건뿐이라 동결한다. 새 항목은 결정 파일과 PR에 남긴다.
- `docs/architecture.md` 서비스 설명의 “추후 OpenAI 연동”은 현재 `app/providers/` 포트로 고친다. `POST /chat`이 아직 미구현이라는 문장은 유지한다.
- `docs/decision-log.md` 상단 동결 안내에 2026-09-13 항목의 `/check`·`/checklists` 유지 문장을 [2026-09-14 퇴역 결정](2026-09-14-retire-check-and-checklists.md)이 대체했다는 포인터를 둔다. 항목 본문은 고치지 않는다.

## 검토한 대안·트레이드오프

- **공개 정리 스킬 설치**(`doc-cleanup`, `dead-code-audit`, `codebase-cleanup`, `improve-codebase`). 설치 수가 적거나, 결정 로그 동결·추천 API 분리 같은 이 저장소 규칙과 맞지 않아 설치하지 않는다.
- **`docs/decision-log.md`를 `.cursorignore`에 넣기.** 토큰은 가장 많이 줄지만 `tests/test_app_explore_copy.py`가 본문 문구를 검사하고 옛 결정 조회가 막힌다. 읽기 방식만 제한한다.
- **`.cursor/rules/security.mdc` 제거.** 코드에 바로 적용할 금지만 있어 중복이 적다. 유지한다.
- **로드맵·프로젝트·마케팅 본문을 현재 단계에 맞게 다시 쓰기.** 다음에도 세 곳이 어긋난다. 현재 포인터와 상태 배너만 두고 본문은 기록으로 남긴다.
- **새 목차 문서.** 정본이 하나 더 생기면 다시 어긋난다. 만들지 않는다.

## 바꾸지 않은 것

- 앱 코드, `docs/api.md`, `docs/database.md`, `docs/data-strategy.md`, 추천 엔드포인트, `ChatPanel`, 로고 자산
- `research/`, 대기행렬 제안 본문, [docs/ai-team.md](../ai-team.md) 본문
- gitignore된 전략 스킬(`obviously-awesome`, `jobs-to-be-done`, `landing-page-conversion-audit`, `webapp-testing`, `skill-manager`)과 `landing-funnel-change` 쌍의 이중 추적
- `docs/decision-log.md`의 기존 항목 본문
- 깨진 로컬 venv, gitignore된 archify 전달 스냅샷

## 검증·다음

- 결정 로그 가드 문구는 본문에 남아 있다. `cd backend && uv run pytest ../tests`는 로컬 venv의 `cp949` 오류로 이번에도 실행하지 않는다. UI 변경이 없어 브라우저 검증은 하지 않는다.
- 로고 PNG 무게(`logo.png` 약 768KB를 40px로 표시)는 페이지 성능 문제라 이번 범위 밖이다.
