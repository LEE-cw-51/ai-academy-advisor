"""/app 탐색 흐름 카피·계약이 2026-08-21 제품 언어·2026-09-08 표현 원칙·2026-09-13 첫 MVP
제품 정의와 어긋나지 않는지 검사한다.

표현 원칙(docs/decision-log.md 2026-09-08 · 2026-09-13): 검색창은 학원명·주소·전화만
약속한다, 카드는 이름 → 배지 → 왜 이 후보인지 → 확인일 → 다음 행동이고 근거는 토글 뒤,
태그는 상담 질문 힌트일 뿐 후보 조건이 아니다.
한 흐름(2026-09-13): 상황 입력 → 후보 → 상담 질문 → 후보 위치. 제출·검색 전에는 지도를
그리지 않는다(대기 모드 없음). 키워드 검색은 '이미 알고 있는 학원 찾기' 토글 뒤의 보조다.
마운트 시 전체 fetch 없음, 짧은 폼·글자 제출, 제출 후 조건 요약으로 접기는 그대로다.
"""

import re
from pathlib import Path

from tests.source_slice import slice_between

REPO_ROOT = Path(__file__).resolve().parents[1]
APP = REPO_ROOT / "frontend" / "src" / "components" / "app"
LIB = REPO_ROOT / "frontend" / "src" / "lib"
LANDING_FOOTER = (
    REPO_ROOT / "frontend" / "src" / "components" / "landing" / "LandingFooter.tsx"
)
LANDING_FACTS = (
    REPO_ROOT / "frontend" / "src" / "components" / "landing" / "landingFacts.ts"
)
LANDING_PAGE = (
    REPO_ROOT / "frontend" / "src" / "components" / "landing" / "LandingPage.tsx"
)

CHAT_PANEL = APP / "ChatPanel.tsx"
REC_CARD = APP / "RecommendationCard.tsx"
APP_SHELL = APP / "AppShell.tsx"
EXPLORE_COPY = APP / "exploreCopy.ts"
DETAIL_MODAL = APP / "AcademyDetailModal.tsx"
MAP_PANEL = APP / "MapPanel.tsx"
APP_PAGE = REPO_ROOT / "frontend" / "src" / "app" / "app" / "page.tsx"
API_TS = LIB / "api.ts"
TYPES_TS = LIB / "types.ts"

BANNED_RESULT_COPY = (
    "확정 추천",
    "가장 맞는 학원",
    "교육비 대비 우수",
    "AI 학원 추천",
    # 2026-09-13 — 순위·적합성 확정·출시 후 약속도 학부모 화면에 두지 않는다.
    "AI 추천",
    "1순위",
    "2순위",
    "3순위",
    "우리 아이에게 맞는",
    "정식 출시 후 제공",
)


def _strip_comments(text: str) -> str:
    """`/** ... */`·`// ...` 주석을 지운다. exploreCopy 머리말처럼 '무엇을 쓰지 않는지'
    설명하는 주석(확정 추천·별점…)을 위반으로 오탐하지 않게 — 실제 카피·코드만 검사한다.
    tests/test_landing_copy.py 의 것과 같다 (테스트 모듈끼리는 import하지 않는다)."""
    without_block = re.sub(r"/\*[\s\S]*?\*/", "", text)
    return re.sub(r"//[^\n]*", "", without_block)


def component_jsx(chat: str) -> str:
    """ChatPanel 컴포넌트 자신의 렌더 트리.

    `chat.split("return (")[1]` 은 안 된다 — 파일의 첫 `return (` 는 이제
    conditionsChanged useMemo 안이라 앵커가 어긋나고, 오른쪽이 EOF 까지 열려
    보조 컴포넌트(FilterRow·ChangedConditionsNotice)까지 삼킨다.
    들여쓰기로 컴포넌트 자신의 return 을 집고 보조 컴포넌트 앞에서 끊는다.
    """
    return slice_between(chat, "\n  return (", "\nfunction FilterRow")


def card_open_tag(source: str) -> str:
    """`<Card ... >` 여는 태그의 props 부분.

    두 호출부의 들여쓰기가 달라 고정 문자열로는 경계를 못 준다. 닫는 `>` 는
    화살표 함수(`=>`)와 구분해야 하므로 줄 시작의 `>` 만 잡는다.
    """
    match = re.search(r"<Card\b(.*?)\n\s*>", source, re.S)
    assert match, "Card 여는 태그를 찾지 못했다"
    return match.group(1)


def rec_card_jsx(card: str) -> str:
    """RecommendationCard 컴포넌트 자신의 렌더 트리.

    `card.split("return (", 1)[1]` 은 EOF 까지 열려 CardSection 정의의
    showEmpty 기본값 등을 삼킨다.
    """
    return slice_between(card, "\n  return (", "\n}\n\nfunction CardSection")


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
    map_panel = MAP_PANEL.read_text(encoding="utf-8")
    modal = DETAIL_MODAL.read_text(encoding="utf-8")

    assert 'CANDIDATES_HEADING = "지금 조건으로 확인해 볼 후보예요"' in copy
    assert 'SUBMIT_LABEL = "후보와 질문 정리하기"' in copy
    assert 'WHY_CANDIDATE_HEADING = "왜 이 후보를 보여드렸나요?"' in copy
    assert 'ASK_AT_CONSULTATION_HEADING = "상담에서 확인할 점"' in copy
    assert 'UNVERIFIED_FIELDS_LABEL = "아직 확인하지 못한 항목"' in copy
    # 신뢰 문구는 랜딩(`/`)과 `/app`이 같은 상수를 쓴다 — 두 모듈에 복제하지 않는다.
    assert "TRUST_NOTE" in copy
    assert "TRUST_NOTE" in chat
    assert "WHY_CANDIDATE_HEADING" in card
    assert "QUESTIONS_HEADING" in chat
    assert "CANDIDATES_HEADING" in chat
    assert "SUBJECT_FORM_HELPER" in chat
    assert "SUBJECT_HELPER" in chat

    # 주석은 뺀다 — exploreCopy 머리말이 '확정 추천을 쓰지 않는다'고 적는 것은 위반이 아니다.
    for banned in BANNED_RESULT_COPY:
        for path, text in (
            ("exploreCopy.ts", copy),
            ("RecommendationCard.tsx", card),
            ("ChatPanel.tsx", chat),
            ("AppShell.tsx", shell),
            ("MapPanel.tsx", map_panel),
            ("AcademyDetailModal.tsx", modal),
        ):
            assert banned not in _strip_comments(text), f"{banned!r} found in {path}"


def test_subject_detail_input_and_badges():
    """국/영/수 외엔 "기타"를 고른 뒤 실제 과목을 적고, 배지는 그 이름으로 보인다."""
    chat = CHAT_PANEL.read_text(encoding="utf-8")
    copy = EXPLORE_COPY.read_text(encoding="utf-8")
    card = REC_CARD.read_text(encoding="utf-8")
    map_panel = (APP / "MapPanel.tsx").read_text(encoding="utf-8")
    modal = DETAIL_MODAL.read_text(encoding="utf-8")
    types = TYPES_TS.read_text(encoding="utf-8")

    assert "export function subjectBadges" in copy
    assert "SUBJECT_DETAIL_PLACEHOLDER" in copy
    # "기타" 선택 시에만 실제 과목 입력이 뜬다.
    assert 'subject === "기타"' in chat
    assert "SUBJECT_DETAIL_PLACEHOLDER" in chat
    assert "setSubjectDetail" in chat
    # 세부 라벨 placeholder 는 "예)" 로 시작하지 않는다 (고민 예시 테스트와 충돌 방지).
    detail_placeholder = next(
        line for line in copy.splitlines() if "SUBJECT_DETAIL_PLACEHOLDER =" in line
    )
    assert '"예)' not in detail_placeholder
    # 배지는 세 화면 모두 subjectBadges 로 "기타"→세부 라벨 치환.
    assert "subjectBadges(academy.subjects, academy.subject_detail)" in card
    assert "subjectBadges(a.subjects, a.subject_detail)" in map_panel
    assert "subjectBadges(detail.subjects, detail.subject_detail)" in modal
    assert "subject_detail" in types


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
        # 주석은 뺀다 — exploreCopy 머리말은 '별점을 쓰지 않는다'고 적는다.
        text = _strip_comments(path.read_text(encoding="utf-8"))
        assert "item.score" not in text, f"score rendered in {path.name}"
        assert "별점" not in text, f"별점 in {path.name}"
        assert "신뢰도" not in text, f"신뢰도 in {path.name}"
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


def test_landing_hero_is_the_only_entry_to_app():
    """메인 주 CTA 는 `/app`(2026-09-13). 상황 카드(/checklists·/check 보조 퍼널)는
    2026-09-14에 퇴역했다 — 알아보는 중·다니는 중 두 상황 모두 `/app`의 상황 선택이 받는다.
    푸터에는 `/app` 링크를 두지 않는다 — 주 CTA는 히어로 하나로 충분하다."""
    facts = LANDING_FACTS.read_text(encoding="utf-8")
    page = LANDING_PAGE.read_text(encoding="utf-8")
    footer = LANDING_FOOTER.read_text(encoding="utf-8")

    assert 'HOME_CTA_HREF = "/app"' in facts
    assert 'HOME_CTA_LABEL = "후보와 질문 정리하기"' in facts
    assert 'href: "/checklists"' not in facts
    assert 'href: "/check"' not in facts
    assert "href={HOME_CTA_HREF}" in page
    assert "HOME_CTA_LABEL" in page
    assert 'href="/app"' not in footer
    assert "APP_EXPLORE_LINK_LABEL" not in footer
    assert "APP_EXPLORE_LINK_LABEL" not in facts
    assert "daangn" not in footer.lower()
    assert "AI 학원 추천" not in footer


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
    # onActivate = 마우스 + Enter/Space (Card 가 role·tabIndex 를 붙인다).
    assert "onActivate={() => onOpenDetail(a.id)}" in map_panel
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


def test_candidate_card_reads_why_then_verified_then_actions():
    """카드 첫 화면은 이름 → 과목 배지 → 왜 이 후보인지 → 확인일 → 다음 행동(전화·길찾기)
    (2026-09-13). 확인된 조건·다른 점·리뷰 스니펫은 '근거 더 보기' 토글 뒤에 둔다 —
    투명성 필드는 계속 그리되 첫 시선을 차지하지 않게. '후보 정보' 배지·미확인 나열·
    고정 3문항은 카드에 두지 않는다 (왼쪽 상담 질문·상세 모달과 중복)."""
    card = REC_CARD.read_text(encoding="utf-8")
    map_panel = MAP_PANEL.read_text(encoding="utf-8")

    # 토글 state 가 있으니 클라이언트 컴포넌트다 — BOM 없이 첫 줄.
    assert card.startswith('"use client"')

    jsx = rec_card_jsx(card)
    badges_at = jsx.index("subjects.map")  # 과목 배지 (있을 때만)
    reason_at = jsx.index("WHY_CANDIDATE_HEADING")
    verified_at = jsx.index("VERIFIED_AT_LABEL")
    actions_at = jsx.index('onTrack?.("phone")')
    assert badges_at < reason_at < verified_at < actions_at

    # 근거 토글 — 접근성 상태·라벨과, 그 뒤에 남는 투명성 필드.
    assert "aria-expanded" in jsx
    assert "EVIDENCE_TOGGLE_LABEL" in jsx
    # 토글·행 표시는 원본 키 배열이 아니라 conditionLabel 을 거친 라벨 배열로 판단한다 —
    # 모르는 키만 있으면 "확인된 조건:" 뒤가 비는 채로 토글이 열리기 때문이다.
    assert "matchedLabels" in jsx
    assert "conflictLabels" in jsx
    assert "matched_conditions.map(conditionLabel)" in card
    assert "conflicts.map(conditionLabel)" in card
    assert "REVIEW_EVIDENCE_HEADING" in jsx

    assert "unknown_conditions" not in jsx
    assert "CANDIDATE_BADGE" not in card
    assert "ASK_AT_CONSULTATION_HEADING" not in card
    assert "ASK_AT_CONSULTATION_ITEMS" not in card
    # 확인된 과목이 있는 행만 배지 — 지도 목록도 같은 규칙.
    assert "a.subjects" in map_panel


def test_card_separates_name_signals_from_registered_facts():
    """학원 이름에만 과목이 보이는 경우(백엔드 `subject_name`)는 등록 정보가 아니다.
    카드는 '등록 정보와 맞는 조건'과 '학원 이름에서 추정한 신호'를 다른 줄로 적고,
    한 키가 두 사전에 동시에 있지 않다 (Phase 5c 1개월차: 사실·탐색 신호·미확인 구분,
    docs/decisions/2026-09-19-round1-engineering-scope.md)."""
    copy = EXPLORE_COPY.read_text(encoding="utf-8")
    card = REC_CARD.read_text(encoding="utf-8")

    assert 'MATCHED_CONDITIONS_LABEL = "등록 정보와 맞는 조건"' in copy
    assert 'NAME_SIGNAL_LABEL = "학원 이름에서 추정한 신호"' in copy
    helper = slice_between(copy, "NAME_SIGNAL_HELPER =", ";")
    assert "확인된 것은 아니" in helper

    conditions = copy.split("CONDITION_LABELS: Record<string, string> = {", 1)[1].split(
        "};", 1
    )[0]
    signals = copy.split("SIGNAL_LABELS: Record<string, string> = {", 1)[1].split(
        "};", 1
    )[0]
    assert "subject_name" in signals
    assert "subject_name" not in conditions
    condition_keys = set(re.findall(r"^\s*(\w+):", conditions, re.M))
    signal_keys = set(re.findall(r"^\s*(\w+):", signals, re.M))
    assert signal_keys and condition_keys.isdisjoint(signal_keys)
    # 모르는 키는 raw 로 새지 않는다 — conditionLabel 과 같은 원칙.
    fn = slice_between(copy, "export function signalLabel", "\n}")
    assert '?? ""' in fn
    assert "?? key" not in fn

    assert "matched_conditions.map(signalLabel)" in card
    assert "signalLabels" in slice_between(card, "const hasEvidence =", ";")
    jsx = rec_card_jsx(card)
    assert jsx.index("MATCHED_CONDITIONS_LABEL") < jsx.index("NAME_SIGNAL_LABEL")
    assert "NAME_SIGNAL_HELPER" in jsx
    # 사실 줄과 신호 줄은 서로 다른 <p> 다 — 한 문장에 이어 붙이지 않는다.
    between = jsx.split("MATCHED_CONDITIONS_LABEL", 1)[1].split("NAME_SIGNAL_LABEL", 1)[0]
    assert "</p>" in between


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
    # 태그는 계속 상담 질문에만 간다. 이제 제출 스냅샷을 거쳐 가므로 화면 요약과
    # 실제로 보낸 값이 같은 객체에서 나온다.
    assert "style_tags: snapshot.tags" in chat
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
    # <dl> 로 경계를 준다 — EOF 까지 열어 두면 마지막 조각이 DetailRow 함수 정의
    # (showEmpty = false 기본값)를 삼켜, 진짜 행에서 showEmpty 를 지워도 통과한다.
    rows = slice_between(modal, "<dl", "</dl>")
    assert rows.count("showEmpty") == 1
    last_row = rows.split("<DetailRow")[-1]
    assert "정보 확인일" in last_row and "showEmpty" in last_row
    # 라벨과 null 판정은 factRows 한 곳에서만 나온다 — 두 벌로 들고 있으면
    # 한쪽만 고쳤을 때 값이 있는 학원과 없는 학원을 다른 이름으로 부르게 된다.
    assert "factRows" in modal
    assert modal.count('"월 수강료"') == 1
    assert "factRows" in slice_between(modal, "const unverifiedFields", ";")
    assert "ASK_AT_CONSULTATION_ITEMS" in modal


def test_card_and_modal_do_not_render_source_note():
    """운영용 source_note는 학부모 화면(카드·상세 모달)에 그리지 않는다.

    확인일은 기존 last_verified_at / 정보 확인일 행만 남긴다. AI reason 가공은
    백엔드 몫이라 여기서 파싱하지 않는다.
    """
    modal = DETAIL_MODAL.read_text(encoding="utf-8")
    card = REC_CARD.read_text(encoding="utf-8")

    assert "source_note" not in modal
    assert "source_note" not in card
    assert "정보 확인일" in modal
    assert "last_verified_at" in modal


def test_subject_helpers_split_form_and_results():
    """과목 칩 아래는 폼 도움말, 배지 안내는 후보 결과 옆에만 둔다."""
    chat = CHAT_PANEL.read_text(encoding="utf-8")
    copy = EXPLORE_COPY.read_text(encoding="utf-8")
    jsx = component_jsx(chat)

    assert "SUBJECT_FORM_HELPER" in copy
    assert "선택한 과목은 상담 질문과 후보 정리에 쓰여요" in copy

    form_block = jsx.split('label="과목"', 1)[1].split("explore-concern", 1)[0]
    assert "SUBJECT_FORM_HELPER" in form_block
    assert "SUBJECT_HELPER" not in form_block

    candidates_block = jsx.split("{CANDIDATES_HEADING}", 1)[1].split(
        "items.map", 1
    )[0]
    assert "SUBJECT_HELPER" in candidates_block


def test_results_show_candidates_before_questions():
    """결과는 후보 → 상담 질문 순 (2026-09-13). 후보가 주 산출물이고 질문은 그 후보와
    함께 들고 갈 것이라 뒤에 온다. 후보 5건은 백엔드에 그대로 청하고 화면에서 자르지
    않는다. 옛 EMPTY_RESULTS 는 NO_CANDIDATES(+검색 힌트)로 대체됐다."""
    chat = CHAT_PANEL.read_text(encoding="utf-8")
    copy = EXPLORE_COPY.read_text(encoding="utf-8")
    jsx = component_jsx(chat)

    assert jsx.index("{CANDIDATES_HEADING}") < jsx.index("{QUESTIONS_HEADING}")
    assert "requestAiRecommendations(trimmed, 5)" in chat
    assert "items.slice(" not in chat
    assert "EMPTY_RESULTS" not in chat
    assert "EMPTY_RESULTS" not in copy


def test_state_copy_is_user_facing_with_next_action():
    """로딩·실패·0건 문구는 학부모가 읽는 말이고 다음 행동이 바로 보인다. 'API 서버'·
    환경변수 같은 개발자 문장은 화면에 두지 않는다 (frontend/README.md 몫)."""
    copy = EXPLORE_COPY.read_text(encoding="utf-8")
    chat = CHAT_PANEL.read_text(encoding="utf-8")
    map_panel = MAP_PANEL.read_text(encoding="utf-8")

    assert "API 서버" not in copy
    assert 'RETRY_LABEL = "다시 보내기"' in copy
    assert 'LOADING_LABEL = "후보와 질문을 정리하는 중…"' in copy
    assert "NO_CANDIDATES" in copy
    assert "RETRY_LABEL" in chat
    assert "NO_CANDIDATES_SEARCH_HINT" in chat
    assert 'aria-live="polite"' in chat
    # 지도 키가 없거나 스크립트가 실패해도 목록·길찾기는 그대로 — 환경변수 안내는 주석까지만.
    assert "MAP_UNAVAILABLE" in map_panel
    assert "NEXT_PUBLIC_NAVER_MAP_CLIENT_ID를 설정하면" not in _strip_comments(map_panel)


def test_app_page_has_h1_and_title():
    """`/app`에도 h1 과 문서 제목이 있어야 한다 — 없으면 탭·공유·스크린리더가 페이지를
    이름 없이 만난다. 색인은 계속 막는다 (noindex)."""
    chat = CHAT_PANEL.read_text(encoding="utf-8")
    page = APP_PAGE.read_text(encoding="utf-8")

    assert '<h1 id="explore-heading"' in chat
    assert "FORM_HEADING" in chat
    assert "title:" in page
    assert "robots" in page
    assert "index: false" in page


def test_back_to_candidates_skips_full_list_refetch():
    """검색 해제(후보로 돌아가기·검색 지우기)는 GET /academies를 다시 치지 않는다."""
    shell = APP_SHELL.read_text(encoding="utf-8")
    fn = slice_between(
        shell, "const onSearchClear = useCallback(", "}, [recItems]);"
    )

    assert "nextCandidateSelectedId" in fn
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
    """제출 전 지도 없음 — 마운트 시 useEffect로 전체 GET /academies를 치지 않는다."""
    shell = APP_SHELL.read_text(encoding="utf-8")

    # useEffect 자체는 금지하지 않는다 — 포커스 관리·리사이즈처럼 정당한 용도가 있고,
    # 금지해 봐야 useLayoutEffect·데이터 훅으로 쓴 진짜 마운트 fetch 는 통과한다.
    # 실제 규칙: 목록 fetch 는 runSearch 안에서만, runSearch 는 제출 핸들러에서만.
    assert shell.count("fetchAllAcademies(") == 1  # import 줄은 괄호가 없다
    run_search = slice_between(
        shell, "const runSearch = useCallback(", "}, [recItems]);"
    )
    assert "fetchAllAcademies({ q })" in run_search
    assert run_search.index("if (!q)") < run_search.index("fetchAllAcademies")
    assert shell.count("void runSearch(") == 1
    submit = slice_between(
        shell,
        "const onSearchSubmit = useCallback(",
        "[runSearch, searchInput, onSearchClear],",
    )
    assert "void runSearch(searchInput)" in submit
    assert 'runSearch("")' not in shell
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


def test_explore_query_responses_are_sequence_guarded():
    """상황 제출 더블클릭·Enter 연타 뒤 늦게 온 응답이 상태를 덮으면 안 된다.

    AppShell searchSeq 와 같이 요청 시작 시 번호를 올리고, 반영·finally 전에 최신인지 본다.
    """
    chat = CHAT_PANEL.read_text(encoding="utf-8")

    assert "useRef" in chat
    assert "const querySeq = useRef(0)" in chat
    run_query = chat.split("async function runQuery()", 1)[1]
    assert "const seq = ++querySeq.current" in run_query
    assert "if (seq !== querySeq.current) return;" in run_query
    assert "if (seq === querySeq.current) setLoading(false);" in run_query


def test_condition_label_hides_unknown_backend_keys():
    """모르는 필터 키는 raw 로 새지 않는다 — `?? key` 폴백 금지."""
    copy = EXPLORE_COPY.read_text(encoding="utf-8")
    fn = slice_between(copy, "export function conditionLabel", "\n}")
    assert "?? key" not in fn
    assert '?? ""' in fn


def test_short_form_hides_optional_fields_and_shows_text_submit():
    """필수(상황·학년·과목·고민)+글자 제출. 학교·학원·태그는 더 알려주기. 지역 행 없음."""
    chat = CHAT_PANEL.read_text(encoding="utf-8")
    copy = EXPLORE_COPY.read_text(encoding="utf-8")
    jsx = component_jsx(chat)

    assert 'SUBMIT_LABEL = "후보와 질문 정리하기"' in copy
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
    assert "setSubmitted(snapshot)" in run_query
    assert "const hasSubmitted = submitted !== null" in chat


def test_condition_summary_reads_submitted_snapshot_not_live_form():
    """요약 칩은 제출 시점 조건만 적는다. 폼만 바꾸고 다시 보내지 않았는데 칩이
    새 조건을 적으면, 아래 질문·후보가 어떤 조건에서 나온 사실인지 잘못 알린다."""
    chat = CHAT_PANEL.read_text(encoding="utf-8")

    assert "interface SubmittedConditions" in chat
    assert "useState<SubmittedConditions | null>(null)" in chat

    run_query = chat.split("async function runQuery()", 1)[1]
    before_request, _, _ = run_query.partition("Promise.allSettled")
    assert "const snapshot: SubmittedConditions = {" in before_request
    assert "setSubmitted(snapshot)" in before_request

    # 요약 본문은 스냅샷만 읽고, 의존성에 라이브 폼 state 가 없다.
    _, _, after = chat.partition("const conditionSummary = useMemo(")
    body, _, deps = after.partition("}, [")
    for field in ("submitted.intent", "submitted.grade", "submitted.subject"):
        assert field in body, field
    assert deps.startswith("submitted]);")


def test_changed_conditions_offer_resubmit_instead_of_silent_mismatch():
    """폼이 스냅샷과 달라지면 안내 + 다시 보내기. 접기만 하는 '질문·후보 보기'가
    새 조건을 요약에 적고 옛 결과를 아래 두는 상태를 만들면 안 된다."""
    chat = CHAT_PANEL.read_text(encoding="utf-8")
    copy = EXPLORE_COPY.read_text(encoding="utf-8")

    assert "조건이 바뀌었어요" in copy
    assert 'RESUBMIT_LABEL = "바뀐 조건으로 다시 보내기"' in copy
    assert "CONDITIONS_CHANGED_NOTE" in chat
    assert "RESUBMIT_LABEL" in chat

    # 요약에 안 보이는 학교·현재 학원·태그·고민도 결과를 바꾸므로 전부 비교한다.
    changed = chat.split("const conditionsChanged = useMemo(", 1)[1].split("}, [", 1)[0]
    for field in (
        "submitted.intent",
        "submitted.grade",
        "submitted.subject",
        "submitted.school",
        "submitted.currentAcademy",
        "submitted.note",
        "submitted.tags",
    ):
        assert field in changed, field

    # 접힌 요약과 펼친 폼 두 곳 모두에서 다시 보내기가 runQuery 를 다시 친다.
    assert chat.count("onResubmit={() => void runQuery()}") == 2
    # 안내 컴포넌트는 ChatPanel 뒤에 정의한다 (JSX 슬라이스 테스트 보호).
    assert chat.index("export function ChatPanel") < chat.index(
        "function ChangedConditionsNotice"
    )


def test_relaxed_banner_uses_sentences_not_backend_filter_keys():
    """완화 배너는 백엔드 필터 키(q·region)를 그대로 보여 주지 않는다. region 은
    폼에 없는 고정값(하남 미사)이라 키만 보면 사용자가 건 적 없는 조건이 튀어나온다."""
    chat = CHAT_PANEL.read_text(encoding="utf-8")
    copy = EXPLORE_COPY.read_text(encoding="utf-8")

    assert 'relaxed.join(", ")' not in chat
    assert "RELAXED_HEADING" in chat
    assert "relaxedNotes" in chat
    assert 'RELAXED_HEADING = "조건을 조금 넓혀 찾은 후보예요."' in copy

    notes = copy.split("RELAXED_NOTES: Record<string, string> = {", 1)[1].split(
        "};", 1
    )[0]
    assert "하남 미사" in notes
    assert "인근 지역" in notes
    assert "q:" in notes

    # 모르는 키는 문장이 없으면 버린다 — conditionLabel 의 `?? key` 폴백을 쓰지 않는다.
    # 슬라이스를 함수 본문으로 끊는다 — EOF 까지 열어 두면 아래 conditionLabel 의
    # `?? key` 를 잡아 이 단정문이 영원히 통과한다.
    fn = slice_between(copy, "export function relaxedNotes", "\n}")
    assert "?? key" not in fn
    assert "filter(" in fn

    # 배너는 키 배열을 직접 그리지 않는다.
    jsx = component_jsx(chat)
    banner = jsx.split("relaxed.length > 0", 1)[1].split("min-h-0 flex-1", 1)[0]
    assert "relaxed.map" not in banner
    assert "relaxed.join" not in banner

    # region 은 계속 쿼리에 넣는다(= /app 하남 미사 고정). 배너 문구로만 설명한다.
    assert 'const REGION = "하남 미사"' in chat
    assert "region: REGION" in chat


def test_empty_search_and_clear_share_candidate_pin_restore():
    """빈 검색과 '후보로 돌아가기'는 같은 핀 복원을 쓴다. !q 분기가
    무조건 setSelectedId(null)이면 후보는 보이는데 하이라이트만 빠진다."""
    shell = APP_SHELL.read_text(encoding="utf-8")

    helper = slice_between(shell, "function nextCandidateSelectedId(", "\n}")
    assert "recItems.length === 0" in helper
    assert "recItems[0]" in helper
    assert "setSelectedId(null)" not in helper

    empty_branch = slice_between(shell, "if (!q) {", "return;")
    assert "nextCandidateSelectedId" in empty_branch
    assert "setSelectedId(null)" not in empty_branch

    clear = slice_between(
        shell, "const onSearchClear = useCallback(", "}, [recItems]);"
    )
    assert "nextCandidateSelectedId" in clear

    submit = slice_between(
        shell,
        "const onSearchSubmit = useCallback(",
        "[runSearch, searchInput, onSearchClear],",
    )
    assert "onSearchClear()" in submit
    assert 'runSearch("")' not in shell


def test_map_renders_only_after_explore_or_search():
    """제출·검색 전에는 지도를 그리지 않는다 — 입력이 주인공이다 (2026-09-13).
    MapMode 는 candidates·search 둘뿐이고, 제출 뒤(로딩·후보 0건 포함) 검색 중이 아니면
    candidates 다. 후보 0건 안내는 MAP_EMPTY_CANDIDATES, 옛 대기 힌트(MAP_EMPTY_HINT ·
    '조건을 보내면…')는 없다. 키워드 검색창은 토글 뒤에 접혀 있다."""
    shell = APP_SHELL.read_text(encoding="utf-8")
    copy = EXPLORE_COPY.read_text(encoding="utf-8")

    assert 'type MapMode = "candidates" | "search"' in shell
    mode = slice_between(shell, "const mapMode: MapMode =", ";")
    assert "activeQuery" in mode
    assert "idle" not in mode
    assert "hasExplored" not in mode

    # 조건부 렌더 — 제출했거나 검색 중일 때만 MapPanel 이 트리에 올라간다.
    assert "hasExplored || activeQuery" in shell
    assert "<MapPanel" in shell
    # 후보 모드는 왼쪽 카드가 목록이라 지도 아래 목록을 감춘다.
    assert 'hideList={mapMode === "candidates"}' in shell
    assert "MAP_EMPTY_CANDIDATES" in shell
    assert "MAP_EMPTY_HINT" not in shell
    assert "MAP_HEADING_IDLE" not in shell
    assert "MAP_EMPTY_HINT" not in copy
    assert "조건을 보내면 후보 위치가 여기에 표시됩니다" not in copy

    # 키워드 검색은 토글 뒤의 보조 — 기본 화면에 검색창을 펼쳐 두지 않고,
    # 검색 해제가 토글도 닫는다.
    assert "SEARCH_MODE_LABEL" in shell
    assert "const [searchOpen, setSearchOpen] = useState(false)" in shell
    assert "aria-expanded={searchOpen}" in shell
    clear = slice_between(
        shell, "const onSearchClear = useCallback(", "}, [recItems]);"
    )
    assert "setSearchOpen(false)" in clear


def test_map_headings_distinguish_candidates_and_search():
    """지도는 제출·검색 뒤에만 그리므로 대기(idle) 헤딩은 없다 (2026-09-13). 남은 두 모드
    후보·검색은 헤딩이 서로 달라야 지금 지도가 무엇을 보여 주는지 읽힌다."""
    copy = EXPLORE_COPY.read_text(encoding="utf-8")

    assert 'MAP_HEADING_CANDIDATES = "후보 위치"' in copy
    assert 'MAP_HEADING_SEARCH = "검색 결과"' in copy
    assert "MAP_HEADING_IDLE" not in copy

    headings = {
        line.split("= ", 1)[1]
        for line in copy.splitlines()
        if line.startswith("export const MAP_HEADING_")
    }
    assert len(headings) == 2


def test_clickable_cards_are_keyboard_reachable():
    """카드 클릭이 선택·이동을 하면 키보드로도 닿아야 한다. Card 가 onActivate 를
    받으면 role·tabIndex·Enter/Space 를 한 번에 붙인다 — 호출부 복사 금지."""
    card = (REPO_ROOT / "frontend" / "src" / "components" / "ui" / "Card.tsx").read_text(
        encoding="utf-8"
    )
    map_panel = (APP / "MapPanel.tsx").read_text(encoding="utf-8")
    rec_card = REC_CARD.read_text(encoding="utf-8")

    assert "onActivate" in card
    assert 'role: "button"' in card
    assert "tabIndex: 0" in card
    assert '"Enter"' in card and '" "' in card
    # 중첩 버튼에서 올라온 키 이벤트로 카드까지 발화하면 안 된다.
    assert "event.target !== event.currentTarget" in card

    # 호출부는 접근성 속성을 직접 붙이지 않는다. 파일 전역에서 onKeyDown 을 막으면
    # 무관한 키보드 처리(목록 Escape 닫기 등)까지 걸리므로 <Card> 여는 태그만 본다.
    for name, source in (("MapPanel", map_panel), ("RecommendationCard", rec_card)):
        props = card_open_tag(source)
        assert "onActivate" in props, name
        assert 'role="button"' not in props, name
        assert "tabIndex" not in props, name
        assert "onKeyDown" not in props, name


def test_detail_event_is_tracked_once_at_the_shared_entry_point():
    """상세 모달 경로는 둘(후보 카드·지도 목록)이고 둘 다 AppShell.onOpenDetail 을
    지난다. 계측을 거기 두지 않으면 지도 경로가 통째로 빠져 퍼널이 과소 집계된다."""
    shell = APP_SHELL.read_text(encoding="utf-8")
    rec_card = REC_CARD.read_text(encoding="utf-8")

    open_detail = slice_between(
        shell, "const onOpenDetail = useCallback(", "}, ["
    )
    assert 'trackEventSafe(id, "detail")' in open_detail
    # 카드에 남겨 두면 카드 경로만 두 번 센다. 문자열 "detail" 자체를 막으면
    # variant="detail" 같은 무관한 쓰임까지 걸리므로 실제 호출 형태로 좁힌다.
    assert 'onTrack?.("detail")' not in rec_card
    assert 'onTrack?.("phone")' in rec_card
