/** `/app` 탐색 화면 카피. 2026-08-21 제품 언어 — 조건과 관련해 확인해 볼 후보 정보.
 *
 * 표현 원칙 (2026-09-08, docs/decision-log.md):
 * - 검색창은 DB가 실제로 찾는 것(학원명·주소·전화)만 약속한다. 과목 예시를 넣지 않는다.
 * - 카드는 사실 먼저(이름 → 과목 배지 → 주소·전화 → 확인일), AI 이유는 그다음. score 비표시.
 * - 태그(소수정예·선행 등)는 검색 조건이 아니라 상담 질문 힌트다. AI 쿼리에 넣지 않는다.
 * - 한 흐름: 짧은 상황 입력 → 질문·후보 → 그 후보 지도. 첫 화면에서 전체 목록을 뿌리지 않는다.
 */

export const APP_TITLE = "학원콕";
export const APP_BADGE = "하남 미사";
export const APP_HEADER_NOTE = "후보 정보 · 상담 질문";
export const APP_NO_BROKERAGE =
  "학원을 중개하거나 예약·결제를 대행하지 않습니다. 전화·웹사이트·길찾기는 직접 진행해 주세요.";

export const FORM_HEADING = "상황 입력";
export const FORM_SUPPORT =
  "학년·과목·걱정을 알려 주시면, 상담에서 확인할 질문과 후보 정보를 정리해 드려요.";
export const SUBJECT_FORM_HELPER =
  "선택한 과목은 상담 질문과 후보 정리에 쓰여요.";
export const SUBJECT_HELPER = "과목 정보가 확인된 학원만 배지로 표시돼요.";
export const TAGS_HEADING = "상담에서 확인하고 싶은 것";
export const TAGS_HELPER =
  "선택하면 상담 질문에 반영돼요. 후보를 거르는 조건은 아니에요.";
export const MORE_DETAILS_LABEL = "더 알려주기";
export const MORE_DETAILS_HIDE_LABEL = "추가 정보 접기";
export const EDIT_CONDITIONS_LABEL = "조건 바꾸기";
export const SUBMIT_LABEL = "질문과 후보 정보 보기";
export const EMPTY_RESULTS =
  "조건을 고른 뒤 보내면 상담에서 확인할 질문과 후보 정보가 여기에 표시됩니다.";
export const LOADING_LABEL = "질문과 후보 정보를 정리하는 중…";
export const QUESTIONS_HEADING = "상담에서 확인할 질문";
export const CANDIDATES_HEADING = "조건과 관련해 확인해 볼 후보 정보";
export const CANDIDATE_BADGE = "후보 정보";
export const WHY_CANDIDATE_HEADING = "왜 이 후보를 보여드렸나요?";
export const MATCHED_CONDITIONS_LABEL = "확인된 조건";
export const ASK_AT_CONSULTATION_HEADING = "상담에서 확인할 점";
export const CONFLICTS_HEADING = "조건과 다른 점";
export const REVIEW_EVIDENCE_HEADING = "공개 리뷰 (주관적 경험)";
export const VERIFIED_AT_LABEL = "정보 확인일";
export const UNCONFIRMED_VALUE = "미확인";
export const UNVERIFIED_FIELDS_LABEL = "아직 확인하지 못한 항목";
export const QUESTIONS_ERROR =
  "상담 질문을 불러오지 못했어요. API 서버가 실행 중인지 확인해 주세요.";
export const CANDIDATES_ERROR =
  "후보 정보를 불러오지 못했어요. API 서버가 실행 중인지 확인해 주세요.";
export const NO_CANDIDATES =
  "조건에 맞는 후보 정보를 찾지 못했어요. 학년·과목·고민을 조금 바꿔 다시 정리해 보세요.";

// 지도 헤딩 — 지금 지도가 무엇을 보여 주는지 모드별로 읽힌다.
export const MAP_HEADING_IDLE = "후보 위치";
export const MAP_HEADING_CANDIDATES = "후보 위치";
export const MAP_HEADING_SEARCH = "검색 결과";
export const MAP_EMPTY_HINT =
  "조건을 보내면 후보 위치가 여기에 표시됩니다.";
export const MAP_EMPTY_LIST = "표시할 학원이 없습니다.";

// 키워드 검색 — 기존 GET /academies?q=(학원명·주소·전화 부분 일치)를 그대로 쓴다.
// 과목·조건은 여기서 찾지 않는다. 카피도 그 이상을 약속하지 않는다.
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
  return CONDITION_LABELS[key] ?? key;
}

export const INTENTS = [
  { id: "find_new_academy" as const, label: "새 학원을 알아보는 중" },
  { id: "counsel_only" as const, label: "지금 다니는 학원 상담" },
] as const;
