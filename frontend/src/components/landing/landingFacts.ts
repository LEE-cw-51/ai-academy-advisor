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

/** 홈 히어로. 메인은 기능 하나를 파는 페이지가 아니라 **상황을 고르는 분기 페이지**다.
 *  그래서 제목이 특정 도구를 약속하지 않고, 주 CTA 버튼도 두지 않는다 —
 *  첫 콘텐츠가 `SITUATIONS` 카드 두 장이다.
 *  제목은 두 줄로 나눈다 — 좁은 폭에서 애매하게 접히지 않게. */
export const HERO_BADGE = "하남 미사 학부모를 위한 학원 선택 가이드";
export const HERO_HEADLINE = "학원을 알아볼 때도, 다니는 동안에도";
export const HERO_HEADLINE_LINE2 = "우리 아이에게 맞는 선택을 돕습니다";
/** sm 미만에서 h1 줄바꿈 고정 — 좁은 폭에서 자동 줄바꿈에 맡기지 않는다. */
export const HERO_HEADLINE_MOBILE_LINES = [
  "학원을 알아볼 때도,",
  "다니는 동안에도",
  "우리 아이에게 맞는",
  "선택을 돕습니다",
] as const;
export const HERO_SUPPORT =
  "상담에서 무엇을 확인할지, 지금 학원이 아이에게 맞는지부터 차근차근 정리해 드립니다.";
/** `/checklists`의 `CONSULT_REASSURANCE`, `/check`의 `CHECK_CTA_HINT`와 같은
 *  " · " 3항목 배지 형식 — 세 페이지가 같은 자리에서 같은 형식으로 즉시 효익을 말한다. */
export const HERO_REASSURANCE = "로그인 · 개인정보 입력 없음 · 지금 바로 확인";

/** 헤더 로고 옆. 배지가 아니라 문장이다 — 2026-08-16이 헤더에서 뺀 것은
 *  스크롤 내내 따라다니는 **배지**였고, 운영 전·판매 없음은 광고 심사에 필요해서
 *  텍스트로 되돌린다. 푸터 상세 고지와 겹쳐도 된다. */
export const HEADER_STATUS_NOTICE =
  "현재는 정식 운영 중이 아니고, 소개용 랜딩 페이지입니다. 학원을 중개하거나 수강료를 받지 않습니다.";

/** 전 소개 페이지 하단 고정 바. 누르면 바로 카카오로 가지 않고 모달을 연다.
 *  모달 제목·KAKAO_REWARD_LABEL이 "상담 질문"으로 통일돼 있어 같은 프레이밍을 쓴다. */
export const FOOTER_KAKAO_CTA_LABEL = "카카오톡 채널 추가하고 상담 질문 받기";

/** 상황 카드 아래. 지금 없는 기능을 예고한다 — 공개 퍼널에 입력 폼이 없고
 *  학원 속성 필드(과목·수준·성향)는 정본에서 0%이며, 시기별(1·3·6·12개월) 구조도
 *  코드에 없다. 그래서 현재형 단정 없이 예정형 + 준비 중 배지다. */
export const PLANNED_BADGE_LABEL = "준비 중";
export const PLANNED_FEATURES_HEADING = "학원콕은 이렇게 도와드립니다";
export const PLANNED_FEATURES = [
  {
    id: "before-enroll",
    title: "학원 다니기전",
    body: "아이의 학년, 학교, 수준, 성향을 입력하시면 3개 학원을 추천해드릴 예정입니다.",
  },
  {
    id: "during",
    title: "학원 다니는 중",
    body: "시기별(1개월, 3개월, 6개월, 1년) 상담 질문, 확인할 포인트를 보내드릴 예정입니다.",
  },
] as const;

/** 가상 추천 카드. data/academies/*.json을 참조하지 않는다.
 *  OO/△△/□□ 표기는 docs/design/academy-kok-landing.html 목업의 관례를 따른다. */
export const PREVIEW_HEADING = "서비스 화면 예시";
export const PREVIEW_NOTICE =
  "추천 결과가 어떤 근거와 함께 보이는지 보여주는 가상 예시입니다.";
export const PREVIEW_DISCLAIMER =
  "실제 학원 정보가 아닌 예시이며, 정식 출시 후 이 화면으로 제공될 예정입니다.";
export const EXAMPLE_ITEMS = [
  {
    rank: 1,
    name: "OO수학학원",
    tagline: "소수정예 · 내신 대비 · 도보 6분",
    reason: "아이가 경쟁 분위기에 예민하다고 하셔서 소수정예 위주로 골랐어요.",
  },
  {
    rank: 2,
    name: "△△영어학원",
    tagline: "그룹수업 · 선행 · 도보 9분",
    reason: "또래와 같이 할 때 더 잘한다고 하셔서 그룹수업을 함께 담았어요.",
  },
  {
    rank: 3,
    name: "□□국어학원",
    tagline: "1:1 · 독해 · 도보 4분",
    reason: "글쓰기를 어려워한다고 하셔서 1:1 첨삭이 되는 곳을 넣었어요.",
  },
] as const;

/** 메인의 상황 분기 두 장. 학부모가 자기 상황을 고르는 것이 이 페이지의 유일한 과업이다.
 *  세 번째 카드(옮기기 전)를 두지 않는다 — 이전은 `/checklists`의 마지막 묶음이 담는다.
 *  `event`는 backend ClickEvent·lib/types.ts와 함께 고친다.
 *  `다니는 중`은 기존 `home_check_clicked`를 이어받아 지표 연속성을 지킨다. */
export const SITUATION_SECTION_HEADING = "지금 어떤 도움이 필요하세요?";
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

/** 메인 하단. 지금 확인 가능한 사실(410곳)과 준비 중인 것(맞춤 추천)을 한 덩어리로 구분해 말한다.
 *  가상 추천 카드는 예시 고지·배지·Disclaimer를 조건으로 다시 두었다.
 *  결정 로그에 근거가 없는 약속(영수증 인증 리뷰 등)은 여기에 쓰지 않는다. */
export const GROUNDWORK_HEADING = "학원콕이 쌓아가는 근거";
export const GROUNDWORK_BODY =
  "하남 미사 등록 학원 410곳을 바탕으로, 더 나은 상담과 선택을 돕는 자료를 먼저 만들고 있습니다. 등록 전 맞춤 추천은 정식 출시 후 제공됩니다.";
export const GROUNDWORK_SOURCE_NOTE =
  "410곳 = 경기도 공공데이터 기준 미사 지역 등록 학원·교습소";

/** `/checklists` — 학원을 알아보는 중 (당근 광고 A 착지).
 *  2026-08-19에 체크리스트 3종 허브에서 상담 랜딩으로 개편했다. */
export const CONSULT_BADGE = "학원 상담 전 질문";
export const CONSULT_HEADLINE = "상담 전에 이 질문부터 챙기세요.";
export const CONSULT_SUPPORT =
  "수업·강사·학습 관리·분위기까지, 우리 아이에게 맞는 학원인지 확인하는 질문을 모았습니다.";
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

/** `/` 검색·공유 메타. 두 상황을 모두 말한다 — 메인이 분기 페이지이기 때문이다. */
export const META_DESCRIPTION =
  "학원을 알아보는 중이라면 상담 전에 확인할 질문을, 다니는 중이라면 1분 점검을 받아보세요. 등록 전 맞춤 추천은 정식 출시 후 제공됩니다.";

/** 푸터 고지. 상담 질문·점검은 현재형, 맞춤 추천만 출시 후. */
export const FOOTER_STATUS_COPY =
  "학원콕은 아직 정식 출시 전입니다. 지금은 상담 전 확인할 질문과 1분 학원 점검을 이용하실 수 있습니다. 등록 전 맞춤 추천은 정식 출시 후 제공될 예정입니다.";

/** data/academies/*.json 중 주소에 "미사"가 포함된 건수.
 *  tests/test_landing_copy.py 가 JSON 정본과 일치하는지 검사한다. */
export const MISA_ACADEMY_COUNT = 410;
