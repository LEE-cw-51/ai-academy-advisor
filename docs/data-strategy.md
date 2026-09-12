# 데이터 전략

## 목표

**"대한민국에서 가장 정확한 미사 교육 DB"**

서비스(UI)가 아니라 데이터 자산을 만든다. UI는 얼마든지 바꿀 수 있지만
수백 개 학원의 구조화된 사실 데이터는 쉽게 복제되지 않는다. 미사처럼 한 지역을
깊게 파는 전략에서는 시간이 지날수록 DB의 완성도가 곧 경쟁력이 된다.

## 3단계 로드맵

### Phase 1 — 사실(Fact) DB ← 지금
객관적 사실만 수집한다. 평가·리뷰를 처음부터 넣으면 객관성 문제, 학원의 항의,
수집·업데이트 난이도 문제가 생긴다. 사실만 모으는 것은 명확하고 확장하기 쉽다.

핵심 UX: 체크박스 필터 → **"검색 결과 N개 학원"**.
"고등 과정 있는 미사 수학학원"을 맘카페 글 수십 개 대신 필터 한 번으로 찾는다.
사실 DB만으로도 이 검색 경험이 성립한다.

### Phase 2 — AI 요약 (추후)
홈페이지/블로그 등 공개된 내용을 읽어 "고등 비중이 높음", "내신 대비를 강조함" 같은
구조화된 요약을 만든다. 의견이 아니라 **공개된 정보의 구조화**다.
요약 필드는 사실 테이블과 분리해 별도 테이블로 둔다 — 사실과 추론을 섞지 않는다.

### Phase 3 — 리뷰·사용자 경험 데이터 (추후)
공개 웹에서 탐색한 리뷰와 실제 학부모 경험은 **주관적 정보**다. 학원 사실을
덮어쓰거나 사실 필드로 변환하지 않으며, 출처·작성/수집 시점·적용 한계가 보이는
경험 근거로 다룬다. 후기, 별점, 추천, 실제 학부모 경험의 쓰기는 DB 직접 쓰기이며
git 정본을 거치지 않는다 (사실 데이터와 저장 경로가 다르다).

공개 화면에는 원문을 그대로 재게시하는 대신, 필요한 범위의 AI 요약과 근거
메타데이터를 노출한다. 단일 리뷰·별점·감성 점수만으로 학원 품질이나 교육비 대비
가치를 단정하지 않는다.

### 운영·관리 신호 — Phase 1~3을 가로지르는 후속 실험

반의 실제 인원, 수업 중 질문 가능 시간, 동시 질문 대응 인력, 오답·클리닉 제공처럼
학습 관리 경험에 영향을 주는 운영 조건은 학원 전체의 고정 사실로 취급하지 않는다.
이 값은 **과목·학년군·수업반·시간대·관측일**에 따라 달라질 수 있고, 단일 값만으로
학원의 교육 품질을 판정할 수 없다.

따라서 `질문 대응 여유` 같은 신호는 사실 DB의 필드나 학원 별점으로 저장하지 않는다.
공개 출처에서 확인한 값은 출처·확인일을 가진 별도 운영 프로필에, 학부모가 등록 후
확인한 경험은 개인 점검 또는 사용자 데이터에 분리한다. 충분한 입력값이 없으면
`미확인`으로 표현하고 상담 질문만 제공한다. 상세 적용은
[대기행렬 기반 질문 대응 여유 신호 제안](queueing-management-signal-proposal.md)을
따른다.

## 3상태(tri-state) 원칙

Boolean 필드는 3가지 상태를 갖는다.

| 값 | 의미 |
|---|---|
| `true` | 확인됨 — 있음 |
| `false` | 확인됨 — 없음 |
| `null` | **미확인** |

"고등 과정이 없다"와 "아직 확인 안 했다"의 구분이 이 DB의 정확성을 만든다.
필터는 `IS TRUE`/`IS FALSE`로 동작하며 미확인(`null`)은 결과에 포함되지 않는다.
확인하지 않은 사실을 추측으로 채우지 않는다.

## 필드 사전

JSON 키(정본 파일)와 DB 컬럼은 1:1로 같다.

| 키 | 타입 | 라벨 | 수집 기준 |
|---|---|---|---|
| `registration_number` | string \| null | 학원 등록번호 | 공식 등록정보(나이스 학원민원서비스). **자연키 #1** |
| `name` | string (필수) | 학원명 | 공식 명칭 |
| `address` | string \| null | 주소 | 도로명 주소. `(name, address)`가 자연키 #2 |
| `phone` | string \| null | 전화번호 | 공개된 대표번호 |
| `website_url` / `blog_url` / `instagram_url` | string \| null | 홈페이지/블로그/인스타그램 | **공식 채널만.** 네이버 플레이스·지도 단축 URL, 맘카페 글 URL은 넣지 않는다. `blog_url`은 학원 공식 블로그 홈. |
| `subjects` | string[] \| null | 과목 | **허용 값만:** `국어` · `영어` · `수학` · `기타` (4종, 2026-09-11). 복수 가능(`["영어","수학"]`). 국·영·수는 확정 분류하고 그 외는 `기타`. 표시·소프트 랭킹용(하드 필터 미지원). 검색 근거 없이 학원명만으로 기입하지 않는다. |
| `subject_detail` | string \| null | 과목 세부 | `기타` 버킷의 실제 이름(예: `피아노`·`미술`·`과학`·`무용`). `subjects`에 `기타`가 있을 때만 채운다(결합 CHECK). 어휘는 강제하지 않는다. 검색 근거(지역검색 category) 없이 기입하지 않는다. |
| `level_elementary` / `level_middle` / `level_high` | bool \| null | 초/중/고 | 개설 과정을 확인한 뒤에만 기입 |
| `class_small_group` / `class_group` / `class_one_on_one` | bool \| null | 소수정예/그룹/1:1 | 학원이 공개한 수업 형태 |
| `curriculum_seonhaeng` / `curriculum_naesin` / `curriculum_suneung` | bool \| null | 선행/내신/수능 | 학원이 **스스로 공개한** 커리큘럼만. 리뷰·특징 라벨(`mentions_*`)로 자동 기입하지 않는다. |
| `shuttle_available` | bool \| null | 차량운행 | |
| `operating_hours` | string \| null | 운영시간 | 자유 서술 |
| `established_year` | int \| null | 개원년도 | |
| `teacher_count` | int \| null | 강사수 | 학원 전체의 공개 강사 수. 특정 반의 질문 대응 인력 또는 학생당 강사 수로 추론하지 않는다. |
| `classroom_count` | int \| null | 강의실수 | 학원 전체의 공개 강의실 수. 반별 수업 환경이나 정원으로 추론하지 않는다. |
| `tagline` | string \| null | 한 줄 소개 | 홈페이지 요약. 의견이 아닌 사실 요약으로 유지 |
| `latitude` / `longitude` | float \| null | 좌표 | 추후 지도 기능용 |
| `source_note` | string \| null | 출처 메모 | 어디서 확인한 사실인지 |
| `last_verified_at` | date \| null | 최종 확인일 | 목록 API에 노출되는 신뢰 신호 |

## 수집 원칙

1. **공개된 사실만** 수집한다 (홈페이지, 블로그, 공식 등록정보, 전화 확인).
2. **추측 금지** — 확인하지 못한 값은 `null`로 남긴다.
3. 출처(`source_note`)와 확인일(`last_verified_at`)을 기록한다.
4. 평가·의견은 쓰지 않는다. 한 줄 소개(`tagline`)도 사실 요약으로 유지한다.
5. 실존 학원에 대해서는 검증된 사실만 기입한다. 개발용 가짜 데이터는 "(예시)"를 표기한다.

## 운영: Supabase Postgres + Studio

- **운영 정본(source of truth)** 은 Supabase Postgres `academies` 테이블이다. Founder는
  **Table Editor**로 전화·URL·과목·운영시간 등을 수정한다. 배포 없이 공개 API에 반영된다.
- **git JSON** (`data/academies/*.json`)은 시드·재해복구 백업용이다. 공공데이터 변환·
  enrich CSV 반영 파이프라인은 여전히 JSON 파일을 거칠 수 있으나, 운영 반영은 Studio 또는
  컷오버용 `--force` import로 DB에 올린다.
- **DB 가드** (Alembic `0006`): 과목 taxonomy, 비홈페이지 URL(호스트 목록은
  `is_homepage_url`과 공유, 스킴·이름 일치는 CHECK에 없음), 신원 필드 불변(등록번호
  NULL 백필은 허용), `last_verified_at` 스탬프, `academy_fact_revisions` 이력.
  스키마 변경은 Alembic만.
- **임포트**: `uv run python -m app.cli.import_academies ../data/academies`는 로컬 Docker
  Postgres·SQLite에서만 기본 허용. Supabase/Railway URL은 `--force` 또는
  `ALLOW_ACADEMY_IMPORT=1` 없이 거부한다(Studio 수정 덮어쓰기 방지).
- **백업**: `uv run python -m app.cli.export_academies ../data/backups/YYYY-MM-DD`로
  DB→JSON 덤프(정본 아님).
- **공개 쓰기 API 없음**. (Phase 3 사용자 리뷰는 예외 — 그건 DB 직접 쓰기)

## 공공데이터 부트스트랩 (2-소스)

`backend/app/cli/convert_registry.py --source {neis,gg}`로 공공데이터를 뼈대
파일로 변환한다. 두 소스는 상호보완적이며, `--enrich`로 순차 실행해 서로
보강할 수 있다 (나이스 먼저 → 경기데이터드림 enrich). 절차와 API 키 발급은
`data/README.md` 참고.

### neis — 나이스 학원민원서비스(`acaInsTiInfo`)

| NEIS 필드 | 정본 키 |
|---|---|
| `ACA_ASNUM` | `registration_number` |
| `ACA_NM` | `name` |
| `FA_RDNMA` + `FA_RDNDA` | `address` |
| `ESTBL_YMD` (앞 4자리) | `established_year` |

강점: 등록번호(자연키)·개원년도·폐원상태. 분야/교습과정(`REALM_SC_NM`,
`LE_CRSE_NM`)은 과목과의 매핑이 부정확해 자동 변환하지 않는다.

### gg — 경기데이터드림 "경기도_학원 및 교습소 현황" (`openapi.gg.go.kr/TninsttInstutM`)

강점: 나이스에 없는 **전화번호·좌표(위경도)·교습과정명**(과목 힌트로 활용,
`--course-keyword`로 필터링 가능).

**필드명 확정 (2026-07-08, 실제 API 응답으로 검증됨).** 이전에는 포털 상세
페이지가 봇 차단으로 확인 불가해 여러 후보 키를 시도하는 best-effort 매핑이었으나,
실제 서비스키로 호출한 응답을 확보해 아래 표로 확정했다. 등록번호 필드는
이 데이터셋에 없어 자연키는 이름+주소만 사용한다. 등록/영업 상태 필드도 없어
gg 소스 행은 상태 기준으로 걸러지지 않는다 (기본 포함).

**응답은 XML 고정이다** — `Type=json` 파라미터를 줘도 XML로 응답한다.
`convert_registry.py`가 `.xml` 확장자 또는 `<`로 시작하는 입력을 자동으로 XML로
파싱해 처리한다 (`parse_xml_payload()`).

| 개념 | 실제 API 필드 | 정본 키 | 비고 |
|---|---|---|---|
| 시설명 | `FACLT_NM` | `name` | |
| 전화번호 | `TELNO` | `phone` | neis에는 없는 필드 |
| 도로명주소 | `REFINE_ROADNM_ADDR` | `address` | 우선 사용 |
| 지번주소 | `REFINE_LOTNO_ADDR` | `address` | 도로명주소 없을 때 대체 |
| 위도 | `REFINE_WGS84_LAT` | `latitude` | neis에는 없는 필드 |
| 경도 | `REFINE_WGS84_LOGT` | `longitude` | neis에는 없는 필드 |
| 교습과정명 | `CRSE_CLASS_NM` | (필터 전용) | `subjects`에 자동 반영하지 않음 — 과목 매핑 오류 방지, `--course-keyword`로만 사용 |

검색으로 `subjects`/`website_url`/`blog_url` **제안**을 만들 때는
`uv run python -m app.cli.enrich_academy_from_search`가 CSV만 쓴다. JSON 시드는
`uv run python -m app.cli.apply_enrich_csv … --apply`로 **high** 신뢰 제안만 null
필드에 반영한 뒤, 운영 DB에는 Studio 또는 `--force` import로 올린다(2026-09-01 A3:
411건 중 high 190건 반영 → subjects 35.8%,
website_url 16.5%, blog_url 23.6%; phone·주소·좌표는 건드리지 않음). 플레이스
크롤링은 하지 않는다.

### 채움 우선순위 (2026-09-08)

기준은 "필터를 만들고 싶다"가 아니라 **지금 `/app` 카드·검색·전화 CTA가 비지 않게**다.
운영 정본은 Supabase Studio, git JSON은 시드·백업, 공개 쓰기 API 없음 — 새 파이프라인을
만들지 않고 아래 기존 CLI·Studio 루프만 쓴다. 반영마다 `source_note`·`last_verified_at`을
남긴다.

| 우선 | 필드 | 이유 | 방법 |
|---|---|---|---|
| P0 | `phone` (남은 ~32%) | 검색 키이자 핵심 CTA | gg 공공데이터 재확인 `convert_registry <gg.xml> ../data/academies --source gg --filter 미사 --enrich`(null만 채움) → 남는 건 Studio. enrich CSV의 `proposed_phone`은 정본에 자동 반영하지 않음(2026-09-01 A3) |
| P0 | `subjects`+`subject_detail` | 카드·지도 목록 배지, 소프트 랭킹. 기타 버킷은 세부 라벨로 구분(피아노·미술·과학…) | `enrich_academy_from_search` → CSV(`proposed_subject_detail` 포함) → Founder가 **high** 행 검토 → `apply_enrich_csv --apply --today 2026-09-11`(null만; 컬럼 없으면 evidence의 `category=`에서 파생) 또는 Studio → `export_academies` 백업. 지역검색 `category`만 근거. 이름에 "수학"이 있어도 채우지 않음 |
| P1 | `website_url` / `blog_url` | 상세 CTA | enrich high + `is_homepage_url`·이름 일치 가드 유지(2026-09-01 롤백 교훈) |
| P1 | `registration_number` | 자연키. gg만 쓰면 0% | neis 하남시 변환 후 `(name, address)` 매칭 `--enrich`. 강제 덮어쓰기 없음 |
| P2 | `level_*` / `class_*` / `curriculum_*` | 하드 필터·태그 매칭 | 학원 공개 URL·공식 문구가 있을 때만 Founder가 Studio에서 null만 채움. 리뷰에 "내신"이 있다고 true로 쓰지 않음. 채워지기 전에는 UI에 필터를 열지 않음 |
| 하지 않음 | 수강료·셔틀·강사 수·수업 품질 | 0%이거나 학원 전체 값으로 품질 추론 금지 | 상담 질문으로만 |

## 리뷰·engagement 테이블 (DB 직접 쓰기)

`reviews`(임베딩 포함) / `academy_trait_labels` / `search_history` / `click_logs` /
`feedback` / `waitlist`는
학원 사실(Fact) 테이블과 **저장 경로가 다르다** — git 정본을 거치지 않는 DB 직접 쓰기다.
`reviews`는 위 3단계 로드맵의 Phase 2(AI 요약)·Phase 3(리뷰·사용자 경험)에 해당한다.
리뷰 탐색 결과는 객관적 학원 사실과 분리하고, 출처·시점·한계를 갖춘 주관적 경험
근거로만 상담 보조와 후보 비교에 활용한다. engagement 로그는 KPI 측정을 위한
런타임 기록이다. 사실 DB의 data-as-git 원칙과 분리해 운영한다.

### 리뷰 수집 런북 (공개 검색만)

로그인 없이 네이버가 색인한 글만 모은다. 크롤이 아니라 NAVER API HUB Search다.
응답 `description`은 ~200자 스니펫이며 카페 전문은 수집하지 않는다.

| 소스 | 엔드포인트 | 이번 범위 |
|---|---|---|
| 공개 카페글 (맘카페 공개글 포함) | `cafearticle` | 한다. 검색에 안 뜨면 로그인 벽 뒤이므로 버린다. 학원당 0건이 많아도 정상 |
| 공개 블로그 | `blog` | 한다. 학원명이 제목/본문에 있는 스니펫만 |
| 지식iN·웹문서 | `kin` / `webkr` | HUB 노출을 `--dry-run`으로 확인한 뒤에만. 전체 수집과 동시에 켜지 않음 |
| 회원제 맘카페 본문 | 카페 로그인·세션 쿠키 | **하지 않음** (본인인증·거주확인·등업 담벼락, 약관·개인정보) |
| 네이버 플레이스·카카오맵 별점 | 브라우저 | **하지 않음** (robots상 RAG 금지 + 429) |
| 당근 게시글 | 스크랩 | **하지 않음** (공식 검색 API 없음) |

질의는 학원명 단독이다. `"미사 맘카페"`를 붙이면 네이버가 AND로 걸어 공개 후기까지
떨어진다. 학원명이 제목/본문에 없으면 오귀속 방지로 버린다. 원문은 git에 커밋하지
않는다 (`data/raw/`, gitignored).

**실행 (로컬 CLI만, 운영 정본에 DB 직접 쓰기):**

```bash
cd backend
# DATABASE_URL = Supabase session pooler 5432 (transaction 6543 금지)
# REVIEW_SOURCE=naver, NAVER_CLIENT_ID / NAVER_CLIENT_SECRET (API HUB)
uv run python -m app.cli.ingest_reviews --dry-run --limit 5
uv run python -m app.cli.ingest_reviews --limit 5   # 파일럿 합격 후에만 전체
```

리포트의 `naver_blog` / `naver_cafearticle` 건수는 API가 돌려준 수(삽입 전)다.
공개 카페 0건 학원이 많아도 실패가 아니다. 로그인해서 채우지 않는다.

운영 URL + `REVIEW_SOURCE=stub` 은 가짜 후기 적재를 막기 위해 거부한다. stub은
로컬·테스트 DB에서만 허용한다. `REVIEW_SOURCE`는 수집 CLI 전용이며 Vercel 런타임
추천 경로가 쓰지 않는다.

### 학원 특징 라벨 (닫힌 어휘 — `academy_trait_labels`)

리뷰·공개 문구에서 뽑는 언급은 **별도 테이블** `academy_trait_labels`에만 둔다.
사실 컬럼과 섞지 않는다. Phase 2 "요약은 별도 테이블"과 같다.

**닫힌 집합** (자유 태그 금지):

- 커리큘럼 언급: `mentions_seonhaeng` / `mentions_naesin` / `mentions_suneung`
- 운영 경험 언급: `mentions_homework` / `mentions_clinic` / `mentions_qna` (질문 대응)
- 넣지 않음: 좋음/나쁨, 가성비, 별점, "최고", 반 정원·강사 수 추론
- `mentions_qna`: bare `질문`은 매칭하지 않는다. 질문대응·질문 가능·질문하기·
  질의응답·QnA 등 복합어만 (`app.services.trait_label_matcher`).

어휘 정본은 `app.core.trait_labels` 하나다. 모델 CHECK가 거기서 생성되고, 키워드
사전이 같은 집합인지는 테스트가 강제한다. 어휘를 바꾸면 새 마이그레이션이 필요하다.

**어절 경계 규칙 (bare 키워드 전체에 적용).** 한국어엔 어절 경계가 없어 부분 문자열
매칭은 반드시 오탐한다. 첫 실행이 그대로 걸렸다 — `보내신`·`안내신청`·`지내신`이
`mentions_naesin`으로, `보강공사`가 `mentions_clinic`, `수능시계`가 `mentions_suneung`
으로 잡혔다. 그래서 bare 키워드는 앞뒤 문맥이 맞을 때만 센다:

- 앞: 한글이 아니거나(문장 시작·공백·문장부호·영숫자) 허용 접두사(`중등`·`수학`…)
- 뒤: 한글이 아니거나 조사(`은`·`이랑`…) 또는 허용 복합어(`대비`·`관리`…)

bare 키워드 금지는 `질문` 한정 규칙이 아니라 **전 라벨 규칙**이다. 정밀도를 재현율
앞에 둔 선택이며(스니펫이 카드 근거로 노출되므로 오탐은 없는 것보다 나쁘다),
놓친 복합어는 매처의 `_SUFFIXES`에 추가한다.

각 행: `academy_id`, `label`, `source_type`(`review` | `homepage` | `blog`),
`source_url`, `snippet`, `observed_at`, `status`(`candidate` | `published`).
공개 전에는 `candidate`. 원문 재게시가 아니라 라벨+짧은 근거 메타만 노출한다.
Dedup `(academy_id, label, source_url)`. Data API는 `0009`에서 RLS+REVOKE로 잠근다.

**배치 CLI** (session pooler 5432):

```bash
cd backend
uv run alembic upgrade head   # 0009, 0010
uv run python -m app.cli.ingest_trait_labels [--dry-run] [--limit N]
```

매처 규칙이 바뀌면 dedup 만으로는 옛 행이 남는다. 그때만
`--purge-candidates`로 기존 candidate 를 지우고 다시 뽑는다 (`published`는 그대로).
`--dry-run`과 같이 주면 지울 건수만 센다. 규칙이 그대로면 재실행은 dedup 으로 충분하다.

**쓰는 곳 (배선은 Stage 3 이후):** 후보 카드·상세의 주관 신호(출처·시점 포함)와
`POST /consultation/questions` 보강.

**쓰지 않는 곳:**

- `academies.curriculum_*` / `level_*` / `class_*` 자동 기입 (리뷰에 "내신"이 있어도
  학원이 공개한 커리큘럼이 아니다)
- `services/scoring.py` 가산, 별점·품질·가성비 판정
- `POST /recommendations` · `/recommendations/ai` 점수 공식

소프트 랭킹 재검토는 라벨 커버리지가 생긴 뒤 별도 결정. 학원이 홈페이지/블로그에
선행·내신·수능을 **스스로 적은** 경우만 제안 CSV → Founder가 Studio에서 null 필드만
채운다 (`source_note`·`last_verified_at`). URL이 없는 학원은 사실 커리큘럼을
미확인(`null`)으로 둔다.

## 확장 경로 (비파괴적)

- 과목 필터가 필요해지면 `subjects` JSON 컬럼 → `academy_subjects` junction 테이블 마이그레이션.
- 필터 파라미터 다중값(`level=middle,high`), 정렬 옵션 추가.
- Phase 2 AI 요약은 별도 테이블로 추가 (기존 스키마 변경 없음).
- 질문 대응·오답 관리 같은 운영 신호도 사실 테이블과 분리한다. 향후 운영 프로필은
  `academy_id` 외에 `course_scope`, `observed_at`, `source_type`, `source_note`,
  `calculation_version`, `status`를 포함해 반 단위·관측일 단위로 해석 가능해야 한다.
