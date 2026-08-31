"""상담 질문 생성. LLM JSON 파싱 실패 시 체크리스트 fallback.

학원 사실·ORM을 쓰지 않는다. LLM은 `get_llm_provider` 포트만 탄다.
"""

from __future__ import annotations

import json
import logging
import re

from app.prompts.consultation import SYSTEM_PROMPT, build_user_message
from app.providers.factory import get_llm_provider
from app.schemas.consultation import (
    ConsultationQuestion,
    ConsultationRequest,
    ConsultationResponse,
)

logger = logging.getLogger(__name__)

DISCLAIMER = "학원 평가가 아닌 상담 확인용 질문입니다."

# checklistsData.ts CHECKLISTS id=before-enroll (앞 5문항)
FALLBACK_BEFORE_ENROLL = [
    ConsultationQuestion(
        topic="강사와 아이와의 관계",
        prompt="이 수업을 담당할 강사는 누구이고, 아이와 어떻게 맞춰 가나요?",
    ),
    ConsultationQuestion(
        topic="학습 상황 진단과 수업 적합도",
        prompt="입학 전에 수준을 어떻게 진단하고, 반은 어떻게 정하나요?",
    ),
    ConsultationQuestion(
        topic="숙제 확인과 오답 피드백",
        prompt="숙제는 누가, 어떻게 확인하고 오답은 어떻게 다루나요?",
    ),
    ConsultationQuestion(
        topic="테스트·학습 기록 관리",
        prompt="테스트 주기와 결과를 학부모에게 어떻게 공유하나요?",
    ),
    ConsultationQuestion(
        topic="보강·보충 체계",
        prompt="결석이나 이해 부족이 있을 때 보강·클리닉은 어떻게 되나요?",
    ),
]

# checkData.ts counseling (needs_work / sometimes / unknown)
FALLBACK_CURRENT = [
    ConsultationQuestion(
        topic="학습 상황 진단과 수업 적합도",
        prompt="지금 반의 진도와 난이도가 아이 수준과 맞는지, 최근 수업에서 어떻게 판단하고 계신가요?",
    ),
    ConsultationQuestion(
        topic="숙제 확인과 오답 피드백",
        prompt="오답이 반복될 때 어떤 피드백과 보충을 하시나요?",
    ),
    ConsultationQuestion(
        topic="수업 분위기와 학습 문화",
        prompt="아이가 질문하거나 이해를 표현하기 어려울 때, 어떤 방식으로 확인하고 돕나요?",
    ),
    ConsultationQuestion(
        topic="테스트·학습 기록 관리",
        prompt="숙제와 테스트 결과를 학부모가 어떤 방식으로, 얼마나 자주 확인할 수 있나요?",
    ),
    ConsultationQuestion(
        topic="학부모와 실제 담당 강사의 소통",
        prompt="담당 강사와 학부모가 아이의 수업 적응·또래 관계를 어떻게 공유하나요?",
    ),
]

# checklistsData.ts CHECKLISTS id=before-switch
FALLBACK_BEFORE_SWITCH = [
    ConsultationQuestion(
        topic="현재 학원에서 보완 가능한 부분",
        prompt="옮기기 전에 현재 학원에서 보완할 수 있는 방법을 구체적으로 물어봤나요?",
    ),
    ConsultationQuestion(
        topic="새 학원에 전달할 학습 정보",
        prompt="새 학원에 전달할 현재 진도·반복 오답·목표를 정리했나요?",
    ),
    ConsultationQuestion(
        topic="학습 상황 진단과 수업 적합도",
        prompt="지금 수업이 너무 쉽거나 어려운 이유를 학원이 설명했나요?",
    ),
    ConsultationQuestion(
        topic="보강·보충 체계",
        prompt="보강이 없는 것이 옮기는 이유라면, 다음 학원에는 어떤 보충이 필요한가요?",
    ),
    ConsultationQuestion(
        topic="장기 학습 계획과 성장 방향",
        prompt="옮긴 뒤 6개월 목표가 아이 기준으로 정리되어 있나요?",
    ),
]


def fallback_questions(payload: ConsultationRequest) -> list[ConsultationQuestion]:
    if payload.intent == "find_new_academy":
        return list(FALLBACK_BEFORE_SWITCH)
    if payload.current_academy.strip():
        return list(FALLBACK_CURRENT)
    return list(FALLBACK_BEFORE_ENROLL)


def _extract_json_object(text: str) -> dict | None:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, count=1, flags=re.IGNORECASE)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, re.DOTALL)
        if match is None:
            return None
        try:
            payload = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return payload if isinstance(payload, dict) else None


def _questions_from_payload(payload: dict) -> list[ConsultationQuestion] | None:
    raw = payload.get("questions")
    if not isinstance(raw, list):
        return None
    questions: list[ConsultationQuestion] = []
    for item in raw:
        if isinstance(item, str):
            prompt = item.strip()
            if not prompt:
                continue
            questions.append(ConsultationQuestion(topic="상담 확인", prompt=prompt[:300]))
        elif isinstance(item, dict):
            topic = str(item.get("topic") or item.get("title") or "").strip()
            prompt = str(item.get("prompt") or "").strip()
            if not topic or not prompt:
                continue
            questions.append(ConsultationQuestion(topic=topic[:40], prompt=prompt[:300]))
        else:
            continue
        if len(questions) >= 5:
            break
    if len(questions) < 3:
        return None
    return questions


def generate_questions(payload: ConsultationRequest) -> ConsultationResponse:
    fallback = fallback_questions(payload)
    try:
        llm = get_llm_provider()
    except Exception:
        logger.warning("get_llm_provider() 실패 — fallback 질문으로 대체", exc_info=True)
        return ConsultationResponse(
            questions=fallback,
            disclaimer=DISCLAIMER,
            model="unavailable",
            used_fallback=True,
        )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": build_user_message(
                grade=payload.grade,
                subject=payload.subject,
                school=payload.school,
                current_academy=payload.current_academy,
                style_tags=payload.style_tags,
                concern=payload.concern,
                intent=payload.intent,
            ),
        },
    ]
    try:
        raw = llm.chat(messages)
        parsed = _extract_json_object(raw)
        questions = _questions_from_payload(parsed) if parsed else None
        if questions:
            return ConsultationResponse(
                questions=questions,
                disclaimer=DISCLAIMER,
                model=type(llm).__name__,
                used_fallback=False,
            )
    except Exception:
        logger.warning("LLM 호출/파싱 실패 — fallback 질문으로 대체", exc_info=True)
    return ConsultationResponse(
        questions=fallback,
        disclaimer=DISCLAIMER,
        model=type(llm).__name__,
        used_fallback=True,
    )
