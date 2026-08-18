"""랜딩 카피의 실측 숫자가 data/academies 정본과 어긋나지 않는지 검사한다."""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ACADEMIES = REPO_ROOT / "data" / "academies"
LANDING = (
    REPO_ROOT / "frontend" / "src" / "components" / "landing"
)
LANDING_FACTS = LANDING / "landingFacts.ts"
HERO = LANDING / "HeroSection.tsx"
STICKY = LANDING / "StickyCtaBar.tsx"
CHECK_CTA = LANDING / "CheckCtaLink.tsx"


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


def test_home_check_cta_points_to_check_and_tracks_home_check_clicked():
    link = CHECK_CTA.read_text(encoding="utf-8")
    facts = LANDING_FACTS.read_text(encoding="utf-8")
    hero = HERO.read_text(encoding="utf-8")
    sticky = STICKY.read_text(encoding="utf-8")

    assert 'href="/check"' in link
    assert "home_check_clicked" in link
    assert 'HOME_CHECK_CTA_LABEL = "1분 학원 점검 시작하기"' in facts
    assert "HOME_CHECK_REASSURANCE" in facts
    assert "STICKY_CHECK_REASSURANCE" in facts
    assert "CheckCtaLink" in hero
    assert "CheckCtaLink" in sticky
    assert "CTA_REASSURANCE" not in sticky
    assert "inert" in sticky
    assert "aria-hidden" in sticky
    assert "tabIndex" in sticky


def test_hero_secondary_cta_still_opens_waitlist():
    hero = HERO.read_text(encoding="utf-8")
    link = CHECK_CTA.read_text(encoding="utf-8")
    mini = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "components"
        / "check"
        / "MiniAcademyCheck.tsx"
    ).read_text(encoding="utf-8")

    assert "WAITLIST_CTA_LABEL" in hero
    assert "onClick={onRequestWaitlist}" in hero
    assert "CheckCtaLink" in hero
    assert 'event: "home_check_clicked"' in link
    assert 'event: "mini_check_started"' in mini
    assert 'event: "home_check_clicked"' not in mini


def test_check_cta_does_not_latch_modified_clicks():
    link = CHECK_CTA.read_text(encoding="utf-8")
    modified_at = link.index("if (modified)")
    latch_at = link.index("trackedRef.current = true")
    assert "event.metaKey" in link
    assert "event.ctrlKey" in link
    assert modified_at < latch_at
    assert "return;" in link[modified_at:latch_at]


def test_home_lifecycle_stages_not_feature_nouns():
    facts = LANDING_FACTS.read_text(encoding="utf-8")
    section = (LANDING / "PlannedFeaturesSection.tsx").read_text(encoding="utf-8")
    footer = (LANDING / "LandingFooter.tsx").read_text(encoding="utf-8")

    assert 'LIFECYCLE_SECTION_HEADING = "학원을 고를 때, 다닐 때, 옮길 때"' in facts
    assert 'title: "등록 전"' in facts
    assert 'title: "다니는 중"' in facts
    assert 'title: "옮기기 전"' in facts
    assert "LIFECYCLE_STAGES" in section
    assert "맞춤 학원 추천" not in facts
    assert "학원 정보 비교" not in facts
    assert "상담 연결" not in facts
    assert "FOOTER_STATUS_COPY" in footer
    assert "등록 전 맞춤 추천은 정식 출시 후" in facts
    assert "상담 연결은 정식 출시 후" not in footer
