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
- `ck_academies_subjects_taxonomy` — Postgres: `subjects`는 null이거나 taxonomy 4종만
  (`국어`/`영어`/`수학`/`기타`). 4종 재적용은 Alembic `0008` (원래 5종은 `0006`)
- `ck_academies_subject_detail_requires_etc` — Postgres: `subject_detail`은 null이거나
  `subjects @> '["기타"]'`일 때만 (Alembic `0008`, `app.core.studio_guards`)
- `ck_academies_website_not_social` — Postgres: `website_url` netloc이
  instagram/pf.kakao/youtube/litt.ly/ok114 및 플레이스·카페·블로그 호스트와
  정확히 일치하거나 해당 호스트의 서브도메인이면 거부 (`host = marker OR
  host LIKE '%.marker'`). Python `website_url_has_rejected_host`와 같다.
  CHECK에 없는 것: http(s) 스킴, 빈 netloc, `names_match`, 블로그 id 관련성.
- UPDATE 트리거: `id` 변경 금지. `registration_number`는 이미 있는 값 변경 금지
  (NULL→값 백필은 허용). `last_verified_at`이 비어 있으면 `CURRENT_DATE` — 단,
  트랜잭션 GUC `app.skip_academy_stamp=1`(JSON 임포트)이면 스탬프하지 않음.

### subjects 컬럼 + subject_detail
SQLite(테스트)에서는 JSON, PostgreSQL(운영)에서는 JSONB로 저장된다
(`with_variant`). 허용 값은 `국어`/`영어`/`수학`/`기타` 4종(2026-09-11)이며 복수 기입
가능하다. 국·영·수는 확정 분류하고 그 외는 `기타`로 넣되, 실제 이름은 `subject_detail`
(`String(50)`, 예: `피아노`·`미술`·`과학`)에 남긴다. `subject_detail`은 `subjects`에
`기타`가 있을 때만 채운다. JSON containment 연산이 dialect 간 호환되지 않으므로
표시·소프트 랭킹 전용이며, 과목 하드 필터가 필요해지면 `academy_subjects` junction
테이블로 이관한다.

## reviews (후기·임베딩) — Phase 2/3, DB 직접 쓰기
학원별 공개 게시물 스니펫. `0003`에서 생성돼 이미 존재한다. 컬럼: `academy_id`(FK),
`content`, `source`(`naver_blog`/`naver_cafearticle`/…), `rating`(nullable),
`source_url`, `published_at`, `embedding`(pgvector `Vector(1024)`/SQLite JSON),
`created_at`. `(academy_id, source_url)` 복합 유니크로 재수집 중복을 막는다.
사용자·수집 데이터라 git 정본을 거치지 않고 DB에 직접 쓴다. 원문은 커밋하지 않는다
(`data/raw/`, gitignored). 수집 CLI는 `app.cli.ingest_reviews`, 임베딩 백필은
`app.cli.ingest_review_embeddings`.

## 마이그레이션
- Alembic으로 관리 (`backend/alembic/`)
- `Base.metadata`에 네이밍 컨벤션 적용 (ix_/uq_/ck_/fk_/pk_) — 제약 이름이 결정적
- 초기 마이그레이션 `0001_create_academies_table.py`는 수작성
  (autogenerate는 라이브 DB가 필요하므로)
- `0002_add_tuition_monthly_fee.py` — 추천 API의 예산 조건을 위해 nullable 컬럼 추가
- `0006_academy_studio_guards.py` — Postgres 전용: 기존 행 CHECK 사전 검사(위반 시
  중단), 과목/URL CHECK(호스트 매칭), 신원 필드 불변, `last_verified_at` 스탬프
  (임포트 GUC 우회), `academy_fact_revisions` 이력 (Supabase Studio 운영용)
- `0007_academy_fact_revisions_rls.py` — `academy_fact_revisions`에 정책 없는 RLS
  ENABLE + `REVOKE ALL … FROM anon, authenticated` (Data API 잠금). Studio·
  service_role은 계속 접근. `academies` 전체 RLS·MVP 로그인은 범위 밖.
- `0008_subjects_taxonomy_4_and_subject_detail.py` — `subject_detail` 컬럼 추가(전
  dialect), Postgres 전용: `과학` 등 4종 밖 subjects·기타 없는 subject_detail 사전
  검사(위반 시 중단) → 과목 CHECK 4종 재생성 + subject_detail 결합 CHECK. downgrade는
  옛 5종을 하드코딩.
- `0009_academy_trait_labels.py` — `academy_trait_labels` 생성(닫힌 라벨·
  source_type·status CHECK, `(academy_id, label, source_url)` 유니크). Postgres:
  정책 없는 RLS + REVOKE(Data API 잠금, `0007`과 동일). 배치 CLI
  `app.cli.ingest_trait_labels` (reviews → candidate, 사실 컬럼 미기입).
- `0010_trait_label_constraint_names.py` — `0009`의 CHECK 이름이 모델과 갈라진 것을
  맞춘다. `op.create_table` 안의 `sa.CheckConstraint(name=...)`에 완성된 이름을
  넘겨서 Alembic이 `Base.metadata`의 `ck_%(table_name)s_%(constraint_name)s`를 한 번
  더 씌웠고, 운영에 `ck_academy_trait_labels_ck_academy_trait_labels_label`이 들어갔다.
  `0009`는 짧은 이름을 넘기도록 고쳤으므로 새 DB는 처음부터 맞고, 이 리비전은 이미
  적용된 DB만 존재 검사 후 rename 한다(신규 DB에서는 no-op). 중복 인덱스
  `ix_academy_trait_labels_academy_id`도 제거 — 유니크 제약
  `(academy_id, label, source_url)`의 선두 컬럼이 같은 조회를 커버한다.

### academy_trait_labels (Postgres, 주관 언급 메타)

| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | integer PK | |
| academy_id | integer FK → academies | |
| label | text | 닫힌 6종 `mentions_*` |
| source_type | text | `review` \| `homepage` \| `blog` |
| source_url | text | dedup 키 (URL 없으면 `review:{id}`) |
| snippet | text | 짧은 근거 창 |
| observed_at | date | 원문 시점(있으면) |
| status | text | `candidate` \| `published` (기본 candidate) |
| created_at | timestamptz | |

카드/상담 노출은 Stage 3 이후. scoring·`curriculum_*`와 연결하지 않는다.

닫힌 어휘(라벨 6종·source_type·status)의 정본은 `app.core.trait_labels` 하나다.
모델 CHECK가 거기서 생성되고, 키워드 사전(`app.services.trait_label_matcher`)이
같은 집합인지는 테스트가 강제한다. 어휘를 바꾸면 새 마이그레이션이 필요하다.
인덱스는 `label` 단독과 유니크 제약 두 개뿐이다.

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
감사 테이블 Data API 잠금(`0007`)은 MVP 사용자 로그인/RLS 도입이 아니다.

```bash
cd backend
uv run alembic upgrade head      # 적용
uv run alembic downgrade base    # 롤백
```
