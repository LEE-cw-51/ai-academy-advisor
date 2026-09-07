"""/app 탐색 흐름 카피·계약이 2026-08-21 제품 언어와 어긋나지 않는지 검사한다."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
APP = REPO_ROOT / "frontend" / "src" / "components" / "app"
LIB = REPO_ROOT / "frontend" / "src" / "lib"
LANDING_FOOTER = (
    REPO_ROOT / "frontend" / "src" / "components" / "landing" / "LandingFooter.tsx"
)
LANDING_FACTS = (
    REPO_ROOT / "frontend" / "src" / "components" / "landing" / "landingFacts.ts"
)

CHAT_PANEL = APP / "ChatPanel.tsx"
REC_CARD = APP / "RecommendationCard.tsx"
APP_SHELL = APP / "AppShell.tsx"
EXPLORE_COPY = APP / "exploreCopy.ts"
DETAIL_MODAL = APP / "AcademyDetailModal.tsx"
API_TS = LIB / "api.ts"
TYPES_TS = LIB / "types.ts"

BANNED_RESULT_COPY = (
    "확정 추천",
    "가장 맞는 학원",
    "교육비 대비 우수",
    "AI 학원 추천",
)


def test_explore_submit_calls_consultation_and_ai_recs_in_parallel():
    chat = CHAT_PANEL.read_text(encoding="utf-8")
    api = API_TS.read_text(encoding="utf-8")

    assert "requestConsultationQuestions" in chat
    assert "requestAiRecommendations" in chat
    assert "Promise.allSettled" in chat
    assert "/consultation/questions" in api
    assert "/recommendations/ai" in api
    # used_fallback은 응답 필드일 뿐 — 에러 분기에 쓰이면 안 된다 (주석은 허용).
    assert "if (questionsResult.value.used_fallback" not in chat
    assert "questionsResult.value.used_fallback ?" not in chat
    assert "used_fallback" in TYPES_TS.read_text(encoding="utf-8")


def test_explore_clears_stale_candidates_before_request():
    chat = CHAT_PANEL.read_text(encoding="utf-8")
    run_query = chat.split("async function runQuery()", 1)[1]
    before_request, _, after_request = run_query.partition("Promise.allSettled")

    assert "onResults([])" in before_request
    assert "onSelectAcademy(null)" in after_request
    assert "onSelectAcademy(null)" in chat


def test_explore_copy_uses_candidate_not_recommendation_language():
    copy = EXPLORE_COPY.read_text(encoding="utf-8")
    card = REC_CARD.read_text(encoding="utf-8")
    chat = CHAT_PANEL.read_text(encoding="utf-8")
    shell = APP_SHELL.read_text(encoding="utf-8")

    assert 'CANDIDATE_BADGE = "후보 정보"' in copy
    assert 'WHY_CANDIDATE_HEADING = "왜 이 후보를 보여드렸나요?"' in copy
    assert 'ASK_AT_CONSULTATION_HEADING = "상담에서 확인할 점"' in copy
    assert 'UNCONFIRMED_HEADING = "미확인"' in copy
    assert "CANDIDATE_BADGE" in card
    assert "WHY_CANDIDATE_HEADING" in card
    assert "ASK_AT_CONSULTATION_HEADING" in card
    assert "UNCONFIRMED_HEADING" in card
    assert "QUESTIONS_HEADING" in chat
    assert "CANDIDATES_HEADING" in chat

    for banned in BANNED_RESULT_COPY:
        for path, text in (
            ("exploreCopy.ts", copy),
            ("RecommendationCard.tsx", card),
            ("ChatPanel.tsx", chat),
            ("AppShell.tsx", shell),
        ):
            assert banned not in text, f"{banned!r} found in {path}"


def test_score_is_not_rendered_as_stars_percent_or_trust():
    app_files = [
        CHAT_PANEL,
        REC_CARD,
        APP_SHELL,
        EXPLORE_COPY,
        DETAIL_MODAL,
        APP / "MapPanel.tsx",
    ]
    for path in app_files:
        text = path.read_text(encoding="utf-8")
        assert "item.score" not in text, f"score rendered in {path.name}"
        assert "별점" not in text
        assert "신뢰도" not in text
        assert "evidence_reviews[0].rating" not in text
        assert "review.rating" not in text


def test_app_shell_chrome_does_not_block_explore_as_coming_soon():
    shell = APP_SHELL.read_text(encoding="utf-8")
    copy = EXPLORE_COPY.read_text(encoding="utf-8")

    assert "출시 준비 중" not in shell
    assert "APP_NO_BROKERAGE" in shell
    assert "중개" in copy
    assert "예약" in copy
    assert "결제" in copy


def test_landing_keeps_funnel_ctas_and_adds_minimum_app_entry():
    """상황 카드는 /checklists·/check 유지. /app 진입은 푸터 링크만."""
    facts = LANDING_FACTS.read_text(encoding="utf-8")
    footer = LANDING_FOOTER.read_text(encoding="utf-8")

    assert 'href: "/checklists"' in facts
    assert 'href: "/check"' in facts
    assert 'href: "/app"' not in facts
    assert 'href="/app"' in footer
    assert "APP_EXPLORE_LINK_LABEL" in footer
    assert "APP_EXPLORE_LINK_LABEL" in facts
    assert "daangn" not in footer.lower()


def test_consultation_form_maps_required_api_fields():
    chat = CHAT_PANEL.read_text(encoding="utf-8")
    copy = EXPLORE_COPY.read_text(encoding="utf-8")
    modal = DETAIL_MODAL.read_text(encoding="utf-8")
    for field in (
        "grade",
        "subject",
        "school",
        "current_academy",
        "style_tags",
        "concern",
        "intent",
    ):
        assert field in chat
    for intent in ("counsel_only", "find_new_academy"):
        assert intent in copy
    assert "INTENTS" in chat
    assert "ASK_AT_CONSULTATION_HEADING" in modal
    assert "UNCONFIRMED_VALUE" in modal
    assert "trackEvent" in chat


def test_app_shell_keyword_search_uses_existing_academies_q():
    """검색창은 기존 GET /academies?q=만 쓴다 — 새 엔드포인트·별도 검색 API 금지."""
    shell = APP_SHELL.read_text(encoding="utf-8")
    copy = EXPLORE_COPY.read_text(encoding="utf-8")
    api = API_TS.read_text(encoding="utf-8")

    assert "SEARCH_PLACEHOLDER" in shell
    assert "SEARCH_CLEAR_LABEL" in shell
    assert "SEARCH_NO_RESULTS" in shell
    assert "searchResultCount" in shell  # total 기반 "검색 결과 N개 학원"
    assert "fetchAllAcademies" in shell

    assert 'SEARCH_CLEAR_LABEL = "전체 보기"' in copy
    assert "검색 결과 ${total}개 학원" in copy

    # 검색 전용 신규 엔드포인트를 만들지 않았는지 — /academies만 사용.
    assert "/academies" in api
    assert "/search" not in api
