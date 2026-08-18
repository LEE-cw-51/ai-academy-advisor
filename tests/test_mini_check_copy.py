"""미니 점검·체크리스트 카피가 비지 않았는지 검사한다."""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CHECK_DATA = (
    REPO_ROOT / "frontend" / "src" / "components" / "check" / "checkData.ts"
)
CHECKLIST_DATA = (
    REPO_ROOT
    / "frontend"
    / "src"
    / "components"
    / "checklists"
    / "checklistsData.ts"
)
MINI_CHECK = (
    REPO_ROOT / "frontend" / "src" / "components" / "check" / "MiniAcademyCheck.tsx"
)

ANSWER_IDS = ("well", "sometimes", "needs_work", "unknown")
COUNSELING_PRIORITY = ("needs_work", "unknown", "sometimes", "well")


def _parse_counseling_prompts(text: str) -> list[dict[str, str]]:
    """checkData.ts QUESTIONS[].counseling 블록을 읽어 피커 스펙을 검증한다."""
    blocks = re.findall(r"counseling:\s*\{(.*?)\n\s*\},", text, re.DOTALL)
    assert len(blocks) == 3
    questions: list[dict[str, str]] = []
    for body in blocks:
        counseling: dict[str, str] = {}
        for key in ANSWER_IDS:
            match = re.search(rf'{key}:\s*"([^"]+)"', body)
            assert match is not None, f"missing {key} counseling prompt"
            counseling[key] = match.group(1)
        questions.append(counseling)
    return questions


def _pick_counseling(
    answers: list[str], questions: list[dict[str, str]]
) -> list[str]:
    """frontend/src/components/check/checkData.ts pickCounselingQuestions 와 동일."""
    picked: list[str] = []
    for level in COUNSELING_PRIORITY:
        for index, question in enumerate(questions):
            if answers[index] != level:
                continue
            prompt = question.get(level)
            if prompt:
                picked.append(prompt)
        if len(picked) >= 3:
            break
    return picked[:3]


def test_mini_check_has_three_questions_and_four_answers():
    text = CHECK_DATA.read_text(encoding="utf-8")
    assert 'id: "fit"' in text
    assert 'id: "feedback"' in text
    assert 'id: "climate"' in text
    for label in (
        "잘 되고 있어요",
        "가끔 아쉬워요",
        "개선이 필요해요",
        "잘 모르겠어요",
    ):
        assert label in text


def test_checklists_have_three_sets_of_ten():
    text = CHECKLIST_DATA.read_text(encoding="utf-8")
    assert text.count('id: "') == 3
    assert text.count("title:") >= 3 + 30
    assert "학원 등록 전 상담 체크리스트" in text
    assert "지금 다니는 학원 점검 체크리스트" in text
    assert "학원 옮기기 전 체크리스트" in text


def test_counseling_includes_well_prompts_and_new_checklist_items():
    check = CHECK_DATA.read_text(encoding="utf-8")
    lists = CHECKLIST_DATA.read_text(encoding="utf-8")
    assert "아이의 현재 수준을 어떤 근거로 판단했고" in check
    assert "숙제·테스트·오답에서 반복되는 유형은 무엇이며" in check
    assert "아이가 질문하거나 이해를 표현하기 어려울 때" in check
    assert "다음 상담에서 확인해 보세요" in check
    for title in (
        "레벨 테스트와 반 배정 기준",
        "학습 기록 공유 주기",
        "최근 한 달 반복된 어려움",
        "다음 상담 시점과 확인 기준",
        "현재 학원에서 보완 가능한 부분",
        "새 학원에 전달할 학습 정보",
    ):
        assert title in lists


def test_pick_counseling_questions_priority_and_well_prompts():
    text = CHECK_DATA.read_text(encoding="utf-8")
    priority_block = re.search(
        r"COUNSELING_PRIORITY[^=]*=\s*\[(.*?)\]",
        text,
        re.DOTALL,
    )
    assert priority_block is not None
    ids = re.findall(r'"(\w+)"', priority_block.group(1))
    assert ids == list(COUNSELING_PRIORITY)
    assert ids[-1] == "well"

    questions = _parse_counseling_prompts(text)
    assert all("well" in question for question in questions)

    all_well = _pick_counseling(["well", "well", "well"], questions)
    assert len(all_well) == 3
    assert all_well == [q["well"] for q in questions]

    mixed = _pick_counseling(["well", "sometimes", "well"], questions)
    assert mixed == [
        questions[1]["sometimes"],
        questions[0]["well"],
        questions[2]["well"],
    ]

    mixed_priority = _pick_counseling(
        ["needs_work", "unknown", "well"], questions
    )
    assert mixed_priority == [
        questions[0]["needs_work"],
        questions[1]["unknown"],
        questions[2]["well"],
    ]
    assert len(mixed_priority) == 3


def test_check_intro_copy_is_two_complete_lines():
    facts = (
        REPO_ROOT / "frontend" / "src" / "components" / "landing" / "landingFacts.ts"
    ).read_text(encoding="utf-8")
    check_page = (
        REPO_ROOT / "frontend" / "src" / "app" / "check" / "page.tsx"
    ).read_text(encoding="utf-8")
    mini = MINI_CHECK.read_text(encoding="utf-8")
    assert 'CHECK_INTRO_HEADLINE = "지금 다니는 아이의 학원,"' in facts
    assert 'CHECK_INTRO_HEADLINE_LINE2 = "1분만 점검해 보세요"' in facts
    assert "짚어 드려요" in facts
    assert "짚어\n" not in check_page
    assert 'src="/logo.png"' in mini
    assert "CHECK_INTRO_HEADLINE" in mini
    assert 'alt=""' in mini
    assert '<h1 className="text-sm font-semibold text-ink">{CHECK_CTA_LABEL}</h1>' in mini
    assert "1분 학원 점검</p>" not in mini
