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
      "tuition_monthly_fee": 280000,
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

### POST /recommendations
조건 기반 학원 추천 (규칙 기반 필터링). `GET /academies`의 모든 파라미터
(`level`, `class_type`, `curriculum`, `shuttle`, `q`, `limit`, `offset`)에 더해
다음 두 조건을 지원하며, 모든 조건은 AND로 결합된다.

| 필드 | 값 | 의미 |
|---|---|---|
| `region` | 문자열 | 주소(`address`) 부분 일치 (`q`와 별개로 지역 조건 전용) |
| `budget_max` | 정수 ≥ 0 | 월 수강료 상한 (원). 수강료가 **확인되고** 상한 이하인 학원만 포함 (미확인은 제외) |

요청/응답 예시:

```json
POST /recommendations
{ "level": "middle", "region": "미사", "budget_max": 300000 }
```

```json
{
  "items": [
    {
      "id": 1,
      "name": "미사한결수학(예시)",
      "address": "경기도 하남시 미사강변대로 100, 3층 (예시 주소)",
      "tuition_monthly_fee": 280000,
      "level_middle": true,
      "...": "..."
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

응답 형태는 `GET /academies`와 동일한 요약 필드(`AcademySummary`)를 사용한다.
잘못된 enum 값이나 음수 `budget_max`는 422를 반환한다.

### POST /recommendations/ai
자연어 질문 기반 AI 추천 (기획안 §6 기능2·§9). 파이프라인은 provider 포트를 경유한다:
질문 기록 → 의도 분석 → 조건 필터링 → RAG 근거 검색 → 추천 이유 생성.

현재 provider는 기본 **stub**이며(키·비용 0), 의도 분석은 규칙 기반이다. 실제
임베딩/LLM/pgvector·LlamaIndex는 config만 바꿔 교체된다 (`docs/architecture.md`).
리뷰 ingest 전에는 `evidence_reviews`가 빈 배열일 수 있다.

| 필드 | 값 | 의미 |
|---|---|---|
| `query` | 문자열 (1–500, 필수) | 자연어 질문 |
| `limit` | 1–10 (기본 3) | 추천 개수 |

```json
POST /recommendations/ai
{ "query": "고1 내신 미사 수학학원" }
```

```json
{
  "query": "고1 내신 미사 수학학원",
  "parsed_intent": { "level": "high", "curriculum": "naesin", "region": "미사" },
  "items": [
    {
      "academy": { "id": 1, "name": "가온수학(예시)", "...": "..." },
      "reason": "추천 이유 (AI 생성)",
      "score": 3.0,
      "evidence_reviews": [
        { "content": "고1 내신 대비가 좋았습니다", "source": "맘카페", "rating": 5 }
      ]
    }
  ]
}
```

`parsed_intent`는 질문 해석 결과(적용된 필터)를 투명하게 노출한다. `items`의 학원은
`AcademySummary` 요약 필드를 사용한다.

## engagement 쓰기 API

학원 데이터의 정본은 git(읽기 전용)이지만, 사용자 행동 데이터는 DB 직접 쓰기다
(`docs/data-strategy.md`). KPI(외부 행동률·대기자 등록률 등) 측정용. 성공 시 `201`과
`{ "id", "created_at" }`를 반환한다.

### POST /events
외부 행동 클릭 추적 (기획안 §6 기능5).

| 필드 | 값 | 의미 |
|---|---|---|
| `academy_id` | 정수 ≥ 1 \| null | 대상 학원 (없어도 됨) |
| `event` | `phone` \| `website` \| `directions` \| `detail` | 전화/홈페이지/길찾기/상세보기 |

잘못된 `event`는 422, 존재하지 않는 `academy_id`는 404.

```json
POST /events
{ "academy_id": 1, "event": "phone" }
```

### POST /feedback
완료 화면 만족도 피드백 (기획안 §6 기능6).

| 필드 | 값 | 의미 |
|---|---|---|
| `rating` | 문자열 (1–20, 필수) | 만족도 (예: `😀`/`😐`/`☹️`) |
| `comment` | 문자열 \| null | 자유 코멘트 |

### POST /waitlist
정식 출시 알림 신청 (기획안 §6 기능6). `email`과 `kakao` 중 **최소 하나**는 필요하며,
둘 다 비면 422.

| 필드 | 값 | 의미 |
|---|---|---|
| `email` | 문자열 \| null | 이메일 |
| `kakao` | 문자열 \| null | 카카오 플러스친구 식별자 |

---

학원 데이터에 대한 쓰기(POST/PUT) API는 의도적으로 없다 — 정본은 git의
`data/academies/*.json`이며 임포터로 DB에 반영한다 (`docs/data-strategy.md`).
`POST /recommendations`는 읽기 전용 조회다. 단, `POST /recommendations/ai`는 질문을 `SearchHistory`로 기록하며,
위 engagement 엔드포인트들과 함께 사용자 행동 데이터를 DB에 직접 쓴다 (승인된 예외).
