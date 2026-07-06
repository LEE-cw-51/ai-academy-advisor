# API 문서

## 현재 구현된 엔드포인트

### GET /
서비스 상태 메시지를 반환한다.

```json
{ "message": "AI Academy Advisor API is running" }
```

### GET /health
헬스체크 엔드포인트.

```json
{ "status": "ok" }
```

### GET /version
현재 API 버전을 반환한다.

```json
{ "version": "0.1.0" }
```

### GET /academies
학원 목록을 필터 조건으로 조회한다. 모든 파라미터는 선택이며 AND로 결합된다.

| 파라미터 | 값 | 의미 |
|---|---|---|
| `level` | `elementary` \| `middle` \| `high` | 해당 과정이 **확인된** 학원만 (`IS TRUE`) |
| `class_type` | `small_group` \| `group` \| `one_on_one` | 수업 형태 (소수정예/그룹/1:1) |
| `curriculum` | `seonhaeng` \| `naesin` \| `suneung` | 커리큘럼 (선행/내신/수능) |
| `shuttle` | `true` \| `false` | 차량운행. `false`는 "확인된 미운행"만 (미확인 제외) |
| `q` | 문자열 | 학원명·주소 부분 일치 검색 |
| `limit` | 1–100 (기본 20) | 페이지 크기 |
| `offset` | ≥0 (기본 0) | 페이지 시작 |

Boolean 필드의 `null`은 '미확인'을 뜻하며 어떤 필터에도 매치되지 않는다.
잘못된 enum 값은 422를 반환한다. 정렬은 이름 가나다순.

```json
{
  "items": [
    {
      "id": 1,
      "name": "미사한결수학(예시)",
      "address": "경기도 하남시 미사강변대로 100, 3층 (예시 주소)",
      "phone": "031-000-0001",
      "tagline": "초·중등 대상 소수정예 수학 전문학원(예시 데이터).",
      "subjects": ["수학"],
      "level_elementary": true,
      "level_middle": true,
      "level_high": false,
      "class_small_group": true,
      "class_group": false,
      "class_one_on_one": null,
      "curriculum_seonhaeng": true,
      "curriculum_naesin": true,
      "curriculum_suneung": false,
      "shuttle_available": true,
      "last_verified_at": "2026-07-01"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

`total`은 필터 조건에 맞는 전체 개수다 ("검색 결과 N개 학원" 표시용).

### GET /academies/{academy_id}
학원 상세를 반환한다. 목록 필드에 더해 `registration_number`, `website_url`,
`blog_url`, `instagram_url`, `operating_hours`, `established_year`,
`teacher_count`, `classroom_count`, `latitude`, `longitude`, `source_note`가 포함된다.

없는 id면 404:

```json
{ "detail": "Academy not found" }
```

## 향후 추가 예정 엔드포인트
- `POST /recommendations` — 조건 기반 학원 추천

쓰기(POST/PUT) API는 의도적으로 없다 — 학원 데이터의 정본은 git의
`data/academies/*.json`이며 임포터로 DB에 반영한다 (`docs/data-strategy.md`).
