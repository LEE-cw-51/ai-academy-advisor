# public 테이블을 Data API에서 잠근다

- 날짜: 2026-09-29
- 상태: 채택
- 대체: decision-log.md 2026-09-07 — PR #40 리뷰 픽스: deadline · RLS · Preview 가드 · export · Netlify 문서
  (그 항목의 "`academies` 전체 RLS는 범위 밖"만 좁힌다. 사용자 로그인을 넣지 않는다는 부분은 유지)

## 계기

Supabase가 `rls_disabled_in_public`(ERROR)를 알렸다. 프로젝트
`ai-academy-advisor`(`xpdyuvydfrdinpobktlx`)의 Advisors와 권한을 확인했다.

`public`은 PostgREST에 노출된다. 아래 7개 테이블은 RLS가 꺼져 있고
`anon`·`authenticated`에 SELECT/INSERT/UPDATE/DELETE/TRUNCATE가 있었다.

| 테이블 | 당시 행 수 |
|---|---|
| academies | 411 |
| reviews | 1146 |
| search_history | 43 |
| click_logs | 40 |
| feedback | 0 |
| waitlist | 0 |
| alembic_version | 1 |

프론트는 supabase-js를 쓰지 않는다. 학원 조회는 FastAPI → SQLAlchemy →
`postgres` 연결이다. 그래도 publishable 키만 있으면 Data API로 학원 사실과
리뷰·검색 이력을 읽고 고치고 지울 수 있었다.

`academy_fact_revisions`와 `academy_trait_labels`는 이미 `0007`·`0009`로
잠겨 있었다. 2026-09-07 결정은 그 감사 테이블만 잠그고 `academies` 전체 RLS는
그 PR 범위 밖으로 두었다. Data API GRANT가 남아 있으면 "공개 쓰기 API를 만들지
않는다"는 앱 계약만으로는 막히지 않는다.

## 결정

나머지 public 테이블도 같은 방식으로 잠근다. Alembic `0011`.

- `ALTER TABLE … ENABLE ROW LEVEL SECURITY`
- `REVOKE ALL ON TABLE … FROM anon, authenticated`
- 정책은 만들지 않는다. 정책이 없으면 `anon`·`authenticated`는 행에 닿지 못한다.

대상: `academies`, `reviews`, `search_history`, `click_logs`, `feedback`,
`waitlist`, `alembic_version`.

`postgres`와 `service_role`은 `BYPASSRLS`다. Studio Table Editor와 FastAPI는
그대로다. 사용자 로그인이나 행 단위 정책을 도입하는 결정이 아니다.

새 public 테이블도 마이그레이션에 같은 두 문을 넣는다. `postgres`의 기본
권한은 새 테이블에 `anon` GRANT를 다시 붙인다.

## 검토한 대안·트레이드오프

- **API 설정에서 `public` 스키마 노출을 빼기.** Data API 전체를 막지만, 설정이
  저장소 밖에 있고 테이블을 나중에 다시 노출하면 같은 구멍이 돌아온다. 테이블
  잠금이 저장소에 남는다.
- **읽기용 RLS 정책을 만들어 anon SELECT를 허용.** 학원 연락처·리뷰·검색
  이력을 브라우저 키로 열게 된다. 앱은 FastAPI만 쓰면 된다.
- **`FORCE ROW LEVEL SECURITY`.** 테이블 소유자에게도 RLS를 적용한다.
  `postgres`는 `BYPASSRLS`라 Studio는 남지만, 소유자 우회를 막는 추가 장치는
  이번 잠금에 필요 없다.

## 바꾸지 않은 것

- FastAPI 라우트, 프론트, Studio로 학원 사실을 고치는 운영
- `0007`·`0009`의 기존 잠금
- 사용자 로그인

## 하지 않은 것

- `postgres` 기본 권한(`ALTER DEFAULT PRIVILEGES`)을 바꾸지 않았다. Supabase가
  프로젝트 쪽에서 다시 깔 수 있고, 새 테이블은 마이그레이션에서 잠그는 쪽이
  이 저장소의 방식과 같다.
- 트리거 함수 `search_path` 고정(WARN 3건), `vector` 확장을 `public` 밖으로
  옮기기(WARN). 컬럼 타입을 갈아 끼우는 일이고 이번 메일 범위가 아니다.
- 행 내용은 읽지 않았다. 노출 여부는 권한·RLS·행 수로만 확인했다.

## 검증·다음

운영 DB(`ai-academy-advisor`)에 같은 잠금을 적용했다.

- `public` 테이블 9개 모두 RLS가 켜져 있다. `anon`·`authenticated`의 테이블 권한은 없다.
- `anon`의 `academies` 조회, `authenticated`의 `reviews` 조회는 권한 거부로 끝난다.
  `postgres`로는 학원 411행이 그대로 보인다.
- Security advisor의 `rls_disabled_in_public`(ERROR)는 없다. 정책이 없다는 INFO
  (`rls_enabled_no_policy`)는 잠금 방식 그대로다.
- `alembic_version`은 `0011`이다. 이 데이터베이스에서 `alembic upgrade head`는
  다시 실행되지 않는다. Supabase 마이그레이션 이력에도 같은 적용이 한 줄 있다.
  스키마 정본은 계속 Alembic이다.

아직 남은 advisor: 트리거 함수 `search_path` WARN 3건, `vector` 확장이
`public`에 있는 WARN. 이번 잠금과 별개다.
