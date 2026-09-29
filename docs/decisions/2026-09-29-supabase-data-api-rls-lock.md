# Supabase Data API 잠금 — public 핵심 테이블 RLS+REVOKE

- 날짜: 2026-09-29
- 상태: 채택
- 대체: 없음 (decision-log 2026-09-07 `0007` 범위를 확대; `academies` 전체 RLS·MVP 로그인 도입은 여전히 아님)

## 계기

Supabase Security Advisor가 `rls_disabled_in_public`(ERROR)로 `public` 스키마 7개 테이블
(`academies`, `reviews`, engagement 4종, `alembic_version`)을 지적했다. `anon`/`authenticated`에
전체 CRUD GRANT + RLS 미적용이면 publishable 키와 REST URL만으로 PostgREST 경유 읽기·수정·삭제가
가능하다. 앱은 FastAPI `DATABASE_URL`만 쓰지만 DB 레이어 방어가 없었다.

## 결정

- Alembic **`0011`**: 위 7테이블에 **`0007`/`0009`와 동일 패턴** — `ENABLE ROW LEVEL SECURITY` +
  `REVOKE ALL ON TABLE … FROM anon, authenticated`만 적용한다. **`service_role`·`postgres`는
  REVOKE하지 않는다.**
- **운영 적용**: session pooler **5432** `DATABASE_URL`에서 `cd backend && uv run alembic upgrade head`.
  스키마 정본은 git Alembic이며 Supabase MCP `apply_migration`으로 대체하지 않는다.
- **Cursor·Claude Supabase MCP**: OAuth + `postgres`(bypass RLS) 경로 — 설정(`read_only`, `project_ref`)·
  `list_tables`/`execute_sql` SELECT 점검 **변경 없음**.
- **Studio Table Editor**·**Vercel FastAPI**·공개 쓰기 API 없음 원칙 — **변경 없음**.

## 검토한 대안·트레이드오ff

- **RLS만 켜고 policy 추가**: anon 읽기 policy 등은 “공개 쓰기 API 없음”·현재 아키텍처(백엔드 전용 DB)와
  맞지 않고, Advisor “Enable RLS” 일괄 적용은 policy 설계 없이 혼란만 키운다.
- **`academies` 노출 유지**: 운영 정본 tampering 위험이 커서 이번에 Data API에서 제외하지 않는다.

## 바꾸지 않은 것

- FastAPI engagement·추천 API, 프론트 Supabase 클라이언트 미사용, 학원 사실 Studio 정본
- `academy_fact_revisions`/`academy_trait_labels` 잠금(`0007`/`0009`) — 0011은 나머지 7테이블만

## 검증·다음

- **2026-09-29 운영 적용 완료**: Supabase `xpdyuvydfrdinpobktlx`에 DDL 반영, `alembic_version` = `0011`.
  Security Advisor `rls_disabled_in_public` ERROR **0건**(INFO `rls_enabled_no_policy` 9건은 의도된 잠금 패턴).
  MCP `list_tables`·`execute_sql`·`anon` on `academies` privileges 빈 결과 확인.
- 다른 환경/복구 시: session 5432 `DATABASE_URL`에서 `cd backend && uv run alembic upgrade head`만 사용한다.
