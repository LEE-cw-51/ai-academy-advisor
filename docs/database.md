# 데이터베이스

## 현재 상태
도메인 테이블 `academies`가 정의되어 있다 (마이그레이션 `0001`).
**운영 정본은 Supabase Postgres `academies` 테이블**이고 Founder는 Studio Table Editor로
일상 수정한다. `data/academies/*.json`은 시드·백업 덤프이며 `import_academies`는
컷오버·로컬 개발용이다. 전략·필드 사전·수집 원칙은 `docs/data-strategy.md`, 파일 포맷은
`data/README.md` 참고.

## academies (학원)

| 컬럼 | 타입 | NULL | 설명 |
|---|---|---|---|
| id | integer PK autoincrement | X | 내부 식별자 (환경 간 안정성 없음 — 외부 식별은 자연키 사용) |
| registration_number | varchar(50) UNIQUE | O | 학원 등록번호 (공식). 자연키 #1 |
| name | varchar(100), index | X | 학원명 |
| address | varchar(200) | O | 주소 |
| phone | varchar(20) | O | 전화번호 |
| website_url / blog_url / instagram_url | varchar(300) | O | 공식 채널 URL |
| subjects | JSON (PG: JSONB) | O | 과목 리스트. 표시 전용 — 필터 불가 |
| level_elementary / level_middle / level_high | boolean | O | 초/중/고 (3상태) |
| class_small_group / class_group / class_one_on_one | boolean | O | 소수정예/그룹/1:1 (3상태) |
| curriculum_seonhaeng / curriculum_naesin / curriculum_suneung | boolean | O | 선행/내신/수능 (3상태) |
| shuttle_available | boolean | O | 차량운행 (3상태) |
| tuition_monthly_fee | integer | O | 월 수강료 (원). `NULL` = 미확인 (불리언이 아니므로 "확인됨-없음" 상태는 없음) |
| operating_hours | text | O | 운영시간 (자유 서술) |
| established_year / teacher_count / classroom_count | integer | O | 개원년도/강사수/강의실수 |
| tagline | varchar(200) | O | 한 줄 소개 (수동 큐레이션) |
| latitude / longitude | float | O | 좌표 (추후 지도) |
| source_note | text | O | 출처 메모 |
| last_verified_at | date | O | 최종 확인일 |
| created_at / updated_at | timestamptz | X | 생성/수정일시 (API 비노출) |

### 3상태 Boolean 원칙
`NULL` = 미확인, `FALSE` = 확인됨-없음, `TRUE` = 확인됨-있음.
필터 쿼리는 `IS TRUE` / `IS FALSE`를 명시해 미확인을 결과에서 제외한다.
이 구분이 "가장 정확한 DB" 목표의 핵심 설계다.

### 제약 / 인덱스
- `pk_academies` — PK(id)
- `uq_academies_registration_number` — 등록번호 유니크
- `uq_academies_name_address` — 등록번호 없는 학원의 중복 방지 안전망
  (address가 NULL이면 DB 레벨에서는 중복이 허용되므로, 임포터의 파일 간 중복 검사가 원천 차단한다)
- `ix_academies_name` — 이름 검색/정렬용
- `ck_academies_subjects_taxonomy` — Postgres: `subjects`는 null이거나 taxonomy 5종만
  (`app.core.studio_guards`, Alembic `0006`)
- `ck_academies_website_not_social` — Postgres: `website_url` netloc이
  instagram/pf.kakao/youtube/litt.ly/ok114 및 플레이스·카페·블로그 호스트와
  정확히 일치하거나 해당 호스트의 서브도메인이면 거부 (`host = marker OR
  host LIKE '%.marker'`). Python `website_url_has_rejected_host`와 같다.
  CHECK에 없는 것: http(s) 스킴, 빈 netloc, `names_match`, 블로그 id 관련성.
- UPDATE 트리거: `id` 변경 금지. `registration_number`는 이미 있는 값 변경 금지
  (NULL→값 백필은 허용). `last_verified_at`이 비어 있으면 `CURRENT_DATE` — 단,
  트랜잭션 GUC `app.skip_academy_stamp=1`(JSON 임포트)이면 스탬프하지 않음.

### subjects 컬럼
SQLite(테스트)에서는 JSON, PostgreSQL(운영)에서는 JSONB로 저장된다
(`with_variant`). 허용 값은 `국어`/`영어`/`수학`/`과학`/`기타` 뿐이며 복수 기입 가능하다.
JSON containment 연산이 dialect 간 호환되지 않으므로 표시·소프트 랭킹 전용이며,
과목 하드 필터가 필요해지면 `academy_subjects` junction 테이블로 이관한다.

## reviews (후기) — Phase 3에서 검토
학원별 후기/평점. 사용자 쓰기 데이터이므로 git 정본을 거치지 않고 DB에 직접 쓴다.

## 마이그레이션
- Alembic으로 관리 (`backend/alembic/`)
- `Base.metadata`에 네이밍 컨벤션 적용 (ix_/uq_/ck_/fk_/pk_) — 제약 이름이 결정적
- 초기 마이그레이션 `0001_create_academies_table.py`는 수작성
  (autogenerate는 라이브 DB가 필요하므로)
- `0002_add_tuition_monthly_fee.py` — 추천 API의 예산 조건을 위해 nullable 컬럼 추가
- `0006_academy_studio_guards.py` — Postgres 전용: 기존 행 CHECK 사전 검사(위반 시
  중단), 과목/URL CHECK(호스트 매칭), 신원 필드 불변, `last_verified_at` 스탬프
  (임포트 GUC 우회), `academy_fact_revisions` 이력 (Supabase Studio 운영용)

### academy_fact_revisions (Postgres, Studio 이력)

| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | bigint PK | |
| academy_id | integer (FK 없음) | 학원 행을 지워도 이력을 남긴다 |
| old_row | jsonb | UPDATE 직전 행 전체 |
| changed_at | timestamptz | |
| db_role | text | DB role (`current_user`) |

Studio에서 `academies` 행을 수정하면 AFTER UPDATE 트리거가 이전 스냅샷을 남긴다.
롤백은 SQL로 스냅샷을 참고해 수동 복구한다. 스키마 변경은 Studio DDL이 아니라 Alembic만.

```bash
cd backend
uv run alembic upgrade head      # 적용
uv run alembic downgrade base    # 롤백
```
