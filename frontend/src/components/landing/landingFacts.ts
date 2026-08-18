/** WaitlistModal 세 항목의 압축. 모달 문구를 바꾸면 여기도 같이 고친다. */
export const CTA_REASSURANCE = "무료 · 이름·연락처 입력 없음 · 언제든 차단 가능";

export const WAITLIST_CTA_LABEL = "카카오톡으로 무료 출시 알림 받기";

/** 홈(`/`) 주 CTA. `/check` 인트로 문구(`CHECK_CTA_LABEL`)와 의도적으로 다르다. */
export const HOME_CHECK_CTA_LABEL = "1분 학원 점검 시작하기";
export const HOME_CHECK_REASSURANCE = "1분 · 이름·연락처 입력 없음 · 결과 바로 확인";
export const STICKY_CHECK_REASSURANCE =
  "3문항 · 개인정보 입력 없음 · 결과 바로 확인";

/** `/check` 인트로 전용. 홈 주 CTA에는 `HOME_CHECK_CTA_LABEL`을 쓴다.
 *  제목은 두 줄로 나눈다 — 한 문장을 뷰포트에 맡겨 애매하게 접히지 않게. */
export const CHECK_CTA_LABEL = "1분 학원 점검";
export const CHECK_INTRO_HEADLINE = "지금 다니는 아이의 학원,";
export const CHECK_INTRO_HEADLINE_LINE2 = "1분만 점검해 보세요";
export const CHECK_INTRO_BADGE = "1분 · 3문항 · 하남 미사";
export const CHECK_INTRO_SUPPORT =
  "학원을 좋거나 나쁘다고 나누지 않습니다.";
export const CHECK_INTRO_SUPPORT_NEXT =
  "지금 확인할 점만 짧게 짚어 드려요.";
export const CHECK_CTA_HINT = "로그인 · 개인정보 입력 없음 · 약 1분";

export const CHECK_RESULT_KAKAO_LABEL =
  "카카오톡 친구 추가하고 점검리스트 받기";
export const CHECK_RESULT_HOME_LABEL = "학원콕 더 알아보기";

export const KAKAO_WELCOME_HINT = "채널 추가 후 웰컴메시지로 보내드려요";

/** 홈 중간 3칸. 출시 기능 목록이 아니라 학부모 시점이다.
 *  등록 전 맞춤 추천은 아직 없고, 다니는 중·옮기기 전 점검은 이미 `/check`·`/checklists`에 있다.
 *  화면 문구는 학부모 말(등록 전/다니는 중/옮기기 전)을 쓰고, 내부 용어 재원·퇴원은 쓰지 않는다. */
export const LIFECYCLE_SECTION_HEADING = "학원을 고를 때, 다닐 때, 옮길 때";
export const LIFECYCLE_STAGES = [
  {
    title: "등록 전",
    body: "학년·과목·성향에 맞는 곳을 근거와 함께 추릴 준비를 하고 있어요.",
  },
  {
    title: "다니는 중",
    body: "점검 시점과 상담 때 물어볼 질문을 지금 챙겨 드립니다.",
  },
  {
    title: "옮기기 전",
    body: "옮기기 전에 확인할 점만 정리해, 결정에 도움이 되게 합니다.",
  },
] as const;

/** 푸터·메타 설명. 점검·체크리스트는 현재형, 맞춤 추천만 출시 후. */
export const FOOTER_STATUS_COPY =
  "학원콕은 아직 정식 출시 전입니다. 지금은 1분 학원 점검, 체크리스트 웹 자료, 무료 출시 알림 신청을 이용하실 수 있습니다. 등록 전 맞춤 추천은 정식 출시 후 제공될 예정입니다.";

/** data/academies/*.json 중 주소에 "미사"가 포함된 건수.

/** data/academies/*.json 중 주소에 "미사"가 포함된 건수.
 *  tests/test_landing_copy.py 가 JSON 정본과 일치하는지 검사한다. */
export const MISA_ACADEMY_COUNT = 410;
