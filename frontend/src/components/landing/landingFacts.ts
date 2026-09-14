/** KakaoChannelModal 세 항목의 압축. 모달 문구를 바꾸면 여기도 같이 고친다. */
/** 목록 구분자 "·"와 "이름/연락처" 합성어를 같은 기호로 겹치지 않게 "/"로 구분한다
 *  (2026-08-19, 띄어쓰기 정리). 약속 범위(이름·연락처를 특정해 좁힌 2026-08-17 결정)는 그대로다. */
export const CTA_REASSURANCE = "무료 · 이름/연락처 입력 없음 · 언제든 차단 가능";

/** 카카오 채널이 주는 것. `체크리스트 3종`이라는 수량 프레이밍은 2026-08-19에 버렸다 —
 *  웰컴메시지가 실제로 주는 것이 "상담 때 물어볼 질문"이라서다.
 *  실제 웰컴메시지와 같은 말이어야 한다. 범위를 바꾸려면 채널 관리자센터를 먼저 고친다. */
export const KAKAO_REWARD_LABEL = "상담 질문 받아보기";
export const KAKAO_REWARD_NOTE =
  "채널을 추가하시면 상담 때 물어볼 질문을 정리해 보내드려요";
export const KAKAO_WELCOME_HINT = "채널 추가 후 웰컴메시지로 보내드려요";

/** 홈 히어로 (`/` 전용). 2026-09-13 첫 MVP 확정 — 메인은 더 이상 상황 분기 페이지가
 *  아니라 `상황 입력 → 후보·상담 질문` 도구(`/app`)로 보내는 페이지다. 헤드라인·설명·
 *  제출 버튼 문구는 `/app`의 exploreCopy(FORM_HEADING·FORM_SUPPORT·SUBMIT_LABEL)와 같다.
 *  신뢰 문구는 exploreCopy.TRUST_NOTE 를 import한다 — 두 모듈에 복제하지 않는다.
 *  제목은 좁은 폭에서 두 줄로 고정한다. */
export const HOME_HEADLINE = "하남 미사에서 학원을 알아보고 있나요?";
export const HOME_HEADLINE_MOBILE_LINES = [
  "하남 미사에서",
  "학원을 알아보고 있나요?",
] as const;
export const HOME_SUPPORT =
  "아이의 학년·과목·고민을 입력하면, 확인해 볼 후보와 상담 질문을 정리해 드려요.";
export const HOME_CTA_LABEL = "후보와 질문 정리하기";
/** 주 CTA 목적지. 2026-08-15의 `/app` 링크 제거(광고 심사용 대기자 페이지)를 2026-09-13
 *  결정이 대체했다 — `/app`이 후보·질문 정리 도구로 정리됐고 중개·예약·결제 없음은
 *  헤더·푸터가 계속 말한다. */
export const HOME_CTA_HREF = "/app";

/** 홈 히어로 배지와 즉시 효익 한 줄. `/check`·`/checklists`와 공유하던 HERO_* 제목·설명은
 *  2026-09-14 두 페이지 퇴역과 함께 걷어냈다 — 홈 제목·설명은 위 HOME_* 이 맡는다.
 *  적합성을 확정하는 표현은 쓰지 않는다. */
export const HERO_BADGE = "하남 미사 학부모를 위한 학원 선택 가이드";
export const HERO_REASSURANCE = "로그인 · 개인정보 입력 없음 · 지금 바로 확인";

/** 헤더 로고 옆. 배지가 아니라 문장이다 — 2026-08-16이 헤더에서 뺀 것은
 *  스크롤 내내 따라다니는 **배지**였고, 출시 전·판매 없음은 광고 심사에 필요해서
 *  텍스트로 되돌린다. 푸터 상세 고지와 겹쳐도 된다. "소개용 랜딩 페이지"라는
 *  표현은 `/app`을 주 CTA로 연결한 뒤 사실과 어긋나 2026-09-13에 뺐다. */
export const HEADER_STATUS_NOTICE =
  "학원콕은 아직 정식 출시 전입니다. 학원을 중개하거나 수강료를 받지 않습니다.";

/** 전 소개 페이지 하단 고정 바. 누르면 바로 카카오로 가지 않고 모달을 연다.
 *  모달 제목·KAKAO_REWARD_LABEL이 "상담 질문"으로 통일돼 있어 같은 프레이밍을 쓴다. */
export const FOOTER_KAKAO_CTA_LABEL = "카카오톡 채널 추가하고 상담 질문 받기";

/** data/academies/*.json 중 주소에 "미사"가 포함된 건수.
 *  tests/test_landing_copy.py 가 JSON 정본과 일치하는지 검사한다. GROUNDWORK_BODY·
 *  GROUNDWORK_SOURCE_NOTE가 이 숫자를 보간하므로, 여기 값이 바뀌면 화면 문구도
 *  같이 바뀐다 (하드코딩된 별도 문자열로 어긋나지 않게). */
export const MISA_ACADEMY_COUNT = 410;

/** 메인 하단. 지금 확인 가능한 사실(위 학원 수)과 후보 정리가 그 사실 위에서 돌아간다는
 *  것을 말한다. "정식 출시 후 제공"은 `/app`이 주 CTA가 되며 사실이 아니게 돼 뺐다.
 *  결정 로그에 근거가 없는 약속(영수증 인증 리뷰 등)은 여기에 쓰지 않는다. */
export const GROUNDWORK_HEADING = "학원콕이 쌓아가는 근거";
export const GROUNDWORK_BODY =
  `하남 미사 등록 학원 ${MISA_ACADEMY_COUNT}곳의 공개 정보와 확인일을 바탕으로 확인해 볼 후보를 정리합니다. 확인되지 않은 정보는 미확인으로 표시합니다.`;
export const GROUNDWORK_SOURCE_NOTE =
  `${MISA_ACADEMY_COUNT}곳 = 경기도 공공데이터 기준 미사 지역 등록 학원·교습소`;

/** `/` 검색·공유 메타. 알아보는 중·다니는 중 두 상황 모두 `/app`의 상황 선택이 받는다 —
 *  다니는 중을 따로 받던 1분 점검(`/check`)은 2026-09-14에 퇴역했다. */
export const META_DESCRIPTION =
  "학원을 알아보는 중이든 다니는 중이든, 학년·과목·고민을 입력하면 확인해 볼 후보 정보와 상담 질문을 정리해 드립니다. 특정 학원을 정해 드리거나 중개·예약·결제를 하지는 않습니다.";

/** 푸터 고지. 하남 미사 후보 정보·상담 질문은 현재형. 중개·예약·결제는 없음.
 *  푸터에는 `/app` 링크를 두지 않는다 — 주 CTA는 히어로 하나로 충분하다. */
export const FOOTER_STATUS_COPY =
  "학원콕은 아직 정식 출시 전입니다. 지금은 하남 미사 후보 정보와 상담에서 확인할 질문을 이용하실 수 있습니다. 특정 학원을 정해 드리거나 중개·예약·결제를 하지는 않습니다.";
