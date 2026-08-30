"""상담 질문 생성 프롬프트. 학원 평가·단정 금지, JSON만 출력.

톤의 정본은 프론트 `checkData.ts` 상담 문항과 `checklistsData.ts` 체크리스트다.
few-shot은 그 문장을 그대로 쓴다 — 새 말투를 만들지 않는다.
"""

from __future__ import annotations

# checkData.ts QUESTIONS[].counseling (fit/needs_work, feedback/sometimes, climate/sometimes)
FEW_SHOT_CHECK = (
    ("수업 난이도", "지금 반의 진도와 난이도가 아이 수준과 맞는지, 최근 수업에서 어떻게 판단하고 계신가요?"),
    ("숙제·오답", "숙제와 테스트 결과를 학부모가 어떤 방식으로, 얼마나 자주 확인할 수 있나요?"),
    ("분위기", "아이가 수업 시간에 질문하거나 어려움을 말하기 편한 분위기인가요?"),
)

# checklistsData.ts CHECKLISTS before-enroll items
FEW_SHOT_CHECKLIST = (
    ("학습 상황 진단과 수업 적합도", "입학 전에 수준을 어떻게 진단하고, 반은 어떻게 정하나요?"),
    ("보강·보충 체계", "결석이나 이해 부족이 있을 때 보강·클리닉은 어떻게 되나요?"),
)

_FEW_SHOT_LINES = "\n".join(
    f'- topic: {topic} / prompt: {prompt}'
    for topic, prompt in (*FEW_SHOT_CHECK, *FEW_SHOT_CHECKLIST)
)

SYSTEM_PROMPT = f"""너는 하남 미사 학부모가 학원 상담에서 그대로 읽을 수 있는 확인 질문을 만든다.

규칙:
- 학원을 좋다/나쁘다고 판정하지 않는다. 추천·별점·순위·"이 학원은 맞습니다" 금지.
- 확인되지 않은 사실을 단정하지 않는다. "이 학원은 ~합니다" 금지.
- 질문은 학부모가 상담 때 소리 내 읽을 한 문장이다. checkData/체크리스트와 같은 말투(…나요?).
- 출력은 JSON 객체만. 설명·마크다운·코드펜스 금지.
- 형식: {{"questions":[{{"topic":"짧은 주제","prompt":"질문 한 문장"}}]}}
- 질문은 3~5개. topic와 prompt는 비우지 않는다.

좋은 질문 예:
{_FEW_SHOT_LINES}
"""


def build_user_message(
    *,
    grade: str,
    subject: str,
    school: str,
    current_academy: str,
    style_tags: list[str],
    concern: str,
    intent: str,
) -> str:
    tags = ", ".join(style_tags) if style_tags else "(없음)"
    academy = current_academy.strip() or "(알아보는 중 — 현재 학원 없음)"
    school_line = school.strip() or "(미입력)"
    intent_hint = (
        "새 학원을 찾고 싶어 하므로 비교·전환 시 확인할 질문을 포함하라. 학원을 고르거나 평가하지 마라."
        if intent == "find_new_academy"
        else "현재 학원 상담용 질문에 집중하라. 학원 추천은 하지 마라."
    )
    return (
        f"학년: {grade}\n"
        f"과목: {subject}\n"
        f"학교: {school_line}\n"
        f"현재 학원: {academy}\n"
        f"학습 스타일: {tags}\n"
        f"걱정·원하는 점: {concern}\n"
        f"의도: {intent}\n"
        f"{intent_hint}\n"
        "JSON만 출력하라.\n"
    )
