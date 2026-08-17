"""미니 점검·체크리스트 카피가 비지 않았는지 검사한다."""

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
