"""랜딩 카피의 실측 숫자·경로·이벤트가 정본·코드와 어긋나지 않는지 검사한다."""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ACADEMIES = REPO_ROOT / "data" / "academies"
LANDING = REPO_ROOT / "frontend" / "src" / "components" / "landing"
CHECKLISTS_DIR = REPO_ROOT / "frontend" / "src" / "components" / "checklists"
LANDING_FACTS = LANDING / "landingFacts.ts"
HERO = LANDING / "HeroSection.tsx"
PAGE_HERO = LANDING / "PageHero.tsx"
TRACKED_LINK = LANDING / "TrackedLink.tsx"
KAKAO_LINK = LANDING / "KakaoChannelLink.tsx"
SITUATION_SECTION = LANDING / "SituationSection.tsx"
SITUATION_CARD = LANDING / "SituationCard.tsx"
GROUNDWORK_SECTION = LANDING / "GroundworkSection.tsx"
PLANNED_FEATURES_SECTION = LANDING / "PlannedFeaturesSection.tsx"
SERVICE_PREVIEW_SECTION = LANDING / "ServicePreviewSection.tsx"
LANDING_PAGE = LANDING / "LandingPage.tsx"
LANDING_HEADER = LANDING / "LandingHeader.tsx"
SITE_CHROME = LANDING / "SiteChrome.tsx"
STICKY_KAKAO = LANDING / "StickyKakaoBar.tsx"
KAKAO_MODAL = LANDING / "KakaoChannelModal.tsx"
KAKAO_CTA = LANDING / "KakaoChannelCta.tsx"
LANDING_FOOTER = LANDING / "LandingFooter.tsx"
CHECKLIST_DATA = CHECKLISTS_DIR / "checklistsData.ts"
CHECKLIST_GROUP = CHECKLISTS_DIR / "ChecklistGroup.tsx"
CHECKLISTS_PAGE = (
    REPO_ROOT / "frontend" / "src" / "app" / "checklists" / "page.tsx"
)
CHECK_PAGE = REPO_ROOT / "frontend" / "src" / "app" / "check" / "page.tsx"
PRIVACY_PAGE = REPO_ROOT / "frontend" / "src" / "app" / "privacy" / "page.tsx"
MODAL = REPO_ROOT / "frontend" / "src" / "components" / "ui" / "Modal.tsx"
MINI_CHECK = (
    REPO_ROOT / "frontend" / "src" / "components" / "check" / "MiniAcademyCheck.tsx"
)
LAYOUT = REPO_ROOT / "frontend" / "src" / "app" / "layout.tsx"
CLICK_EVENT_TYPES = REPO_ROOT / "frontend" / "src" / "lib" / "types.ts"
CLICK_EVENT_ENUM = REPO_ROOT / "backend" / "app" / "core" / "constants.py"

# 2026-08-19 이전 3시점 카드가 쓰던 값. 되돌아오지 않는지 감시한다.
RETIRED_STAGE_EVENTS = (
    "home_stage_enroll_clicked",
    "home_stage_current_clicked",
    "home_stage_switch_clicked",
)
# 3페이지 퍼널 재구성이 도입한 값.
FUNNEL_EVENTS = (
    "home_check_clicked",
    "home_explore_selected",
    "explore_check_clicked",
    "check_explore_clicked",
)

ALL_LANDING_FILES = [
    LANDING_FACTS,
    HERO,
    PAGE_HERO,
    TRACKED_LINK,
    KAKAO_LINK,
    SITUATION_SECTION,
    SITUATION_CARD,
    GROUNDWORK_SECTION,
    PLANNED_FEATURES_SECTION,
    SERVICE_PREVIEW_SECTION,
    LANDING_PAGE,
    LANDING_HEADER,
    SITE_CHROME,
    STICKY_KAKAO,
    KAKAO_MODAL,
    KAKAO_CTA,
    LANDING_FOOTER,
    CHECKLIST_DATA,
    CHECKLISTS_PAGE,
    MINI_CHECK,
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


def test_groundwork_copy_interpolates_the_academy_count_not_a_literal():
    """GROUNDWORK_BODY/SOURCE_NOTE가 리터럴 "410"을 박아두면 MISA_ACADEMY_COUNT가
    바뀌어도 화면 문구가 따라가지 않는다 — 반드시 그 상수를 보간해야 한다."""
    facts = LANDING_FACTS.read_text(encoding="utf-8")
    body = facts.split("GROUNDWORK_BODY =")[1].split(";")[0]
    note = facts.split("GROUNDWORK_SOURCE_NOTE =")[1].split(";")[0]
    assert "${MISA_ACADEMY_COUNT}" in body
    assert "${MISA_ACADEMY_COUNT}" in note


def test_tracked_link_and_kakao_link_do_not_latch_modified_clicks():
    """수정 클릭(새 탭)에서 latch를 걸면, 같은 페이지에서 이어지는 일반 클릭이
    계측되지 않는다 — TrackedLink/KakaoChannelLink 둘 다 수정 클릭을 감지해야 한다."""
    for path in (TRACKED_LINK, KAKAO_LINK):
        text = path.read_text(encoding="utf-8")
        assert "metaKey" in text, f"{path.name} does not check metaKey"
        assert "ctrlKey" in text, f"{path.name} does not check ctrlKey"
        modified_at = text.index("modified")
        latch_at = text.index("trackedRef.current = true")
        assert modified_at < latch_at, (
            f"{path.name}: modifier-click check must run before the latch is set"
        )


def test_hero_logo_uses_the_cropped_mark_not_the_padded_original():
    """logo.png(정사각 캔버스, 헤더 전용)는 히어로 로고에서 더 이상 쓰지 않는다."""
    hero = PAGE_HERO.read_text(encoding="utf-8")
    header = LANDING_HEADER.read_text(encoding="utf-8")

    assert 'src="/logo-mark.png"' in hero
    assert 'src="/logo.png"' not in hero
    # 헤더 로고는 이번 변경 범위 밖이다 — 계속 원본을 쓴다.
    assert 'src="/logo.png"' in header


def test_check_intro_reuses_home_hero():
    """`/check` 인트로가 홈 HeroSection을 쓰면 배지 톤이 `/`·`/checklists`와 자동으로 같아진다."""
    hero = PAGE_HERO.read_text(encoding="utf-8")
    mini = MINI_CHECK.read_text(encoding="utf-8")

    assert 'tone="neutral"' in hero
    assert "HeroSection" in mini
    assert "PageHero" not in mini
    # 인트로 마크업을 더 이상 여기서 직접 그리지 않는다.
    assert 'tone="warn"' not in mini


def test_result_disclaimer_badge_is_not_brand_colored():
    """면책 고지는 AI·차별점 강조용 브랜드 오렌지와 의미가 다르다."""
    mini = MINI_CHECK.read_text(encoding="utf-8")
    assert '<Badge tone="neutral">학원 평가가 아닙니다</Badge>' in mini


def test_reassurance_lines_do_not_nest_a_bare_middle_dot_inside_a_dot_list():
    """`CTA_REASSURANCE`처럼 띄어쓴 " · " 목록 구분자 안에 무공백 "·" 합성어가
    끼어 있으면 항목 수를 오인하게 만든다 — 되돌아오기 방지 가드."""
    facts = LANDING_FACTS.read_text(encoding="utf-8")

    cta_line = facts.split('CTA_REASSURANCE = "')[1].split('"')[0]
    assert " · " in cta_line
    assert "·" not in cta_line.replace(" · ", ""), (
        f"CTA_REASSURANCE still nests a bare middle dot: {cta_line!r}"
    )

    consult_line = facts.split('CONSULT_REASSURANCE = "')[1].split('"')[0]
    assert " · " in consult_line
    assert "·" not in consult_line.replace(" · ", "")
    # `/check`의 CHECK_CTA_HINT와 같은 3항목 " · " 배지 형식으로 통일했는지.
    check_hint = facts.split('CHECK_CTA_HINT = "')[1].split('"')[0]
    assert consult_line.split(" · ")[0] == check_hint.split(" · ")[0] == "로그인"


def test_home_is_a_situation_router_not_a_single_feature_page():
    """메인은 기능 하나를 팔지 않는다 — 두 상황 카드가 첫 과업이다."""
    facts = LANDING_FACTS.read_text(encoding="utf-8")
    hero = HERO.read_text(encoding="utf-8")
    page = LANDING_PAGE.read_text(encoding="utf-8")

    assert 'HERO_HEADLINE = "학원을 알아볼 때도, 다니는 동안에도"' in facts
    assert "SituationSection" in page
    assert "GroundworkSection" in page
    # 옛 3시점 카드·단일 CTA 히어로로 되돌아가지 않았는지.
    assert "LIFECYCLE_STAGES" not in facts
    assert "WaitlistModal" not in page
    for const in (
        "HERO_BADGE",
        "HERO_HEADLINE",
        "HERO_HEADLINE_LINE2",
        "HERO_HEADLINE_MOBILE_LINES",
        "HERO_SUPPORT",
    ):
        assert const in hero, f"{const} not rendered by HeroSection"


def test_home_explains_the_service_around_the_situation_choice():
    """상황 선택 다음에 준비 중 기능 예고와 예시 화면이 오고, 근거는 맨 아래다."""
    page = LANDING_PAGE.read_text(encoding="utf-8")

    order = [
        page.index("<HeroSection"),
        page.index("<SituationSection"),
        page.index("<PlannedFeaturesSection"),
        page.index("<ServicePreviewSection"),
        page.index("<GroundworkSection"),
    ]
    assert order == sorted(order), f"main section order changed: {order}"
    assert "ServiceRoleSection" not in page
    assert "PrinciplesSection" not in page


def test_planned_features_are_marked_as_planned():
    """없는 기능을 현재형으로 단정하지 못하게 강제한다."""
    facts = LANDING_FACTS.read_text(encoding="utf-8")
    section = PLANNED_FEATURES_SECTION.read_text(encoding="utf-8")

    features_block = facts.split("export const PLANNED_FEATURES = [")[1].split(
        "] as const;"
    )[0]
    assert features_block.count("title:") == 2
    assert features_block.count("예정입니다.") == 2
    assert "추천해드립니다" not in features_block
    assert "보내드립니다" not in features_block
    assert "PLANNED_FEATURES" in section
    assert "PLANNED_BADGE_LABEL" in section
    assert 'tone="neutral"' in section


def test_service_preview_says_example_before_the_cards():
    """예시 고지가 카드보다 먼저 오고, 배지·Disclaimer·카드 3개가 남아 있는지."""
    facts = LANDING_FACTS.read_text(encoding="utf-8")
    section = SERVICE_PREVIEW_SECTION.read_text(encoding="utf-8")

    notice_at = section.index("PREVIEW_NOTICE")
    cards_at = section.index("EXAMPLE_ITEMS.map")
    assert notice_at < cards_at
    assert "AI 추천 예시" in section
    assert "Disclaimer" in section
    assert "PREVIEW_DISCLAIMER" in section

    items_block = facts.split("export const EXAMPLE_ITEMS = [")[1].split(
        "] as const;"
    )[0]
    assert items_block.count("rank:") == 3
    assert "OO수학학원" in items_block
    assert "△△영어학원" in items_block
    assert "□□국어학원" in items_block


def test_home_has_no_sticky_cta_bar():
    """분기 페이지에는 단일 행동이 없다 — 하단 고정 CTA가 가리킬 곳이 없다.
    (설명 주석에서 이름을 언급하는 것은 허용하고, 실제 렌더링 여부만 본다.)"""
    page = LANDING_PAGE.read_text(encoding="utf-8")
    assert "<StickyCtaBar" not in page
    assert '"./StickyCtaBar"' not in page


def test_two_situation_cards_link_to_the_right_pages_with_events():
    facts = LANDING_FACTS.read_text(encoding="utf-8")
    card = SITUATION_CARD.read_text(encoding="utf-8")

    assert 'id: "explore"' in facts
    assert 'id: "current"' in facts
    assert 'href: "/checklists"' in facts
    assert 'href: "/check"' in facts
    assert 'event: "home_explore_selected"' in facts
    # '다니는 중' 카드는 기존 home_check_clicked를 이어받는다 (지표 연속성).
    assert 'event: "home_check_clicked"' in facts
    # 세 번째 카드(옮기기 전)는 없다 — /checklists의 마지막 묶음이 그 맥락을 흡수했다.
    assert facts.count("ctaLabel:") == 2
    assert "TrackedLink" in card


def _strip_comments(text: str) -> str:
    """`/** ... */`·`// ...` 주석을 지운다. 되돌아오기 방지 가드가 '왜 뺐는지' 설명하는
    주석 자체를 위반으로 오탐하지 않게 하기 위해서다 — 실제 카피·코드만 검사한다."""
    without_block = re.sub(r"/\*[\s\S]*?\*/", "", text)
    return re.sub(r"//[^\n]*", "", without_block)


def test_no_dead_stage_vocabulary_remains():
    """되돌아오기 방지 가드: 3시점 카드·수량 프레이밍·근거 없는 새 약속이 다시 들어오지 않는지.
    (설명 주석 안에서 옛 이름을 언급하는 것은 허용하고, 실제 카피·코드만 본다.)"""
    banned_everywhere = RETIRED_STAGE_EVENTS
    banned_copy = ("체크리스트 3종", "영수증 인증", "인증 리뷰")

    for path in ALL_LANDING_FILES:
        code_only = _strip_comments(path.read_text(encoding="utf-8"))
        for banned in banned_everywhere:
            assert banned not in code_only, f"{banned} still referenced in {path.name}"
        for banned in banned_copy:
            assert banned not in code_only, f"{banned} still referenced in {path.name}"


def test_launch_status_notice_still_on_home_first_screen():
    """배지가 중립 문구로 바뀌어도 출시 전 사실은 첫 화면 어딘가에 남아야 한다."""
    facts = LANDING_FACTS.read_text(encoding="utf-8")
    assert "정식 출시 후" in facts.split("GROUNDWORK_BODY =")[1][:200]
    groundwork = GROUNDWORK_SECTION.read_text(encoding="utf-8")
    assert "GROUNDWORK_BODY" in groundwork


def test_kakao_reward_is_question_framed_not_a_count():
    """`3종`처럼 웰컴메시지와 어긋나기 쉬운 수량 약속 대신 '상담 질문'으로 통일한다."""
    facts = LANDING_FACTS.read_text(encoding="utf-8")
    modal = KAKAO_MODAL.read_text(encoding="utf-8")

    assert "상담" in facts.split("KAKAO_REWARD_NOTE =")[1][:200]
    assert "KAKAO_REWARD_LABEL" in GROUNDWORK_SECTION.read_text(encoding="utf-8")
    assert "체크리스트 3종" not in modal


def test_every_kakao_entry_point_goes_through_the_modal_first():
    """카카오로 나가기 전 보상·고지 팝업을 반드시 거치게 한다.
    외부로 실제로 나가는 링크(KakaoChannelLink)는 모달 안에만 있어야 한다 —
    호출부가 직접 쓰면 팝업을 건너뛰고 바로 외부로 나간다."""
    callers = [
        GROUNDWORK_SECTION,
        CHECKLISTS_PAGE,
        MINI_CHECK,
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

    # 점검 결과 경로만 별도 이벤트를 유지한다 (모달까지 그대로 전달되는지).
    cta = KAKAO_CTA.read_text(encoding="utf-8")
    assert "event" in cta
    assert 'event="checklist_kakao_clicked"' in MINI_CHECK.read_text(encoding="utf-8")


def test_consult_groups_reference_every_before_enroll_item_exactly_once():
    """설계안의 4묶음 매핑에서 빠졌던 '장기 학습 계획과 성장 방향'까지 포함해
    before-enroll 12항목을 정확히 한 번씩만 참조하는지 검사한다."""
    checklists_text = CHECKLIST_DATA.read_text(encoding="utf-8")

    enroll_block = re.search(
        r'id: "before-enroll".*?items: \[(.*?)\n    \],\n  \},\n  \{',
        checklists_text,
        re.DOTALL,
    )
    assert enroll_block is not None, "before-enroll block not found"
    enroll_titles = set(re.findall(r'title: "([^"]+)"', enroll_block.group(1)))
    assert len(enroll_titles) == 12, f"expected 12 before-enroll items, found {len(enroll_titles)}"

    consult_block = re.search(
        r"export const CONSULT_GROUPS: ConsultGroup\[\] = \[(.*?)\n\];",
        checklists_text,
        re.DOTALL,
    )
    assert consult_block is not None, "CONSULT_GROUPS not found"
    refs = re.findall(
        r'checklistId: "([a-z-]+)", itemTitle: "([^"]+)"', consult_block.group(1)
    )
    enroll_refs = [title for checklist_id, title in refs if checklist_id == "before-enroll"]
    switch_refs = [title for checklist_id, title in refs if checklist_id == "before-switch"]

    assert set(enroll_refs) == enroll_titles, (
        f"CONSULT_GROUPS before-enroll refs {set(enroll_refs)} != actual items {enroll_titles}"
    )
    assert len(enroll_refs) == 12, "each before-enroll item must be referenced exactly once"
    assert len(switch_refs) == 2, "이전 고민 묶음은 before-switch에서 2항목만 추가로 흡수한다"


def test_consult_group_refs_resolve_against_checklist_titles():
    """묶음이 참조하는 checklistId·title이 실제 CHECKLISTS 정본에 있는지(죽은 참조 방지)."""
    text = CHECKLIST_DATA.read_text(encoding="utf-8")

    checklist_blocks = dict(
        re.findall(
            r'id: "([a-z-]+)",[\s\S]*?items: \[([\s\S]*?)\n    \],\n  \}',
            text,
        )
    )
    assert set(checklist_blocks) >= {"before-enroll", "before-switch"}

    consult_block = re.search(
        r"export const CONSULT_GROUPS: ConsultGroup\[\] = \[(.*?)\n\];", text, re.DOTALL
    )
    assert consult_block is not None
    refs = re.findall(
        r'checklistId: "([a-z-]+)", itemTitle: "([^"]+)"', consult_block.group(1)
    )
    for checklist_id, item_title in refs:
        items_text = checklist_blocks[checklist_id]
        assert f'title: "{item_title}"' in items_text, (
            f'"{item_title}" not found in checklist "{checklist_id}"'
        )
    assert "resolveConsultGroups" in text


def test_checklist_items_are_numbered_continuously_across_the_whole_page():
    """광고가 '질문 12가지'라고 말하므로 번호는 묶음 안이 아니라 페이지 전체에서
    이어져야 한다 — page.tsx가 누적 오프셋을 계산해 ChecklistGroup에 넘기고,
    ChecklistGroup이 실제로 그 번호를 항목 앞에 렌더하는지 확인한다."""
    page = CHECKLISTS_PAGE.read_text(encoding="utf-8")
    group = CHECKLIST_GROUP.read_text(encoding="utf-8")

    assert "startIndex" in page, "page.tsx must compute a running offset per group"
    assert "startIndex={startIndexes[index]}" in page or "startIndex={" in page
    assert "startIndex" in group, "ChecklistGroup must accept the offset prop"
    assert re.search(r"startIndex\s*\+\s*itemIndex\s*\+\s*1", group), (
        "ChecklistGroup must render a page-wide item number, not a per-group one"
    )


def test_checklists_page_is_the_consult_landing_for_ad_a():
    page = CHECKLISTS_PAGE.read_text(encoding="utf-8")
    facts = LANDING_FACTS.read_text(encoding="utf-8")

    assert "resolveConsultGroups" in page
    assert "HeroSection" in page
    assert "CONSULT_KAKAO_CTA_LABEL" in page
    assert 'CONSULT_HEADLINE = "상담 전에 이 질문부터 챙기세요."' in facts
    # 광고 A → /checklists, 하단에서 /check로 교차 CTA.
    assert 'event="explore_check_clicked"' in page
    assert 'href="/check"' in page


def test_check_result_offers_consult_questions_before_home():
    """새 학원 탐색을 과하게 밀지 않되, 상담 준비 자료로는 이어준다."""
    mini = MINI_CHECK.read_text(encoding="utf-8")

    kakao_at = mini.index("checklist_kakao_clicked")
    consult_at = mini.index("check_explore_clicked")
    home_at = mini.index('href="/"')
    assert kakao_at < consult_at < home_at
    assert 'href="/checklists"' in mini


def test_new_funnel_events_exist_on_both_sides_of_the_wire():
    """프론트에서 보내는 이벤트를 백엔드가 422로 거절하지 않게, 양쪽 정본을 함께 검사한다."""
    types_ts = CLICK_EVENT_TYPES.read_text(encoding="utf-8")
    constants_py = CLICK_EVENT_ENUM.read_text(encoding="utf-8")

    for event in FUNNEL_EVENTS:
        assert f'"{event}"' in types_ts, f"{event} missing from ClickEventType"
        assert f'= "{event}"' in constants_py, f"{event} missing from ClickEvent"

    for event in RETIRED_STAGE_EVENTS:
        assert f'"{event}"' not in types_ts, f"retired event {event} still in ClickEventType"
        assert f'= "{event}"' not in constants_py, f"retired event {event} still in ClickEvent"


def test_home_metadata_reflects_the_two_situations():
    facts = LANDING_FACTS.read_text(encoding="utf-8")
    layout = LAYOUT.read_text(encoding="utf-8")

    assert "META_DESCRIPTION" in layout
    description = facts.split("META_DESCRIPTION =")[1][:300]
    assert "알아보는 중" in description
    assert "다니는 중" in description
    assert "정식 출시 후" in description
    # 푸터 고지는 메타로 대체되지 않고 그대로 남는다.
    assert "FOOTER_STATUS_COPY" in facts


def test_header_status_notice_sits_beside_the_logo():
    facts = LANDING_FACTS.read_text(encoding="utf-8")
    header = LANDING_HEADER.read_text(encoding="utf-8")

    assert "HEADER_STATUS_NOTICE" in header
    notice = facts.split('HEADER_STATUS_NOTICE =')[1][:400]
    assert "정식 운영" in notice
    assert "랜딩 페이지" in notice
    assert "중개" in notice
    assert "수강료" in notice
    # 배지 형태로 되돌리지 않는다.
    assert "Badge" not in header


def test_intro_pages_share_site_chrome_and_sticky_kakao():
    """/`·`/check`·`/checklists`·`/privacy`가 같은 헤더·고정 카카오 바를 쓴다. `/app`은 제외."""
    for path in (LANDING_PAGE, CHECK_PAGE, CHECKLISTS_PAGE, PRIVACY_PAGE):
        text = path.read_text(encoding="utf-8")
        assert "SiteChrome" in text, f"{path.name} is missing SiteChrome"
        assert "<LandingHeader" not in text, f"{path.name} still mounts header directly"
        assert "<LandingFooter" not in text, f"{path.name} still mounts footer directly"

    chrome = SITE_CHROME.read_text(encoding="utf-8")
    assert "LandingHeader" in chrome
    assert "LandingFooter" in chrome
    assert "StickyKakaoBar" in chrome

    bar = STICKY_KAKAO.read_text(encoding="utf-8")
    assert "KakaoChannelCta" in bar
    assert "FOOTER_KAKAO_CTA_LABEL" in bar
    assert "<KakaoChannelLink" not in bar
    assert "fixed" in bar
    # 모달 제목(KAKAO_REWARD_LABEL "상담 질문 받아보기")과 같은 프레이밍.
    facts_text = LANDING_FACTS.read_text(encoding="utf-8")
    assert "상담 질문" in facts_text.split("FOOTER_KAKAO_CTA_LABEL =")[1][:200]
    assert "출시 알림 받기" not in facts_text.split("FOOTER_KAKAO_CTA_LABEL =")[1][:200]


def test_funnel_pages_share_the_home_hero_copy():
    """화면 히어로는 홈과 같다. `/privacy`는 방침 h1을 유지한다."""
    checklists = CHECKLISTS_PAGE.read_text(encoding="utf-8")
    mini = MINI_CHECK.read_text(encoding="utf-8")
    privacy = PRIVACY_PAGE.read_text(encoding="utf-8")
    facts = LANDING_FACTS.read_text(encoding="utf-8")

    assert "HeroSection" in checklists
    assert "CONSULT_HEADLINE" not in checklists
    assert "HeroSection" in mini
    assert "CHECK_INTRO_HEADLINE" not in mini
    assert 'HERO_HEADLINE = "학원을 알아볼 때도, 다니는 동안에도"' in facts
    assert "개인정보처리방침" in privacy
    assert "HeroSection" not in privacy


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
