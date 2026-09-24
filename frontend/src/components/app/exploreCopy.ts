/** `/app` 탐색 화면 카피. 2026-09-13 첫 MVP 제품 정의 — 하남 미사에서 학원을 알아볼 때,
 *  내 상황을 입력하면 확인해 볼 후보와 상담 질문을 한 번에 정리해 주는 도구.
 *
 * 표현 원칙 (2026-09-08 · 2026-09-13, docs/decision-log.md):
 * - 학원의 품질을 단정하지 않는다. 확정 추천·순위·별점·적합성 확정 표현을 쓰지 않는다.
 * - 검색창은 DB가 실제로 찾는 것(학원명·주소·전화)만 약속한다. 과목 예시를 넣지 않는다.
 * - 카드는 이름 → 과목 배지 → 왜 이 후보인지 → 확인일 → 다음 행동. score 비표시.
 * - 태그(소수정예·선행 등)는 검색 조건이 아니라 상담 질문 힌트다. AI 쿼리에 넣지 않는다.
 * - 한 흐름: 상황 입력 → 후보 → 상담 질문 → 후보 위치. 검색·지도는 결과 뒤의 보조다.
 */

export const APP_TITLE = "학원콕";
export const APP_BADGE = "하남 미사";
export const APP_HEADER_NOTE = "확인해 볼 후보 · 상담 질문";
export const APP_NO_BROKERAGE =
  "학원을 중개하거나 예약·결제를 대행하지 않습니다. 전화·웹사이트·길찾기는 직접 진행해 주세요.";

// 랜딩(`/`)과 `/app`이 같은 문장을 쓴다. 랜딩은 여기서 import한다 — 두 모듈에 복제하지 않는다.
export const FORM_HEADING = "하남 미사에서 학원을 알아보고 있나요?";
export const FORM_SUPPORT =
  "아이의 학년·과목·고민을 입력하면, 확인해 볼 후보와 상담 질문을 정리해 드려요.";
export const TRUST_NOTE =
  "학원의 품질을 단정하지 않아요. 공개 정보와 확인일을 보여드리고, 상담에서 물어볼 점을 함께 정리합니다.";

export const SUBJECT_FORM_HELPER =
  "선택한 과목은 상담 질문과 후보 정리에 쓰여요.";
export const SUBJECT_HELPER = "과목 정보가 확인된 학원만 배지로 표시돼요.";
// 국어·영어·수학은 버킷으로 확정 분류하고, 그 외 과목은 "기타"를 고른 뒤 실제
// 이름을 적게 한다 — "기타"만으로는 후보를 좁힐 신호가 없기 때문이다.
export const SUBJECT_DETAIL_LABEL = "어떤 과목인가요?";
export const SUBJECT_DETAIL_HELPER =
  "국어·영어·수학이 아니면 실제 과목을 적어 주세요. 후보 정리에 쓰여요.";
export const SUBJECT_DETAIL_PLACEHOLDER = "피아노, 미술, 코딩 등";
export const TAGS_HEADING = "상담에서 확인하고 싶은 것";
export const TAGS_HELPER =
  "선택하면 상담 질문에 반영돼요. 후보를 거르는 조건은 아니에요.";
export const MORE_DETAILS_LABEL = "더 알려주기";
export const MORE_DETAILS_HIDE_LABEL = "추가 정보 접기";
export const EDIT_CONDITIONS_LABEL = "조건 바꾸기";
// 펼친 폼을 접고 결과로 돌아가는 버튼. 결과 순서(후보 → 질문)와 같은 순서로 부른다.
export const SHOW_RESULTS_LABEL = "후보·질문 보기";
export const SUBMIT_LABEL = "후보와 질문 정리하기";
export const LOADING_LABEL = "후보와 질문을 정리하는 중…";
export const QUESTIONS_HEADING = "상담에서 확인할 질문";
export const CANDIDATES_HEADING = "지금 조건으로 확인해 볼 후보예요";
export const WHY_CANDIDATE_HEADING = "왜 이 후보를 보여드렸나요?";
export const MATCHED_CONDITIONS_LABEL = "등록 정보와 맞는 조건";
// 학원 이름에만 과목이 보이는 경우(백엔드 `subject_name`)는 등록 정보가 아니라 런타임 탐색
// 신호다. "등록 정보와 맞는 조건"과 같은 줄에 섞지 않고 따로 적는다 — Phase 5c 1개월차의
// 점검 항목(공개 사실 / 탐색 신호 / 미확인의 구분, docs/decisions/2026-09-19-round1-engineering-scope.md).
export const NAME_SIGNAL_LABEL = "학원 이름에서 추정한 신호";
export const NAME_SIGNAL_HELPER =
  "등록 정보로 확인된 것은 아니에요. 상담에서 확인해 주세요.";
export const ASK_AT_CONSULTATION_HEADING = "상담에서 확인할 점";
export const CONFLICTS_HEADING = "조건과 다른 점";
export const REVIEW_EVIDENCE_HEADING = "공개 리뷰 (주관적 경험)";
export const VERIFIED_AT_LABEL = "정보 확인일";
export const UNCONFIRMED_VALUE = "미확인";
export const UNVERIFIED_FIELDS_LABEL = "아직 확인하지 못한 항목";
// 카드 첫 화면은 이름·배지·이유·확인일·다음 행동만. 확인된 조건·다른 점·리뷰 스니펫은
// 이 토글 뒤에 둔다 — 투명성 필드는 계속 보여 주되 첫 시선을 차지하지 않게.
export const EVIDENCE_TOGGLE_LABEL = "근거 더 보기";
export const EVIDENCE_TOGGLE_HIDE_LABEL = "근거 접기";

// 상태 문구 — 어떤 상태에서도 다음 행동이 바로 보이게 짧게. 개발자 대상 문장은 넣지 않는다.
export const RETRY_LABEL = "다시 보내기";
export const QUESTIONS_ERROR =
  "상담 질문을 정리하지 못했어요. 후보는 아래에 그대로 있어요. 다시 보내면 질문을 다시 정리해요.";
export const CANDIDATES_ERROR =
  "후보를 불러오지 못했어요. 잠시 후 다시 보내 주세요.";
export const NO_CANDIDATES =
  "지금 조건에 맞는 후보를 찾지 못했어요. 과목이나 고민 문장을 조금 바꿔 다시 보내 보세요.";
export const NO_CANDIDATES_SEARCH_HINT =
  "이미 알고 있는 학원이 있다면 아래에서 이름으로 찾을 수 있어요.";

// 완화 배너 — 백엔드 relaxed 는 필터 키(`q`·`region`)라 그대로 찍으면 영문 키가
// 그대로 보인다. region 은 폼에 지역 행이 없는데도 쿼리에 늘 들어가는 고정값
// (하남 미사)이라, 키만 보면 사용자가 설정한 적도 볼 수도 없는 조건이 튀어나온다.
// CONDITION_LABELS 처럼 '이름'으로 바꾸는 걸론 부족하다 — region → "지역"이 돼도
// 여전히 내가 건 적 없는 조건이다. 키마다 무엇이 왜 넓어졌는지 문장으로 적는다.
export const RELAXED_HEADING = "조건을 조금 넓혀 찾은 후보예요.";
export const RELAXED_NOTES: Record<string, string> = {
  q: "적어 주신 내용과 딱 맞는 곳이 적어, 찾는 범위를 조금 넓혔어요.",
  region:
    "하남 미사 안에 조건에 맞는 곳이 적어, 인근 지역 후보도 함께 담았어요.",
};

/** 아는 키의 문장만 남긴다. conditionLabel 과 같이 키로 폴백하지 않는다 —
 *  백엔드가 완화 사다리에 키를 늘려도 raw 키가 화면에 새면 안 된다.
 *  순서는 백엔드가 담아 준 순서를 그대로 따른다(사다리 순서는 백엔드 소유). */
export function relaxedNotes(keys: readonly string[]): string[] {
  return keys
    .map((key) => RELAXED_NOTES[key])
    .filter((note): note is string => Boolean(note));
}

// 라이브 폼이 제출 스냅샷과 달라졌을 때의 안내 — 요약 칩과 펼친 폼 두 곳에서 같이 쓴다.
export const CONDITIONS_CHANGED_NOTE = "조건이 바뀌었어요. 아래 후보·질문은 이전 조건으로 정리한 내용이에요.";
export const RESUBMIT_LABEL = "바뀐 조건으로 다시 보내기";

// 지도 헤딩 — 지금 지도가 무엇을 보여 주는지 모드별로 읽힌다. 제출 전·검색 전에는
// 지도를 그리지 않으므로 대기 모드 헤딩은 없다(입력이 주인공).
export const MAP_HEADING_CANDIDATES = "후보 위치";
export const MAP_HEADING_SEARCH = "검색 결과";
export const MAP_EMPTY_LIST = "표시할 학원이 없습니다.";
export const MAP_EMPTY_CANDIDATES = "아직 표시할 후보 위치가 없어요.";
// 지도 키가 없거나 스크립트가 실패해도 목록·길찾기는 그대로 쓸 수 있다. 환경변수
// 안내(NEXT_PUBLIC_NAVER_MAP_CLIENT_ID)는 frontend/README.md에만 둔다.
export const MAP_UNAVAILABLE =
  "지도를 표시할 수 없어요. 후보 카드의 길찾기는 그대로 쓸 수 있어요.";
export const MAP_LOADING = "지도 준비 중…";

// 검색 모드 — 기본 흐름(상황 입력 → 후보)의 보조. 기존 GET /academies?q=
// (학원명·주소·전화 부분 일치)를 그대로 쓴다. 과목·조건은 여기서 찾지 않는다.
export const SEARCH_MODE_LABEL = "이미 알고 있는 학원 찾기";
export const SEARCH_MODE_HIDE_LABEL = "학원 찾기 닫기";
export const SEARCH_PLACEHOLDER = "학원명·주소·전화 (예: 미사강변, 031-796)";
export const SEARCH_LABEL = "검색";
export const SEARCH_HELPER =
  "아는 학원을 이름·주소·전화로 찾아요. 과목·조건은 상황 입력에서 정리해요.";
export const SEARCH_CLEAR_LABEL = "검색 지우기";
export const SEARCH_OVERRIDES_CANDIDATES =
  "검색 중에는 후보 대신 검색 결과가 지도에 표시돼요.";
export const BACK_TO_CANDIDATES_LABEL = "후보로 돌아가기";
export const SEARCH_ERROR =
  "검색하지 못했어요. 잠시 후 다시 시도해 주세요.";

export function searchResultCount(total: number): string {
  return `검색 결과 ${total}개 학원`;
}

export function searchNoResults(q: string): string {
  return `학원명·주소·전화에 '${q}'이(가) 포함된 학원이 없어요.`;
}

export const ASK_AT_CONSULTATION_ITEMS = [
  "반의 실제 인원과 질문 대응은 어떻게 되나요?",
  "오답은 누가, 어떻게 다루나요?",
  "클리닉·보강은 어떤 조건인가요?",
] as const;

export const CONDITION_LABELS: Record<string, string> = {
  subject: "과목",
  level_elementary: "초등",
  level_middle: "중등",
  level_high: "고등",
  class_small_group: "소수정예",
  class_group: "그룹수업",
  class_one_on_one: "1:1",
  curriculum_seonhaeng: "선행",
  curriculum_naesin: "내신",
  curriculum_suneung: "수능",
  shuttle_available: "셔틀",
  budget_max: "수강료",
  region: "지역",
};

export function conditionLabel(key: string): string {
  // 모르는 백엔드 키는 raw 로 새지 않게 숨긴다 (relaxedNotes 와 같은 원칙).
  // 호출부는 빈 문자열을 걸러 쓰는 것이 이상적이지만, 폴백만으로도 키 유출은 막는다.
  return CONDITION_LABELS[key] ?? "";
}

/** 런타임 탐색 신호 키의 학부모용 이름. CONDITION_LABELS 와 키가 겹치면 안 된다 —
 *  같은 키가 두 줄에 다 찍히면 사실과 신호의 구분이 무너진다 (테스트가 지킨다).
 *  `matched_conditions` 배열 하나를 두 사전으로 갈라 읽는다. */
export const SIGNAL_LABELS: Record<string, string> = {
  subject_name: "과목",
};

export function signalLabel(key: string): string {
  return SIGNAL_LABELS[key] ?? "";
}

/** 배지 표시용 과목 목록. 버킷 "기타"는 세부 라벨(subject_detail)이 있으면
 *  그 이름으로 바꿔 보여 준다 — "기타" 배지 대신 "피아노"·"미술"이 보이게. */
export function subjectBadges(
  subjects: string[] | null,
  subjectDetail: string | null,
): string[] {
  if (!subjects) return [];
  return subjects.map((s) =>
    s === "기타" && subjectDetail ? subjectDetail : s,
  );
}

export const INTENTS = [
  { id: "find_new_academy" as const, label: "새 학원을 알아보는 중" },
  { id: "counsel_only" as const, label: "지금 다니는 학원 상담" },
] as const;
