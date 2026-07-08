# 데이터베이스

## 현재 상태
도메인 테이블 `academies`가 정의되어 있다 (마이그레이션 `0001`).
**정본 데이터는 `data/academies/*.json`이고 DB는 임포터로 재구성되는 파생 저장소다.**
전략·필드 사전·수집 원칙은 `docs/data-strategy.md`, 파일 포맷은 `data/README.md` 참고.

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

### subjects 컬럼
SQLite(테스트)에서는 JSON, PostgreSQL(운영)에서는 JSONB로 저장된다
(`with_variant`). JSON containment 연산이 dialect 간 호환되지 않으므로
표시 전용이며, 과목 필터가 필요해지면 `academy_subjects` junction 테이블로 이관한다.

## reviews (후기) — Phase 3에서 검토
학원별 후기/평점. 사용자 쓰기 데이터이므로 git 정본을 거치지 않고 DB에 직접 쓴다.

## 마이그레이션
- Alembic으로 관리 (`backend/alembic/`)
- `Base.metadata`에 네이밍 컨벤션 적용 (ix_/uq_/ck_/fk_/pk_) — 제약 이름이 결정적
- 초기 마이그레이션 `0001_create_academies_table.py`는 수작성
  (autogenerate는 라이브 DB가 필요하므로)
- `0002_add_tuition_monthly_fee.py` — 추천 API의 예산 조건을 위해 nullable 컬럼 추가

```bash
cd backend
uv run alembic upgrade head      # 적용
uv run alembic downgrade base    # 롤백
```
