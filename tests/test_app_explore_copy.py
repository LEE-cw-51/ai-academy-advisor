"""/app 탐색 흐름 카피·계약이 2026-08-21 제품 언어·2026-09-08 표현 원칙과 어긋나지 않는지 검사한다.

표현 원칙(docs/decision-log.md 2026-09-08): 검색창은 학원명·주소·전화만 약속한다,
카드는 사실 먼저·AI 이유는 나중, 태그는 상담 질문 힌트일 뿐 후보 조건이 아니다.
한 흐름: 마운트 시 전체 fetch 없음, 짧은 폼·글자 제출, 제출 후 조건 요약으로 접기.
"""

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
    assert 'UNVERIFIED_FIELDS_LABEL = "아직 확인하지 못한 항목"' in copy
    assert "CANDIDATE_BADGE" in card
    assert "WHY_CANDIDATE_HEADING" in card
    assert "QUESTIONS_HEADING" in chat
    assert "CANDIDATES_HEADING" in chat
    assert "SUBJECT_FORM_HELPER" in chat
    assert "SUBJECT_HELPER" in chat

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
    assert "SEARCH_HELPER" in shell
    assert "SEARCH_CLEAR_LABEL" in shell
    assert "BACK_TO_CANDIDATES_LABEL" in shell  # 검색이 후보 지도를 덮었을 때 복귀
    assert "searchNoResults" in shell
    assert "searchResultCount" in shell  # total 기반 "검색 결과 N개 학원"
    assert "fetchAllAcademies" in shell

    # 검색창 카피는 DB가 실제로 찾는 것(학원명·주소·전화)만 약속한다 — 과목 예시 금지.
    placeholder_line = next(
        line for line in copy.splitlines() if "SEARCH_PLACEHOLDER =" in line
    )
    assert "학원명·주소·전화" in placeholder_line
    for subject in ("국어", "영어", "수학", "과학"):
        assert subject not in placeholder_line
    clear_line = next(
        line for line in copy.splitlines() if "SEARCH_CLEAR_LABEL =" in line
    )
    # 제출 전 지도는 빈 상태라 검색 해제가 전체 디렉터리("전체 보기")를 약속하면 안 된다.
    assert "전체 보기" not in clear_line
    assert "SEARCH_CLEAR_LABEL" in copy
    assert "검색 결과 ${total}개 학원" in copy
    assert "학원명·주소·전화에 '${q}'" in copy
    assert "다시 검색해 보세요" not in copy

    # 검색 전용 신규 엔드포인트를 만들지 않았는지 — /academies만 사용.
    assert "/academies" in api
    assert "/search" not in api
    # 빈 q로 411곳을 올리지 않는다. 키워드가 있을 때만 fetch.
    assert 'runSearch("")' not in shell
    assert "fetchAllAcademies({ q })" in shell


def test_map_list_card_shows_phone_and_opens_canonical_detail():
    """지도 목록은 정본 전화만 보여주고, 카드 클릭은 GET /academies/{id} 상세 모달을 연다."""
    map_panel = (APP / "MapPanel.tsx").read_text(encoding="utf-8")
    shell = APP_SHELL.read_text(encoding="utf-8")
    chat = CHAT_PANEL.read_text(encoding="utf-8")
    modal = DETAIL_MODAL.read_text(encoding="utf-8")
    types = TYPES_TS.read_text(encoding="utf-8")
    api = API_TS.read_text(encoding="utf-8")

    assert "a.phone" in map_panel
    assert "onOpenDetail" in map_panel
    # 마커는 하이라이트만, 목록 카드가 상세를 연다.
    assert "onClick={() => onOpenDetail(a.id)}" in map_panel
    assert "website_url" not in map_panel
    assert "blog_url" not in map_panel

    assert "AcademyDetailModal" in shell
    assert "onOpenDetail" in shell
    assert "AcademyDetailModal" not in chat

    assert "fetchAcademyDetail" in modal
    assert "UNCONFIRMED_VALUE" in modal
    assert "`/academies/${academyId}`" in api

    summary, _, rest = types.partition("export interface AcademySummary")
    summary_block, _, detail_block = rest.partition("export interface AcademyDetail")
    assert "phone" in summary_block
    assert "website_url" not in summary_block
    assert "blog_url" not in summary_block
    assert "website_url" in detail_block
    assert "blog_url" in detail_block


def test_candidate_card_shows_facts_before_ai_reason():
    """카드는 이름 → 과목 배지 → 주소·전화 → 확인일 → AI 이유 순. 미확인 나열·고정 3문항은
    카드에 두지 않는다 (왼쪽 상담 질문·상세 모달과 중복)."""
    card = REC_CARD.read_text(encoding="utf-8")
    map_panel = (APP / "MapPanel.tsx").read_text(encoding="utf-8")

    jsx = card.split("return (", 1)[1]
    facts_at = jsx.index("subjects.map")  # 과목 배지 (있을 때만)
    verified_at = jsx.index("VERIFIED_AT_LABEL")
    reason_at = jsx.index("WHY_CANDIDATE_HEADING")
    assert facts_at < verified_at < reason_at

    assert "unknown_conditions" not in jsx
    assert "ASK_AT_CONSULTATION_HEADING" not in card
    assert "ASK_AT_CONSULTATION_ITEMS" not in card
    # 확인된 과목이 있는 행만 배지 — 지도 목록도 같은 규칙.
    assert "a.subjects" in map_panel


def test_style_tags_feed_consultation_questions_not_ai_query():
    """소수정예·선행 같은 태그는 후보 조건이 아니라 상담 질문 힌트다."""
    chat = CHAT_PANEL.read_text(encoding="utf-8")
    copy = EXPLORE_COPY.read_text(encoding="utf-8")

    build_query = (
        chat.split("function buildQuery", 1)[1]
        .split("}): string {", 1)[1]
        .split("return chunks.join", 1)[0]
    )
    assert "tags" not in build_query
    assert "style_tags: tags" in chat
    assert "TAGS_HELPER" in chat
    assert "후보를 거르는 조건은 아니에요" in copy


def test_detail_modal_groups_unverified_fields_into_one_line():
    """0% 필드(운영 시간·수강료·셔틀 등)는 행마다 '미확인' 대신 한 줄로 묶는다."""
    modal = DETAIL_MODAL.read_text(encoding="utf-8")

    assert "UNVERIFIED_FIELDS_LABEL" in modal
    assert "unverifiedFields" in modal
    for field in ("operating_hours", "tuition_monthly_fee", "shuttle_available"):
        assert field in modal
    # 정보 확인일만 빈 값을 행으로 남긴다.
    rows_with_empty = [
        block for block in modal.split("<DetailRow")[1:] if "showEmpty" in block
    ]
    assert len(rows_with_empty) == 1
    assert "source_note" in modal
    assert "ASK_AT_CONSULTATION_ITEMS" in modal


def test_subject_helpers_split_form_and_results():
    """과목 칩 아래는 폼 도움말, 배지 안내는 후보 결과 옆에만 둔다."""
    chat = CHAT_PANEL.read_text(encoding="utf-8")
    copy = EXPLORE_COPY.read_text(encoding="utf-8")
    jsx = chat.split("return (", 1)[1]

    assert "SUBJECT_FORM_HELPER" in copy
    assert "선택한 과목은 상담 질문과 후보 정리에 쓰여요" in copy

    form_block = jsx.split('label="과목"', 1)[1].split("explore-concern", 1)[0]
    assert "SUBJECT_FORM_HELPER" in form_block
    assert "SUBJECT_HELPER" not in form_block

    candidates_block = jsx.split("{CANDIDATES_HEADING}", 1)[1].split(
        "items.map", 1
    )[0]
    assert "SUBJECT_HELPER" in candidates_block


def test_back_to_candidates_skips_full_list_refetch():
    """검색 해제(후보로 돌아가기·검색 지우기)는 GET /academies를 다시 치지 않는다."""
    shell = APP_SHELL.read_text(encoding="utf-8")
    fn = shell.split("const onSearchClear", 1)[1].split("}, [", 1)[0]

    assert "recItems.length > 0" in fn
    assert 'setActiveQuery("")' in fn
    assert "runSearch" not in fn
    assert "fetchAllAcademies" not in fn


def test_concern_placeholder_does_not_seed_empty_filter_keywords():
    """필수 고민 예시가 내신·선행·소수정예 같은 빈 컬럼 키워드를 넣지 않는다."""
    chat = CHAT_PANEL.read_text(encoding="utf-8")
    placeholder_line = next(
        line
        for line in chat.splitlines()
        if 'placeholder="예)' in line and "학교" not in line
    )
    for banned in ("내신", "선행", "소수정예", "숙제"):
        assert banned not in placeholder_line
    assert "다시 검색해 보세요" not in EXPLORE_COPY.read_text(encoding="utf-8")


def test_app_stays_one_route_keyword_search_is_map_helper():
    """질문/검색 전용 라우트를 만들지 않는다. 키워드 검색은 지도 위 보조다."""
    app_pages = REPO_ROOT / "frontend" / "src" / "app"
    assert (app_pages / "app" / "page.tsx").exists()
    assert not (app_pages / "search").exists()
    assert not (app_pages / "questions").exists()

    shell = APP_SHELL.read_text(encoding="utf-8")
    # DOM 순서 = 모바일 순서: 상황 입력이 지도·검색보다 앞.
    assert shell.index("<ChatPanel") < shell.index("<MapPanel")
    assert "SEARCH_PLACEHOLDER" in shell
    assert "MAP_HEADING_CANDIDATES" in shell
    assert "BACK_TO_CANDIDATES_LABEL" in shell


def test_data_strategy_fill_priority_forbids_name_heuristics():
    """P0 채움은 Founder 검토 루프. 학원명으로 subjects를 추정하지 않는다."""
    text = (REPO_ROOT / "docs" / "data-strategy.md").read_text(encoding="utf-8")
    assert "### 채움 우선순위" in text
    assert "이름에 \"수학\"이 있어도 채우지 않음" in text
    assert "공개 쓰기 API 없음" in text
    assert "Founder가 **high** 행 검토" in text


def test_decision_log_records_expression_principles():
    """표현 원칙은 이미 2026-09-08 항목으로 남긴다. 새 날짜 항목이 위에 와도 본문은 유지."""
    text = (REPO_ROOT / "docs" / "decision-log.md").read_text(encoding="utf-8")
    assert "q는 신원 검색" in text
    assert "카드는 사실 우선" in text
    assert "태그는 상담 힌트" in text
    assert "이름 휴리스틱 금지" in text
    assert "한 흐름 레이아웃" in text
    assert "빈 지도" in text


def test_app_shell_does_not_fetch_all_academies_on_mount():
    """제출 전 빈 지도 — 마운트 시 useEffect로 전체 GET /academies를 치지 않는다."""
    shell = APP_SHELL.read_text(encoding="utf-8")
    copy = EXPLORE_COPY.read_text(encoding="utf-8")

    assert "useEffect" not in shell
    assert 'runSearch("")' not in shell
    assert "MAP_EMPTY_HINT" in shell
    assert "조건을 보내면 후보 위치가 여기에 표시됩니다" in copy
    assert "fetchAllAcademies({ q })" in shell


def test_search_responses_are_sequence_guarded():
    """검색 해제·연속 검색 뒤 늦게 온 응답이 상태를 덮으면 안 된다.

    fetchAllAcademies 응답을 쓰는 모든 경로(성공·실패·finally)와 해제 핸들러가
    같은 일련번호를 본다.
    """
    shell = APP_SHELL.read_text(encoding="utf-8")

    assert "useRef" in shell
    assert "const searchSeq = useRef(0)" in shell
    # 요청 시작 시 번호를 올리고, 응답 반영 전에 최신인지 확인한다.
    assert "const seq = ++searchSeq.current" in shell
    assert shell.count("if (seq !== searchSeq.current) return;") == 2
    assert "if (seq === searchSeq.current) setSearching(false);" in shell
    # 검색 해제도 진행 중인 요청을 무효화한다.
    assert "searchSeq.current += 1;" in shell.split("const onSearchClear", 1)[1]


def test_short_form_hides_optional_fields_and_shows_text_submit():
    """필수(상황·학년·과목·고민)+글자 제출. 학교·학원·태그는 더 알려주기. 지역 행 없음."""
    chat = CHAT_PANEL.read_text(encoding="utf-8")
    copy = EXPLORE_COPY.read_text(encoding="utf-8")
    jsx = chat.split("return (", 1)[1]

    assert 'SUBMIT_LABEL = "질문과 후보 정보 보기"' in copy
    assert "{loading ? LOADING_LABEL : SUBMIT_LABEL}" in chat
    assert "SendIcon" not in chat
    assert "aria-label={SUBMIT_LABEL}" not in chat

    assert "MORE_DETAILS_LABEL" in chat
    assert 'MORE_DETAILS_LABEL = "더 알려주기"' in copy
    assert "moreDetailsOpen" in chat
    assert 'label="지역"' not in jsx

    details_block = jsx.split("moreDetailsOpen", 1)[1]
    assert 'label="학교"' in details_block
    assert 'label="학원"' in details_block
    assert "TAGS_HEADING" in details_block
    main_form = jsx.split("moreDetailsOpen", 1)[0]
    assert 'label="학교"' not in main_form
    assert 'label="학원"' not in main_form
    assert 'label="상황"' in main_form
    assert 'label="학년"' in main_form
    assert 'label="과목"' in main_form


def test_form_collapses_to_summary_after_submit():
    """제출 후 조건 요약 + 조건 바꾸기. 질문·후보가 폼보다 앞에 보이게 접는다."""
    chat = CHAT_PANEL.read_text(encoding="utf-8")
    copy = EXPLORE_COPY.read_text(encoding="utf-8")

    assert 'EDIT_CONDITIONS_LABEL = "조건 바꾸기"' in copy
    assert "EDIT_CONDITIONS_LABEL" in chat
    assert "formExpanded" in chat
    assert "conditionSummary" in chat
    run_query = chat.split("async function runQuery()", 1)[1].split(
        "Promise.allSettled", 1
    )[0]
    assert "setFormExpanded(false)" in run_query
    assert "onExplored" in chat
