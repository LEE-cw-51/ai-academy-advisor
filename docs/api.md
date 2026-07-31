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
      "last_verified_at": "2026-07-01",
      "latitude": 37.5601526466,
      "longitude": 127.1866028387
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

`total`은 필터 조건에 맞는 전체 개수다 ("검색 결과 N개 학원" 표시용).
`latitude`/`longitude`는 목록 응답에도 포함된다 (지도에 검색 결과를 바로 표시하기 위함).
미확인이면 `null`.

### GET /academies/{academy_id}
학원 상세를 반환한다. 목록 필드에 더해 `registration_number`, `website_url`,
`blog_url`, `instagram_url`, `operating_hours`, `established_year`,
`teacher_count`, `classroom_count`, `source_note`가 포함된다.

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
자연어 질문 기반 AI 추천 (기획안 §6 기능2·§9). `POST /recommendations`(하드 필터)와
달리 **넓은 후보 풀 + 적합도 랭킹**이다. 3상태 bool·예산은 SQL에서 배제하지 않고
점수로 반영하므로, 미확인(NULL) 학원도 결과에 나타날 수 있다.

파이프라인: 질문 기록 → 의도 분석 → 소프트 후보 풀(완화 사다리) → RAG 근거 검색 →
적합도 채점 → 상위 `limit`건만 추천 이유 생성.

현재 provider 기본값은 **stub**이며(키·비용 0), 의도 분석은 규칙 기반이다.
`EMBEDDING_PROVIDER=openai` + `VECTOR_STORE=pgvector`로 전환하면 실제 임베딩(OpenAI
`text-embedding-3-small`)과 pgvector 코사인 검색이 동작한다 (config만 바꿔 교체,
`docs/decision-log.md`). LLM은 여전히 config로 별도 선택(`LLM_PROVIDER=groq` 등).
실제 provider로 전환한 뒤에도 `Review.embedding`을 채우는 백필 CLI
(`uv run python -m app.cli.ingest_review_embeddings`)를 먼저 실행하지 않았다면
`evidence_reviews`가 빈 배열일 수 있다.

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
  "parsed_intent": {
    "level": "high",
    "curriculum": "naesin",
    "region": "미사",
    "subjects": ["수학"]
  },
  "relaxed": [],
  "items": [
    {
      "academy": { "id": 1, "name": "가온수학(예시)", "...": "..." },
      "reason": "추천 이유 (AI 생성)",
      "score": 6.0,
      "matched_conditions": ["subject", "level_high", "curriculum_naesin", "region"],
      "unknown_conditions": [],
      "conflicts": [],
      "evidence_reviews": [
        { "content": "고1 내신 대비가 좋았습니다", "source": "맘카페", "rating": 5 }
      ]
    }
  ]
}
```

**`score`**: 무한대 상대 랭킹 점수(대략 0–12). 절대값에 의미가 없으므로 별점·신뢰도(%)처럼
렌더링하면 안 된다. 같은 응답 안에서의 순서 비교에만 쓴다.

**투명성 필드** (`matched_conditions` / `unknown_conditions` / `conflicts`):

| 키 | 출처 |
|---|---|
| `subject` | 질문 과목 휴리스틱(이름·`subjects` 매치). 검증된 컬럼이 아니라 추정 신호 |
| `level_elementary` / `level_middle` / `level_high` | 학교급 3상태 |
| `class_small_group` / `class_group` / `class_one_on_one` | 수업형태 3상태 |
| `curriculum_seonhaeng` / `curriculum_naesin` / `curriculum_suneung` | 커리큘럼 3상태 |
| `shuttle_available` | 셔틀 3상태 |
| `budget_max` | 월수강료 vs 예산 |
| `region` | 주소 부분일치 |

- `matched` = 확인된 일치(+점수), `unknown` = 미확인(NULL, 벌점 없음),
  `conflicts` = 확인된 불일치.
- `conflicts`는 감점과 동의어가 아니다. `region` 불일치는 점수 0.0이지만 리스트에는
  남긴다(완화된 뒤에도 사용자가 이유를 본다).

**`relaxed`**: 후보가 비어 조건 완화가 일어났을 때 풀린 필터 이름 목록.
사다리는 `q` → `region` 순. 직격 히트면 `[]`.

`parsed_intent`는 질문 해석 결과(적용된 필터)를 투명하게 노출한다. 과목이 추출되면
`subjects` 키를 추가한다. `items`의 학원은 `AcademySummary` 요약 필드를 사용한다.

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
