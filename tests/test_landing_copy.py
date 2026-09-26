"""랜딩 카피의 실측 숫자·경로·이벤트가 정본·코드와 어긋나지 않는지 검사한다.

2026-09-13 첫 MVP 확정: 메인(`/`)은 상황 분기 페이지가 아니라 `상황 입력 → 후보·상담 질문`
도구(`/app`)로 보내는 페이지다. 준비 중 기능 예고·예시 화면 섹션은 없다.
2026-09-14: 보조 퍼널 `/check`(1분 학원 점검)·`/checklists`(상담 전 질문)와 홈 상황 카드를
퇴역시키고 옛 URL은 `/app`으로 리다이렉트한다. 되돌아오지 않는지 감시한다.
"""

import json
import re
from pathlib import Path

import pytest

from tests.source_slice import slice_between

REPO_ROOT = Path(__file__).resolve().parents[1]
ACADEMIES = REPO_ROOT / "data" / "academies"
FRONTEND = REPO_ROOT / "frontend"
LANDING = FRONTEND / "src" / "components" / "landing"
LANDING_FACTS = LANDING / "landingFacts.ts"
PAGE_HERO = LANDING / "PageHero.tsx"
KAKAO_LINK = LANDING / "KakaoChannelLink.tsx"
LANDING_PAGE = LANDING / "LandingPage.tsx"
LANDING_HEADER = LANDING / "LandingHeader.tsx"
SITE_CHROME = LANDING / "SiteChrome.tsx"
STICKY_KAKAO = LANDING / "StickyKakaoBar.tsx"
KAKAO_MODAL = LANDING / "KakaoChannelModal.tsx"
KAKAO_CTA = LANDING / "KakaoChannelCta.tsx"
LANDING_FOOTER = LANDING / "LandingFooter.tsx"
PRIVACY_PAGE = FRONTEND / "src" / "app" / "privacy" / "page.tsx"
MODAL = FRONTEND / "src" / "components" / "ui" / "Modal.tsx"
LAYOUT = FRONTEND / "src" / "app" / "layout.tsx"
NEXT_CONFIG = FRONTEND / "next.config.ts"
CLICK_EVENT_TYPES = FRONTEND / "src" / "lib" / "types.ts"
CLICK_EVENT_ENUM = REPO_ROOT / "backend" / "app" / "core" / "constants.py"

# 2026-08-19 이전 3시점 카드가 쓰던 값. 되돌아오지 않는지 감시한다.
RETIRED_STAGE_EVENTS = (
    "home_stage_enroll_clicked",
    "home_stage_current_clicked",
    "home_stage_switch_clicked",
)
# 2026-09-14 `/check`·`/checklists`·홈 상황 카드 퇴역과 함께 걷어낸 값.
RETIRED_FUNNEL_EVENTS = (
    "mini_check_started",
    "mini_check_completed",
    "mini_check_result_viewed",
    "mini_check_home_clicked",
    "home_check_clicked",
    "checklist_kakao_clicked",
    "home_explore_selected",
    "explore_check_clicked",
    "check_explore_clicked",
)
# 2026-09-14에 지운 라우트·컴포넌트. 되살아나지 않는지 감시한다.
# 2026-09-25: GroundworkSection도 홈에서 걷어냈다.
RETIRED_PATHS = (
    FRONTEND / "src" / "app" / "check",
    FRONTEND / "src" / "app" / "checklists",
    FRONTEND / "src" / "components" / "check",
    FRONTEND / "src" / "components" / "checklists",
    LANDING / "HeroSection.tsx",
    LANDING / "SituationSection.tsx",
    LANDING / "SituationCard.tsx",
    LANDING / "TrackedLink.tsx",
    LANDING / "GroundworkSection.tsx",
)

ALL_LANDING_FILES = [
    LANDING_FACTS,
    PAGE_HERO,
    KAKAO_LINK,
    LANDING_PAGE,
    LANDING_HEADER,
    SITE_CHROME,
    STICKY_KAKAO,
    KAKAO_MODAL,
    KAKAO_CTA,
    LANDING_FOOTER,
    MODAL,
]


def test_misa_academy_count_matches_json_source():
    text = LANDING_FACTS.read_text(encoding="utf-8")
    match = re.search(r"export const MISA_ACADEMY_COUNT = (\d+);", text)
    assert match is not None, "MISA_ACADEMY_COUNT not found in landingFacts.ts"
    declared = int(match.group(1))

    counted = 0
    for path in ACADEMIES.glob("*.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        address = record.get("address") or ""
        if "미사" in address:
            counted += 1

    assert counted == declared, (
        f"landing copy says {declared} Misa academies but JSON has {counted}. "
        "Update MISA_ACADEMY_COUNT in landingFacts.ts."
    )


def test_groundwork_copy_is_gone_from_landing_facts():
    """2026-09-25: 홈 근거 구간과 함께 GROUNDWORK_* 카피를 걷어냈다.
    MISA_ACADEMY_COUNT는 JSON 건수 검사용으로만 남긴다."""
    facts = LANDING_FACTS.read_text(encoding="utf-8")
    facts_code = _strip_comments(facts)
    for gone in (
        "GROUNDWORK_HEADING",
        "GROUNDWORK_BODY",
        "GROUNDWORK_SOURCE_NOTE",
        "학원콕이 쌓아가는 근거",
    ):
        assert gone not in facts_code, f"{gone} still in landingFacts.ts"
    assert "MISA_ACADEMY_COUNT" in facts_code


def test_academy_count_carries_source_and_as_of_date():
    """학원 수량은 고정된 제품 약속이 아니라 기준일이 있는 데이터 현황이다 (2026-09-18,
    docs/project.md·data-strategy.md). 출처·수집 기준일 없이 숫자만 적지 않고, 기준일은
    data/README.md "현재 들어있는 데이터"가 말하는 수집일과 같아야 한다."""
    facts = LANDING_FACTS.read_text(encoding="utf-8")
    source = re.search(r'MISA_ACADEMY_COUNT_SOURCE = "([^"]+)";', facts)
    as_of = re.search(r'MISA_ACADEMY_COUNT_AS_OF = "([^"]+)";', facts)
    assert source and source.group(1).strip()
    assert as_of and re.fullmatch(r"\d{4}-\d{2}-\d{2}", as_of.group(1)), as_of
    assert "GROUNDWORK_SOURCE_NOTE" not in facts

    data_readme = (REPO_ROOT / "data" / "README.md").read_text(encoding="utf-8")
    current = data_readme.split("## 현재 들어있는 데이터", 1)[1]
    assert f"{as_of.group(1)} 기준" in current


def test_kakao_link_does_not_latch_modified_clicks():
    """수정 클릭(새 탭)에서 latch를 걸면, 같은 페이지에서 이어지는 일반 클릭이
    계측되지 않는다 — KakaoChannelLink는 수정 클릭을 latch보다 먼저 감지해야 한다."""
    text = KAKAO_LINK.read_text(encoding="utf-8")
    assert "metaKey" in text
    assert "ctrlKey" in text
    modified_at = text.index("modified")
    latch_at = text.index("trackedRef.current = true")
    assert modified_at < latch_at, (
        "modifier-click check must run before the latch is set"
    )


def test_hero_logo_uses_the_cropped_mark_not_the_padded_original():
    """logo.png(정사각 캔버스, 헤더 전용)는 히어로 로고에서 더 이상 쓰지 않는다.
    대체 텍스트는 브랜드명만 — 적합성 확정 문구를 alt 에 숨기지 않는다 (2026-09-13)."""
    hero = PAGE_HERO.read_text(encoding="utf-8")
    header = LANDING_HEADER.read_text(encoding="utf-8")

    assert 'src="/logo-mark.png"' in hero
    assert 'alt="학원콕"' in hero
    assert 'tone="neutral"' in hero
    assert "우리 아이에게 맞는" not in hero
    assert 'src="/logo.png"' not in hero
    # 헤더 로고는 이번 변경 범위 밖이다 — 계속 원본을 쓴다.
    assert 'src="/logo.png"' in header


def test_reassurance_lines_do_not_nest_a_bare_middle_dot_inside_a_dot_list():
    """`CTA_REASSURANCE`처럼 띄어쓴 " · " 목록 구분자 안에 무공백 "·" 합성어가
    끼어 있으면 항목 수를 오인하게 만든다 — 되돌아오기 방지 가드."""
    facts = LANDING_FACTS.read_text(encoding="utf-8")

    for const in ("CTA_REASSURANCE", "HERO_REASSURANCE"):
        line = slice_between(facts, f'export const {const} = "', '";')
        assert " · " in line
        assert "·" not in line.replace(" · ", ""), (
            f"{const} still nests a bare middle dot: {line!r}"
        )


def test_home_leads_with_explore_cta_and_has_no_situation_cards():
    """메인은 2026-09-13부터 주 CTA(`/app` 후보·상담 질문 정리) 하나로 시작한다.
    2026-09-25에 근거 구간도 걷어내 홈은 히어로만 남긴다.
    준비 중 기능 예고·예시 화면·대기자 모달·공용 HeroSection 도 되돌아오지 않는다."""
    facts = LANDING_FACTS.read_text(encoding="utf-8")
    page = LANDING_PAGE.read_text(encoding="utf-8")

    assert 'HOME_HEADLINE = "하남 미사에서 학원을 알아보고 있나요?"' in facts
    assert 'HOME_CTA_LABEL = "후보와 질문 정리하기"' in facts
    assert 'HOME_CTA_HREF = "/app"' in facts
    # 제목은 좁은 폭에서 두 줄로 고정한다.
    mobile_lines = slice_between(
        facts, "export const HOME_HEADLINE_MOBILE_LINES = [", "] as const;"
    )
    assert len(re.findall(r'"[^"]+"', mobile_lines)) == 2

    assert "PageHero" in page
    assert "href={HOME_CTA_HREF}" in page
    assert "HOME_CTA_LABEL" in page
    # 신뢰 문구는 `/app`의 것을 그대로 쓴다 — 착지한 뒤 같은 말을 다시 만나게.
    assert "TRUST_NOTE" in page
    # 히어로·CTA는 왼쪽 정렬.
    assert "items-start" in page
    assert "text-left" in PAGE_HERO.read_text(encoding="utf-8")

    # 설명 주석이 옛 이름을 언급하므로 주석은 빼고 실제 코드만 본다.
    page_code = _strip_comments(page)
    assert "<HomeHero" in page_code
    for gone in (
        "GroundworkSection",
        "HeroSection",
        "SituationSection",
        "PlannedFeaturesSection",
        "ServicePreviewSection",
        "WaitlistModal",
    ):
        assert gone not in page_code, f"{gone} still rendered on /"
    facts_code = _strip_comments(facts)
    assert "LIFECYCLE_STAGES" not in facts_code
    assert "SITUATIONS" not in facts_code
    assert not (LANDING / "PlannedFeaturesSection.tsx").exists()
    assert not (LANDING / "ServicePreviewSection.tsx").exists()
    assert not (LANDING / "GroundworkSection.tsx").exists()


def test_home_support_promises_candidates_and_questions_from_inputs():
    """홈 서포트는 무엇을 넣으면 무엇이 나오는지(학년·과목·고민 → 후보·상담 질문)만 말한다.
    옛 '맞는 곳부터'(적합성 확정)·'아래에서 상황을 고르세요'(분기 페이지)·숫자 약속으로
    되돌아가지 않는다."""
    facts = LANDING_FACTS.read_text(encoding="utf-8")
    support = slice_between(facts, "HOME_SUPPORT =", '";')
    for word in ("학년", "과목", "고민", "후보", "상담 질문"):
        assert word in support, word
    assert "맞는 곳부터" not in support
    assert "410" not in support
    assert "우리 아이에게 맞는" not in support


def test_footer_keeps_status_copy_without_app_link():
    """주 CTA 는 히어로 하나(`/app`)로 충분하다 — 푸터에는 `/app` 링크를 두지 않고
    출시 전 고지·후보 가이드 문구만 남긴다."""
    footer_code = _strip_comments(LANDING_FOOTER.read_text(encoding="utf-8"))

    assert 'href="/app"' not in footer_code
    assert "APP_EXPLORE_LINK_LABEL" not in footer_code
    assert "AI 학원 추천" not in footer_code
    assert "학원 후보 가이드" in footer_code


def test_home_has_no_sticky_cta_bar():
    """홈에는 StickyCtaBar도 StickyKakaoBar도 없다 — 주 CTA는 히어로 하나로 충분하다.
    (설명 주석에서 이름을 언급하는 것은 허용하고, 실제 렌더링 여부만 본다.)"""
    page = LANDING_PAGE.read_text(encoding="utf-8")
    page_code = _strip_comments(page)
    assert "<StickyCtaBar" not in page_code
    assert '"./StickyCtaBar"' not in page_code
    # 홈은 SiteChrome 기본값(footer·kakaoBar 끔)을 쓴다 — prop을 넘기지 않는다.
    assert "footer" not in page_code
    assert "kakaoBar" not in page_code


def _strip_comments(text: str) -> str:
    """`/** ... */`·`// ...` 주석을 지운다. 되돌아오기 방지 가드가 '왜 뺐는지' 설명하는
    주석 자체를 위반으로 오탐하지 않게 하기 위해서다 — 실제 카피·코드만 검사한다."""
    without_block = re.sub(r"/\*[\s\S]*?\*/", "", text)
    return re.sub(r"//[^\n]*", "", without_block)


def test_no_dead_stage_vocabulary_remains():
    """되돌아오기 방지 가드: 3시점 카드·퇴역 퍼널 이벤트·수량 프레이밍·근거 없는 새 약속·
    순위·적합성 확정·출시 후 약속·1분 점검이 다시 들어오지 않는지. (설명 주석 안에서
    옛 이름을 언급하는 것은 허용하고, 실제 카피·코드만 본다.)"""
    banned_everywhere = (*RETIRED_STAGE_EVENTS, *RETIRED_FUNNEL_EVENTS)
    banned_copy = (
        "체크리스트 3종",
        "영수증 인증",
        "인증 리뷰",
        # 2026-09-13
        "우리 아이에게 맞는",
        "정식 출시 후 제공",
        "AI 추천",
        "1순위",
        # 2026-09-14
        "1분 학원 점검",
        "1분 점검",
    )

    for path in ALL_LANDING_FILES:
        code_only = _strip_comments(path.read_text(encoding="utf-8"))
        for banned in banned_everywhere:
            assert banned not in code_only, f"{banned} still referenced in {path.name}"
        for banned in banned_copy:
            assert banned not in code_only, f"{banned} still referenced in {path.name}"


def test_footer_status_copy_keeps_pre_launch_notice():
    """출시 전 고지는 푸터 카피가 계속 맡는다. 근거 구간은 2026-09-25에 없앴다."""
    facts = LANDING_FACTS.read_text(encoding="utf-8")
    footer = slice_between(facts, "FOOTER_STATUS_COPY =", '";')
    assert "정식 출시 전" in footer
    assert "GROUNDWORK_BODY" not in facts


def test_kakao_reward_is_question_framed_not_a_count():
    """`3종`처럼 웰컴메시지와 어긋나기 쉬운 수량 약속 대신 '상담 질문'으로 통일한다."""
    facts = LANDING_FACTS.read_text(encoding="utf-8")
    modal = KAKAO_MODAL.read_text(encoding="utf-8")

    reward_note = slice_between(facts, "KAKAO_REWARD_NOTE =", ";")
    assert "상담" in reward_note
    reward_label = slice_between(facts, 'KAKAO_REWARD_LABEL = "', '"')
    assert "상담 질문" in reward_label
    assert "상담" in modal
    assert "질문" in modal
    assert "체크리스트 3종" not in modal
    # 고정 바 CTA도 같은 프레이밍.
    footer_cta = slice_between(facts, "FOOTER_KAKAO_CTA_LABEL =", ";")
    assert "상담 질문" in footer_cta
    assert "FOOTER_KAKAO_CTA_LABEL" in STICKY_KAKAO.read_text(encoding="utf-8")


def test_every_kakao_entry_point_goes_through_the_modal_first():
    """카카오로 나가기 전 보상·고지 팝업을 반드시 거치게 한다.
    외부로 실제로 나가는 링크(KakaoChannelLink)는 모달 안에만 있어야 한다 —
    호출부가 직접 쓰면 팝업을 건너뛰고 바로 외부로 나간다.
    2026-09-25: 홈 근거 구간의 카카오 CTA는 없앴고, 푸터·고정 바만 `/privacy`에서 켠다."""
    callers = [
        LANDING_FOOTER,
        STICKY_KAKAO,
    ]
    for path in callers:
        code_only = _strip_comments(path.read_text(encoding="utf-8"))
        assert "KakaoChannelCta" in code_only, f"{path.name} has no Kakao CTA"
        assert "<KakaoChannelLink" not in code_only, (
            f"{path.name} links straight to Kakao, skipping the modal"
        )

    # 모달이 보상을 말해야 팝업을 띄우는 의미가 있다.
    modal = KAKAO_MODAL.read_text(encoding="utf-8")
    assert "웰컴메시지" in modal
    assert "질문" in modal

    # 2026-09-14: `/check` 결과 전용 이벤트가 퇴역해 카카오 링크는 `kakao_channel` 하나만 보낸다.
    link_code = _strip_comments(KAKAO_LINK.read_text(encoding="utf-8"))
    assert 'event: "kakao_channel"' in link_code
    for path in (KAKAO_CTA, KAKAO_MODAL, KAKAO_LINK):
        code_only = _strip_comments(path.read_text(encoding="utf-8"))
        assert "KakaoTrackEvent" not in code_only, f"{path.name} still threads an event prop"


def test_retired_events_are_gone_on_both_sides_of_the_wire():
    """퇴역 이벤트가 프론트 타입·백엔드 enum 어느 쪽에도 되살아나지 않게 한다.
    한쪽에만 되살리면 프론트가 보낸 값을 백엔드가 422로 거절하거나 죽은 값이 남는다."""
    types_ts = CLICK_EVENT_TYPES.read_text(encoding="utf-8")
    constants_py = CLICK_EVENT_ENUM.read_text(encoding="utf-8")

    assert '"kakao_channel"' in types_ts
    assert '= "kakao_channel"' in constants_py

    for event in (*RETIRED_STAGE_EVENTS, *RETIRED_FUNNEL_EVENTS):
        assert f'"{event}"' not in types_ts, f"retired event {event} still in ClickEventType"
        assert f'= "{event}"' not in constants_py, f"retired event {event} still in ClickEvent"


def test_check_and_checklists_are_retired_and_redirect_to_app():
    """2026-09-14: `/check`·`/checklists`는 지웠지만 카카오 웰컴 메시지·광고 초안의 옛 링크가
    404가 되지 않게 `/app`으로 임시(307) 리다이렉트한다 — 308은 브라우저가 캐시해 되돌리기
    어렵다. 홈·공용 크롬·방침 페이지 어디에서도 두 경로로 보내지 않는다."""
    for path in RETIRED_PATHS:
        assert not path.exists(), f"retired path came back: {path.relative_to(REPO_ROOT)}"

    config = NEXT_CONFIG.read_text(encoding="utf-8")
    assert "async redirects()" in config
    for source in ("/check", "/checklists"):
        assert (
            f'{{ source: "{source}", destination: "/app", permanent: false }}' in config
        ), f"{source} must redirect to /app with a temporary (307) redirect"

    for path in (*ALL_LANDING_FILES, PRIVACY_PAGE, LAYOUT):
        code_only = _strip_comments(path.read_text(encoding="utf-8"))
        for href in ('"/check"', '"/checklists"'):
            assert href not in code_only, f"{href} still linked from {path.name}"

    privacy_code = _strip_comments(PRIVACY_PAGE.read_text(encoding="utf-8"))
    assert "1분" not in privacy_code
    assert "/check" not in privacy_code


def test_home_metadata_reflects_the_two_situations():
    facts = LANDING_FACTS.read_text(encoding="utf-8")
    layout = LAYOUT.read_text(encoding="utf-8")

    assert "META_DESCRIPTION" in layout
    # [:300] 은 상수를 넘어 다음 주석과 FOOTER_STATUS_COPY 까지 삼켰다 —
    # 중개·예약·결제 고지를 여기서 통째로 지워도 그 spillover 때문에 통과했다.
    description = slice_between(facts, "META_DESCRIPTION =", '";')
    assert "알아보는 중" in description
    assert "다니는 중" in description
    assert "후보 정보" in description
    assert "중개" in description
    assert "예약" in description
    assert "결제" in description
    # 푸터 고지는 메타로 대체되지 않고 그대로 남는다.
    assert "FOOTER_STATUS_COPY" in facts
    footer = slice_between(facts, "FOOTER_STATUS_COPY =", '";')
    assert "정식 출시 전" in footer
    assert "후보 정보" in footer


def test_meta_description_slice_catches_removed_brokerage_notice():
    """[:300] 슬라이스는 META에서 중개 고지를 지워도 FOOTER spillover 로 통과했다."""
    facts = LANDING_FACTS.read_text(encoding="utf-8")
    mutated = facts.replace(
        "특정 학원을 정해 드리거나 중개·예약·결제를 하지는 않습니다.",
        "특정 학원을 정해 드리거나 예약·결제를 하지는 않습니다.",
        1,
    )
    description = slice_between(mutated, "META_DESCRIPTION =", '";')
    with pytest.raises(AssertionError):
        assert "중개" in description


def test_header_status_notice_lives_below_hero_not_in_header():
    """출시 전·중개 없음 고지는 삭제하지 않되, 히어로와 경쟁하지 않게 헤더 옆에서
    홈 하단으로 내린다 (2026-09-25). '소개용 랜딩 페이지'는 `/app`을 주 CTA로
    연결한 뒤 사실과 어긋나 2026-09-13에 뺐다."""
    facts = LANDING_FACTS.read_text(encoding="utf-8")
    header = LANDING_HEADER.read_text(encoding="utf-8")
    page = LANDING_PAGE.read_text(encoding="utf-8")

    assert "HEADER_STATUS_NOTICE" not in header
    assert "HEADER_STATUS_NOTICE" in page
    notice = slice_between(facts, "HEADER_STATUS_NOTICE =", ";")
    assert "정식 출시" in notice
    assert "중개" in notice
    assert "수강료" in notice
    assert "랜딩 페이지" not in notice
    # 배지 형태로 되돌리지 않는다.
    assert "Badge" not in header


def test_intro_pages_share_site_chrome_footer_and_kakao_opt_in():
    """`/`·`/privacy`가 같은 SiteChrome(헤더)을 쓴다. 푸터·고정 카카오 바는 기본 끔이고
    `/privacy`만 켠다. `/app`은 제외."""
    for path in (LANDING_PAGE, PRIVACY_PAGE):
        text = path.read_text(encoding="utf-8")
        assert "SiteChrome" in text, f"{path.name} is missing SiteChrome"
        assert "<LandingHeader" not in text, f"{path.name} still mounts header directly"
        assert "<LandingFooter" not in text, f"{path.name} still mounts footer directly"

    home = _strip_comments(LANDING_PAGE.read_text(encoding="utf-8"))
    assert "footer" not in home
    assert "kakaoBar" not in home

    privacy_code = _strip_comments(PRIVACY_PAGE.read_text(encoding="utf-8"))
    assert "footer" in privacy_code
    assert "kakaoBar" in privacy_code

    chrome = SITE_CHROME.read_text(encoding="utf-8")
    chrome_code = _strip_comments(chrome)
    assert "LandingHeader" in chrome_code
    assert "LandingFooter" in chrome_code
    assert "StickyKakaoBar" in chrome_code
    assert "footer = false" in chrome_code
    assert "kakaoBar = false" in chrome_code
    # 하단 8rem 패딩은 카카오 바를 켤 때만.
    assert "kakaoBar" in chrome
    assert "8rem" in chrome

    bar = STICKY_KAKAO.read_text(encoding="utf-8")
    assert "KakaoChannelCta" in bar
    assert "FOOTER_KAKAO_CTA_LABEL" in bar
    assert "<KakaoChannelLink" not in bar
    assert "fixed" in bar
    # 모달 제목(KAKAO_REWARD_LABEL "상담 질문 받아보기")과 같은 프레이밍.
    facts_text = LANDING_FACTS.read_text(encoding="utf-8")
    footer_cta = slice_between(facts_text, "FOOTER_KAKAO_CTA_LABEL =", ";")
    assert "상담 질문" in footer_cta
    assert "출시 알림 받기" not in footer_cta

    # `/privacy`는 방침 h1을 유지하고 소개 히어로를 쓰지 않는다.
    privacy = PRIVACY_PAGE.read_text(encoding="utf-8")
    assert "개인정보처리방침" in privacy
    assert "PageHero" not in privacy


def test_modal_portals_to_document_body():
    """고정 바(`backdrop-filter`) 안에 두면 fixed 모달이 바에 갇혀 화면을 덮지 못한다.
    createPortal(..., document.body)가 그 장치다 — 빠지면 카피 테스트는 다 통과하고
    고정 바 카카오만 조용히 깨진다."""
    modal = MODAL.read_text(encoding="utf-8")
    assert "createPortal" in modal
    assert "react-dom" in modal
    assert "document.body" in modal
    # 포털은 open일 때만 그려야 한다 — 닫혔을 렌더 잔여를 남기지 않게.
    assert "if (!open) return null" in modal
