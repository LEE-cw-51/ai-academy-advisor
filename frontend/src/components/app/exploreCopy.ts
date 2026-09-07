/** `/app` 탐색 화면 카피. 2026-08-21 제품 언어 — 조건과 관련해 확인해 볼 후보 정보. */

export const APP_TITLE = "학원콕";
export const APP_BADGE = "하남 미사";
export const APP_HEADER_NOTE = "후보 정보 · 상담 질문";
export const APP_NO_BROKERAGE =
  "학원을 중개하거나 예약·결제를 대행하지 않습니다. 전화·웹사이트·길찾기는 직접 진행해 주세요.";

export const FORM_HEADING = "상황 입력";
export const FORM_SUPPORT =
  "학년·과목·걱정을 알려 주시면, 상담에서 확인할 질문과 후보 정보를 정리해 드려요.";
export const SUBMIT_LABEL = "질문과 후보 정보 보기";
export const EMPTY_RESULTS =
  "조건을 고른 뒤 전송하면 상담에서 확인할 질문과 후보 정보가 여기에 표시됩니다.";
export const LOADING_LABEL = "질문과 후보 정보를 정리하는 중…";
export const QUESTIONS_HEADING = "상담에서 확인할 질문";
export const CANDIDATES_HEADING = "조건과 관련해 확인해 볼 후보 정보";
export const CANDIDATE_BADGE = "후보 정보";
export const WHY_CANDIDATE_HEADING = "왜 이 후보를 보여드렸나요?";
export const UNCONFIRMED_HEADING = "미확인";
export const ASK_AT_CONSULTATION_HEADING = "상담에서 확인할 점";
export const CONFLICTS_HEADING = "조건과 다른 점";
export const REVIEW_EVIDENCE_HEADING = "공개 리뷰 (주관적 경험)";
export const VERIFIED_AT_LABEL = "정보 확인일";
export const UNCONFIRMED_VALUE = "미확인";
export const QUESTIONS_ERROR =
  "상담 질문을 불러오지 못했어요. API 서버가 실행 중인지 확인해 주세요.";
export const CANDIDATES_ERROR =
  "후보 정보를 불러오지 못했어요. API 서버가 실행 중인지 확인해 주세요.";
export const NO_CANDIDATES =
  "조건에 맞는 후보 정보를 찾지 못했어요. 조건을 조금 바꿔 다시 검색해 보세요.";
export const MAP_HEADING = "지도";

// 키워드 검색 — 기존 GET /academies?q=(학원명·주소 부분 일치)를 그대로 쓴다.
export const SEARCH_PLACEHOLDER = "학원명·주소로 검색 (예: 미사강변, 수학)";
export const SEARCH_LABEL = "검색";
export const SEARCH_CLEAR_LABEL = "전체 보기";
export const SEARCH_NO_RESULTS =
  "검색어와 일치하는 학원이 없어요. 다른 키워드로 검색해 보세요.";
export const SEARCH_ERROR =
  "검색하지 못했어요. 잠시 후 다시 시도해 주세요.";

export function searchResultCount(total: number): string {
  return `검색 결과 ${total}개 학원`;
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
