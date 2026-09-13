/** KakaoChannelModal 세 항목의 압축. 모달 문구를 바꾸면 여기도 같이 고친다. */
/** 목록 구분자 "·"와 "이름/연락처" 합성어를 같은 기호로 겹치지 않게 "/"로 구분한다
 *  (2026-08-19, 띄어쓰기 정리). 약속 범위(이름·연락처를 특정해 좁힌 2026-08-17 결정)는 그대로다. */
export const CTA_REASSURANCE = "무료 · 이름/연락처 입력 없음 · 언제든 차단 가능";

/** 카카오 채널이 주는 것. `체크리스트 3종`이라는 수량 프레이밍은 2026-08-19에 버렸다 —
 *  화면(`/checklists`·`/check`)이 실제로 주는 것이 "상담 때 물어볼 질문"이라서다.
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

/** `/check`·`/checklists`가 공유하는 히어로 (홈은 위 HOME_* 을 쓴다).
 *  적합성을 확정하는 표현(`우리 아이에게 맞는`)은 쓰지 않는다 — 프로젝트 상위 목표
 *  (더 나은 질문과 판단)를 그대로 말한다. 제목은 두 줄로 나눈다. */
export const HERO_BADGE = "하남 미사 학부모를 위한 학원 선택 가이드";
export const HERO_HEADLINE = "학원을 알아볼 때도, 다니는 동안에도";
export const HERO_HEADLINE_LINE2 = "더 나은 질문과 판단을 돕습니다";
/** sm 미만에서 h1 줄바꿈 고정 — 좁은 폭에서 자동 줄바꿈에 맡기지 않는다. */
export const HERO_HEADLINE_MOBILE_LINES = [
  "학원을 알아볼 때도,",
  "다니는 동안에도",
  "더 나은 질문과",
  "판단을 돕습니다",
] as const;
export const HERO_SUPPORT =
  "아래에서 지금 상황을 고르시면, 상담 전 확인할 질문이나 1분 점검부터 시작할 수 있습니다.";
/** `/checklists`의 `CONSULT_REASSURANCE`, `/check`의 `CHECK_CTA_HINT`와 같은
 *  " · " 3항목 배지 형식 — 세 페이지가 같은 자리에서 같은 형식으로 즉시 효익을 말한다. */
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

/** 메인의 상황 카드 두 장. 2026-09-13부터 주 과업은 위 히어로 CTA(`/app`)이고, 이 카드는
 *  다른 목적의 보조 퍼널(상담 질문만 보기 · 다니는 학원 점검)이다. 삭제하지 않는다.
 *  세 번째 카드(옮기기 전)를 두지 않는다 — 이전은 `/checklists`의 마지막 묶음이 담는다.
 *  `event`는 backend ClickEvent·lib/types.ts와 함께 고친다.
 *  `다니는 중`은 기존 `home_check_clicked`를 이어받아 지표 연속성을 지킨다. */
export const SITUATION_SECTION_HEADING = "다른 도움이 필요하세요?";
export const SITUATIONS = [
  {
    id: "explore",
    label: "학원을 알아보는 중",
    title: "상담 전에 확인할 질문",
    body: "처음 등록하거나 새 학원을 찾고 있다면, 상담 전에 꼭 확인할 질문을 정리하세요.",
    ctaLabel: "상담 질문 보기",
    href: "/checklists",
    event: "home_explore_selected",
  },
  {
    id: "current",
    label: "학원을 다니는 중",
    title: "1분 학원 점검",
    body: "지금 수업 수준·학습 관리·수업 분위기를 1분 만에 점검해 보세요.",
    ctaLabel: "1분 학원 점검하기",
    href: "/check",
    event: "home_check_clicked",
  },
] as const;

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

/** `/checklists` — 학원을 알아보는 중 (당근 광고 A 착지).
 *  2026-08-19에 체크리스트 3종 허브에서 상담 랜딩으로 개편했다. */
export const CONSULT_BADGE = "학원 상담 전 질문";
export const CONSULT_HEADLINE = "상담 전에 이 질문부터 챙기세요.";
export const CONSULT_SUPPORT =
  "수업·강사·학습 관리·분위기까지, 아이에게 맞을지 상담에서 확인하는 질문을 모았습니다.";
/** `/check`의 `CHECK_CTA_HINT`와 같은 " · " 3항목 배지 형식으로 통일했다
 *  (2026-08-19) — 완전한 문장형이던 이전 문구는 페이지를 오갈 때 톤이 흔들렸다. */
export const CONSULT_REASSURANCE = "로그인 · 개인정보 입력 없음 · 지금 바로 확인";
export const CONSULT_CHECK_CTA_LABEL = "1분 학원 점검도 해보기";
/** `/checklists` 본문 하단 카카오 CTA. 모달 제목·KAKAO_REWARD_LABEL과 같은 프레이밍. */
export const CONSULT_KAKAO_CTA_LABEL = "카카오톡으로 상담 질문 받기";

/** `/check` — 학원을 다니는 중 (당근 광고 B 착지).
 *  제목은 두 줄로 나눈다 — 한 문장을 뷰포트에 맡겨 애매하게 접히지 않게. */
export const CHECK_CTA_LABEL = "1분 학원 점검";
export const CHECK_INTRO_BADGE = "지금 다니는 학원 1분 점검";
export const CHECK_INTRO_HEADLINE = "지금 수업,";
export const CHECK_INTRO_HEADLINE_LINE2 = "우리 아이에게 계속 맞을까요?";
export const CHECK_INTRO_SUPPORT =
  "수업 수준·학습 관리·수업 분위기를 짧게 확인하고, 다음 상담 때 물어볼 질문을 받아보세요.";
export const CHECK_CTA_HINT = "로그인 · 개인정보 입력 없음 · 약 1분";

/** 점검 결과 CTA. 새 학원 탐색을 과하게 밀지 않되, 상담 준비 자료로는 이어준다. */
export const CHECK_RESULT_KAKAO_LABEL = "카카오톡으로 상담 질문 받기";
export const CHECK_RESULT_CONSULT_LABEL = "상담 질문 전체 보기";
export const CHECK_RESULT_HOME_LABEL = "학원콕 더 알아보기";

/** `/` 검색·공유 메타. 주 과업(후보·상담 질문)과 보조 퍼널(1분 점검)을 함께 말한다. */
export const META_DESCRIPTION =
  "학원을 알아보는 중이라면 학년·과목·고민을 입력해 확인해 볼 후보 정보와 상담 질문을, 다니는 중이라면 1분 점검을 받아보세요. 특정 학원을 정해 드리거나 중개·예약·결제를 하지는 않습니다.";

/** 푸터 고지. 상담 질문·점검·하남 미사 후보 정보는 현재형. 중개·예약·결제는 없음.
 *  푸터에는 `/app` 링크를 두지 않는다 — 주 CTA는 히어로 하나로 충분하다. */
export const FOOTER_STATUS_COPY =
  "학원콕은 아직 정식 출시 전입니다. 지금은 상담 전 확인할 질문, 1분 학원 점검, 하남 미사 후보 정보를 이용하실 수 있습니다. 특정 학원을 정해 드리거나 중개·예약·결제를 하지는 않습니다.";
