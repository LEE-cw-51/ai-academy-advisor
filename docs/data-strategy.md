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

### Phase 3 — 사용자 데이터 (추후)
후기, 별점, 추천, 실제 학부모 경험. 이 단계의 쓰기는 DB 직접 쓰기이며
git 정본을 거치지 않는다 (사실 데이터와 저장 경로가 다르다).

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
| `website_url` / `blog_url` / `instagram_url` | string \| null | 홈페이지/블로그/인스타그램 | 공식 채널만 |
| `subjects` | string[] \| null | 과목 | 예: `["수학"]`. 표시 전용(필터 미지원) |
| `level_elementary` / `level_middle` / `level_high` | bool \| null | 초/중/고 | 개설 과정을 확인한 뒤에만 기입 |
| `class_small_group` / `class_group` / `class_one_on_one` | bool \| null | 소수정예/그룹/1:1 | 학원이 공개한 수업 형태 |
| `curriculum_seonhaeng` / `curriculum_naesin` / `curriculum_suneung` | bool \| null | 선행/내신/수능 | 학원이 공개한 커리큘럼 |
| `shuttle_available` | bool \| null | 차량운행 | |
| `operating_hours` | string \| null | 운영시간 | 자유 서술 |
| `established_year` | int \| null | 개원년도 | |
| `teacher_count` | int \| null | 강사수 | |
| `classroom_count` | int \| null | 강의실수 | |
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

## 운영: data-as-git

- 정본(source of truth)은 `data/academies/*.json` (학원당 1파일). git이 이력·리뷰·출처 추적을 제공한다.
- DB는 파생 저장소: `uv run python -m app.cli.import_academies ../data/academies`로 재구성한다.
- 수정 흐름: 파일 수정 → PR 리뷰 → 머지 → 임포트.
- 쓰기 API는 만들지 않는다. (Phase 3 사용자 리뷰는 예외 — 그건 DB 직접 쓰기)

## 공공데이터 부트스트랩

나이스 학원민원서비스(`acaInsTiInfo`)의 하남시 학원 명단으로 뼈대 파일을 생성한다.

| NEIS 필드 | 정본 키 |
|---|---|
| `ACA_ASNUM` | `registration_number` |
| `ACA_NM` | `name` |
| `FA_RDNMA` + `FA_RDNDA` | `address` |
| `ESTBL_YMD` (앞 4자리) | `established_year` |

나머지 필드는 전부 `null`(미확인)로 생성되고 수동 큐레이션으로 채운다.
분야/교습과정(`REALM_SC_NM`, `LE_CRSE_NM`)은 과목과의 매핑이 부정확해 자동 변환하지 않는다.
사용법: `data/README.md`.

## 확장 경로 (비파괴적)

- 과목 필터가 필요해지면 `subjects` JSON 컬럼 → `academy_subjects` junction 테이블 마이그레이션.
- 필터 파라미터 다중값(`level=middle,high`), 정렬 옵션 추가.
- Phase 2 AI 요약은 별도 테이블로 추가 (기존 스키마 변경 없음).
